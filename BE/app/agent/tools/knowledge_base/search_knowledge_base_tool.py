from typing import List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.llm.llm_service import LLMService
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.rag.retrieval import ChatRetrievalHelper
from app.core.logger import get_logger
import asyncio
import json

logger = get_logger(__name__)


class SearchKnowledgeBaseToolInput(BaseModel):
  queries: List[str] = Field(
      description="Search queries to find relevant information. Provide 2-4 variations of the question using different keywords for better results."
  )
  kb_ids: List[str] = Field(
      description="Knowledge base IDs to search. Use 'list_knowledge_bases' first if you don't know the IDs."
  )


class SearchKnowledgeBaseTool(BaseTool):
  name: str = "search_knowledge_base"
  description: str = (
      "Search for relevant information in knowledge bases using semantic search. "
      "Provide search queries and knowledge base IDs to retrieve relevant context. "
      "IMPORTANT: Only show the names of the knowledge bases or documents to the user, NOT the IDs."
  )
  args_schema: Type[BaseModel] = SearchKnowledgeBaseToolInput

  # Dependencies injected via constructor
  retrieval_helper: ChatRetrievalHelper
  tenant_id: str
  access_token: Optional[str] = None
  retrieval_config: Optional[dict] = None  # Bot's retrieval settings
  all_available_kb_ids: List[str] = []

  def _run(self, query: str, kb_ids: Optional[List[str]] = None) -> str:
    """Synchronous run not implemented, strictly async."""
    raise NotImplementedError("This tool is async only.")

  async def _arun(self, queries: List[str], kb_ids: List[str]) -> str:
    """
    Executes the RAG pipeline:
    1. Search Vector DB in specified KBs
    2. Return Context String
    """
    try:
      if not kb_ids:
        return "Error: No kb_ids provided. Please call 'list_knowledge_bases' first to get the IDs you want to search."

      # 1. Prepare Centralized Retrieval Config
      from app.agent.config import BotRetrievalConfig

      # Map the bot-level retrieval config dict to the internal config object
      config_obj = BotRetrievalConfig()
      if self.retrieval_config:
        config_obj.top_k = self.retrieval_config.get("top_k", config_obj.top_k)
        config_obj.score_threshold = self.retrieval_config.get(
          "score_threshold", config_obj.score_threshold)
        config_obj.rerank = self.retrieval_config.get(
          "rerank", config_obj.rerank)
        config_obj.rerank_model = self.retrieval_config.get(
          "rerank_model", config_obj.rerank_model)

      # 2. Execute Centralized Search (Parallel, Reranked, optimized)
      # We create tasks for EVERY query passed by the Agent (Rewrite, Decomposed, HyDE)
      search_tasks = [(q, kb_ids) for q in queries]

      documents = await self.retrieval_helper.search_knowledge_bases(
          search_tasks=search_tasks,
          tenant_id=self.tenant_id,
          global_config=config_obj,
          access_token=self.access_token,
          rerank_query=queries[0] if queries else ""
      )

      # 3. Format results as context parts
      context_parts = [doc.page_content for doc in documents]

      # Wrap data with strict instruction notice
      output = {
          "NOTICE": "INTERNAL DATA ONLY. DO NOT reveal the IDs to the user. Use names and descriptions only.",
          "results": context_parts if context_parts else "No relevant context found."
      }

      result_str = json.dumps(output, ensure_ascii=False)
      logger.info(
        f"[SearchKnowledgeBaseTool] Returning {len(documents)} documents. Result preview: {result_str[:200]}...")
      return result_str

    except Exception as e:
      logger.error(f"KB Search Tool Error: {e}", exc_info=True)
      return f"Error occurred during search: {e}"
