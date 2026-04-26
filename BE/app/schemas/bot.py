from typing import List, Optional
from pydantic import BaseModel

class BotKBItem(BaseModel):
  id: str
  name: str
  description: Optional[str] = None

class BotItem(BaseModel):
  id: str
  name: str
  description: Optional[str] = None
  config_prompt: Optional[str] = None
  config_model: Optional[dict] = None
  provider_id: Optional[str] = None
  model_id: Optional[str] = None
  knowledge_bases: Optional[List[BotKBItem]] = []

class BotResponse(BaseModel):
  id: str
  name: str
  description: Optional[str] = None
  knowledge_bases: List[BotKBItem]
