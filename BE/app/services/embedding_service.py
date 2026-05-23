# app/services/indexer/embedding_service.py

from typing import Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_ollama import OllamaEmbeddings

# LangChain Providers
from langchain_openai import OpenAIEmbeddings
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.langchain import LangchainEmbedding

from app.config.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def create_embedding_model(
  provider: str,
  model_name: str,
  api_key: Optional[str] = None,
  endpoint: Optional[str] = None,
) -> BaseEmbedding:
  """
  Factory function to create a LlamaIndex-compatible embedding model
  using LangChain integrations.
  """
  try:
    logger.info(
      f"[EmbeddingService] Creating embedding model for {provider}/{model_name}"
    )

    if provider == "openai":
      lc_embed_model = OpenAIEmbeddings(model=model_name, api_key=api_key)

    elif provider == "google":
      lc_embed_model = GoogleGenerativeAIEmbeddings(
        model=f"models/{model_name}"
        if not model_name.startswith("models/")
        else model_name,
        google_api_key=api_key,
      )

    elif provider == "ollama":
      target_endpoint = endpoint or settings.OLLAMA_EMBEDDING_API_URL
      lc_embed_model = OllamaEmbeddings(
        model=model_name,
        base_url=target_endpoint,
      )

    else:
      # TODO: TBC - Add support for other providers or generic fallback
      logger.error(f"[EmbeddingService] Unsupported provider: {provider}")
      raise ValueError(f"Unsupported embedding provider: {provider}")

    return LangchainEmbedding(
      langchain_embeddings=lc_embed_model, model_name=model_name
    )

  except Exception as e:
    logger.exception(f"Failed to create embedding model: {e}")
    raise e
