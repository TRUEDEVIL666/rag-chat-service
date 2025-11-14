# app/schemas/bot.py
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Any


class BotCreateRequest(BaseModel):
	name: str
	description: Optional[str] = None


class BotResponse(BaseModel):
	id: str
	name: str
	description: Optional[str]
	config_prompt: Optional[str]
	config_model: Optional[dict]
	kb_ids: Optional[List[str]]
	created_at: datetime
	tenant_id: str


class ModelConfig(BaseModel):
	model: Literal["gpt-3.5-turbo", "gpt-4", "llama3", "phi4:latest", "gpt-oss:20b"] = Field(...,
	                                                                                         description="Name")  # đoạn này m để option cũng được, nhưng m nên để bắt buộc chọn 1 trong các model đã đăng ký (user mà truyền sai thì sao chạy đc)
	temperature: float = Field(..., ge=0, le=1,
	                           description="Temperature")  # đoạn này cũng nên bắt buộc chọn, có thể để default là 0.7, ge le là limit của temp á, 0 -> 1


class BotUpdateConfigRequest(BaseModel):
	config_prompt: Optional[str] = None
	config_model: Optional[ModelConfig] = None
	kb_ids: Optional[List[str]] = None


class BotAskRequest(BaseModel):
	message: str
	streaming: bool = False
	# history: Optional[List[Tuple[str, str]]] = None


class BotAskResponse(BaseModel):
	answer: str
	context: Optional[str] = None


class RetrievedChunk(BaseModel):
	content: str
	metadata: Dict[str, Any]
	score: float
