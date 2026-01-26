import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Any, Union, NamedTuple

from pydantic import BaseModel

# Langchain imports
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory

# Local imports - Core
from app.config.config import settings
from app.core.factory import get_vector_store
from app.core.logger import get_logger
from app.services.chat.history import RepositoryChatMessageHistory

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
from app.services.tools.knowledge_base_tool import KnowledgeBaseTool
from app.services.tools.list_knowledge_bases_tool import ListKnowledgeBasesTool

# Local imports - Repositories
from app.services.supabase.bot_repository import BotRepository
from app.services.supabase.chat_message_repository import ChatMessageRepository
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.supabase.session_repository import SessionRepository
from app.services.ai_model.ai_model_service import AiModelService

# Local imports - Chat Helpers
from .config import ChatConfigHelper
from .retrieval import ChatRetrievalHelper

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
      # Annotated as Any to avoid circular import issues if type checking is strict, or import ToolService
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

  # ----------------------------------------------------------------------
  # CHAT INTERFACE
  # ----------------------------------------------------------------------
  async def ask_bot(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None, access_token: str = None, quiz_mode: bool = False
  ) -> Tuple[Optional[str], Optional[str]]:
    start_time = time.perf_counter()
    logger.info(
      f"[ChatService]: Starting chat request for session {session_id} (Bot: {bot_id}, User: {user_id})")
    try:
      # Prepare chat execution with common logic
      session_id, chat_result = await self._initialize_chat(
          bot_id, query, tenant_id, user_id, session_id, access_token, quiz_mode
      )

      bot_name = chat_result.bot.get(
        "name", "AI Assistant") if chat_result.bot else "AI Assistant"

      if chat_result.error_message:
        return chat_result.error_message, session_id

      # Should be unreachable if error_msg is None, but for type safety
      if not chat_result.llm_config:
        return "Internal Configuration Error", session_id

      start_llm = time.perf_counter()
      logger.info(
        f"[LLM Call]: Starting final generation... (Model: {chat_result.llm_config.model})")

      response = await self._call_llm(
          query=chat_result.unified_query or query,
          history=chat_result.history,
          context=chat_result.context,
          config=chat_result.llm_config,
          session_id=session_id,
          access_token=access_token,
          streaming=False,
          quiz_mode=quiz_mode
      )
      logger.info(
        f"[LLM Call]: Finished. Duration: {time.perf_counter() - start_llm:.2f}s")
      # 9. Save Response (convert QuizOutput to JSON if needed)
      if quiz_mode and isinstance(response, QuizOutput):
        # Extract just the quiz array, not the wrapper object
        quiz_list = [q.model_dump() for q in response.quiz]
        response_content = json.dumps(quiz_list)
      else:
        response_content = str(response)

      await self.message_repo.create_message(
          session_id,
          response_content,
          role=bot_name,
          sender_id=bot_id,
          access_token=access_token
      )

      # Update Session Summary with Bot Response
      await self._update_session_summary(session_id, response_content, access_token)

      total_time = time.perf_counter() - start_time
      logger.info(
        f"[ChatService]: Chat request completed for session {session_id} in {total_time:.2f}s")
      return response, session_id

    except Exception as e:
      logger.error(
        f"[ChatService]: Error generating chat response: {e}", exc_info=True)
      await self._handle_chat_error(session_id, bot_id, access_token, str(e))
      raise e

  async def ask_bot_stream(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None, access_token: str = None, quiz_mode: bool = False
  ):
    start_time = time.perf_counter()
    logger.info(
      f"[ChatService]: Starting chat stream handling for session {session_id}")
    try:
      # Prepare chat execution with common logic
      session_id, chat_result = await self._initialize_chat(
          bot_id, query, tenant_id, user_id, session_id, access_token, quiz_mode
      )

      bot_name = chat_result.bot.get(
        "name", "AI Assistant") if chat_result.bot else "AI Assistant"

      if chat_result.error_message:
        async def error_generator():
          yield chat_result.error_message
        return error_generator(), session_id

      if not chat_result.llm_config:
        async def config_error_generator():
          yield "Internal Configuration Error"
        return config_error_generator(), session_id

      # Init Tools (only if model supports them - using cached result from _prepare_chat_execution)
      dynamic_tools = []

      if chat_result.supports_tools and chat_result.bot:
        kb_ids = [str(k) for k in (chat_result.bot.get("kb_ids") or [])]
        if kb_ids:
          # Parse Bot's retrieval config
          retrieval_config = self._parse_bot_retrieval_config(chat_result.bot)
          retrieval_config_dict = {
              "top_k": retrieval_config.top_k,
              "score_threshold": retrieval_config.score_threshold,
              "rerank": retrieval_config.rerank,
              "rerank_model": retrieval_config.rerank_model
          }

          # List KB Tool
          list_kb_tool = ListKnowledgeBasesTool(
              kb_repo=self.kb_repo,
              kb_ids=kb_ids,
              tenant_id=tenant_id,
              access_token=access_token
          )
          dynamic_tools.append(list_kb_tool)

          # Search KB Tool (no longer initialized with kb_ids, Agent passes them)
          kb_tool = KnowledgeBaseTool(
              llm_service=self.llm_service,
              kb_repo=self.kb_repo,
              vector_repo=get_vector_store(),
              tenant_id=tenant_id,
              access_token=access_token,
              retrieval_config=retrieval_config_dict,
              all_available_kb_ids=kb_ids
          )
          dynamic_tools.append(kb_tool)

      # Quiz Tool (only if model supports tools)
      if chat_result.supports_tools:
        dynamic_tools.append(QuizOutput)

        # Force Quiz Tool if Quiz Mode
        if quiz_mode:
          pass
        elif quiz_mode:
          logger.warning(
            "[ChatService]: Quiz mode with non-tool model: using fallback quiz generation")

      # Create generator
      return self._stream_response_wrapper(
          query=chat_result.unified_query or query,
          history=chat_result.history,
          documents=chat_result.context,
          config=chat_result.llm_config,
          session_id=session_id,
          bot_id=bot_id,
          bot_name=bot_name,
          access_token=access_token,
          dynamic_tools=dynamic_tools
      ), session_id

    except Exception as e:
      logger.error(
        f"[ChatService]: Error initializing chat stream: {e}", exc_info=True)
      await self._handle_chat_error(session_id, bot_id, access_token, str(e))
      raise e

  async def _stream_response_wrapper(
      self,
      query: str,
      history: str,
      documents: List[Document],
      config: Any,
      session_id: str,
      bot_id: str,
      bot_name: str,
      access_token: str,
      dynamic_tools: List[Any] = None
  ):
    """
    Internal helper to handle the streaming, aggregation, and final logging.
    """
    start_time = time.perf_counter()
    # Stream from LLM via Utility
    full_response = ""
    try:
      logger.info(f"[LLM Stream]: Starting... (Model: {config.model})")
      # Use the unified LLM interaction helper
      stream = await self._call_llm(
          query=query,
          history=history,
          context=documents,
          config=config,
          session_id=session_id,
          access_token=access_token,
          streaming=True,
          dynamic_tools=dynamic_tools
      )

      async for chunk in stream:
        if chunk is not None:
          # Extract text if it's a LangChain chunk object
          content = chunk.content if hasattr(chunk, 'content') else str(chunk)

          if content:
            yield content
            full_response += content
        else:
          logger.debug("Received None/Empty chunk from stream")

      if not full_response:
        logger.warning(
            f"[ChatService]: Stream completed with empty response for session {session_id}")

      # Only start saving to DB after stream completes successfully
      await self.message_repo.create_message(
          session_id,
          full_response,
          role=bot_name,
          sender_id=bot_id,
          access_token=access_token
      )

      # Update Session Summary with Bot Response (Streaming)
      await self._update_session_summary(session_id, full_response, access_token)

    except asyncio.CancelledError:
      if full_response:
        async def _save_cleanup():
          try:
            await self.message_repo.create_message(
                session_id,
                full_response,
                role=bot_name,
                sender_id=bot_id,
                access_token=access_token
            )
            await self._update_session_summary(session_id, full_response, access_token)
          except Exception as inner_e:
            logger.error(
              f"[ChatService]: Failed to save partial response on cancellation: {inner_e}")

        # Protect the cleanup task from being cancelled immediately
        cleanup_task = asyncio.create_task(_save_cleanup())
        try:
          await asyncio.shield(cleanup_task)
        except asyncio.CancelledError:
          raise

    except Exception as e:
      logger.error(
        f"[ChatService]: Error during streaming: {e}", exc_info=True)
      msg = f"Error during streaming: {str(e)}"
      try:
        await self.message_repo.create_message(
            session_id,
            msg,
            role=MessageRole.SYSTEM,
            sender_id=bot_id,
            access_token=access_token
        )
      except Exception:
        pass
      yield f"Error: {str(e)}"

    total_time = time.perf_counter() - start_time
    logger.info(
      f"[ChatService]: Chat stream completed for session {session_id} in {total_time:.2f}s")

  # ----------------------------------------------------------------------
  # LLM INTERACTION
  # ----------------------------------------------------------------------
  async def _call_llm(
      self,
      query: str,
      history: str,
      context: Union[str, List[Document]],
      config: LLMConfig,
      session_id: str,
      access_token: str = None,
      streaming: bool = False,
      quiz_mode: bool = False,
      dynamic_tools: List[Any] = None,
      supports_tools: bool = False
  ):
    # Handle legacy context string or new Document list
    if isinstance(context, list):
      context_str = "\n\n".join([d.page_content for d in context])
    else:
      context_str = context

    # Use configured system prompt + Educational Guardrail
    base_instruction = config.system_prompt or "You are a helpful AI assistant."

    if quiz_mode:
      base_instruction += f"\n\n{QUIZ_PROMPT}\n\nSPECIAL INSTRUCTION: You have access to Knowledge Base tools. If the user asks for a quiz on a specific topic (e.g., 'lecture 3'), USE THE SEARCH TOOL FIRST to retrieve the content. Then, generate the quiz using the 'QuizOutput' tool. Do NOT return raw text; you MUST call the QuizOutput tool to submit your answer."

    instruction = f"{EDUCATIONAL_GUARDRAIL_PROMPT}\n\n{base_instruction}"

    # Resolve provider and model from config
    provider = config.provider
    model = config.model
    if "/" in config.model and provider != "ollama":
      provider, model = config.model.split("/", 1)

    # ----------------------------------------------------------------------
    # AGENT / LLM EXECUTION
    # ----------------------------------------------------------------------
    tools = []
    if self.tool_service:
      tools.extend(self.tool_service.get_tools())

    if dynamic_tools:
      tools.extend(dynamic_tools)

    # If we have tools AND model supports them (from cached check), use the Agent Graph
    if tools and not quiz_mode and supports_tools:
      agent_graph = self.llm_service.get_agent(config, instruction, tools)

      # Define history factory
      def get_session_history(sid: str):
        return RepositoryChatMessageHistory(sid, self.message_repo, access_token)

      # StateGraph Integration with RunnableWithMessageHistory
      # 1. Chain: Adapter to format inputs for StateGraph
      def merge_history_to_messages(input_dict):
        return {
            "messages": input_dict["chat_history"] + [HumanMessage(content=input_dict["input"])]
        }

      graph_chain = (
          RunnablePassthrough.assign(chat_history=lambda x: x["chat_history"])
          | merge_history_to_messages
          | agent_graph
      )

      # 2. Wrap Adapter Chain with History
      agent_with_history = RunnableWithMessageHistory(
          graph_chain,
          get_session_history,
          input_messages_key="input",
          history_messages_key="chat_history",
      )

      # Prepare Input
      user_msg_content = f"Context from Knowledge Base:\n{context_str}\n\nUser Question:\n{query}"

      # --- STREAMING ---
      if streaming:
        async def tool_stream_generator():
          accumulated_content = ""
          try:
            # Stream events from the WRAPPED agent
            async for event in agent_with_history.astream_events(
                {"input": user_msg_content},
                config={"configurable": {"session_id": session_id}},
                version="v2"
            ):
              kind = event["event"]
              if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, 'content') and chunk.content:
                  accumulated_content += chunk.content
                  yield chunk.content
              elif kind == "on_tool_start":
                tool_input = event['data'].get('input')
                logger.info(
                  f"[Tool]: Executing '{event['name']}' with input: {tool_input}")
              elif kind == "on_tool_end":
                tool_output = event['data'].get('output')
                output_str = str(tool_output)
                if len(output_str) > 200:
                  output_str = output_str[:200] + "... (truncated)"
                logger.info(
                  f"[Tool]: Finished '{event['name']}' -> Output: {output_str}")
          except Exception as e:
            logger.error(
              f"[ChatService]: Agent Graph Streaming Failed: {e}", exc_info=True)
            yield f"Error: {e}"

        return tool_stream_generator()

      # --- NON-STREAMING ---
      try:
        result = await agent_with_history.ainvoke(
            {"input": user_msg_content},
            config={"configurable": {"session_id": session_id}}
        )

        # Result is final state dict
        final_messages = result.get("messages", [])
        if final_messages and isinstance(final_messages[-1], (str, dict)):
          return str(final_messages[-1])
        if final_messages:
          return final_messages[-1].content
        return "No response generated."
      except Exception as e:
        logger.error(
          f"[ChatService]: Agent Graph Execution Failed: {e}", exc_info=True)
        raise e

    # Fallback to Standard Chain (No Tools or Quiz Mode)
    if quiz_mode:
      # Use centralized quiz chain (standardized Structured Output)
      chain = self.llm_service.get_quiz_chain(config, QUIZ_PROMPT)
    else:
      # Standard Chat Chain
      prompt = ChatPromptTemplate.from_messages([
          ("system", instruction),
          ("human",
           "Here's the previous conversation:\n{history}\n\nContext from Knowledge Base:\n{context}\n\nUser Question:\n{query}")
      ])

      llm = self.llm_service._get_llm(
          provider=provider,
          model=model,
          temperature=config.temperature,
          api_key=config.api_key,
          base_url=config.base_url
      )
      chain = prompt | llm | StrOutputParser()

    inputs = {
        "history": history if history else "No previous history.",
        "context": context_str,
        "query": query + "\n\nREMINDER: Output ONLY valid JSON as requested." if quiz_mode else query,
        "max_questions": 5
    }

    try:
      if streaming and not quiz_mode:
        # --- STREAMING STANDARD CHAIN ---
        async def standard_stream_generator():
          try:
            # Use astream instead of ainvoke
            async for chunk in chain.astream(inputs):
              # StrOutputParser returns partial strings
              if chunk:
                yield chunk
          except Exception as e:
            logger.error(
                f"[ChatService]: Standard Chain Streaming Failed: {e}", exc_info=True)
            yield f"Error: {e}"
        return standard_stream_generator()
      elif streaming and quiz_mode:
        # --- STREAMING QUIZ (Mock Stream) ---
        async def quiz_stream_generator():
          try:
            # ainvoke instead of astream for structural integrity
            response = await chain.ainvoke(inputs)

            # Check formatting
            content = response
            if hasattr(response, 'content'):
              content = response.content

            # If it's a Pydantic object (QuizOutput), dump to JSON string
            if not isinstance(content, str) and not isinstance(content, dict):
              # Likely Pydantic model
              if hasattr(content, 'model_dump_json'):
                content = content.model_dump_json()
              elif hasattr(content, 'dict'):
                content = json.dumps(content.dict())
              else:
                content = str(content)
            elif isinstance(content, dict):
              content = json.dumps(content)

            yield content
          except Exception as e:
            logger.error(
              f"[ChatService]: Quiz Generation Failed: {e}", exc_info=True)
            yield f"Error: {e}"
        return quiz_stream_generator()
      else:
        # --- NON-STREAMING ---
        response = await chain.ainvoke(inputs)
        if hasattr(response, 'content'):
          return response.content
        return response

    except Exception as e:
      logger.error(
        f"[ChatService]: LLM Chain Execution Failed: {e}", exc_info=True)
      raise e

  # ----------------------------------------------------------------------
  # INTERNAL HELPERS
  # ----------------------------------------------------------------------
  async def _initialize_chat(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str, access_token: str, quiz_mode: bool
  ) -> Tuple[str, ChatPreparationResult]:
    """
    Initialize chat execution with common setup logic for both streaming and non-streaming modes.

    Returns:
        Tuple of (session_id, chat_preparation_result)
    """
    session_id = await self._ensure_session(session_id, tenant_id, user_id, bot_id, access_token)

    chat_result = await self._prepare_chat_execution(
        bot_id, query, tenant_id, user_id, session_id, access_token, quiz_mode
    )

    return session_id, chat_result

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

  async def _ensure_session(self, session_id: str, tenant_id: str, user_id: str, bot_id: str, access_token: str = None) -> str:
    """
    Ensures session exists.
    Returns (session_id, additional_kb_ids_from_session).
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
    # Assuming create_session might return None on failure based on repo code
    if not session:
      raise RuntimeError("Failed to create new session.")

    return session["id"]

  async def _prepare_chat_execution(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str, access_token: str = None, quiz_mode: bool = False
  ) -> ChatPreparationResult:
    """
    Orchestrate the context retrieval and prompt setup.
    Returns: ChatPreparationResult containing all necessary data for chat execution
    """
    # 1. Initialize History Manager
    history_manager = RepositoryChatMessageHistory(
        session_id=session_id,
        message_repo=self.message_repo,
        access_token=access_token,
        sender_id=user_id
    )

    # 1a. Load History first (Async)
    await history_manager.load_messages()

    # 1b. Save User Message via History Manager (Async)
    await history_manager.aadd_message(HumanMessage(content=query))

    # 1c. Update Session Summary with User Query
    await self._update_session_summary(session_id, query, access_token)

    # 1d. Fetch History (already loaded by history_manager)
    history = "\n".join([
        f"{msg.__class__.__name__.replace('Message', '')}: {msg.content}"
        for msg in history_manager.messages
    ])

    # 2. Get Bot
    bot = await self.bot_repo.get_bot(bot_id, tenant_id, access_token)
    if not bot:
      return ChatPreparationResult(
          history=None,
          context=None,
          llm_config=None,
          bot=None,
          unified_query=None,
          error_message=f"Bot {bot_id} not found",
          supports_tools=False
      )

    # 3. Resolve Model Config (needed for rewriting/routing)
    llm_config = await self.config_helper.resolve_model_config(bot, access_token=access_token)

    # 4. Agentic RAG vs Pre-Retrieval RAG
    # FORCE FALLBACK (as per user request) - Skip tool check to save time/resources
    supports_tools = False

    # supports_tools = self.llm_service.supports_tools(
    #     llm_config.provider,
    #     llm_config.model,
    #     llm_config.api_key,
    #     llm_config.base_url
    # )

    if supports_tools:
      # Agentic RAG: Empty context, Agent retrieves via tools
      unified_query = query
      context = []

    else:
      # Pre-Retrieval RAG: Rewrite, Decompose, Search
      unified_query, context = await self.retrieval_helper.pre_retrieval_rag(
          history, query, bot, llm_config, tenant_id, access_token
      )

    return ChatPreparationResult(
        history=history,
        context=context,
        llm_config=llm_config,
        bot=bot,
        unified_query=unified_query,
        error_message=None,
        supports_tools=supports_tools
    )
