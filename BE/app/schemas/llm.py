from typing import Optional
from pydantic import BaseModel


class LLMConfig(BaseModel):
  model: str
  temperature: float
  system_prompt: Optional[str] = None
  api_key: Optional[str] = None
  base_url: Optional[str] = None
  provider: str
  tool_choice: Optional[str] = None


class QueryRefinement(BaseModel):
  rewritten_query: str
  decomposed_queries: list[str] = []


class KbRoutingOutput(BaseModel):
  kb_ids: list[str]
