from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Annotated
from uuid import UUID

from fastapi import Path, Query
from pydantic import BaseModel, Field

from app.schemas.ai_model import AiModelResponse, AiProviderResponse


class ModelConfig(BaseModel):
  temperature: Annotated[
    float,
    Field(ge=0, le=1, description="Temperature")
  ]
  top_k: Annotated[
    Optional[int],
    Field(description="Top K results to retrieve")
  ] = 10
  score_threshold: Annotated[
    Optional[float],
    Field(description="Similarity score threshold")
  ] = 0.4
  score_threshold_enabled: Annotated[
    Optional[bool],
    Field(description="Enable similarity threshold")
  ] = False
  reranking_enable: Annotated[
    Optional[bool],
    Field(description="Enable reranking")
  ] = False
  reranking_model: Annotated[
    Optional[str],
    Field(description="Reranking model name")
  ] = None


class BotCreateRequest(BaseModel):
  name: str
  description: Optional[str] = None
  provider_id: Optional[UUID] = None
  model_id: Optional[UUID] = None
  config_prompt: Optional[str] = None
  config_model: Optional[ModelConfig] = None


class BotResponse(BaseModel):
  id: UUID
  name: str
  description: Optional[str]
  config_prompt: Optional[str]
  config_model: Optional[dict]
  provider_id: Optional[UUID]
  model_id: Optional[UUID]
  kb_ids: Optional[List[UUID]]
  created_at: datetime
  tenant_id: UUID
  provider: Optional[AiProviderResponse] = None
  model: Optional[AiModelResponse] = None
  knowledge_bases: Optional[List[Dict[str, Any]]] = None


class BotUpdateConfigRequest(BaseModel):
  name: Optional[str] = None
  description: Optional[str] = None
  config_prompt: Optional[str] = None
  config_model: Optional[ModelConfig] = None
  provider_id: Optional[UUID] = None
  model_id: Optional[UUID] = None
  kb_ids: Optional[List[UUID]] = None


class BotAskRequest(BaseModel):
  message: str
  streaming: bool = False
  quiz_mode: bool = False


class BotAskResponse(BaseModel):
  answer: str
  session_id: Optional[str] = None
  context: Optional[str] = None


class RetrievedChunk(BaseModel):
  content: str
  metadata: Dict[str, Any]
  score: float


class BotIdRequest(BaseModel):
  bot_id: Annotated[UUID, Path(description="Bot ID")]


class BotUpdateConfigIdRequest(BaseModel):
  bot_id: Annotated[UUID, Path(description="Bot ID")]


class BotAskIdRequest(BaseModel):
  bot_id: Annotated[UUID, Path(description="Bot ID")]
  session_id: Optional[str] = None
