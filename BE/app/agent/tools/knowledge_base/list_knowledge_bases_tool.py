import json
from typing import List, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.core.logger import get_logger
import asyncio

logger = get_logger(__name__)


class ListKnowledgeBasesInput(BaseModel):
  """Input schema for listing knowledge bases."""
  pass


class ListKnowledgeBasesTool(BaseTool):
  name: str = "list_knowledge_bases"
  description: str = (
      "Source Discovery. Use this to identify available knowledge bases and their metadata. "
      "IMPORTANT: Do NOT reveal the internal IDs to the user; only use them for passing to other tools."
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
    Returns a JSON string of available knowledge bases with explicit privacy instructions.
    """
    try:
      # Fetch KB metadata
      kb_configs = await self.kb_repo.get_retrieval_configs_by_ids(
          self.kb_ids,
          self.tenant_id,
          access_token=self.access_token
      )

      if not kb_configs:
        return json.dumps({
            "NOTICE": "No knowledge bases found.",
            "knowledge_bases": {}
        })

      # Wrap data with a strict instruction notice as suggested
      # This reinforces the system prompt at the point of data delivery
      output = {
          "NOTICE": "INTERNAL DATA ONLY. DO NOT reveal the IDs to the user. Use names and descriptions only.",
          "knowledge_bases": kb_configs
      }

      result_str = json.dumps(output, ensure_ascii=False)
      logger.info(
        f"[ListKnowledgeBasesTool] Returning {len(kb_configs)} knowledge bases. Result preview: {result_str[:200]}...")
      return result_str

    except Exception as e:
      logger.error(f"List KB Tool Error: {e}")
      return json.dumps({"error": f"Error listing knowledge bases: {e}"})
