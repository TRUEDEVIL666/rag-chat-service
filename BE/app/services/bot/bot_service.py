
import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from pydantic import BaseModel

from app.config.config import settings
from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest
from app.services.indexer.vector_store import VectorRepository
from app.services.llm.llm_service import LLMService

# Import Repositories
from app.services.supabase.bot_repository import BotRepository
from app.services.supabase.chat_message_repository import ChatMessageRepository
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.supabase.session_repository import SessionRepository

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# DOMAIN MODELS & ENUMS
# ----------------------------------------------------------------------
class MessageRole(str, Enum):
  USER = "user"
  SYSTEM = "system"
  ASSISTANT = "AI assistant"


class LLMConfig(BaseModel):
  provider: str
  model: str
  temperature: float
  system_prompt: Optional[str] = None


class RetrievalConfig(BaseModel):
  top_k: int
  score_threshold: float
  rerank: bool
  rerank_model: Optional[str] = None
  embedding_model: Optional[str] = None
  search_method: str = "semantic"
  auto_merging: bool = False


class BotService:
  def __init__(
      self,
      bot_repo: BotRepository,
      session_repo: SessionRepository,
      vector_repo: VectorRepository,
      llm_service: LLMService,
      message_repo: ChatMessageRepository,
      kb_repo: KnowledgeBaseRepository
  ):
    self.bot_repo = bot_repo
    self.session_repo = session_repo
    self.vector_repo = vector_repo
    self.llm_service = llm_service
    self.message_repo = message_repo
    self.kb_repo = kb_repo

  # ----------------------------------------------------------------------
  # BOT MANAGEMENT (CRUD) - Now Async to avoid blocking
  # ----------------------------------------------------------------------
  async def create_bot(self, data: BotCreateRequest, tenant_id: str, user_id: str, access_token: str = None):
    return await asyncio.to_thread(self.bot_repo.create_bot, data, tenant_id, user_id, access_token)

  async def update_config(self, bot_id: str, tenant_id: str, request: BotUpdateConfigRequest, access_token: str = None):
    return await asyncio.to_thread(self.bot_repo.update_config, bot_id, tenant_id, request, access_token)

  async def list_bots(self, tenant_id: str, access_token: str = None):
    return await asyncio.to_thread(self.bot_repo.list_bots, tenant_id, access_token)

  async def get_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    return await asyncio.to_thread(self.bot_repo.get_bot, bot_id, tenant_id, access_token)

  async def delete_bot(self, bot_id: str, tenant_id: str, access_token: str = None):
    return await asyncio.to_thread(self.bot_repo.delete_bot, bot_id, tenant_id, access_token)

  # ----------------------------------------------------------------------
  # SESSION HELPER
  # ----------------------------------------------------------------------
  async def _ensure_session(self, session_id: str, tenant_id: str, user_id: str, bot_id: str, access_token: str = None) -> str:
    if session_id:
      try:
        session = await asyncio.to_thread(self.session_repo.get_session, session_id, access_token)
        if session:
          # Verify Session Ownership
          s_bot_id = str(session.get("bot_id"))
          s_user_id = str(session.get("user_id"))

          if s_bot_id != bot_id:
            logger.warning(
                f"Session {session_id} mismatch: Bot {s_bot_id} != {bot_id}"
            )
            # Generic error to avoid leaking existence
            raise ValueError("Session not found")

          elif s_user_id != user_id:
            logger.warning(
                f"Session {session_id} mismatch: User {s_user_id} != {user_id}"
            )
            raise ValueError("Session not found")

          return session["id"]
        else:
          # Session ID provided but not found in DB
          raise ValueError("Session not found")

      except ValueError:
        raise
      except Exception as e:
        logger.error(f"Error checking session {session_id}: {e}")
        raise ValueError("Session not found")

    # Create new session if passed session_id was None/Empty
    session = await asyncio.to_thread(
        self.session_repo.create_session, user_id, bot_id, tenant_id, access_token
    )
    # Assuming create_session might return None on failure based on repo code
    if not session:
      raise RuntimeError("Failed to create new session.")

    return session["id"]

  # ----------------------------------------------------------------------
  # CONTEXT & SEARCH HELPERS
  # ----------------------------------------------------------------------
  def _resolve_model_config(self, bot_config: Dict[str, Any]) -> LLMConfig:
    """
    Parses bot config to determine provider, model, and temperature.
    """
    config_model = bot_config.get("config_model")
    system_prompt = bot_config.get("config_prompt")

    if not config_model:
      combined = settings.DEFAULT_CHAT_MODEL
      temp = settings.DEFAULT_CHAT_TEMPERATURE
      provider = "ollama"  # default fallback
      model = combined

      if "/" in combined:
        parts = combined.split("/", 1)
        provider = parts[0]
        model = parts[1]

      return LLMConfig(provider=provider, model=model, temperature=temp, system_prompt=system_prompt)

    # Config exists
    combined = config_model.get("model", settings.DEFAULT_CHAT_MODEL)
    temp = config_model.get("temperature", settings.DEFAULT_CHAT_TEMPERATURE)

    if "/" in combined:
      parts = combined.split("/", 1)
      provider = parts[0]
      model = parts[1]
    else:
      provider = config_model.get("provider", "ollama")
      model = combined

    return LLMConfig(provider=provider, model=model, temperature=temp, system_prompt=system_prompt)

  async def _resolve_retrieval_config(self, kb_id: str, tenant_id: str) -> RetrievalConfig:
    """
    Fetches retrieval settings for a KB (top_k, threshold, rerank info).
    """
    # Defaults
    top_k = 5
    score_threshold = 0.1
    rerank = False
    rerank_model = settings.RERANKER_MODEL
    embedding_model = settings.EMBEDDING_MODEL

    search_method = "semantic"
    auto_merging = False
    try:
      kb_config = await asyncio.to_thread(
          self.kb_repo.get_retrieval_model, kb_id, tenant_id
      )
      if kb_config:
        if kb_config.get("embedding_model"):
          embedding_model = kb_config.get("embedding_model")

        # Initialize rm to avoid unbound local error if retrieval_model is missing
        rm = {}
        if kb_config.get("retrieval_model"):
          rm_raw = kb_config["retrieval_model"]
          # Handle potential JSON string
          if isinstance(rm_raw, str):
            import json
            try:
              rm = json.loads(rm_raw)
            except Exception:
              rm = {}
          elif isinstance(rm_raw, dict):
            rm = rm_raw

        # Parse fields from rm
        if rm.get("top_k", 0) > 0:
          top_k = rm["top_k"]

        if rm.get("score_threshold_enabled", False):
          score_threshold = rm.get("score_threshold", 0.1)

        rerank = rm.get("reranking_enable", False)
        reranking_mode = rm.get("reranking_mode", {})

        auto_merging = rm.get("auto_merging", False)

        # Extract Search Method
        # It might be under "search_method" or "method" depending on DB consistency
        search_method = rm.get("search_method", "semantic")

        # Parse rerank model
        if reranking_mode:
          raw_model = None
          if isinstance(reranking_mode.get("reranking_model"), str):
            raw_model = reranking_mode["reranking_model"]
          elif isinstance(reranking_mode.get("model_name"), str):
            raw_model = reranking_mode["model_name"]

          if raw_model:
            if "/" in raw_model and not raw_model.startswith("cross-encoder/"):
              _, rerank_model = raw_model.split("/", 1)
            else:
              rerank_model = raw_model

    except Exception as e:
      logger.error(f"Error fetching KB config for {kb_id}: {e}", exc_info=True)
      # Continue with defaults

    return RetrievalConfig(
        top_k=top_k,
        score_threshold=score_threshold,
        rerank=rerank,
        rerank_model=rerank_model,
        embedding_model=embedding_model,
        search_method=search_method,
        auto_merging=auto_merging
    )

  async def _search_knowledge_bases(self, query: str, kb_ids: List[str], tenant_id: str) -> List[Dict]:
    """
    Iterates through KB IDs, searches each, reranks if configured, and aggregates results.
    """
    all_results = []

    # We can optimize this to run in parallel
    # Group KBs by Embedding Model to optimize searching
    # Structure: { model_name: [ (kb_id, config), ... ] }
    grouped_kbs = {}

    for kb_id in kb_ids:
      try:
        config = await self._resolve_retrieval_config(str(kb_id), tenant_id)
        model = config.embedding_model or settings.EMBEDDING_MODEL
        if model not in grouped_kbs:
          grouped_kbs[model] = []
        grouped_kbs[model].append((kb_id, config))
      except Exception as e:
        logger.error(f"Error resolving config for KB {kb_id}: {e}")

    # Process each model group
    for model_name, queue in grouped_kbs.items():
      try:
        # For each KB in this group, perform search using the specific model
        # Note: We can likely optimize to batch search if vector_repo supported it,
        # but standard usage is per-KB filtering.

        # Current vector_repo.search takes 'kb_id' as a filter.
        # We must iterate.
        for kb_id, retrieval_config in queue:
          try:
            # If reranking, fetch more candidates
            search_k = retrieval_config.top_k * \
                3 if retrieval_config.rerank else retrieval_config.top_k

            results = await self.vector_repo.search(
                query=query,
                k=search_k,
                kb_id=str(kb_id),
                score_threshold=retrieval_config.score_threshold,
                model_name=model_name,
                search_method=retrieval_config.search_method,
                enable_auto_merging=retrieval_config.auto_merging  # Pass the flag
            )

            if results:
              if retrieval_config.rerank:
                results = await asyncio.to_thread(
                    self.vector_repo.rerank_results,
                    results=results,
                    query=query,
                    top_k=retrieval_config.top_k,
                    model_name=retrieval_config.rerank_model
                )
              else:
                results = results[:retrieval_config.top_k]

              all_results.extend(results)
          except Exception as e:
            logger.error(
              f"Error searching KB {kb_id} (Model: {model_name}): {e}", exc_info=True)

      except Exception as e:
        logger.error(
          f"Error processing model group {model_name}: {e}", exc_info=True)

    # Sort all aggregated results by score
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:5]  # Global top 5

  async def _prepare_chat_execution(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str, access_token: str = None
  ) -> Tuple[Optional[str], Optional[LLMConfig], Optional[str]]:
    """
    Orchestrate the context retrieval and prompt setup.
    Returns: (context, llm_config, bot_name, error_message)
    """
    # 1. Save User Message
    await asyncio.to_thread(
        self.message_repo.create_message, session_id, query, role=MessageRole.USER, sender_id=user_id, access_token=access_token
    )

    # 2. Get Bot
    bot = await self.get_bot(bot_id, tenant_id, access_token)
    if not bot:
      return None, None, None, f"Bot {bot_id} not found"

    # 3. Check KBs
    kb_ids = bot.get("kb_ids")
    if not kb_ids:
      msg = "Bot is not configured with any knowledge bases."
      await asyncio.to_thread(
          self.message_repo.create_message, session_id, msg, role=MessageRole.SYSTEM, sender_id=bot_id, access_token=access_token
      )
      return None, None, None, msg

    # 4. Resolve Model
    llm_config = self._resolve_model_config(bot)

    # 5. Search
    results = await self._search_knowledge_bases(query, kb_ids, tenant_id)

    if not results:
      msg = "I don't have enough information to answer your question."
      await asyncio.to_thread(
          self.message_repo.create_message, session_id, msg, role=MessageRole.ASSISTANT, sender_id=bot_id
      )
      return None, None, None, msg

    context = "\n".join([r["text"] for r in results])
    return context, llm_config, bot.get("name", "AI Assistant"), None

  # ----------------------------------------------------------------------
  # CHAT INTERFACE
  # ----------------------------------------------------------------------
  async def ask_bot(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None, access_token: str = None
  ) -> Tuple[str, str]:
    session_id = await self._ensure_session(session_id, tenant_id, user_id, bot_id, access_token)

    context, llm_config, bot_name, error_msg = await self._prepare_chat_execution(
        bot_id, query, tenant_id, user_id, session_id, access_token
    )

    if error_msg:
      return error_msg, session_id

    # Should be unreachable if error_msg is None, but for type safety
    if not llm_config:
      return "Internal Configuration Error", session_id

    try:
      response = await self._call_llm(
          query=query,
          context=context,
          config=llm_config,
          streaming=False
      )

      await asyncio.to_thread(
          self.message_repo.create_message, session_id, response, role=bot_name, sender_id=bot_id, access_token=access_token
      )

      return response, session_id

    except Exception as e:
      logger.error(f"Error generating chat response: {e}", exc_info=True)
      msg = "Sorry, I encountered an error providing a response."
      # Best effort to log error to user chat
      try:
        await asyncio.to_thread(
            self.message_repo.create_message, session_id, msg, role=MessageRole.SYSTEM, sender_id=bot_id, access_token=access_token
        )
      except Exception:
        pass  # Fail silently if DB is broken, we already logged the error
      raise e

  async def ask_bot_stream(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None, access_token: str = None
  ):
    session_id = await self._ensure_session(session_id, tenant_id, user_id, bot_id, access_token)

    context, llm_config, bot_name, error_msg = await self._prepare_chat_execution(
        bot_id, query, tenant_id, user_id, session_id, access_token
    )

    if error_msg:
      async def error_generator():
        yield error_msg
      return error_generator(), session_id

    if not llm_config:
      async def config_error_generator():
        yield "Internal Configuration Error"
      return config_error_generator(), session_id

    # Create generator
    return self._stream_response_wrapper(
        query=query,
        context=context,
        config=llm_config,
        session_id=session_id,
        bot_id=bot_id,
        bot_name=bot_name,
        access_token=access_token
    ), session_id

  async def _stream_response_wrapper(
      self,
      query: str,
      context: str,
      config: LLMConfig,
      session_id: str,
      bot_id: str,
      bot_name: str,
      access_token: str = None
  ):
    """
    Internal helper to handle the streaming, aggregation, and final logging.
    """
    full_response = ""
    try:
      stream = await self._call_llm(
          query=query,
          context=context,
          config=config,
          streaming=True
      )

      async for chunk in stream:
        full_response += chunk
        yield chunk

      # Only start saving to DB after stream completes successfully
      await asyncio.to_thread(
          self.message_repo.create_message,
          session_id, full_response, role=bot_name, sender_id=bot_id, access_token=access_token
      )

    except Exception as e:
      logger.error(f"Error during streaming: {e}", exc_info=True)
      msg = f"Error during streaming: {str(e)}"
      try:
        await asyncio.to_thread(
            self.message_repo.create_message, session_id, msg, role=MessageRole.SYSTEM, sender_id=bot_id, access_token=access_token
        )
      except Exception:
        pass
      raise e

  # ----------------------------------------------------------------------
  # LLM INTERACTION
  # ----------------------------------------------------------------------
  async def _call_llm(
      self,
      query: str,
      context: str,
      config: LLMConfig,
      streaming: bool = False
  ):
    # Use configured system prompt or fallback to default
    instruction = config.system_prompt \
      if config.system_prompt \
        else "Based on the information below, answer the question accurately and clearly."

    prompt = f"""
      {instruction}
      ===
      {context}
      ===
      Question: {query}
    """

    if streaming:
      return self.llm_service.stream_chat(
          prompt=prompt,
          provider=config.provider,
          model=config.model,
          temperature=config.temperature
      )
    else:
      return self.llm_service.chat(
          prompt=prompt,
          provider=config.provider,
          model=config.model,
          temperature=config.temperature
      )
