import asyncio
import json
from app.core.logger import get_logger
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Any, Union, NamedTuple
from abc import ABC, abstractmethod

from pydantic import BaseModel

# Langchain imports
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langgraph.checkpoint.memory import MemorySaver

# Local imports - Core
from app.config.config import settings
from app.core.factory import get_vector_store
from app.core.logger import get_logger


# Local imports - LLM Services
from app.schemas.llm import LLMConfig
from app.services.llm.llm_service import LLMService
from app.services.llm.prompt_templates import (
    QUIZ_PROMPT,
    MARKDOWN_INSTRUCTION_PROMPT,
    ROUTER_SYSTEM_PROMPT,
    EDUCATIONAL_GUARDRAIL_PROMPT,
)

# Local imports - Tools
from app.schemas.quiz import QuizOutput
from app.agent.tools.knowledge_base import SearchKnowledgeBaseTool, ListKnowledgeBasesTool

# Local imports - Repositories
from app.services.supabase.bot_repository import BotRepository
from app.services.supabase.chat_message_repository import ChatMessageRepository
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.supabase.session_repository import SessionRepository
from app.services.ai_model.ai_model_service import AiModelService

# Local imports - Chat Helpers
from app.agent.config import ChatConfigHelper
from app.rag.retrieval import ChatRetrievalHelper
from app.agent.graph import ChatGraphBuilder

logger = get_logger(__name__)


class MessageRole(str, Enum):
  USER = "user"
  SYSTEM = "system"
  ASSISTANT = "AI assistant"


class ChatParameters(NamedTuple):
  """Parameters for chat operations."""
  bot_id: str
  query: str
  tenant_id: str
  user_id: str
  session_id: Optional[str] = None
  access_token: Optional[str] = None
  quiz_mode: bool = False


@dataclass
class ChatPreparationResult:
  """Result of chat preparation containing all necessary data for chat execution."""
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
      tool_service: Any = None
  ):
    self.bot_repo = bot_repo
    self.session_repo = session_repo
    self.llm_service = llm_service
    self.message_repo = message_repo
    self.kb_repo = kb_repo
    self.ai_model_service = ai_model_service
    self.tool_service = tool_service

    # Initialize helpers
    self.config_helper = ChatConfigHelper(ai_model_service)
    self.retrieval_helper = ChatRetrievalHelper(
      llm_service, kb_repo, self.config_helper)

    # Tool cache to avoid reinitialization
    self._tool_cache = {}

    # Initialize MemorySaver for state persistence
    self.checkpointer = MemorySaver()

  # ----------------------------------------------------------------------
  # MAIN PUBLIC METHOD
  # ----------------------------------------------------------------------

  async def ask_bot(
      self,
      bot_id: str,
      query: str,
      tenant_id: str,
      user_id: str,
      session_id: str = None,
      access_token: str = None,
      quiz_mode: bool = False,
      stream: bool = False
  ):
    """
    Unified chat method that supports both streaming and non-streaming modes.

    Args:
        stream: If True, returns AsyncGenerator for streaming. If False, returns complete response.

    Returns:
        If stream=True: Tuple[AsyncGenerator[str, None], str] (generator, session_id)
        If stream=False: Tuple[str, str] (response, session_id)
    """
    start_time = time.perf_counter()
    logger.info(
      f"[ChatService]: Starting chat {'stream' if stream else 'request'} for session {session_id} (Bot: {bot_id}, User: {user_id})")

    try:
      # 1. Validate Session
      session_id = await self.validate_session(session_id, bot_id, user_id, tenant_id, access_token)

      # 2. Save User Query & Update Summary
      await self.message_repo.create_message(
          session_id=session_id,
          content=query,
          role="user",
          sender_id=user_id,
          access_token=access_token
      )
      await self._update_session_summary(session_id, query, access_token)

      # 3. Fetch Configuration
      try:
        bot, llm_config = await self.fetch_configuration(bot_id, tenant_id, access_token)
      except ValueError as e:
        if stream:
          async def error_generator(): yield str(e)
          return error_generator(), session_id
        else:
          return str(e), session_id

      # 4. Init Model (Graph)
      graph, dynamic_tools = await self.init_model(bot, llm_config, session_id, tenant_id, access_token, quiz_mode)

      # 5. Load History (Context)
      graph_config = {"configurable": {"thread_id": session_id}}
      snapshot = await graph.aget_state(graph_config)
      existing_messages = snapshot.values.get(
        "messages", []) if snapshot.values else []

      if existing_messages:
        logger.info(
          f"[{'Stream' if stream else 'Graph'}]: Warm Start. Appending new query.")
        input_messages = [HumanMessage(content=query)]
      else:
        logger.info(
          f"[{'Stream' if stream else 'Graph'}]: Cold Start. Hydrating from DB.")
        input_messages = await self.load_chat_history(session_id, access_token)
        if not input_messages:
          input_messages = [HumanMessage(content=query)]

      # 6. Prepare Initial State
      supports_tools = len(dynamic_tools) > 0 or \
          self.llm_service.supports_tools(
          llm_config.provider,
          llm_config.model,
          llm_config.api_key,
          llm_config.base_url
        )

      context = []
      unified_query = query

      if not supports_tools:
        # Pre-Retrieval RAG: Rewrite, Decompose, Search
        unified_query, context = await self.retrieval_helper.pre_retrieval_rag(
            input_messages, query, bot, llm_config, tenant_id, access_token
        )

      initial_state = {
          "messages": input_messages,
          "context": context,
          "query": unified_query,
          "llm_config": llm_config,
          "session_id": session_id,
          "bot_id": bot_id,
          "user_id": user_id,
          "access_token": access_token,
          "retry_count": 0,
          "is_grounded": True,
          "supports_tools": supports_tools,
          "quiz_mode": quiz_mode
      }

      # 7. Execute Graph (Stream or Batch)
      if stream:
        # Return streaming generator
        bot_name = bot.get("name", "AI Assistant")
        return self._stream_graph_response(
            graph=graph,
            initial_state=initial_state,
            session_id=session_id,
            bot_id=bot_id,
            bot_name=bot_name,
            access_token=access_token,
            graph_config=graph_config
        ), session_id
      else:
        # Collect all chunks from stream and return complete response
        bot_name = bot.get("name", "AI Assistant")
        full_response = ""

        async for chunk in self._stream_graph_response(
            graph=graph,
            initial_state=initial_state,
            session_id=session_id,
            bot_id=bot_id,
            bot_name=bot_name,
            access_token=access_token,
            graph_config=graph_config,
            save_to_db=False  # We'll save after collecting all chunks
        ):
          # Filter out status messages
          if not chunk.startswith("__STATUS__:"):
            full_response += chunk

        # Save complete response to DB
        if full_response:
          await self.message_repo.create_message(
              session_id,
              full_response,
              role=bot_name,
              sender_id=bot_id,
              access_token=access_token
          )
          await self._update_session_summary(session_id, full_response, access_token)

        total_time = time.perf_counter() - start_time
        logger.info(
          f"[ChatService]: Chat request completed for session {session_id} in {total_time:.2f}s")
        return full_response, session_id

    except Exception as e:
      logger.error(
        f"[ChatService]: Error generating chat response: {e}", exc_info=True)
      await self._handle_chat_error(session_id, bot_id, access_token, str(e))
      raise e

  # ----------------------------------------------------------------------
  # HELPER METHODS
  # ----------------------------------------------------------------------

  async def validate_session(self, session_id: str, bot_id: str, user_id: str, tenant_id: str, access_token: str = None) -> str:
    """
    Validates an existing session or creates a new one.
    Returns the valid session_id.
    """
    if session_id:
      try:
        session = await self.session_repo.get_session(session_id, access_token)
        if session:
          # Verify Session Ownership
          s_bot_id = str(session.get("bot_id"))
          s_user_id = str(session.get("user_id"))

          if s_bot_id != bot_id:
            logger.warning(
                f"[ChatService]: Session {session_id} mismatch: Bot {s_bot_id} != {bot_id}"
            )
            # Generic error to avoid leaking existence
            raise ValueError("Session not found")

          elif s_user_id != user_id:
            logger.warning(
                f"[ChatService]: Session {session_id} mismatch: User {s_user_id} != {user_id}"
            )
            raise ValueError("Session not found")

          return session["id"]
        else:
          # Session ID provided but not found in DB
          raise ValueError("Session not found")

      except ValueError:
        raise
      except Exception as e:
        logger.error(
          f"[ChatService]: Error checking session {session_id}: {e}")
        raise ValueError("Session not found")

    # Create new session if passed session_id was None/Empty
    session = await self.session_repo.create_session(user_id, bot_id, tenant_id, access_token)
    if not session:
      raise RuntimeError("Failed to create new session.")

    return session["id"]

  async def fetch_configuration(self, bot_id: str, tenant_id: str, access_token: str = None) -> Tuple[dict, LLMConfig]:
    """
    Fetches the Bot configuration and resolves the LLM configuration.
    """
    # 1. Get Bot
    bot = await self.bot_repo.get_bot(bot_id, tenant_id, access_token)
    if not bot:
      raise ValueError(f"Bot {bot_id} not found")

    # 2. Resolve Model Config
    llm_config = await self.config_helper.resolve_model_config(bot, access_token=access_token)

    return bot, llm_config

  async def init_model(self, bot: dict, llm_config: LLMConfig, session_id: str, tenant_id: str, access_token: str, quiz_mode: bool) -> Tuple[Any, List[Any]]:
    """
    Initializes the Chat Graph and determines the tools to use.
    Returns (graph, tools).
    """
    # 1. Determine Tool Support
    supports_tools = self.llm_service.supports_tools(
        llm_config.provider,
        llm_config.model,
        llm_config.api_key,
        llm_config.base_url
    )

    # 2. Get Tools if supported
    dynamic_tools = []
    if supports_tools and bot:
      kb_ids = [str(k) for k in (bot.get("kb_ids") or [])]
      if kb_ids:
        dynamic_tools = self._get_cached_tools(
            session_id=session_id,
            bot_id=bot.get("id"),
            tenant_id=tenant_id,
            access_token=access_token,
            kb_ids=kb_ids
        )

    # 3. Build Graph
    graph_builder = ChatGraphBuilder(
        self.llm_service,
        self.retrieval_helper,
        tools=dynamic_tools,
        checkpointer=self.checkpointer
    )
    graph = graph_builder.build_graph()

    return graph, dynamic_tools

  async def load_chat_history(self, session_id: str, access_token: str = None, limit: int = 20) -> List[BaseMessage]:
    """
    Fetches messages from the repository and converts them to LangChain message objects.
    """
    return await self._load_history_messages(session_id, access_token, limit)

  async def _stream_graph_response(
      self, graph, initial_state, session_id, bot_id, bot_name, access_token, graph_config, save_to_db: bool = True
  ):
    """Stream events from LangGraph."""
    full_response = ""
    buffer = ""
    in_tool_block = False

    try:
      async for event in graph.astream_events(initial_state, version="v2", config=graph_config):
        kind = event["event"]

        # Capture generated tokens
        if kind == "on_chat_model_stream":
          chunk = event["data"]["chunk"]
          if hasattr(chunk, 'content') and chunk.content:
            content = chunk.content
            # DO NOT capture 'is_grounded' status messages if any
            buffer += content

            # Logic to hide ```tool_call ... ``` (reused from old strategy)
            while True:
              if not in_tool_block:
                start_idx = buffer.find("```tool_call")
                if start_idx != -1:
                  if start_idx > 0:
                    yield buffer[:start_idx]
                    full_response += buffer[:start_idx]
                  buffer = buffer[start_idx:]
                  in_tool_block = True
                else:
                  safe_to_yield = max(0, len(buffer) - 13)
                  if safe_to_yield > 0:
                    chunk_to_yield = buffer[:safe_to_yield]
                    yield chunk_to_yield
                    full_response += chunk_to_yield
                    buffer = buffer[safe_to_yield:]
                  break
              else:
                end_idx = buffer.find("```", 1)
                if end_idx != -1:
                  buffer = buffer[end_idx + 3:]
                  in_tool_block = False
                else:
                  break

        # Capture Graph Node Events for UI Status
        elif kind == "on_chain_start":
          node_name = event.get('name', '')
          # Emit status for major graph nodes
          if 'agent' in node_name.lower() or 'run_agent' in node_name.lower():
            yield f"__STATUS__: {json.dumps({'text': '🤔 Thinking...'})}"
          elif 'check_hallucination' in node_name.lower():
            yield f"__STATUS__: {json.dumps({'text': '✓ Verifying response...'})}"

        # Capture Tool Events for UI Status
        elif kind == "on_tool_start":
          tool_name = event['name']
          tool_input = event.get('data', {}).get('input', {})

          # Emit tool call details for frontend
          tool_call = {
              "tool": tool_name,
              "input": tool_input
          }
          yield f"__TOOL_CALL__: {json.dumps(tool_call)}"

          # Emit status message
          status_map = {
              "search_knowledge_base": "🔍 Searching knowledge bases...",
              "list_knowledge_bases": "📋 Listing knowledge bases...",
              "QuizOutput": "📝 Generating quiz...",
              "check_hallucination": "✓ Checking answer key..."
          }
          # Only show status for known tools or significant actions
          if tool_name in status_map:
            yield f"__STATUS__: {json.dumps({'text': status_map[tool_name]})}"

      # Yield remaining buffer
      if buffer and not in_tool_block:
        yield buffer
        full_response += buffer

      # Save to DB only if requested
      if save_to_db and full_response:
        await self.message_repo.create_message(
            session_id, full_response, role=bot_name, sender_id=bot_id, access_token=access_token
        )
        await self._update_session_summary(session_id, full_response, access_token)

    except Exception as e:
      logger.error(f"[Graph Stream]: Error: {e}", exc_info=True)
      yield f"Error: {e}"

  # ----------------------------------------------------------------------
  # INTERNAL HELPERS
  # ----------------------------------------------------------------------

  def _get_cached_tools(self, session_id: str, bot_id: str, tenant_id: str,
                        access_token: str = None, kb_ids: List[str] = None) -> List[Any]:
    """Get cached tools for a session, initializing if necessary."""
    import hashlib
    import json

    # Create cache key based on session and configuration
    cache_key_data = {
        "session_id": session_id,
        "bot_id": bot_id,
        "tenant_id": tenant_id,
        "kb_ids": sorted(kb_ids) if kb_ids else [],
    }

    cache_key = hashlib.md5(json.dumps(
      cache_key_data, sort_keys=True).encode()).hexdigest()

    # Check if tools are already cached
    if cache_key in self._tool_cache:
      cached_tools, timestamp = self._tool_cache[cache_key]
      # Cache for 5 minutes
      if time.time() - timestamp < 300:
        return cached_tools

    # Initialize tools
    tools = []

    # Add static tools from tool_service
    if self.tool_service:
      tools.extend(self.tool_service.get_tools())

    # Add dynamic tools based on bot configuration
    if kb_ids:
      from app.agent.tools.knowledge_base import ListKnowledgeBasesTool, SearchKnowledgeBaseTool

      # List KB Tool
      list_kb_tool = ListKnowledgeBasesTool(
          kb_repo=self.kb_repo,
          kb_ids=kb_ids,
          tenant_id=tenant_id,
          access_token=access_token
      )
      tools.append(list_kb_tool)

      # Search KB Tool - only add if we have KBs configured
      if kb_ids:
        # Get retrieval config for the bot
        # Note: This would need to be passed in or fetched separately
        retrieval_config_dict = {
            "top_k": 5,
            "score_threshold": 0.3,
            "rerank": False,
            "rerank_model": None
        }

        kb_tool = SearchKnowledgeBaseTool(
            retrieval_helper=self.retrieval_helper,
            tenant_id=tenant_id,
            access_token=access_token,
            retrieval_config=retrieval_config_dict,
            all_available_kb_ids=kb_ids
        )
        tools.append(kb_tool)

    # Cache the tools
    self._tool_cache[cache_key] = (tools, time.time())

    return tools

  async def _handle_chat_error(self, session_id: str, bot_id: str, access_token: str, error_message: str):
    """Handle chat errors by logging them and attempting to save error message to chat history."""
    try:
      # Best effort to log error to user chat
      if session_id:
        await self.message_repo.create_message(
            session_id,
            "Sorry, I encountered an error providing a response.",
            role=MessageRole.SYSTEM,
            sender_id=bot_id,
            access_token=access_token
        )
    except Exception as e:
      logger.warning(
        f"[ChatService]: Failed to save error message to chat history: {e}")

  async def _update_session_summary(self, session_id: str, text: str, access_token: str = None):
    summary = text[:150] + "..." if len(text) > 150 else text
    try:
      # Update summary AND updated_at to ensure it bubbles to top
      payload = {
          "summary_text": summary,
          "updated_at": datetime.utcnow().isoformat()
      }
      await self.session_repo.update_session(session_id, payload, access_token)
    except Exception as e:
      pass

  async def _load_history_messages(self, session_id: str, access_token: str = None, limit: int = 20) -> List[BaseMessage]:
    """
    Fetches messages from the repository and converts them to LangChain message objects.
    """
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
