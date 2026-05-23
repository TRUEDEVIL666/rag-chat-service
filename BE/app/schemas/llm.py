from typing import Optional

from pydantic import BaseModel


class LLMConfig(BaseModel):
  model: str
  temperature: float
  system_prompt: Optional[str] = None
  api_key: Optional[str] = None
  base_url: Optional[str] = None
  provider: str


class QueryRefinement(BaseModel):
  rewritten_query: str
  decomposed_queries: list[str] = []


class KbRoutingOutput(BaseModel):
  kb_ids: list[str]


class PlannerOutput(BaseModel):
  use_memori: bool
  use_rag: bool
  use_tools: bool = False
  direct: bool = False


class HallucinationGrade(BaseModel):
  score: bool
