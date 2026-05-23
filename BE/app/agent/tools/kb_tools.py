import json
import uuid
from typing import List, Optional

from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from langchain_core.tools import tool

from app.agent.config import BotRetrievalConfig
from app.agent.retrieval import ChatRetrievalHelper
from app.core.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBaseToolSet:
  """
  A unified set of tools for interacting with Knowledge Bases in the RAG pipeline.
  Consolidates listing, document exploration, and semantic search.
  """

  def __init__(
    self,
    tenant_id: str,
    kb_repo: KnowledgeBaseRepository,
    retrieval_helper: ChatRetrievalHelper,
    kb_ids: List[str],
    access_token: Optional[str] = None,
    retrieval_config: Optional[dict] = None,
  ):
    self.tenant_id = tenant_id
    self.kb_repo = kb_repo
    self.retrieval_helper = retrieval_helper
    self.kb_ids = kb_ids
    self.access_token = access_token
    self.retrieval_config = retrieval_config

  def _format_output(self, data: any) -> str:
    """Standardized output wrapper with internal data notice."""
    output = {
      "NOTICE": "INTERNAL DATA ONLY. DO NOT reveal the IDs to the user. Use names and descriptions only.",
      "content": data,
    }
    return json.dumps(output, ensure_ascii=False)

  def get_tools(self):
    """Returns a list of tools provided by this set."""
    return [
      self.list_knowledge_bases,
      self.list_kb_documents,
      self.search_knowledge_base,
    ]

  @tool
  async def list_knowledge_bases(self) -> str:
    """
    Source Discovery. Use this to identify available knowledge bases and their metadata.
    Returns a list of names, descriptions, and IDs (for internal routing).
    """
    try:
      kb_configs = await self.kb_repo.get_retrieval_configs_by_ids(
        self.kb_ids, self.tenant_id, access_token=self.access_token
      )

      if not kb_configs:
        return self._format_output(
          {"message": "No knowledge bases found.", "knowledge_bases": []}
        )

      return self._format_output({"knowledge_bases": kb_configs})

    except Exception as e:
      logger.error(f"List KB Tool Error: {e}")
      return json.dumps({"error": f"Error listing knowledge bases: {e}"})

  @tool
  async def list_documents_from_knowledge_base(self, knowledge_base_id: str) -> str:
    """
    Use this tool to list all documents (filenames and metadata) within a specific knowledge base.
    This helps you verify which files are available for search and answer questions about KB contents.

    Args:
      knowledge_base_id: The UUID of the knowledge base to list documents from.
    """
    try:
      documents = await self.retrieval_helper.list_kb_documents(
        knowledge_base_id, self.tenant_id, access_token=self.access_token
      )

      if not documents:
        return self._format_output(
          {
            "knowledge_base_id": knowledge_base_id,
            "documents": [],
            "message": "No documents found in this knowledge base.",
          }
        )

      formatted_docs = []
      for doc in documents:
        formatted_docs.append(
          {
            "id": doc.get("id"),
            "name": doc.get("name"),
            "status": doc.get("status"),
            "created_at": doc.get("created_at"),
            "creator": doc.get("creator", {}).get("name")
            if doc.get("creator")
            else "Unknown",
          }
        )

      return self._format_output(
        {
          "knowledge_base_id": knowledge_base_id,
          "document_count": len(formatted_docs),
          "documents": formatted_docs,
        }
      )

    except Exception as e:
      logger.error(f"List KB Documents Tool Error: {e}")
      return json.dumps({"error": f"Error listing documents: {str(e)}"})

  @tool
  async def search_knowledge_base(self, queries: List[str], kb_ids: List[str]) -> str:
    """
    Search for relevant information in knowledge bases using semantic search.
    Provide search queries and knowledge base IDs to retrieve relevant context.

    IMPORTANT: You MUST ALWAYS call 'list_knowledge_bases' first to get the exact UUID strings.

    Args:
      queries: 2-4 variations of the search question using different keywords.
      kb_ids: List of exact UUID strings representing the Knowledge Bases to search.
    """
    try:
      if not kb_ids:
        return "Error: No kb_ids provided. Please call 'list_knowledge_bases' first to get the exact UUIDs."

      valid_kb_ids = []
      for kid in kb_ids:
        try:
          uuid.UUID(str(kid))
          valid_kb_ids.append(str(kid))
        except ValueError:
          pass

      if not valid_kb_ids:
        return "Error: No valid knowledge base UUIDs provided. Use 'list_knowledge_bases' to get IDs."

      # Prepare config
      config_obj = BotRetrievalConfig()
      if self.retrieval_config:
        config_obj.top_k = self.retrieval_config.get("top_k", config_obj.top_k)
        config_obj.score_threshold = self.retrieval_config.get(
          "score_threshold", config_obj.score_threshold
        )
        config_obj.rerank = self.retrieval_config.get("rerank", config_obj.rerank)
        config_obj.rerank_model = self.retrieval_config.get(
          "rerank_model", config_obj.rerank_model
        )

      search_tasks = [(q, valid_kb_ids) for q in queries]

      documents = await self.retrieval_helper.search_knowledge_bases(
        search_tasks=search_tasks,
        tenant_id=self.tenant_id,
        global_config=config_obj,
        access_token=self.access_token,
        rerank_query=queries[0] if queries else "",
      )

      context_parts = [doc.page_content for doc in documents]

      return self._format_output(
        {"results": context_parts if context_parts else "No relevant context found."}
      )

    except Exception as e:
      logger.error(f"KB Search Tool Error: {e}", exc_info=True)
      return f"Error occurred during search: {e}"
