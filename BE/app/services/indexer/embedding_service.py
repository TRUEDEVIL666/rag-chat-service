# app/services/indexer/embedding_service.py
import httpx
import tiktoken
import asyncio
from typing import List
from fastapi import HTTPException

from app.core.logger import get_logger
from app.config.config import settings

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.bridge.pydantic import PrivateAttr

logger = get_logger("embedding")


class EmbeddingService:
	def __init__(
			self,
			endpoint: str = settings.embedding_api_url,
			model_name: str = settings.embedding_model,
			max_tokens_per_batch: int = 300_000,
	):
		self.endpoint = endpoint
		self.model_name = model_name
		self.max_tokens_per_batch = max_tokens_per_batch

	def _num_tokens(self, text: str) -> int:
		"""Estimate token count using appropriate encoding."""
		try:
			encoding = tiktoken.encoding_for_model(self.model_name)
		except KeyError:
			encoding = tiktoken.get_encoding("cl100k_base")
		return len(encoding.encode(text))

	def _batch_by_token_limit(self, texts: List[str]) -> List[List[str]]:
		"""Group texts into batches where total token count ≤ max_tokens_per_batch."""
		batches = []
		current_batch = []
		current_tokens = 0

		for text in texts:
			tokens = self._num_tokens(text)

			if tokens > self.max_tokens_per_batch:
				logger.warning(f"Skipping long chunk with {tokens} tokens")
				continue

			if current_tokens + tokens > self.max_tokens_per_batch:
				batches.append(current_batch)
				current_batch = [text]
				current_tokens = tokens
			else:
				current_batch.append(text)
				current_tokens += tokens

		if current_batch:
			batches.append(current_batch)
		return batches

	async def embed_texts(self, texts: List[str]) -> List[List[float]]:
		if not texts:
			raise HTTPException(status_code=422, detail="No texts to embed.")

		logger.info(f"Embedding {len(texts)} chunks using model '{self.model_name}'")
		batches = self._batch_by_token_limit(texts)
		results = []

		try:
			async with httpx.AsyncClient(timeout=60.0) as client:
				for i, batch in enumerate(batches):
					logger.info(f"Embedding batch {i + 1}/{len(batches)} with {len(batch)} chunks")

					payload = {
						"input": batch,
						"model": self.model_name,
					}

					response = await client.post(self.endpoint, json=payload)

					if response.status_code != 200:
						logger.error(f"Embedding failed on batch {i + 1}: {response.text}")
						raise HTTPException(status_code=response.status_code, detail=f"Embedding error: {response.text}")

					data = response.json()
					logger.debug(f"Embedding service response for batch {i + 1}: {data}")

					if "embeddings" not in data or not isinstance(data["embeddings"], list):
						logger.error(f"Invalid embedding response structure for batch {i + 1}: {data}")
						raise HTTPException(status_code=500, detail="Invalid embedding response structure")

					results.extend(data["embeddings"])

			logger.info("All embeddings completed successfully")
			return results

		except Exception as e:
			logger.exception("Failed to generate embeddings")
			if isinstance(e, HTTPException):
				raise e
			raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")


class CustomEmbedding(BaseEmbedding):
	_embedding_service: EmbeddingService = PrivateAttr()

	def __init__(self, embedding_service: EmbeddingService, **kwargs):
		super().__init__(**kwargs)
		self._embedding_service = embedding_service

	def _get_query_embedding(self, query: str) -> List[float]:
		try:
			loop = asyncio.get_running_loop()
			import nest_asyncio
			nest_asyncio.apply()
			return loop.run_until_complete(self._embedding_service.embed_texts([query]))[0]
		except RuntimeError:
			return asyncio.run(self._embedding_service.embed_texts([query]))[0]

	def _get_text_embedding(self, text: str) -> List[float]:
		return self._get_query_embedding(text)

	def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
		try:
			logger.info(f"[CustomEmbedding] Embedding {len(texts)} texts via embedding_service")
			loop = asyncio.get_running_loop()
			import nest_asyncio
			nest_asyncio.apply()
			return loop.run_until_complete(self._embedding_service.embed_texts(texts))
		except RuntimeError:
			return asyncio.run(self._embedding_service.embed_texts(texts))

	async def _aget_query_embedding(self, query: str) -> List[float]:
		return (await self._embedding_service.embed_texts([query]))[0]

	async def _aget_text_embedding(self, text: str) -> List[float]:
		return await self._aget_query_embedding(text)

	async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
		return await self._embedding_service.embed_texts(texts)
