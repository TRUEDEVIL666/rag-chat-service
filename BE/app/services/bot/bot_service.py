
import asyncio
import logging
from datetime import datetime
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
from app.services.ai_model.ai_model_service import AiModelService

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# DOMAIN MODELS & ENUMS
# ----------------------------------------------------------------------
class MessageRole(str, Enum):
  USER = "user"
  SYSTEM = "system"
  ASSISTANT = "AI assistant"


class LLMConfig(BaseModel):
  model: str
  temperature: float
  system_prompt: Optional[str] = None
  api_key: Optional[str] = None
  base_url: Optional[str] = None


class BotRetrievalConfig(BaseModel):
  top_k: int
  score_threshold: float
  rerank: bool
  rerank_model: Optional[str] = None


class KBIndexConfig(BaseModel):
  embedding_model: str
  search_method: str = "semantic"
  auto_merging: bool = False


class BotService:
  def __init__(
      self,
      bot_repo: BotRepository,
      session_repo: SessionRepository,
      llm_service: LLMService,
      message_repo: ChatMessageRepository,
      kb_repo: KnowledgeBaseRepository,
      ai_model_service: AiModelService
  ):
    self.bot_repo = bot_repo
    self.session_repo = session_repo
    self.llm_service = llm_service
    self.message_repo = message_repo
    self.kb_repo = kb_repo
    self.ai_model_service = ai_model_service

  # ----------------------------------------------------------------------
  # INTERNAL HELPERS
  # ----------------------------------------------------------------------
  async def _update_session_summary(self, session_id: str, text: str, access_token: str = None):
    summary = text[:150] + "..." if len(text) > 150 else text
    try:
      # Update summary AND updated_at to ensure it bubbles to top
      payload = {
        "summary_text": summary,
        "updated_at": datetime.utcnow().isoformat()
      }
      await asyncio.to_thread(self.session_repo.update_session, session_id, payload, access_token)
    except Exception as e:
      logger.warning(f"Failed to update session summary for {session_id}: {e}")

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
    Identity is resolved via provider_id/model_id columns.
    Hyperparameters (temperature) are taken from config_model JSONB.
    """
    provider_id = bot_config.get("provider_id")
    model_id = bot_config.get("model_id")
    config_model_json = bot_config.get("config_model") or {}
    system_prompt = bot_config.get("config_prompt")
    temp = config_model_json.get(
      "temperature", settings.DEFAULT_CHAT_TEMPERATURE)

    # 1. Resolve via Structured IDs
    if provider_id and model_id:
      try:
        model_data = self.ai_model_service.get_model_by_id(str(model_id))
        if model_data:
          provider_data = model_data.get("ai_providers", {})
          provider_name = provider_data.get("name", "ollama")

          # Fetch secure API key
          api_key = None
          provider_id = provider_data.get("id")
          if provider_id:
            api_key = self.ai_model_service.get_decrypted_key(provider_id)

          base_url = provider_data.get("base_url")

          model = model_data.get("model_id")
          return LLMConfig(
              model=f"{provider_name}/{model}",
              temperature=temp,
              system_prompt=system_prompt,
              api_key=api_key,
              base_url=base_url
          )
      except Exception as e:
        logger.error(f"Failed to resolve model via structured columns: {e}")

    # 2. Final Fallback to Settings Defaults (No more JSONB identity parsing)
    combined = settings.DEFAULT_CHAT_MODEL

    # Ensure combined has a provider prefix if not present (default to ollama)
    if "/" not in combined:
      combined = f"ollama/{combined}"

    return LLMConfig(model=combined, temperature=temp, system_prompt=system_prompt)

  def _parse_kb_config(self, kb_config: Optional[dict]) -> KBIndexConfig:
    """
    Parses KB-specific settings (embedding model, search method).
    """
    if not kb_config:
      raise ValueError("Knowledge Base configuration is missing entirely.")

    embedding_provider = None
    if kb_config.get("embedding_provider") and isinstance(kb_config["embedding_provider"], dict):
      embedding_provider = kb_config["embedding_provider"].get("name")

    if not embedding_provider:
      raise ValueError(
        "Knowledge Base is missing 'embedding_provider' configuration.")

    embedding_model = None
    if kb_config.get("embedding_model"):
      if isinstance(kb_config["embedding_model"], dict):
        embedding_model = kb_config["embedding_model"].get("model_id")
      else:
        embedding_model = kb_config.get("embedding_model")

    if not embedding_model:
      raise ValueError(
          "Knowledge Base is missing 'embedding_model' configuration.")

    # Check retrieval_model JSON for search_method/auto_merging ONLY
    if kb_config.get("retrieval_model"):
      rm_raw = kb_config["retrieval_model"]
      rm = {}
      if isinstance(rm_raw, dict):
        rm = rm_raw
      elif isinstance(rm_raw, str):
        import json
        try:
          rm = json.loads(rm_raw)
        except Exception:
          pass

      # Only extract what belongs to KB Indexing
      search_method = rm.get("search_method", "semantic")
      auto_merging = rm.get("auto_merging", False)

    # Concatenate for single-string usage
    if "/" not in embedding_model:
      embedding_model = f"{embedding_provider}/{embedding_model}"

    return KBIndexConfig(
        embedding_model=embedding_model,
        search_method=search_method,
        auto_merging=auto_merging
    )

  def _parse_bot_retrieval_config(self, bot_config: Dict[str, Any]) -> BotRetrievalConfig:
    """
    Parses retrieval config from the Bot's config_model column.
    Uses flattened reranking keys.
    """
    config_model = bot_config.get("config_model") or {}

    # Defaults
    top_k = 10
    score_threshold = 0.4
    rerank = False
    rerank_model = settings.RERANKER_MODEL

    # Parse from config_model
    if config_model.get("top_k") is not None:
      top_k = int(config_model["top_k"])

    if config_model.get("score_threshold_enabled"):
      score_threshold = float(config_model.get("score_threshold", 0.4))

    # Flattened Reranking Logic
    rerank = config_model.get("reranking_enable", False)

    # Try flattened key first, fallback to legacy for safety during transition
    raw_model = config_model.get("reranking_model")
    if not raw_model:
      # Legacy fallback
      reranking_mode = config_model.get("reranking_mode", {})
      raw_model = reranking_mode.get(
        "reranking_model") or reranking_mode.get("model_name")

    if raw_model:
      if "/" in raw_model and not raw_model.startswith("cross-encoder/"):
        _, rerank_model = raw_model.split("/", 1)
      else:
        rerank_model = raw_model

    return BotRetrievalConfig(
        top_k=top_k,
        score_threshold=score_threshold,
        rerank=rerank,
        rerank_model=rerank_model
    )

  async def _search_knowledge_bases(
      self,
      query: str,
      kb_ids: List[str],
      tenant_id: str,
      global_config: BotRetrievalConfig,
      access_token: str = None
  ) -> List[Dict]:
    """
    Iterates through KB IDs, searches each in PARALLEL using global bot config.
    Reranking is done GLOBALLY after aggregation.
    """
    if not kb_ids:
      return []

    import time
    start_time = time.perf_counter()

    # 1. Batch Fetch configurations (only for embedding_model and search_method)
    try:
      kb_configs_map = await asyncio.to_thread(
          self.kb_repo.get_retrieval_configs_by_ids,
          kb_ids,
          tenant_id,
          access_token=access_token
      )
    except Exception as e:
      logger.error(f"Failed to batch fetch KB configs: {e}")
      kb_configs_map = {}

    # 2. Prepare Parallel Search Tasks
    tasks = []

    async def search_single_kb(kb_id_inner: str):
      try:
        # Determine Embedding Model & Search Method from KB Config
        raw_kb_config = kb_configs_map.get(kb_id_inner)
        kb_parsed = self._parse_kb_config(raw_kb_config)

        # Use Global Config for Retrieval Params
        local_k = global_config.top_k * 2 if global_config.rerank else global_config.top_k

        # Execute Search
        from app.core.factory import get_vector_store
        results = await get_vector_store().search(
            query=query,
            k=local_k,
            kb_id=str(kb_id_inner),
            score_threshold=global_config.score_threshold,
            model_name=kb_parsed.embedding_model,
            search_method=kb_parsed.search_method,
            enable_auto_merging=kb_parsed.auto_merging
        )
        return results
      except Exception as ex:
        logger.error(f"Error searching KB {kb_id_inner}: {ex}", exc_info=True)
        return []

    for kbid in kb_ids:
      tasks.append(search_single_kb(kbid))

    # 3. Execute Parallel Search
    logger.info(f"Starting parallel search for {len(tasks)} KBs...")
    search_results_list = await asyncio.gather(*tasks)

    # 4. Aggregate
    all_results = []
    for res_list in search_results_list:
      if res_list:
        all_results.extend(res_list)

    # 5. Global Reranking (if enabled)
    if global_config.rerank:
      logger.info(
        f"Executing Global Reranking on {len(all_results)} results with model {global_config.rerank_model}")
      from app.core.factory import get_vector_store
      all_results = await asyncio.to_thread(
          get_vector_store().rerank_results,
          results=all_results,
          query=query,
          top_k=global_config.top_k,
          model_name=global_config.rerank_model
      )
    else:
      # Just Sort by score if no reranking
      all_results.sort(key=lambda x: x["score"], reverse=True)
      all_results = all_results[:global_config.top_k]

    elapsed = time.perf_counter() - start_time
    logger.info(f"Parallel KB search completed in {elapsed:.4f}s")

    return all_results

  async def _get_history(self, session_id: str, limit: int = 20, access_token: str = None) -> str:
    """
    Fetches and formats the last N messages of the session.
    """
    messages = await asyncio.to_thread(
        self.message_repo.get_messages_by_session,
        session_id=session_id,
        limit=limit + 1,
        access_token=access_token
    )
    if not messages or len(messages) <= 1:
      return ""

    # messages[0] is the current query just saved. messages[1:] are the past ones.
    past_messages = messages[1:]
    # Chronological order
    past_messages.reverse()

    history_lines = []
    for msg in past_messages:
      role = msg.get("role", "user")
      content = msg.get("content", "")
      history_lines.append(f"{role.capitalize()}: {content}")

    return "\n".join(history_lines)

  async def _prepare_chat_execution(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str, access_token: str = None, quiz_mode: bool = False
  ) -> Tuple[Optional[str], Optional[str], Optional[LLMConfig], Optional[str], Optional[str]]:
    """
    Orchestrate the context retrieval and prompt setup.
    Returns: (history, context, llm_config, bot_name, error_message)
    """
    # 1. Save User Message
    await asyncio.to_thread(
        self.message_repo.create_message,
        session_id=session_id,
        content=query,
        role=MessageRole.USER,
        sender_id=user_id,
        access_token=access_token
    )

    # 1a. Update Session Summary with User Query
    await self._update_session_summary(session_id, query, access_token)

    # 1b. Fetch History (memory)
    history = await self._get_history(
      session_id=session_id,
      limit=20,
      access_token=access_token
    )

    # 2. Get Bot
    bot = await self.get_bot(bot_id, tenant_id, access_token)
    if not bot:
      return None, None, None, None, f"Bot {bot_id} not found"

    # 3. Check KBs
    kb_ids = bot.get("kb_ids")
    if not kb_ids:
      msg = "Bot is not configured with any knowledge bases."
      await asyncio.to_thread(
          self.message_repo.create_message, session_id, msg, role=MessageRole.SYSTEM, sender_id=bot_id, access_token=access_token
      )
      return None, None, None, None, msg

    # 4. Resolve Model
    llm_config = self._resolve_model_config(bot)

    # Append to System Prompt if Quiz Mode is enabled
    if quiz_mode:
      quiz_prompt = (
          "\n\nIMPORTANT: You are currently in Quiz Mode. "
          "Based on the provided context, generate a multiple-choice quiz. "
          f"If the user specified a number of questions, output that many (maximum {settings.MAX_QUIZ_QUESTIONS}). Otherwise, default to 5 questions. "
          "Output ONLY a raw JSON array. Do not use Markdown code blocks (like ```json). "
          "Use this exact schema: "
          '[{"question": "Question text", "options": ["Option A", "Option B", "Option C", "Option D"], "correct_answer": "Option A"}]'
      )
      if llm_config.system_prompt:
        llm_config.system_prompt += quiz_prompt
      else:
        llm_config.system_prompt = quiz_prompt
    else:
        # Standard Markdown Instruction for normal mode
      mk_instruction = "\nProvide your response in clear Markdown format. Use headers, bold text, lists, and code blocks where appropriate to make the information easy to read."
      if llm_config.system_prompt:
        llm_config.system_prompt += mk_instruction
      else:
        # Fallback will be handled in _call_llm if None, but we can set it here too
        llm_config.system_prompt = "You are a helpful AI assistant." + mk_instruction

    # 5. Resolve Retrieval Config (Global)
    retrieval_config = self._parse_bot_retrieval_config(bot)

    # Override for Quiz Mode: Force top_k to configured value (default 20) to gather more context
    if quiz_mode:
      retrieval_config.top_k = settings.QUIZ_MODE_TOP_K

    # 6. Search
    results = await self._search_knowledge_bases(
        query,
        kb_ids,
        tenant_id,
        retrieval_config,
        access_token=access_token
    )

    if not results:
      msg = "I don't have enough information to answer your question."
      await asyncio.to_thread(
          self.message_repo.create_message, session_id, msg, role=MessageRole.ASSISTANT, sender_id=bot_id
      )
      return None, None, None, None, msg

    context_parts = []
    for r in results:
      meta = r.get("metadata", {})
      source = meta.get("file_name", "Unknown Source")
      if "page_label" in meta:
        source += f" (Page {meta['page_label']})"

      score = r.get("score", 0.0)
      text = r.get("text", "")

      # Format:
      # Source: filename (Page X)
      # Relevance: 0.XX
      # Content: ...
      part = f"Source: {source}\nRelevance: {score:.2f}\nContent:\n{text}\n---"
      context_parts.append(part)

    context = "\n".join(context_parts)
    return history, context, llm_config, bot.get("name", "AI Assistant"), None

  # ----------------------------------------------------------------------
  # CHAT INTERFACE
  # ----------------------------------------------------------------------
  async def ask_bot(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None, access_token: str = None, quiz_mode: bool = False
  ) -> Tuple[str, str]:
    session_id = await self._ensure_session(session_id, tenant_id, user_id, bot_id, access_token)

    history, context, llm_config, bot_name, error_msg = await self._prepare_chat_execution(
        bot_id, query, tenant_id, user_id, session_id, access_token, quiz_mode
    )

    if error_msg:
      return error_msg, session_id

    # Should be unreachable if error_msg is None, but for type safety
    if not llm_config:
      return "Internal Configuration Error", session_id

    try:
      response = await self._call_llm(
          query=query,
          history=history,
          context=context,
          config=llm_config,
          streaming=False
      )

      await asyncio.to_thread(
          self.message_repo.create_message, session_id, response, role=bot_name, sender_id=bot_id, access_token=access_token
      )

      # Update Session Summary with Bot Response
      await self._update_session_summary(session_id, response, access_token)

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
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None, access_token: str = None, quiz_mode: bool = False
  ):
    session_id = await self._ensure_session(session_id, tenant_id, user_id, bot_id, access_token)

    history, context, llm_config, bot_name, error_msg = await self._prepare_chat_execution(
        bot_id, query, tenant_id, user_id, session_id, access_token, quiz_mode
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
        history=history,
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
      history: str,
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
          history=history,
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

      # Update Session Summary with Bot Response (Streaming)
      await self._update_session_summary(session_id, full_response, access_token)

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
      history: str,
      context: str,
      config: LLMConfig,
      streaming: bool = False
  ):
    # Use configured system prompt
    instruction = config.system_prompt

    # Construct clean prompt without leading whitespace
    prompt_user_content = (
      f"Here's the previous conversation:\n{history if history else 'No previous history.'}\n\n"
      f"Context from Knowledge Base:\n{context}\n\n"
      f"User Question:\n{query}\n\n"
    )

    # Parse concatenated model string
    provider = "ollama"
    model = config.model
    if "/" in config.model:
      provider, model = config.model.split("/", 1)

    if streaming:
      return self.llm_service.stream_chat(
          prompt=prompt_user_content,
          system_instruction=instruction,
          provider=provider,
          model=model,
          temperature=config.temperature,
          api_key=config.api_key,
          base_url=config.base_url
      )
    else:
      return self.llm_service.chat(
          prompt=prompt_user_content,
          system_instruction=instruction,
          provider=provider,
          model=model,
          temperature=config.temperature,
          api_key=config.api_key,
          base_url=config.base_url
      )
