import asyncio
from app.core.logger import get_logger
from app.core.factory import get_vector_store, get_graph_edge_repository, get_graph_entity_repository, get_embedding_model
import time
import hashlib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from langchain_core.documents import Document
from app.services.llm.llm_service import LLMService
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.supabase.document_repository import DocumentRepository
from app.agent.config import ChatConfigHelper, BotRetrievalConfig

logger = get_logger(__name__)


@dataclass
class ParsedKBConfig:
  """Pre-parsed KB config for fast lookups."""
  embedding_provider: str
  embedding_model: str
  search_method: str
  auto_merging: bool
  top_k: int


class ChatRetrievalHelper:
  # Class-level embedding cache (shared across instances)
  _embedding_cache: Dict[
    str,
    Tuple[Dict[Tuple[str, str, str], List[float]], float]
  ] = {}

  def __init__(
      self,
      llm_service: LLMService,
      kb_repo: KnowledgeBaseRepository,
      doc_repo: DocumentRepository,
      config_helper: ChatConfigHelper
  ):
    self.llm_service = llm_service
    self.kb_repo = kb_repo
    self.doc_repo = doc_repo
    self.config_helper = config_helper
    # Cache for retrieval results to avoid repeated expensive operations
    self._retrieval_cache = {}

  def clear_cache(self):
    """Clear the retrieval cache."""
    self._retrieval_cache.clear()
    logger.info("[Retrieval]: Cache cleared")

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

    # 1. Collect all unique KB IDs to fetch configs once
    all_kb_ids = set()
    for _, kbs in search_tasks:
      for k in kbs:
        all_kb_ids.add(k)

    # Fallback: If no KB IDs provided, search all KBs for the tenant
    if not all_kb_ids:
      logger.info(
        f"[Retrieval]: No KB IDs provided. Searching all accessible KBs for tenant {tenant_id}")
      kb_list, _ = await self.kb_repo.list_knowledge_bases(tenant_id, access_token)
      all_kb_ids = {row["id"] for row in kb_list}
      # Update search_tasks to include all found KB IDs
      search_tasks = [(q, list(all_kb_ids)) for q, _ in search_tasks]

    if not all_kb_ids:
      logger.warning(
        f"[Retrieval]: No Knowledge Bases found for tenant {tenant_id}")
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

    # --- OPTIMIZATION: PRE-PARSE KB CONFIGS ---
    parsed_configs: Dict[str, ParsedKBConfig] = {}
    for kb_id, raw_config in kb_configs_map.items():
      try:
        kb_parsed = self.config_helper.parse_kb_config(raw_config)
        parsed_configs[kb_id] = ParsedKBConfig(
          embedding_provider=kb_parsed.embedding_provider,
          embedding_model=kb_parsed.embedding_model,
          search_method=kb_parsed.search_method,
          auto_merging=kb_parsed.auto_merging,
          top_k=global_config.top_k * 2 if global_config.rerank else global_config.top_k
        )
      except Exception as e:
        logger.warning(
          f"[Retrieval]: Failed to parse config for KB {kb_id}: {e}")

    # --- OPTIMIZATION: PRE-CALCULATE EMBEDDINGS ---
    embedding_cache = await self.precompute_embeddings(search_tasks, parsed_configs)
    # --- END OPTIMIZATION ---

    # 2. Prepare Parallel Search Tasks
    # Filter to only KBs with valid parsed configs
    tasks = []
    valid_search_tasks = [
      (q, kb) for q, kbs in search_tasks
      for kb in kbs if kb in parsed_configs
    ]

    async def search_single_kb_query(kb_id_inner: str, query_text: str):
      try:
        kb_parsed = parsed_configs[kb_id_inner]

        # Retrieve precomputed vector
        precomputed_vec = embedding_cache.get(
            (query_text, kb_parsed.embedding_provider, kb_parsed.embedding_model))

        if not precomputed_vec:
          logger.debug(
              f"[Retrieval]: No precomputed vector for {kb_parsed.embedding_model}, using internal")

        # Execute Search
        results = await get_vector_store().search(
            query=query_text,
            k=kb_parsed.top_k,
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

    for q_text, kbid in valid_search_tasks:
      tasks.append(search_single_kb_query(kbid, q_text))

    # 3. Execute Parallel Search
    if not tasks:
      logger.warning(
        "[Retrieval]: No valid search tasks. Returning empty results.")
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

    # 7. Graph Traversal (Context Enrichment) - only if we have results
    if not retrieved_chunk_ids:
      return documents

    try:
      logger.info(
        f"[Retrieval]: Traversing Graph Edges starting from {len(retrieved_chunk_ids)} chunks.")

      entity_repo = get_graph_entity_repository()
      edge_repo = get_graph_edge_repository()

      # Step 1: Find which entities are mentioned in these chunks
      entity_ids = await entity_repo.get_entities_by_chunk_ids(retrieved_chunk_ids, access_token)
      if entity_ids:
        logger.info(
          f"[Retrieval]: Found {len(entity_ids)} entities mentioned in chunks.")

        # Step 2: Find all graph edges connected to these entities
        edges = await edge_repo.get_edges_by_entity_ids(entity_ids, access_token)

        if edges:
          graph_relationships = set()
          for edge in edges:
            rel_text = edge.get("properties", {}).get("source_text")
            if rel_text:
              graph_relationships.add(rel_text)

          if graph_relationships:
            logger.info(
              f"[Retrieval]: Expanded to {len(graph_relationships)} graph relationships.")
            graph_context_text = "Knowledge Graph Context (Relationships):\n" + "\n".join(
              f"- {rel}" for rel in graph_relationships) + "\n---"

            # Prepend Graph Context as the highest priority document
            graph_doc = Document(
                page_content=graph_context_text,
                metadata={"source": "Knowledge Graph",
                          "type": "graph_context"}
            )
            documents.insert(0, graph_doc)
    except Exception as e:
      logger.error(
        f"[Retrieval]: Failed during Graph Traversal: {e}", exc_info=True)

    return documents

  async def precompute_embeddings(
      self,
      search_tasks: List[Tuple[str, List[str]]],
      parsed_configs: Dict[str, ParsedKBConfig]
  ) -> Dict[Tuple[str, str, str], List[float]]:
    """
    Identifies all unique (query, model) pairs and computes embeddings in parallel.
    Returns a cache dict: {(text, provider, model_name): vector}
    Results are cached to avoid recomputation.
    """
    # Create cache key for embeddings
    cache_key_data = {
        "tasks": [(q, sorted(kbs)) for q, kbs in search_tasks],
        "kb_configs": {k: (v.embedding_provider, v.embedding_model) for k, v in parsed_configs.items()}
    }

    # Simple hash of the cache key data
    cache_key = hashlib.md5(str(cache_key_data).encode()).hexdigest()

    # Check if we have cached embeddings (10 minute cache)
    current_time = time.time()
    if cache_key in ChatRetrievalHelper._embedding_cache:
      cached_result, timestamp = ChatRetrievalHelper._embedding_cache[cache_key]
      if current_time - timestamp < 600:  # 10 minutes
        logger.info("[Retrieval]: Using cached embeddings")
        return cached_result
      else:
        # Remove expired cache entry
        del ChatRetrievalHelper._embedding_cache[cache_key]

    # 2a. Identify unique (query_text, provider, model_name) pairs in a single pass
    needed_embeddings: set = set()
    for q_text, kbs in search_tasks:
      for kbid in kbs:
        config = parsed_configs.get(kbid)
        if config:
          needed_embeddings.add(
            (q_text, config.embedding_provider, config.embedding_model))

    embedding_cache: Dict[Tuple[str, str, str], List[float]] = {}

    async def fetch_embedding(text: str, provider: str, model_name: str):
      try:
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
        if vec:  # Only cache non-empty vectors
          embedding_cache[(txt, prov, mod)] = vec

    # Cache the embeddings at class level
    ChatRetrievalHelper._embedding_cache[cache_key] = (
      embedding_cache, current_time)

    return embedding_cache

  async def list_kb_documents(self, kb_id: str, tenant_id: str, access_token: str = None) -> List[dict]:
    """
    Lists all documents in a specific knowledge base.
    """
    try:
      return await self.doc_repo.get_documents_by_kb(kb_id, tenant_id, access_token)
    except Exception as e:
      logger.exception(
        f"[Retrieval]: Failed to list documents for KB {kb_id}: {e}")
      return []
