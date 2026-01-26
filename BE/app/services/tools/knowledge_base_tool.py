from typing import List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.llm.llm_service import LLMService
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.indexer.vector_store import VectorRepository
import logging
import asyncio

logger = logging.getLogger(__name__)


class KnowledgeBaseToolInput(BaseModel):
  query: str = Field(description="The user's question or search query.")
  kb_ids: Optional[List[str]] = Field(
      default=None,
      description="List of knowledge base IDs to search. If not provided, searches ALL available KBs."
  )


class KnowledgeBaseTool(BaseTool):
  name: str = "search_knowledge_base"
  description: str = (
      "Search knowledge bases, course materials, and uploaded documents for relevant context. "
      "You can specify kb_ids to narrow the search (ALWAYS do this if looking for a specific document), or leave it empty to search all available KBs."
  )
  args_schema: Type[BaseModel] = KnowledgeBaseToolInput

  # Dependencies injected via constructor
  llm_service: LLMService
  kb_repo: KnowledgeBaseRepository
  vector_repo: VectorRepository
  tenant_id: str
  access_token: Optional[str] = None
  retrieval_config: Optional[dict] = None  # Bot's retrieval settings
  all_available_kb_ids: List[str] = []

  def _run(self, query: str, kb_ids: Optional[List[str]] = None) -> str:
    """Synchronous run not implemented, strictly async."""
    raise NotImplementedError("This tool is async only.")

  async def _arun(self, query: str, kb_ids: Optional[List[str]] = None) -> str:
    """
    Executes the RAG pipeline:
    1. Search Vector DB in specified KBs
    2. Return Context String
    """
    try:
      # Default to all KBs if none specified
      target_kb_ids = kb_ids if kb_ids else self.all_available_kb_ids

      if not target_kb_ids:
        return "No knowledge bases available to search."

      # Fetch KB configs to get embedding models
      kb_configs = {}
      try:
        kb_configs = await asyncio.to_thread(
            self.kb_repo.get_retrieval_configs_by_ids,
            target_kb_ids,
            self.tenant_id,
            access_token=self.access_token
        )
      except Exception as e:
        logger.error(f"Failed to fetch KB configs: {e}")
        return f"Error fetching KB configurations: {e}"

      # Search each KB (they might use different embedding models)
      all_results = []
      for kb_id in target_kb_ids:
        kb_config = kb_configs.get(kb_id)
        if not kb_config:
          continue

        # Extract embedding model
        embedding_model = None
        if kb_config.get("embedding_model"):
          if isinstance(kb_config["embedding_model"], dict):
            embedding_model = kb_config["embedding_model"].get("model_id")
          else:
            embedding_model = kb_config.get("embedding_model")

        if kb_config.get("embedding_provider"):
          provider = kb_config["embedding_provider"].get("name") if isinstance(
              kb_config["embedding_provider"], dict) else kb_config["embedding_provider"]
          if embedding_model and "/" not in embedding_model:
            embedding_model = f"{provider}/{embedding_model}"

        # Search this KB
        try:
          # Use Bot's retrieval config or defaults
          top_k = 5
          score_threshold = 0.4
          if self.retrieval_config:
            top_k = self.retrieval_config.get("top_k", 5)
            score_threshold = self.retrieval_config.get("score_threshold", 0.4)

          results = await self.vector_repo.search(
              query=query,
              k=top_k,
              kb_id=kb_id,
              model_name=embedding_model,
              score_threshold=score_threshold
          )
          all_results.extend(results)
        except Exception as e:
          logger.error(f"Search failed for KB {kb_id}: {e}")

      # Format results
      if not all_results:
        return "No relevant context found."

      context_parts = []
      for r in all_results:
        # Find source KB name
        kb_name = "Unknown KB"
        source_kb_id = r.get("kb_id")  # Assuming search result has kb_id
        if source_kb_id and source_kb_id in kb_configs:
          kb_name = kb_configs[source_kb_id].get("name", "Unknown KB")

        text = r.get("text", "")
        context_parts.append(f"Source (KB: {kb_name}):\n{text}")

      return "\n\n".join(context_parts)

    except Exception as e:
      logger.error(f"KB Search Tool Error: {e}")
      return f"Error occurred during search: {e}"
