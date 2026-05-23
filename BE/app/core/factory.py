from __future__ import annotations

import asyncio

from langchain_core.language_models.chat_models import BaseChatModel
from llama_index.core.base.embeddings.base import BaseEmbedding

from app.config.config import settings
from app.core.logger import get_logger
from app.services.embedding_service import create_embedding_model

logger = get_logger(__name__)

# ----------------------------------------------------------------
# SINGLETON INSTANCES (CACHED LOCALLY FOR BACKWARD COMPATIBILITY)
# ----------------------------------------------------------------
_embedding_model_cache: dict[str, BaseEmbedding] = {}
_embedding_model_lock = asyncio.Lock()


# ----------------------------------------------------------------
# CORE SERVICES
# ----------------------------------------------------------------
async def get_embedding_model(provider: str, model: str) -> BaseEmbedding:
  global _embedding_model_cache, _embedding_model_lock

  if not provider or not model:
    logger.error(f"[Factory]: Missing provider ({provider}) or model ({model})")
    raise ValueError(
      "Both provider and model name must be provided. There is no default embedding model."
    )

  cache_key = f"{provider}:{model}"

  # 1. Quick check outside lock
  if cache_key in _embedding_model_cache:
    return _embedding_model_cache[cache_key]

  # 2. Synchronized creation
  async with _embedding_model_lock:
    # Double-check inside lock
    if cache_key in _embedding_model_cache:
      return _embedding_model_cache[cache_key]

    api_key = None
    endpoint = None

    try:
      from app.repositories import AiModelRepository

      (
        resolved_key,
        resolved_url,
        _,
      ) = await AiModelRepository.get_instance().resolve_model_config(
        provider_name=provider, model_name=model
      )
      api_key = resolved_key
      endpoint = resolved_url

      # Defaults for Ollama if not in DB
      if not endpoint and provider.lower() == "ollama":
        endpoint = settings.OLLAMA_EMBEDDING_API_URL

    except Exception as e:
      logger.warning(f"Failed to resolve config for {provider} from DB: {e}")
      if provider.lower() == "ollama":
        endpoint = settings.OLLAMA_EMBEDDING_API_URL

    new_model = create_embedding_model(
      provider=provider,
      model_name=model,
      api_key=api_key,
      endpoint=endpoint,
    )
    _embedding_model_cache[cache_key] = new_model

    return new_model


async def get_llm(provider: str = None, model: str = None) -> BaseChatModel:
  """
  Factory for LLM models (ChatOpenAI, ChatGoogleGenerativeAI, ChatOllama).
  """
  p = provider or settings.DEFAULT_LLM_PROVIDER
  m = model or settings.DEFAULT_LLM_MODEL

  api_key = None
  endpoint = None

  try:
    if p:
      from app.repositories import AiModelRepository

      (
        resolved_key,
        resolved_url,
        _,
      ) = await AiModelRepository.get_instance().resolve_model_config(
        provider_name=p, model_name=m
      )
      api_key = resolved_key
      endpoint = resolved_url

  except Exception as e:
    logger.warning(f"Failed to resolve config for {p} from DB: {e}")

  if "openai" in p.lower():
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
      model=m,
      api_key=api_key,
      base_url=endpoint,
      temperature=settings.DEFAULT_CHAT_TEMPERATURE,
    )
  elif "google" in p.lower():
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
      model=m, google_api_key=api_key, temperature=settings.DEFAULT_CHAT_TEMPERATURE
    )
  elif "ollama" in p.lower():
    from langchain_ollama import ChatOllama

    target_url = endpoint or settings.OLLAMA_EMBEDDING_API_URL
    return ChatOllama(
      model=m, base_url=target_url, temperature=settings.DEFAULT_CHAT_TEMPERATURE
    )
  else:
    raise ValueError(f"Unsupported LLM provider: {p}")


def get_vector_store():
  from app.repositories.vector_repository import VectorRepository

  return VectorRepository.get_instance()


def get_graph_edge_repository():
  from app.repositories.graph_edge_repository import GraphEdgeRepository

  return GraphEdgeRepository.get_instance()


def get_graph_entity_repository():
  from app.repositories.graph_entity_repository import GraphEntityRepository

  return GraphEntityRepository.get_instance()
