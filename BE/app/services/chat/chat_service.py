import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, NamedTuple, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver

from app.core.logger import get_logger

from app.schemas.llm import LLMConfig
from app.services.llm.llm_service import LLMService

from app.services.supabase.bot_repository import BotRepository
from app.services.supabase.chat_message_repository import ChatMessageRepository
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.supabase.session_repository import SessionRepository
from app.services.supabase.document_repository import DocumentRepository
from app.services.ai_model.ai_model_service import AiModelService

from app.agent.config import ChatConfigHelper
from app.agent.graph import ChatGraphBuilder
from app.agent.retrieval import ChatRetrievalHelper

from app.services.memory.memory_service import memory_service

logger = get_logger(__name__)


class MessageRole(str, Enum):
  USER = "user"
  SYSTEM = "system"
  ASSISTANT = "AI assistant"


class ChatParameters(NamedTuple):
  bot_id: str
  query: str
  tenant_id: str
  user_id: str
  session_id: Optional[str] = None
  access_token: Optional[str] = None
  quiz_mode: bool = False


@dataclass
class ChatPreparationResult:
  history: Optional[str] = None
  context: Optional[List[Document]] = None
  llm_config: Optional[LLMConfig] = None
  bot: Optional[dict] = None
  unified_query: Optional[str] = None
  error_message: Optional[str] = None
  supports_tools: bool = False


class ChatService:
  def __init__(
      self,
      bot_repo: BotRepository,
      session_repo: SessionRepository,
      llm_service: LLMService,
      message_repo: ChatMessageRepository,
      kb_repo: KnowledgeBaseRepository,
      ai_model_service: AiModelService,
      doc_repo: DocumentRepository
  ):
    self.bot_repo = bot_repo
    self.session_repo = session_repo
    self.llm_service = llm_service
    self.message_repo = message_repo
    self.kb_repo = kb_repo
    self.ai_model_service = ai_model_service
    self.doc_repo = doc_repo
    self.config_helper = ChatConfigHelper(ai_model_service)
    self.retrieval_helper = ChatRetrievalHelper(
        llm_service,
        kb_repo,
        doc_repo,
        self.config_helper
    )
    self._tool_cache = {}
    self._graph_cache = {}
    self._graph_lock = asyncio.Lock()
    self.checkpointer = MemorySaver()

  async def ask_bot(
      self,
      bot_id: str,
      query: str,
      tenant_id: str,
      user_id: str,
      session_id: str = None,
      access_token: str = None,
      stream: bool = False
  ):
    start_time = time.perf_counter()
    logger.info(
        f"[ChatService] Start {'stream' if stream else 'chat'} "
        f"session={session_id} bot={bot_id}"
    )

    try:
      # Validate and get/create session
      session_id = await self.validate_session(
          session_id,
          bot_id,
          user_id,
          tenant_id,
          access_token
      )

      # Save user message and update summary
      await self._save_user_message(session_id, query, user_id, access_token)

      # Get bot configuration
      bot, llm_config = await self.fetch_configuration(bot_id, tenant_id, access_token)
      kb_ids = [str(k) for k in (bot.get("kb_ids") or [])]

      # Prepare chat components
      graph, retrieval_config = await self._prepare_chat_components(
          bot, llm_config, session_id, tenant_id, access_token, kb_ids
      )

      # Build initial state
      initial_state = await self._build_initial_state(
          query, session_id, user_id, tenant_id, access_token,
          llm_config, retrieval_config, kb_ids
      )

      # Generate response
      response_gen = self._stream_graph_response(
          graph, initial_state, session_id, bot_id,
          bot.get("name", "AI Assistant"), access_token,
          {"configurable": {"thread_id": session_id}}
      )

      if stream:
        logger.info(
          f"[ChatService] returning generator for session={session_id}")
        return response_gen, session_id

      # Aggregate for non-streaming
      full_response = await self._aggregate_response(response_gen)

      total_time = time.perf_counter() - start_time
      logger.info(
          f"[ChatService] completed session={session_id} "
          f"{total_time:.2f}s"
      )
      return full_response, session_id

    except Exception as e:
      logger.error(f"[ChatService] error {e}", exc_info=True)
      await self._handle_chat_error(session_id, bot_id, access_token)
      raise

  async def init_model(
      self,
      bot: dict,
      llm_config: LLMConfig,
      session_id: str,
      tenant_id: str,
      access_token: str
  ):
    """Initialize or retrieve cached graph with dynamic tools."""
    kb_ids = [str(k) for k in (bot.get("kb_ids") or [])]
    dynamic_tools = await self._get_or_create_tools(session_id, bot, tenant_id, access_token, kb_ids)

    cache_key = self._build_graph_cache_key(bot, tenant_id, llm_config, kb_ids)

    async with self._graph_lock:
      if cache_key in self._graph_cache:
        return self._graph_cache[cache_key], dynamic_tools

      logger.info(f"[Graph] Building new graph {cache_key}")
      graph = await self._build_new_graph(dynamic_tools)
      self._graph_cache[cache_key] = graph
      return graph, dynamic_tools

  async def _get_or_create_tools(
      self,
      session_id: str,
      bot: dict,
      tenant_id: str,
      access_token: str,
      kb_ids: List[str]
  ):
    """Get cached tools or create new ones for knowledge bases."""
    if not kb_ids:
      return []

    return self._get_cached_tools(
        session_id,
        bot.get("id"),
        tenant_id,
        access_token,
        kb_ids
    )

  def _build_graph_cache_key(
      self,
      bot: dict,
      tenant_id: str,
      llm_config: LLMConfig,
      kb_ids: List[str]
  ):
    """Build cache key for graph instances."""
    cache_key_data = {
        "bot_id": bot.get("id"),
        "tenant_id": tenant_id,
        "model": llm_config.model,
        "kb_ids": sorted(kb_ids)
    }
    return hashlib.md5(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()

  async def _build_new_graph(self, dynamic_tools: List):
    """Build a new graph instance with the provided tools."""
    graph_builder = ChatGraphBuilder(
        self.llm_service,
        self.retrieval_helper,
        tools=dynamic_tools,
        checkpointer=self.checkpointer
    )
    return graph_builder.build_graph()

  async def validate_session(
      self,
      session_id: str,
      bot_id: str,
      user_id: str,
      tenant_id: str,
      access_token: str = None
  ) -> str:
    if session_id:
      try:
        session = await self.session_repo.get_session(
            session_id,
            access_token
        )
        if not session:
          raise ValueError("Session not found")
        if str(session.get("bot_id")) != bot_id:
          raise ValueError("Session mismatch")
        if str(session.get("user_id")) != user_id:
          raise ValueError("Session mismatch")
        return session["id"]
      except Exception:
        raise ValueError("Session not found")

    session = await self.session_repo.create_session(
        user_id,
        bot_id,
        tenant_id,
        access_token
    )

    if not session:
      raise RuntimeError("Failed to create session")

    return session["id"]

  async def fetch_configuration(
      self,
      bot_id: str,
      tenant_id: str,
      access_token: str = None
  ) -> Tuple[dict, LLMConfig]:
    bot = await self.bot_repo.get_bot(
        bot_id,
        tenant_id,
        access_token
    )

    if not bot:
      raise ValueError(f"Bot {bot_id} not found")

    llm_config = await self.config_helper.resolve_model_config(
        bot,
        access_token=access_token
    )
    return bot, llm_config

  async def load_chat_history(
      self,
      session_id: str,
      access_token: str = None,
      limit: int = 20
  ) -> List[BaseMessage]:
    db_messages = await self.message_repo.get_messages_by_session(
        session_id=session_id,
        limit=limit,
        access_token=access_token
    )

    parsed_msgs = []

    for msg in reversed(db_messages):
      role = msg.get("role")
      content = msg.get("content")

      if role == "user":
        parsed_msgs.append(HumanMessage(content=content))
      else:
        parsed_msgs.append(AIMessage(content=content))

    return parsed_msgs

  async def _save_user_message(
      self,
      session_id: str,
      content: str,
      user_id: str,
      access_token: str = None
  ):
    """Save user message to database and update session summary."""
    await self.message_repo.create_message(
        session_id=session_id,
        content=content,
        role="user",
        sender_id=user_id,
        access_token=access_token
    )
    await self._update_session_summary(session_id, content, access_token)

  async def _prepare_chat_components(
      self,
      bot: dict,
      llm_config: LLMConfig,
      session_id: str,
      tenant_id: str,
      access_token: str,
      kb_ids: List[str]
  ):
    """Prepare graph and retrieval configuration."""
    retrieval_config = self.config_helper.parse_bot_retrieval_config(bot)
    graph, _ = await self.init_model(
        bot, llm_config, session_id, tenant_id, access_token
    )
    return graph, retrieval_config

  async def _build_initial_state(
      self,
      query: str,
      session_id: str,
      user_id: str,
      tenant_id: str,
      access_token: str,
      llm_config: LLMConfig,
      retrieval_config,
      kb_ids: List[str]
  ):
    """Build the initial state for the graph."""
    graph_config = {"configurable": {"thread_id": session_id}}
    snapshot = await graph.aget_state(graph_config)
    existing_messages = (
        snapshot.values.get("messages", [])
        if snapshot.values else []
    )

    if existing_messages:
      input_messages = [HumanMessage(content=query)]
    else:
      input_messages = await self.load_chat_history(session_id, access_token)
      if not input_messages:
        input_messages = [HumanMessage(content=query)]

    return {
        "messages": input_messages,
        "context": [],
        "llm_config": llm_config,
        "retrieval_config": retrieval_config,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "access_token": access_token,
        "kb_ids": kb_ids,
        "retry_count": 0,
        "is_grounded": True,
    }

  async def _aggregate_response(self, response_gen):
    """Aggregate chunks from a streaming response."""
    full_response = ""
    async for chunk in response_gen:
      if chunk.startswith("__ERROR__:"):
        error_msg = chunk.replace("__ERROR__: ", "").replace("__ERROR__:", "")
        raise Exception(error_msg)
      if not chunk.startswith("__STATUS__:") and not chunk.startswith("__TOOL_CALL__:"):
        full_response += chunk
    return full_response

  async def _stream_graph_response(
      self,
      graph,
      initial_state,
      session_id,
      bot_id,
      bot_name,
      access_token,
      graph_config
  ):
    full_response = ""

    try:
      async for event in graph.astream_events(
          initial_state,
          version="v2",
          config=graph_config
      ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
          # Filter: Only stream content from the 'agent' node
          if event.get("metadata", {}).get("langgraph_node") == "agent":
            chunk = event["data"]["chunk"]
            if hasattr(chunk, "content") and chunk.content:
              content = chunk.content
              full_response += content
              yield content

        elif kind == "on_chain_start":
          node_name = event.get("name", "")
          if "agent" in node_name.lower():
            yield f"__STATUS__: {json.dumps({'text': '🤔 Thinking...'})}"
          elif "check_hallucination" in node_name.lower():
            yield f"__STATUS__: {json.dumps({'text': '✓ Verifying answer...'})}"

        elif kind == "on_tool_start":
          tool_name = event["name"]
          tool_call = {
              "tool": tool_name,
              "input": event.get("data", {}).get("input", {})
          }
          yield f"__TOOL_CALL__: {json.dumps(tool_call)}"

      if full_response:
        await self.message_repo.create_message(
            session_id,
            full_response,
            role=bot_name,
            sender_id=bot_id,
            access_token=access_token
        )

        await self._update_session_summary(
            session_id,
            full_response,
            access_token
        )

      if full_response:
        user_id = initial_state.get("user_id")
        if user_id:
          await memory_service.process_memory(user_id)

    except Exception as e:
      logger.error(f"[Graph Stream] {e}", exc_info=True)
      yield f"__ERROR__: {str(e)}"

  def _get_cached_tools(
      self,
      session_id: str,
      bot_id: str,
      tenant_id: str,
      access_token: str = None,
      kb_ids: List[str] = None
  ):

    cache_key_data = {
        "session_id": session_id,
        "bot_id": bot_id,
        "tenant_id": tenant_id,
        "kb_ids": sorted(kb_ids) if kb_ids else [],
        "access_token": access_token  # Include token to prevent stale auth
    }

    cache_key = hashlib.md5(
        json.dumps(cache_key_data, sort_keys=True).encode()
    ).hexdigest()

    if cache_key in self._tool_cache:
      tools, timestamp = self._tool_cache[cache_key]
      if time.time() - timestamp < 300:
        return tools

    tools = []

    if kb_ids:
      from app.agent.tools.knowledge_base import (
          ListKnowledgeBasesTool,
          SearchKnowledgeBaseTool,
          ListKnowledgeBaseDocumentsTool
      )

      list_kb_tool = ListKnowledgeBasesTool(
          kb_repo=self.kb_repo,
          kb_ids=kb_ids,
          tenant_id=tenant_id,
          access_token=access_token
      )
      tools.append(list_kb_tool)

      list_doc_tool = ListKnowledgeBaseDocumentsTool(
          retrieval_helper=self.retrieval_helper,
          tenant_id=tenant_id,
          access_token=access_token
      )
      tools.append(list_doc_tool)

      kb_tool = SearchKnowledgeBaseTool(
          retrieval_helper=self.retrieval_helper,
          tenant_id=tenant_id,
          access_token=access_token,
          retrieval_config={
              "top_k": 5,
              "score_threshold": 0.3
          },
          all_available_kb_ids=kb_ids
      )
      tools.append(kb_tool)

    self._tool_cache[cache_key] = (tools, time.time())
    return tools

  async def _handle_chat_error(
      self,
      session_id: str,
      bot_id: str,
      access_token: str
  ):
    try:
      if session_id:
        await self.message_repo.create_message(
            session_id,
            "Sorry, I encountered an error.",
            role=MessageRole.SYSTEM,
            sender_id=bot_id,
            access_token=access_token
        )
    except Exception as e:
      logger.warning(
          f"[ChatService] failed to log error {e}"
      )

  async def _update_session_summary(
      self,
      session_id: str,
      text: str,
      access_token: str = None
  ):
    summary = text[:150] + "..." if len(text) > 150 else text

    try:
      payload = {
          "summary_text": summary,
          "updated_at": datetime.utcnow().isoformat()
      }
      await self.session_repo.update_session(
          session_id,
          payload,
          access_token
      )
    except Exception:
      pass
