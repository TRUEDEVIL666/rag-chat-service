# app/services/indexer/embedding_service.py

import openai
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


# ------------------
# EMBEDDING SERVICE
# ------------------
class EmbeddingService:
  def __init__(
      self,
      provider: str = "ollama",
      endpoint: str = settings.OLLAMA_EMBEDDING_API_URL,
      model_name: str = None,
      api_key: str = None,
      max_tokens_per_batch: int = 300_000,
  ):
    self.provider = provider
    self.endpoint = endpoint
    self.model_name = model_name
    self.api_key = api_key
    self.max_tokens_per_batch = max_tokens_per_batch

  # ------------------
  # HELPER METHODS
  # ------------------
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

  # ------------------
  # MAIN EMBEDDING LOGIC
  # ------------------
  async def embed_texts(self, texts: List[str]) -> List[List[float]]:
    if not texts:
      raise HTTPException(status_code=422, detail="No texts to embed.")

    if not self.model_name:
      raise HTTPException(
        status_code=500, detail="EmbeddingService has no configured model_name.")

    logger.info(
      f"Embedding {len(texts)} chunks using provider '{self.provider}' and model '{self.model_name}'")

    if self.provider == "openai":
      return await self._embed_openai(texts)
    elif self.provider == "google":
      return await self._embed_google(texts)
    else:
      return await self._embed_ollama(texts)

  # ------------------
  # PROVIDER IMPLEMENTATIONS
  # ------------------
  async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
    try:
      client = openai.AsyncOpenAI(api_key=self.api_key)
      batches = self._batch_by_token_limit(texts)
      results = []

      for batch in batches:
        response = await client.embeddings.create(
            input=batch,
            model=self.model_name
        )
        results.extend([data.embedding for data in response.data])

      return results
    except Exception as e:
      logger.exception("OpenAI embedding failed")
      raise HTTPException(
        status_code=500, detail=f"OpenAI embedding error: {str(e)}")

  async def _embed_google(self, texts: List[str]) -> List[List[float]]:
    try:
      from google import genai
      from google.genai import types

      client = genai.Client(api_key=self.api_key)
      results = []

      batches = self._batch_by_token_limit(texts)

      for batch in batches:
        response = await client.models.embed_content(
            model=self.model_name,
            contents=batch,
            # TODO: Ask for consultation on this particular part
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        if response.embeddings:
          results.extend([emb.values for emb in response.embeddings])

      return results

    except Exception as e:
      logger.exception("Google embedding failed")
      raise HTTPException(
          status_code=500, detail=f"Google embedding error: {str(e)}")

  async def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
    batches = self._batch_by_token_limit(texts)
    results = []

    try:
      async with httpx.AsyncClient(timeout=300.0) as client:
        for i, batch in enumerate(batches):
          logger.info(
            f"Embedding batch {i + 1}/{len(batches)} with {len(batch)} chunks")

          payload = {
              "input": batch,
              "model": self.model_name,
          }

          target_endpoint = self.endpoint or settings.OLLAMA_EMBEDDING_API_URL
          response = await client.post(target_endpoint, json=payload)

          if response.status_code != 200:
            logger.error(f"Embedding failed on batch {i + 1}: {response.text}")
            raise HTTPException(status_code=response.status_code,
                                detail=f"Embedding error: {response.text}")

          data = response.json()
          logger.debug(f"Embedding service response for batch {i + 1}: {data}")

          if "embeddings" not in data or not isinstance(data["embeddings"], list):
            logger.error(
              f"Invalid embedding response structure for batch {i + 1}: {data}")
            raise HTTPException(
              status_code=500, detail="Invalid embedding response structure")

          results.extend(data["embeddings"])

      logger.info("All embeddings completed successfully")
      return results

    except Exception as e:
      logger.exception("Failed to generate embeddings")
      if isinstance(e, HTTPException):
        raise e
      raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")


# ------------------
# WRAPPER CLASS
# ------------------
class CustomEmbedding(BaseEmbedding):
  _embedding_service: EmbeddingService = PrivateAttr()

  def __init__(self, embedding_service: EmbeddingService, **kwargs):
    super().__init__(model_name=embedding_service.model_name, **kwargs)
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
      logger.info(
        f"[CustomEmbedding] Embedding {len(texts)} texts via embedding_service")
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
