import json
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.agent.retrieval import ChatRetrievalHelper
from app.core.logger import get_logger

logger = get_logger(__name__)


class ListKbDocumentsInput(BaseModel):
  """Input schema for listing documents in a knowledge base."""
  knowledge_base_id: str = Field(
    ..., description="The UUID of the knowledge base to list documents from."
  )


class ListKnowledgeBaseDocumentsTool(BaseTool):
  name: str = "list_knowledge_base_documents"
  description: str = (
    "Use this tool to list all documents (filenames and metadata) within a specific knowledge base. "
    "This helps you verify which files are available for search and answer questions about the contents of a KB."
  )
  args_schema: Type[BaseModel] = ListKbDocumentsInput

  # Dependencies
  retrieval_helper: ChatRetrievalHelper
  tenant_id: str
  access_token: Optional[str] = None

  def _run(self, knowledge_base_id: str) -> str:
    """Synchronous run not implemented."""
    raise NotImplementedError("This tool is async only.")

  async def _arun(self, knowledge_base_id: str) -> str:
    """
    Returns a JSON string of documents within the specified knowledge base.
    """
    try:
      documents = await self.retrieval_helper.list_kb_documents(
        knowledge_base_id,
        self.tenant_id,
        access_token=self.access_token
      )

      if not documents:
        return json.dumps({
          "knowledge_base_id": knowledge_base_id,
          "documents": [],
          "message": "No documents found in this knowledge base."
        })

      # Format the output for the LLM
      formatted_docs = []
      for doc in documents:
        formatted_docs.append({
          "id": doc.get("id"),
          "name": doc.get("name"),
          "status": doc.get("status"),
          "created_at": doc.get("created_at"),
          "creator": doc.get("creator", {}).get("name") if doc.get("creator") else "Unknown"
        })

      output = {
        "knowledge_base_id": knowledge_base_id,
        "document_count": len(formatted_docs),
        "documents": formatted_docs
      }

      result_str = json.dumps(output, ensure_ascii=False)
      logger.info(
        f"[ListKbDocumentsTool] Returning {len(formatted_docs)} documents for KB {knowledge_base_id}")
      return result_str

    except Exception as e:
      logger.error(f"List KB Documents Tool Error: {e}")
      return json.dumps({"error": f"Error listing documents: {str(e)}"})
