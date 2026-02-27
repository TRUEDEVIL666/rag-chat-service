import asyncio
from app.core.logger import get_logger
import time
import hashlib
import json
from typing import Any, Dict, List, Tuple
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from app.core.factory import get_vector_store
from app.services.llm.llm_service import LLMService
from app.services.llm.prompt_templates import ROUTER_SYSTEM_PROMPT
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.llm import LLMConfig
from app.agent.config import ChatConfigHelper, BotRetrievalConfig

logger = get_logger(__name__)


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
    # Cache for retrieval results to avoid repeated expensive operations
    self._retrieval_cache = {}

  def clear_cache(self):
    """Clear the retrieval cache."""
    self._retrieval_cache.clear()
    logger.info("[Retrieval]: Cache cleared")

  async def pre_retrieval_rag(
      self,
      history: List[BaseMessage],
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

    Results are cached to avoid repeated expensive operations.
    """
    # Create cache key
    # For object list, we just hash the length + last message content for simple caching
    history_signature = f"{len(history)}:{history[-1].content if history else 'empty'}"

    cache_key_data = {
        "history_sig": history_signature,
        "query": query,
        "bot_id": bot.get("id"),
        "tenant_id": tenant_id,
        "llm_config": {
            "provider": llm_config.provider,
            "model": llm_config.model,
            "temperature": llm_config.temperature
        },
        "kb_ids": sorted([str(k) for k in (bot.get("kb_ids") or [])])
    }

    cache_key = hashlib.md5(json.dumps(
      cache_key_data, sort_keys=True).encode()).hexdigest()

    # Check cache (5 minute cache)
    current_time = time.time()
    if cache_key in self._retrieval_cache:
      cached_result, timestamp = self._retrieval_cache[cache_key]
      if current_time - timestamp < 300:  # 5 minutes
        logger.info(f"[Retrieval]: Using cached result for query: {query}")
        return cached_result
      else:
        # Remove expired cache entry
        del self._retrieval_cache[cache_key]

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
        result = (rewritten_query, [])
        self._retrieval_cache[cache_key] = (result, current_time)
        return result

      target_kb_ids = await self.route_to_kbs(
          rewritten_query,
          kb_ids,
          tenant_id,
          access_token
      )
      logger.info(
        f"[Retrieval]: KB filtering took {time.perf_counter() - t1:.2f}s")

      if not target_kb_ids:
        result = (rewritten_query, [])
        self._retrieval_cache[cache_key] = (result, current_time)
        return result

      # --- HyDE Step (Hypothetical Document Embeddings) ---
      t_hyde = time.perf_counter()
      hyde_doc = await self.llm_service.generate_hyde_doc(rewritten_query, llm_config)
      logger.info(
        f"[Retrieval]: HyDE Generation took {time.perf_counter() - t_hyde:.2f}s")
      logger.info(f"[Retrieval]: Hypothetical Answer: {hyde_doc[:100]}...")

      # 3. Parallel Search
      # We search for:
      #  a) The Decomposed Queries (Keyword/Concept focus)
      #  b) The Rewritten Query (Semantic focus)
      #  c) The HyDE Document (Answer-similarity focus)

      search_queries = decomposed_queries if decomposed_queries else [
        rewritten_query]

      # Add HyDE doc to search tasks (Treating the hypothetical answer as a query string)
      if hyde_doc and len(hyde_doc) > 20:
        search_queries.append(hyde_doc)

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

      result = (rewritten_query, documents)
      # Cache the result
      self._retrieval_cache[cache_key] = (result, current_time)

      return result

    except Exception as e:
      logger.error(
        f"[Retrieval]: Pre-retrieval RAG failed: {e}", exc_info=True)
      result = (query, [])
      self._retrieval_cache[cache_key] = (result, current_time)
      return result

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
            (query_text, kb_parsed.embedding_provider, kb_parsed.embedding_model))

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
            precomputed_dense_vector=precomputed_vec,
            provider=kb_parsed.embedding_provider
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
          chunk_id = res.get("id")
          if chunk_id and chunk_id in seen_ids:
            continue

          if chunk_id:
            seen_ids.add(chunk_id)
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
    retrieved_chunk_ids = []
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

      # Collect ID for Graph Traversal
      chunk_id = r.get("id")
      if chunk_id:
        retrieved_chunk_ids.append(chunk_id)

    # 7. Graph Traversal (Context Enrichment)
    if retrieved_chunk_ids:
      try:
        logger.info(
          f"[Retrieval]: Traversing Graph Edges for {len(retrieved_chunk_ids)} nodes.")
        from app.core.factory import get_graph_edge_repository
        edge_repo = get_graph_edge_repository()

        edges = await edge_repo.get_edges_by_chunk_ids(retrieved_chunk_ids, access_token)
        if edges:
          graph_relationships = set()
          for edge in edges:
            rel_text = edge.get("properties", {}).get("source_text")
            if rel_text:
              graph_relationships.add(rel_text)

          if graph_relationships:
            logger.info(
              f"[Retrieval]: Found {len(graph_relationships)} graph relationships.")
            graph_context_text = "Knowledge Graph Context (Relationships):\n" + "\n".join(
              f"- {rel}" for rel in graph_relationships) + "\n---"

            # Prepend Graph Context as the highest priority document
            graph_doc = Document(
                page_content=graph_context_text,
                metadata={"source": "Knowledge Graph", "type": "graph_context"}
            )
            documents.insert(0, graph_doc)
      except Exception as e:
        logger.error(
          f"[Retrieval]: Failed during Graph Traversal: {e}", exc_info=True)

    return documents

  async def precompute_embeddings(
      self,
      search_tasks: List[Tuple[str, List[str]]],
      kb_configs_map: Dict
  ) -> Dict[Tuple[str, str, str], List[float]]:
    """
    Identifies all unique (query, model) pairs and computes embeddings in parallel.
    Returns a cache dict: {(text, provider, model_name): vector}
    Results are cached to avoid recomputation.
    """
    # Create cache key for embeddings
    cache_key_data = {
        "tasks": [(q, sorted(kbs)) for q, kbs in search_tasks],
        "kb_configs": {k: (v.get("embedding_provider"), v.get("embedding_model")) for k, v in kb_configs_map.items()}
    }

    # Simple hash of the cache key data
    cache_key = hashlib.md5(str(cache_key_data).encode()).hexdigest()

    # Check if we have cached embeddings (10 minute cache)
    current_time = time.time()
    if hasattr(self, '_embedding_cache') and cache_key in self._embedding_cache:
      cached_result, timestamp = self._embedding_cache[cache_key]
      if current_time - timestamp < 600:  # 10 minutes
        logger.info("[Retrieval]: Using cached embeddings")
        return cached_result
      else:
        # Remove expired cache entry
        del self._embedding_cache[cache_key]

    # 2a. Identify unique (query_text, provider, model_name) pairs

    def get_model_info_for_kb(kb_id_inner):
      raw_kb_config = kb_configs_map.get(kb_id_inner)
      kb_parsed = self.config_helper.parse_kb_config(raw_kb_config)
      return (kb_parsed.embedding_provider, kb_parsed.embedding_model)

    needed_embeddings = set()
    for q_text, kbs in search_tasks:
      for kbid in kbs:
        provider, model = get_model_info_for_kb(kbid)
        needed_embeddings.add((q_text, provider, model))

    embedding_cache = {}

    async def fetch_embedding(text: str, provider: str, model_name: str):
      try:
        from app.core.factory import get_embedding_model
        svc = await get_embedding_model(provider=provider, model=model_name)
        vectors = await svc.aget_text_embedding_batch([text])
        return text, provider, model_name, vectors[0] if vectors else []
      except Exception as e:
        logger.error(
            f"[Retrieval]: Failed to pre-compute embedding for {provider}/{model_name}: {e}")
        return text, provider, model_name, []

    embed_tasks = [fetch_embedding(t, p, m) for t, p, m in needed_embeddings]
    if embed_tasks:
      embed_results = await asyncio.gather(*embed_tasks)
      for txt, prov, mod, vec in embed_results:
        embedding_cache[(txt, prov, mod)] = vec

    # Cache the embeddings
    if not hasattr(self, '_embedding_cache'):
      self._embedding_cache = {}
    self._embedding_cache[cache_key] = (embedding_cache, current_time)

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
