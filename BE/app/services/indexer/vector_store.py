# app/services/indexer/vector_store.py
from typing import List, Optional

from app.config.config import settings
from app.core.logger import get_logger
from app.services.indexer.embedding_service import CustomEmbedding, EmbeddingService
from llama_index.core import Document, Settings, VectorStoreIndex, StorageContext
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterOperator
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PayloadSchemaType

logger = get_logger("vector_repository")


def to_qdrant_payload(node: TextNode) -> dict:
	return {
		"_node_content": node.to_dict(),
		**node.metadata,
	}


class VectorRepository:
	"""
	Handles document indexing and semantic search using Qdrant + LlamaIndex.
	"""

	def __init__(
			self,
			embedding_service: EmbeddingService,
			host: str,
			port: int,
			collection: str,
			vector_size: int = 768
	):
		self.host = settings.qdrant_host
		self.port = settings.qdrant_port
		self.qdrant_collection = settings.qdrant_collection or collection
		self.vector_size = vector_size
		self.embedding_service = embedding_service

		Settings.embed_model = CustomEmbedding(self.embedding_service, embed_batch_size=64)

		self.qdrant_client = QdrantClient(
			# url=settings.qdrant_url,
			# api_key=settings.qdrant_token
			host=self.host,
			port=self.port
		)

		self.vector_store = QdrantVectorStore(
			client=self.qdrant_client,
			collection_name="test_documents"
		)
		self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
		self.index: Optional[VectorStoreIndex] = None

	def create_collection(self, collection: Optional[str] = None):
		target_collection = collection or "test_documents"
		if not self.qdrant_client.collection_exists(target_collection):
			logger.info(f"[VectorRepo] Creating Qdrant collection '{target_collection}'")
			self.qdrant_client.create_collection(
				collection_name=target_collection,
				vectors_config=VectorParams(
					size=self.vector_size,
					distance=Distance.COSINE
				)
			)
			self.create_payload_index()
			logger.info(f"[VectorRepo] Collection '{target_collection}' created successfully.")
		else:
			logger.info(f"[VectorRepo] Collection '{target_collection}' already exists.")

	def create_payload_index(self):
		for field in ["kb_id"]:
			try:
				self.qdrant_client.create_payload_index(
					collection_name="test_documents",
					field_name=field,
					field_schema=PayloadSchemaType.KEYWORD
				)
			except Exception as e:
				if "already exists" in str(e):
					logger.info(f"[VectorRepo] Payload index for '{field}' already exists")
				else:
					logger.error(f"[VectorRepo] Failed to create payload index for '{field}': {e}")

	def upsert_documents(self, documents: List[Document]):
		if self.index is None:
			self.index = VectorStoreIndex.from_documents(
				documents=documents,
				storage_context=self.storage_context
			)
		else:
			document_nodes = [
				TextNode(text=doc.text, metadata=doc.metadata)
				for doc in documents
			]
			self.index.insert_nodes(document_nodes)

	async def embed_text(self, text: str) -> List[float]:
		if not text.strip():
			return []
		embeddings = await self.embedding_service.embed_texts([text])
		return embeddings[0] if embeddings else []

	def search(
			self,
			query: str,
			k: int = 5,
			kb_ids: Optional[List[str]] = None,
			score_threshold: float = 0.1
	) -> List[dict]:
		if self.index is None:
			self.index = VectorStoreIndex.from_vector_store(self.vector_store)

		filters = self.build_kb_filter(kb_ids)
		retriever = self.index.as_retriever(similarity_top_k=k, filters=filters, similarity_cutoff=score_threshold)
		results = retriever.retrieve(query)

		filtered_results = [r for r in results if r.score is not None and r.score >= score_threshold]

		return [
			{
				"text": r.text,
				"score": r.score,
				"source": r.metadata.get("source", ""),
				"document_id": r.metadata.get("document_id", "")
			}
			for r in filtered_results
		]

	def build_kb_filter(self, kb_ids: Optional[List[str]]) -> MetadataFilters:
		filters = []
		if kb_ids:
			filters.append(MetadataFilter(key="kb_id", value=kb_ids, operator=FilterOperator.IN))
		return MetadataFilters(filters=filters)
