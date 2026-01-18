
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from pydantic import BaseModel
import json
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.config.config import settings
from app.schemas.bot import BotCreateRequest, BotUpdateConfigRequest
from app.services.llm.prompt_templates import (
    QUIZ_PROMPT,
    MARKDOWN_INSTRUCTION_PROMPT,
    ROUTER_SYSTEM_PROMPT,
)
from app.services.indexer.vector_store import VectorRepository
from app.services.llm.llm_service import LLMService
from app.schemas.llm import LLMConfig

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
  # ROUTING
  # ----------------------------------------------------------------------
  async def _route_to_kbs(
      self,
      query: str,
      candidate_kb_ids: List[str],
      tenant_id: str,
      access_token: str = None
  ) -> List[str]:
    """
    Uses LLM to select the most relevant KBs for the query.
    """
    # 0. Safety check (no need to route if 0 or 1 KB)
    if not candidate_kb_ids or len(candidate_kb_ids) <= 1:
      return candidate_kb_ids

    # 1. Fetch KB Metadata (Name & Description)
    try:
      kb_details_map = await asyncio.to_thread(
          self.kb_repo.get_retrieval_configs_by_ids,
          candidate_kb_ids,
          tenant_id,
          access_token=access_token
      )
    except Exception as e:
      logger.warning(f"Failed to fetch KB details for routing: {e}")
      return candidate_kb_ids

    # 2. Construct Routing Prompt
    kb_list_text = ""
    valid_kbs = []
    for kb_id in candidate_kb_ids:
      details = kb_details_map.get(kb_id)
      if details:
        name = details.get("name", "Unknown")
        desc = details.get("description") or "No description provided."
        kb_list_text += f"- ID: {kb_id}\n  Name: {name}\n  Description: {desc}\n"
        valid_kbs.append(kb_id)

    if not valid_kbs:
      return candidate_kb_ids

    system_prompt = ROUTER_SYSTEM_PROMPT

    user_prompt = (
        f"Available Knowledge Bases:\n{kb_list_text}\n\n"
        f"User Query: {query}\n\n"
        "Select Relevant KB IDs:"
    )

    # 3. Call LLM via Chain
    llm_config = self._resolve_model_config(
      {"config_model": {"temperature": 0}})

    try:
      selected_ids = await self.llm_service.route_query(user_prompt, system_prompt, llm_config)

      if isinstance(selected_ids, list):
        # Filter to ensure we only return IDs that were in the candidate list
        final_ids = [str(kid)
                     for kid in selected_ids if str(kid) in candidate_kb_ids]
        if final_ids:
          logger.info(
            f"Routing selected {len(final_ids)}/{len(candidate_kb_ids)} KBs: {final_ids}")
          return final_ids
        else:
          logger.warning(
            "Routing returned empty list, falling back to all KBs")
          return candidate_kb_ids
      else:
        logger.warning(
          f"Routing returned invalid JSON type: {type(selected_ids)}")
        return candidate_kb_ids

    except Exception as e:
      logger.error(f"Error during KB routing: {e}")
      return candidate_kb_ids

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
              provider=provider_name,
              model=model,
              temperature=temp,
              system_prompt=system_prompt,
              api_key=api_key,
              base_url=base_url
          )
      except Exception as e:
        logger.error(f"Failed to resolve model via structured columns: {e}")

    # 2. Final Fallback to Settings Defaults (No more JSONB identity parsing)
    combined = settings.DEFAULT_CHAT_MODEL
    provider = "ollama"
    model_name = combined

    if "/" in combined:
      provider, model_name = combined.split("/", 1)

    return LLMConfig(provider=provider, model=model_name, temperature=temp, system_prompt=system_prompt)

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
      queries: List[str],
      kb_ids: List[str],
      tenant_id: str,
      global_config: BotRetrievalConfig,
      access_token: str = None,
      rerank_query: str = None
  ) -> List[Dict]:
    """
    Iterates through KB IDs, searches each in PARALLEL for ALL queries using global bot config.
    Reranking is done GLOBALLY after aggregation against the `rerank_query` (or primary query).
    Deduplicates results based on node_id.
    """
    if not kb_ids or not queries:
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

    async def search_single_kb_query(kb_id_inner: str, query_text: str):
      try:
        # Determine Embedding Model & Search Method from KB Config
        raw_kb_config = kb_configs_map.get(kb_id_inner)
        kb_parsed = self._parse_kb_config(raw_kb_config)

        # Use Global Config for Retrieval Params
        local_k = global_config.top_k * 2 if global_config.rerank else global_config.top_k

        # Execute Search
        from app.core.factory import get_vector_store
        results = await get_vector_store().search(
            query=query_text,
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
      for q in queries:
        tasks.append(search_single_kb_query(kbid, q))

    # 3. Execute Parallel Search
    logger.info(
      f"Starting parallel search for {len(tasks)} tasks (KBs * Queries)...")
    search_results_list = await asyncio.gather(*tasks)

    # 4. Aggregate & Deduplicate
    all_results = []
    seen_ids = set()

    for res_list in search_results_list:
      if res_list:
        for res in res_list:
            # Use metadata node_id or id for deduplication
          meta = res.get("metadata", {})
          node_id = meta.get("node_id") or res.get("id")
          if node_id and node_id in seen_ids:
            continue

          if node_id:
            seen_ids.add(node_id)
          all_results.append(res)

    # 5. Global Reranking (if enabled)
    # Prefer explicitly provided rerank_query (unified), fallback to first query
    primary_query = rerank_query if rerank_query else (
      queries[0] if queries else "")

    if global_config.rerank and all_results:
      logger.info(
        f"Executing Global Reranking on {len(all_results)} results with model {global_config.rerank_model}")
      from app.core.factory import get_vector_store
      all_results = await asyncio.to_thread(
          get_vector_store().rerank_results,
          results=all_results,
          query=primary_query,
          top_k=global_config.top_k,
          model_name=global_config.rerank_model
      )
    else:
      # Just Sort by score if no reranking
      all_results.sort(key=lambda x: x["score"], reverse=True)
      all_results = all_results[:global_config.top_k]

    elapsed = time.perf_counter() - start_time
    logger.info(
      f"Parallel KB search completed in {elapsed:.4f}s. Found {len(all_results)} raw results.")

    # 6. Transform search results (dicts) into LangChain Document objects
    documents = []
    for i, r in enumerate(all_results):
      meta = r.get("metadata", {})
      source = meta.get("source", "Unknown")
      if "page_label" in meta:
        source += f" (Page {meta['page_label']})"

      text = r.get("text", "")
      content_with_header = f"DOCUMENT [{i + 1}]: Source: {source}\nContent:\n{text}\n---"

      doc = Document(
          page_content=content_with_header,
          metadata=meta
      )
      documents.append(doc)

    return documents

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
  ) -> Tuple[Optional[str], Optional[List[Document]], Optional[LLMConfig], Optional[str], Optional[str]]:
    """
    Orchestrate the context retrieval and prompt setup.
    Returns: (history, context (documents),
              llm_config, bot_name, error_message)
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

    # 3. Resolve Model Config (needed for rewriting/routing)
    llm_config = self._resolve_model_config(bot)

    # 4. Advanced Retrieval Part 1: Rewrite Query (Context-Awareness)
    search_queries = [query]
    unified_query = query

    if history.strip():
      try:
        rewritten = await self.llm_service.rewrite_query(history, query, llm_config)
        if rewritten and rewritten != query:
          search_queries[0] = rewritten
          unified_query = rewritten
          logger.info(f"Rewritten Query: '{rewritten}'")
      except Exception as e:
        logger.warning(f"Query rewriting failed: {e}")

    # 5. Intelligent Routing (using potentially rewritten query)
    kb_ids = bot.get("kb_ids")
    if kb_ids and len(kb_ids) > 1:
      candidate_kb_ids = [str(k) for k in kb_ids]
      logger.info(
        f"Routing start for query: '{unified_query}' among {len(candidate_kb_ids)} KBs")
      selected_kb_ids = await self._route_to_kbs(unified_query, candidate_kb_ids, tenant_id, access_token)
      kb_ids = selected_kb_ids
    elif not kb_ids:
      msg = "Bot is not configured with any knowledge bases."
      await asyncio.to_thread(
          self.message_repo.create_message, session_id, msg, role=MessageRole.SYSTEM, sender_id=bot_id, access_token=access_token
      )
      return None, None, None, None, msg

    # 6. Advanced Retrieval Part 2: Decomposition
    try:
      decomposed = await self.llm_service.decompose_query(unified_query, llm_config)
      if decomposed:
        search_queries = decomposed
        logger.info(f"Decomposed Queries: {search_queries}")
    except Exception as e:
      logger.warning(f"Query decomposition failed: {e}")

    # 7. Finalize LLM System Prompt & Retrieval Config
    # Append to System Prompt if Quiz Mode is enabled
    if quiz_mode:
      quiz_prompt = QUIZ_PROMPT.format(
        max_questions=settings.MAX_QUIZ_QUESTIONS)
      if llm_config.system_prompt:
        llm_config.system_prompt += quiz_prompt
      else:
        llm_config.system_prompt = quiz_prompt
    else:
        # Standard Markdown Instruction for normal mode
      mk_instruction = MARKDOWN_INSTRUCTION_PROMPT
      if llm_config.system_prompt:
        llm_config.system_prompt += mk_instruction
      else:
        llm_config.system_prompt = "You are a helpful AI assistant." + mk_instruction

    retrieval_config = self._parse_bot_retrieval_config(bot)
    if quiz_mode:
      retrieval_config.top_k = settings.QUIZ_MODE_TOP_K

    # 8. Search
    logger.info(
      f"Starting parallel KB search for {len(search_queries)} queries")
    documents = await self._search_knowledge_bases(
        search_queries,
        kb_ids,
        tenant_id,
        retrieval_config,
        access_token=access_token,
        rerank_query=unified_query
    )

    if not documents:
      logger.info("No documents found in Knowledge Bases.")
      return history, [], llm_config, bot.get("name", "AI Assistant"), None

    logger.info(
      f"RAG Preparation Complete. Found {len(documents)} context documents.")

    return history, documents, llm_config, bot.get("name", "AI Assistant"), None

  # ----------------------------------------------------------------------
  # CHAT INTERFACE
  # ----------------------------------------------------------------------
  async def ask_bot(
      self, bot_id: str, query: str, tenant_id: str, user_id: str, session_id: str = None, access_token: str = None, quiz_mode: bool = False
  ) -> Tuple[Optional[str], Optional[str]]:
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
        documents=context,  # context is now List[Document]
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
      documents: List[Document],
      config: Any,
      session_id: str,
      bot_id: str,
      bot_name: str,
      access_token: str
  ):
    """
    Internal helper to handle the streaming, aggregation, and final logging.
    """
    # Stream from LLM via Utility
    full_response = ""
    try:
      # Use the unified LLM interaction helper
      stream = await self._call_llm(
          query=query,
          history=history,
          context=documents,
          config=config,
          streaming=True
      )

      async for chunk in stream:
        if chunk is not None:
          # Extract text if it's a LangChain chunk object
          content = chunk.content if hasattr(chunk, 'content') else str(chunk)

          if content:
            yield content
            full_response += content
        else:
          logger.debug("Received None chunk from stream")

      if not full_response:
        logger.warning(
            f"Stream completed with empty response for session {session_id}")

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
      yield f"Error: {str(e)}"

  # ----------------------------------------------------------------------
  # LLM INTERACTION
  # ----------------------------------------------------------------------
  async def _call_llm(
      self,
      query: str,
      history: str,
      context: Union[str, List[Document]],
      config: LLMConfig,
      streaming: bool = False
  ):
    # Handle legacy context string or new Document list
    if isinstance(context, list):
      context_str = "\n".join([d.page_content for d in context])
    else:
      context_str = context

    # Use configured system prompt
    instruction = config.system_prompt

    # Create Prompt Template
    prompt = ChatPromptTemplate.from_messages([
        ("system", instruction),
        ("human",
         "Here's the previous conversation:\n{history}\n\nContext from Knowledge Base:\n{context}\n\nUser Question:\n{query}")
    ])

    # Resolve provider and model from config
    provider = config.provider
    model = config.model
    if "/" in config.model:
      provider, model = config.model.split("/", 1)

    logger.info(
        f"Synthesis call: provider={provider}, model={model}, streaming={streaming}")

    # Initialize model via helper
    llm = self.llm_service._get_llm(
        provider=provider,
        model=model,
        temperature=config.temperature,
        api_key=config.api_key,
        base_url=config.base_url
    )

    inputs = {
        "history": history if history else "No previous history.",
        "context": context_str,
        "query": query
    }

    if streaming:
      return llm.astream(prompt.format_messages(**inputs))
    else:
      response = await llm.ainvoke(prompt.format_messages(**inputs))
      return response.content
