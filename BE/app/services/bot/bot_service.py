
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


class RetrievalConfig(BaseModel):
  top_k: int
  score_threshold: float
  rerank: bool
  rerank_model: Optional[str] = None


class BotService:
  def __init__(
      self,
      bot_repo: BotRepository,
      session_repo: SessionRepository,
      vector_repo: VectorRepository,
      llm_service: LLMService,
      message_repo: ChatMessageRepository,
      kb_repo: KnowledgeBaseRepository,
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
  async def create_bot(self, data: BotCreateRequest, tenant_id: str, user_id: str):
    return await asyncio.to_thread(self.bot_repo.create_bot, data, tenant_id, user_id)

  async def update_config(self, bot_id: str, tenant_id: str, request: BotUpdateConfigRequest):
    return await asyncio.to_thread(self.bot_repo.update_config, bot_id, tenant_id, request)

  async def list_bots(self, tenant_id: str):
    return await asyncio.to_thread(self.bot_repo.list_bots, tenant_id)

  async def get_bot(self, bot_id: str, tenant_id: str):
    return await asyncio.to_thread(self.bot_repo.get_bot, bot_id, tenant_id)

  async def delete_bot(self, bot_id: str, tenant_id: str):
    return await asyncio.to_thread(self.bot_repo.delete_bot, bot_id, tenant_id)

  # ----------------------------------------------------------------------
  # SESSION HELPER
  # ----------------------------------------------------------------------
  async def _ensure_session(self, session_id: str, tenant_id: str, user_id: str, bot_id: str) -> str:
    if session_id:
      try:
        session = await asyncio.to_thread(self.session_repo.get_session, session_id)
        if session:
          return session["id"]
      except Exception:
        logger.warning(
            f"Session {session_id} not found or error accessing it. Creating new session."
        )

    # Create new session if None or not found
    session = await asyncio.to_thread(
        self.session_repo.create_session, user_id, bot_id, tenant_id
    )
    # Assuming create_session might return None on failure based on repo code
    if not session:
      # Fallback or strict error? Original code assumed it returned a dict with "id".
      # If repo raises, it's caught outside or bubbles up.
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

    if not config_model:
      combined = settings.DEFAULT_CHAT_MODEL
      temp = settings.DEFAULT_CHAT_TEMPERATURE
      provider = "ollama"  # default fallback
      model = combined

      if "/" in combined:
        parts = combined.split("/", 1)
        provider = parts[0]
        model = parts[1]

      return LLMConfig(provider=provider, model=model, temperature=temp)

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

    return LLMConfig(provider=provider, model=model, temperature=temp)

  async def _resolve_retrieval_config(self, kb_id: str, tenant_id: str) -> RetrievalConfig:
    """
    Fetches retrieval settings for a KB (top_k, threshold, rerank info).
    """
    # Defaults
    top_k = 5
    score_threshold = 0.1
    rerank = False
    rerank_model = settings.RERANKER_MODEL

    try:
      kb_config = await asyncio.to_thread(
          self.kb_repo.get_retrieval_model, kb_id, tenant_id
      )
      if kb_config and kb_config.get("retrieval_model"):
        rm = kb_config["retrieval_model"]

        if rm.get("top_k", 0) > 0:
          top_k = rm["top_k"]

        if rm.get("score_threshold_enabled", False):
          score_threshold = rm.get("score_threshold", 0.1)

        rerank = rm.get("reranking_enable", False)
        reranking_mode = rm.get("reranking_mode", {})

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
        rerank_model=rerank_model
    )

  async def _search_knowledge_bases(self, query: str, kb_ids: List[str], tenant_id: str) -> List[Dict]:
    """
    Iterates through KB IDs, searches each, reranks if configured, and aggregates results.
    """
    all_results = []

    # We can optimize this to run in parallel
    for kb_id in kb_ids:
      try:
        retrieval_config = await self._resolve_retrieval_config(str(kb_id), tenant_id)

        # If reranking, fetch more candidates
        search_k = retrieval_config.top_k * \
            3 if retrieval_config.rerank else retrieval_config.top_k

        results = await asyncio.to_thread(
            self.vector_repo.search,
            query=query,
            k=search_k,
            kb_id=str(kb_id),
            score_threshold=retrieval_config.score_threshold
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
        logger.error(f"Error searching KB {kb_id}: {e}", exc_info=True)

    # Sort all aggregated results by score
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:5]  # Global top 5

  async def _prepare_chat_execution(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str
  ) -> Tuple[Optional[str], Optional[LLMConfig], Optional[str]]:
    """
    Orchestrate the context retrieval and prompt setup.
    Returns: (context, llm_config, error_message)
    """
    # 1. Save User Message
    await asyncio.to_thread(
        self.message_repo.create_message, session_id, query, role=MessageRole.USER, sender_id=user_id
    )

    # 2. Get Bot
    bot = await self.get_bot(bot_id, tenant_id)
    if not bot:
      return None, None, f"Bot {bot_id} not found"

    # 3. Check KBs
    kb_ids = bot.get("kb_ids")
    if not kb_ids:
      msg = "Bot is not configured with any knowledge bases."
      await asyncio.to_thread(
          self.message_repo.create_message, session_id, msg, role=MessageRole.SYSTEM, sender_id=bot_id
      )
      return None, None, msg

    # 4. Resolve Model
    llm_config = self._resolve_model_config(bot)

    # 5. Search
    results = await self._search_knowledge_bases(query, kb_ids, tenant_id)

    if not results:
      msg = "I don't have enough information to answer your question."
      await asyncio.to_thread(
          self.message_repo.create_message, session_id, msg, role=MessageRole.ASSISTANT, sender_id=bot_id
      )
      return None, None, msg

    context = "\n".join([r["text"] for r in results])
    return context, llm_config, None

  # ----------------------------------------------------------------------
  # CHAT INTERFACE
  # ----------------------------------------------------------------------
  async def ask_bot(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None
  ) -> Tuple[str, str]:
    session_id = await self._ensure_session(session_id, tenant_id, user_id, bot_id)

    context, llm_config, error_msg = await self._prepare_chat_execution(
        bot_id, query, tenant_id, user_id, session_id
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
          self.message_repo.create_message, session_id, response, role=MessageRole.ASSISTANT, sender_id=bot_id
      )

      return response, session_id

    except Exception as e:
      logger.error(f"Error generating chat response: {e}", exc_info=True)
      msg = "Sorry, I encountered an error providing a response."
      # Best effort to log error to user chat
      try:
        await asyncio.to_thread(
            self.message_repo.create_message, session_id, msg, role=MessageRole.SYSTEM, sender_id=bot_id
        )
      except Exception:
        pass  # Fail silently if DB is broken, we already logged the error
      raise e

  async def ask_bot_stream(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None
  ):
    session_id = await self._ensure_session(session_id, tenant_id, user_id, bot_id)

    context, llm_config, error_msg = await self._prepare_chat_execution(
        bot_id, query, tenant_id, user_id, session_id
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
        bot_id=bot_id
    ), session_id

  async def _stream_response_wrapper(
      self,
      query: str,
      context: str,
      config: LLMConfig,
      session_id: str,
      bot_id: str
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
          session_id, full_response, role=MessageRole.ASSISTANT, sender_id=bot_id
      )

    except Exception as e:
      logger.error(f"Error during streaming: {e}", exc_info=True)
      msg = f"Error during streaming: {str(e)}"
      try:
        await asyncio.to_thread(
            self.message_repo.create_message, session_id, msg, role=MessageRole.SYSTEM, sender_id=bot_id
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
    # NOTE: Keeping the naive prompt construction as requested by User Constraints.
    prompt = f"""
      Based on the information below, answer the question accurately and clearly.
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
