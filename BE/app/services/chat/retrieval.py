import asyncio
import logging
import time
from typing import Any, Dict, List, Tuple
from langchain_core.documents import Document
from app.core.factory import get_vector_store
from app.services.llm.llm_service import LLMService
from app.services.llm.prompt_templates import ROUTER_SYSTEM_PROMPT
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.llm import LLMConfig
from .config import ChatConfigHelper, BotRetrievalConfig

logger = logging.getLogger(__name__)


class ChatRetrievalHelper:
  def __init__(
      self,
      llm_service: LLMService,
      kb_repo: KnowledgeBaseRepository,
      config_helper: ChatConfigHelper
  ):
    self.llm_service = llm_service
    self.kb_repo = kb_repo
    self.config_helper = config_helper

  async def pre_retrieval_rag(
      self,
      history: str,
      query: str,
      bot: dict,
      llm_config: LLMConfig,
      tenant_id: str,
      access_token: str = None
  ) -> Tuple[str, List[Document]]:
    """
    Pre-Retrieval RAG for non-tool models:
    1. Rewrite and Decompose query
    2. Route to relevant KBs
    3. Parallel search with decomposed queries (excluding original)
    4. Reranking using rewritten query
    """
    try:
      # 1. Rewrite & Decompose
      t0 = time.perf_counter()
      rewrite_result = await self.llm_service.rewrite_and_decompose_query(history, query, llm_config)
      logger.info(
          f"[Retrieval]: Query rewrite and decompose took {time.perf_counter() - t0:.2f}s")

      rewritten_query = rewrite_result.rewritten_query
      decomposed_queries = rewrite_result.decomposed_queries or []

      logger.info(f"[Retrieval]: Original Query: {query}")
      logger.info(f"[Retrieval]: Rewritten Query: {rewritten_query}")
      if decomposed_queries:
        logger.info(f"[Retrieval]: Decomposed Queries: {decomposed_queries}")

      # 2. Route to KBs
      t1 = time.perf_counter()
      kb_ids = [str(k) for k in (bot.get("kb_ids") or [])]
      if not kb_ids:
        logger.info(
          f"[Retrieval]: KB filtering took {time.perf_counter() - t1:.2f}s")
        return rewritten_query, []

      target_kb_ids = await self.route_to_kbs(
          rewritten_query,
          kb_ids,
          tenant_id,
          access_token
      )
      logger.info(
        f"[Retrieval]: KB filtering took {time.perf_counter() - t1:.2f}s")

      if not target_kb_ids:
        return rewritten_query, []

      # 3. Parallel Search (decomposed queries ONLY, exclude original per user requirement)
      search_queries = decomposed_queries if decomposed_queries else [
          rewritten_query]
      search_tasks = [(q, target_kb_ids) for q in search_queries]

      # 4. Search with reranking (using rewritten query)
      t2 = time.perf_counter()
      retrieval_config = self.config_helper.parse_bot_retrieval_config(bot)
      documents = await self.search_knowledge_bases(
          search_tasks,
          tenant_id,
          retrieval_config,
          access_token,
          rerank_query=rewritten_query  # Use rewritten query for reranking
      )
      logger.info(
        f"[Retrieval]: Vector DB search took {time.perf_counter() - t2:.2f}s")

      return rewritten_query, documents

    except Exception as e:
      logger.error(
        f"[Retrieval]: Pre-retrieval RAG failed: {e}", exc_info=True)
      return query, []

  async def search_knowledge_bases(
      self,
      search_tasks: List[Tuple[str, List[str]]],
      tenant_id: str,
      global_config: BotRetrievalConfig,
      access_token: str = None,
      rerank_query: str = None
  ) -> List[Document]:
    """
    Executes search tasks in parallel.
    search_tasks: List of (query_text, [kb_ids]) tuples.
    Reranking is done GLOBALLY using `rerank_query`.
    """
    if not search_tasks:
      return []

    start_time = time.perf_counter()

    # 1. Collect all unique KB IDs to fetch configs once
    all_kb_ids = set()
    for _, kbs in search_tasks:
      for k in kbs:
        all_kb_ids.add(k)

    if not all_kb_ids:
      return []

    try:
      kb_configs_map = await self.kb_repo.get_retrieval_configs_by_ids(
          list(all_kb_ids),
          tenant_id,
          access_token=access_token
      )
    except Exception as e:
      logger.error(f"[Retrieval]: Failed to batch fetch KB configs: {e}")
      kb_configs_map = {}

    # --- OPTIMIZATION: PRE-CALCULATE EMBEDDINGS ---
    embedding_cache = await self.precompute_embeddings(search_tasks, kb_configs_map)
    # --- END OPTIMIZATION ---

    # 2. Prepare Parallel Search Tasks
    tasks = []

    async def search_single_kb_query(kb_id_inner: str, query_text: str):
      try:
        # Determine Embedding Model & Search Method from KB Config
        raw_kb_config = kb_configs_map.get(kb_id_inner)
        kb_parsed = self.config_helper.parse_kb_config(raw_kb_config)

        # Use Global Config for Retrieval Params
        local_k = global_config.top_k * 2 if global_config.rerank else global_config.top_k

        # Retrieve precomputed vector
        precomputed_vec = embedding_cache.get(
            (query_text, kb_parsed.embedding_model))

        if not precomputed_vec:
          logger.warning(
              f"[Retrieval]: Precomputed vector missing for {kb_parsed.embedding_model}, falling back to internal generation.")

        # Execute Search
        from app.core.factory import get_vector_store
        results = await get_vector_store().search(
            query=query_text,
            k=local_k,
            kb_id=str(kb_id_inner),
            score_threshold=global_config.score_threshold,
            model_name=kb_parsed.embedding_model,
            search_method=kb_parsed.search_method,
            enable_auto_merging=kb_parsed.auto_merging,
            precomputed_dense_vector=precomputed_vec
        )
        return results
      except Exception as ex:
        logger.error(
          f"[Retrieval]: Error searching KB {kb_id_inner}: {ex}", exc_info=True)
        return []

    for q_text, kbs in search_tasks:
      for kbid in kbs:
        tasks.append(search_single_kb_query(kbid, q_text))

    # 3. Execute Parallel Search
    if not tasks:
      logger.warning(
        "[Retrieval]: No search tasks generated. Returning empty results.")
      return []

    search_results_list = await asyncio.gather(*tasks)

    # 4. Aggregate & Deduplicate
    all_results = []
    seen_ids = set()

    for res_list in search_results_list:
      if res_list:
        for res in res_list:
          meta = res.get("metadata", {})
          node_id = meta.get("node_id") or res.get("id")
          if node_id and node_id in seen_ids:
            continue

          if node_id:
            seen_ids.add(node_id)
          all_results.append(res)

    # 5. Global Reranking (if enabled)
    primary_query = rerank_query if rerank_query else (
        search_tasks[0][0] if search_tasks else "")

    if global_config.rerank and all_results:
      logger.info(
          f"[Retrieval]: Starting Reranking. Candidates: {len(all_results)}. Query: {primary_query}")
      from app.core.factory import get_vector_store
      all_results = await asyncio.to_thread(
          get_vector_store().rerank_results,
          results=all_results,
          query=primary_query,
          top_k=global_config.top_k,
          model_name=global_config.rerank_model
      )
      logger.info(
        f"[Retrieval]: Reranking finished. Total candidates: {len(all_results)}. Kept top {global_config.top_k}.")
    else:
      logger.info(
        f"[Retrieval]: Skipping rerank (Enabled: {global_config.rerank}). Sorting by vector score.")
      all_results.sort(key=lambda x: x["score"], reverse=True)
      all_results = all_results[:global_config.top_k]

    # 6. Transform search results (dicts) into LangChain Document objects
    documents = []
    for r in all_results:
      meta = r.get("metadata", {})
      source_file = meta.get("source", "Unknown")
      if "page_label" in meta:
        source_file += f" (Page {meta['page_label']})"

      kb_name = "Unknown KB"
      res_kb_id = r.get("kb_id") or meta.get("kb_id")
      if res_kb_id and res_kb_id in kb_configs_map:
        kb_name = kb_configs_map[res_kb_id].get("name", "Unknown KB")

      text = r.get("text", "")
      content_with_header = f"Source (KB: {kb_name}) - File: {source_file}\nContent:\n{text}\n---"

      doc = Document(
          page_content=content_with_header,
          metadata=meta
      )
      documents.append(doc)

    return documents

  async def precompute_embeddings(
      self,
      search_tasks: List[Tuple[str, List[str]]],
      kb_configs_map: Dict
  ) -> Dict[Tuple[str, str], List[float]]:
    """
    Identifies all unique (query, model) pairs and computes embeddings in parallel.
    Returns a cache dict: {(text, model_name): vector}
    """
    # 2a. Identify unique (query_text, model_name) pairs
    unique_embed_requests = {}

    def get_model_for_kb(kb_id_inner):
      raw_kb_config = kb_configs_map.get(kb_id_inner)
      kb_parsed = self.config_helper.parse_kb_config(raw_kb_config)
      return kb_parsed.embedding_model

    needed_embeddings = set()
    for q_text, kbs in search_tasks:
      for kbid in kbs:
        m_name = get_model_for_kb(kbid)
        needed_embeddings.add((q_text, m_name))

    embedding_cache = {}

    async def fetch_embedding(text: str, model_name: str):
      try:
        from app.core.factory import get_embedding_service
        svc = await get_embedding_service(model=model_name)
        vectors = await svc.embed_texts([text])
        return text, model_name, vectors[0] if vectors else []
      except Exception as e:
        logger.error(
            f"[Retrieval]: Failed to pre-compute embedding for model {model_name}: {e}")
        return text, model_name, []

    embed_tasks = [fetch_embedding(t, m) for t, m in needed_embeddings]
    if embed_tasks:
      embed_results = await asyncio.gather(*embed_tasks)
      for txt, mod, vec in embed_results:
        embedding_cache[(txt, mod)] = vec

    return embedding_cache

  async def route_to_kbs(
      self,
      query: str,
      candidate_kb_ids: List[str],
      tenant_id: str,
      access_token: str = None
  ) -> List[str]:
    """
    Uses LLM to select the most relevant KBs for the query.
    """
    if not candidate_kb_ids or len(candidate_kb_ids) <= 1:
      return candidate_kb_ids

    try:
      kb_details_map = await self.kb_repo.get_retrieval_configs_by_ids(
          candidate_kb_ids,
          tenant_id,
          access_token=access_token
      )
    except Exception as e:
      logger.warning(
        f"[Retrieval]: Failed to fetch KB details for routing: {e}")
      return candidate_kb_ids

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

    llm_config = await self.config_helper.resolve_model_config(
        {"config_model": {"temperature": 0}}, access_token=access_token)

    try:
      selected_ids = await self.llm_service.route_query(user_prompt, system_prompt, llm_config)

      if isinstance(selected_ids, list):
        final_ids = [str(kid)
                     for kid in selected_ids if str(kid) in candidate_kb_ids]
        if final_ids:
          return final_ids
        else:
          logger.warning(
              "[Retrieval]: Routing returned empty list, falling back to all KBs")
          return candidate_kb_ids
      else:
        logger.warning(
            f"[Retrieval]: Routing returned invalid JSON type: {type(selected_ids)}")
        return candidate_kb_ids

    except Exception as e:
      logger.error(f"[Retrieval]: Error during KB routing: {e}")
      return candidate_kb_ids
