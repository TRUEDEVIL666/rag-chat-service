from typing import List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
import logging
import asyncio

logger = logging.getLogger(__name__)


class ListKnowledgeBasesInput(BaseModel):
  """Input schema for listing knowledge bases."""
  pass


class ListKnowledgeBasesTool(BaseTool):
  name: str = "list_knowledge_bases"
  description: str = (
      "Lists all available knowledge bases with their names and descriptions. "
      "Use this to understand what knowledge bases are available before searching."
  )
  args_schema: Type[BaseModel] = ListKnowledgeBasesInput

  # Dependencies
  kb_repo: KnowledgeBaseRepository
  kb_ids: List[str]
  tenant_id: str
  access_token: Optional[str] = None

  def _run(self) -> str:
    """Synchronous run not implemented."""
    raise NotImplementedError("This tool is async only.")

  async def _arun(self) -> str:
    """
    Returns a formatted list of available knowledge bases.
    """
    try:
      # Fetch KB metadata
      kb_configs = await asyncio.to_thread(
          self.kb_repo.get_retrieval_configs_by_ids,
          self.kb_ids,
          self.tenant_id,
          access_token=self.access_token
      )

      if not kb_configs:
        return "No knowledge bases available."

      # Format as readable list
      kb_list = []
      for kb_id, config in kb_configs.items():
        name = config.get("name", "Unknown")
        description = config.get("description", "No description available.")
        kb_list.append(
          f"- ID: {kb_id}\n  Name: {name}\n  Description: {description}")

      return "Available Knowledge Bases:\n\n" + "\n\n".join(kb_list)

    except Exception as e:
      logger.error(f"List KB Tool Error: {e}")
      return f"Error listing knowledge bases: {e}"
