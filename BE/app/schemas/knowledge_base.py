from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class KnowledgeBaseCreateRequest(BaseModel):
	name: str
	description: Optional[str] = None


class KnowledgeBaseItem(BaseModel):
	id: str
	name: str
	description: Optional[str] = None
	# provider: Optional[str] = None
	# permission: Optional[str] = None
	# data_source_type: Optional[str] = None
	# indexing_technique: Optional[str] = None
	# app_count: int = 0
	# document_count: int = 0
	# word_count: int = 0
	# created_by: Optional[str] = None
	created_at: int
	# updated_by: Optional[str] = None
	updated_at: int
	embedding_model: Optional[str] = None
	# embedding_model_provider: Optional[str] = None
	# embedding_available: Optional[bool] = None


class KnowledgeBaseListResponse(BaseModel):
	data: List[KnowledgeBaseItem]
	has_more: bool
	limit: int
	total: int
	page: int


class RetrievalModel(BaseModel):
	search_method: str
	reranking_enable: bool
	reranking_mode: Optional[Dict[str, Any]] = None
	top_k: int
	score_threshold_enabled: bool
	score_threshold: Optional[float] = None
	weights: Optional[float] = None


class KnowledgeBaseInput(BaseModel):
	name: str
	description: str
	# indexing_technique: str
	# permission: str
	# embedding_model_provider: Optional[str] = None
	embedding_model: Optional[str] = None
	# retrieval_model: RetrievalModel
	# partial_member_list: Optional[List[str]] = None


class KnowledgeBaseResponse(BaseModel):
	id: str
	name: str
	description: Optional[str] = None
	# retrieval_model: RetrievalModel


class RetrievalModeSchema(BaseModel):
	reranking_provider_name: Optional[str] = None
	reranking_model_name: Optional[str] = None


class RetrievalModelSchema(BaseModel):
	search_method: str
	reranking_enable: bool
	reranking_mode: Optional[RetrievalModeSchema] = None
	top_k: int
	score_threshold_enabled: bool
	score_threshold: Optional[float] = None
	weights: Optional[float] = None


class KnowledgeBaseDetail(BaseModel):
	id: str
	name: str
	description: Optional[str] = None
	provider: Optional[str] = None
	permission: Optional[str] = None
	data_source_type: Optional[str] = None
	indexing_technique: Optional[str] = None
	app_count: int
	document_count: int
	word_count: int
	created_by: Optional[str] = None
	created_at: int
	updated_by: Optional[str] = None
	updated_at: int
	embedding_model: Optional[str] = None
	embedding_model_provider: Optional[str] = None
	embedding_available: Optional[bool] = None
	retrieval_model_dict: RetrievalModelSchema
	tags: List[Dict[str, Any]]
	doc_form: Optional[str] = None


class UpdateRerankingMode(BaseModel):
	reranking_provider_name: Optional[str] = None
	reranking_model_name: Optional[str] = None


class UpdateRetrievalModel(BaseModel):
	search_method: Optional[str] = None
	reranking_enable: Optional[bool] = None
	reranking_mode: Optional[UpdateRerankingMode] = None
	top_k: Optional[int] = None
	score_threshold_enabled: Optional[bool] = None
	score_threshold: Optional[float] = None
	weights: Optional[float] = None


class UpdateKnowledgeBaseRequest(BaseModel):
	name: Optional[str] = None
	description: Optional[str] = None
	indexing_technique: Optional[str] = None
	permission: Optional[str] = None
	embedding_model_provider: Optional[str] = None
	embedding_model: Optional[str] = None
	retrieval_model: Optional[UpdateRetrievalModel] = None
	partial_member_list: Optional[List[str]] = None
