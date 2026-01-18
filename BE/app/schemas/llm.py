from typing import Optional
from pydantic import BaseModel


class LLMConfig(BaseModel):
  model: str
  temperature: float
  system_prompt: Optional[str] = None
  api_key: Optional[str] = None
  base_url: Optional[str] = None
  provider: str
