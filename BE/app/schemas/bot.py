# app/schemas/bot.py
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Any
from uuid import UUID


class BotCreateRequest(BaseModel):
  name: str
  description: Optional[str] = None


class BotResponse(BaseModel):
  id: UUID
  name: str
  description: Optional[str]
  config_prompt: Optional[str]
  config_model: Optional[dict]
  kb_ids: Optional[List[UUID]]
  created_at: datetime
  tenant_id: UUID


class ModelConfig(BaseModel):
  # Provider is now part of the model string (e.g., "ollama/gemma3:4b")
  model: Literal[
    # "gpt-3.5-turbo",
    # "gpt-4",
    "ollama/llama3",
    "ollama/phi3:mini",
    "ollama/phi4:latest",
    "ollama/gpt-oss:20b",
    "ollama/gemma3:4b"
  ] = Field(..., description="Model Name (e.g., provider/model)")

  temperature: float = Field(..., ge=0, le=1, description="Temperature")


class BotUpdateConfigRequest(BaseModel):
  config_prompt: Optional[str] = None
  config_model: Optional[ModelConfig] = None
  kb_ids: Optional[List[UUID]] = None


class BotAskRequest(BaseModel):
  message: str
  streaming: bool = False


class BotAskResponse(BaseModel):
  answer: str
  session_id: Optional[str] = None
  context: Optional[str] = None


class RetrievedChunk(BaseModel):
  content: str
  metadata: Dict[str, Any]
  score: float
