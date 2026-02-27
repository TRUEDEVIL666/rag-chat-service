from app.core.logger import get_logger
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.config.config import settings
from app.schemas.llm import LLMConfig
from app.services.ai_model.ai_model_service import AiModelService

logger = get_logger(__name__)


class BotRetrievalConfig(BaseModel):
  top_k: int = 10
  score_threshold: float = 0.4
  rerank: bool = False
  rerank_model: Optional[str] = None


class KBIndexConfig(BaseModel):
  embedding_provider: str
  embedding_model: str
  search_method: str = "semantic"
  auto_merging: bool = False


class ChatConfigHelper:
  def __init__(self, ai_model_service: AiModelService):
    self.ai_model_service = ai_model_service

  async def resolve_model_config(self, bot_config: Dict[str, Any], access_token: str = None) -> LLMConfig:
    """
    Parses bot config to determine provider, model, and temperature.
    Identity is resolved via provider_id/model_id columns.
    Hyperparameters (temperature) are taken from config_model JSONB.
    """
    provider_id = bot_config.get("provider_id")
    model_id = bot_config.get("model_id")
    config_model_json = bot_config.get("config_model") or {}
    system_prompt = bot_config.get("config_prompt")
    temp = config_model_json.get(
        "temperature", settings.DEFAULT_CHAT_TEMPERATURE)

    # 1. Resolve via structured IDs
    # (Simplified for brevity, assuming standard resolution or copy pasted)
    if provider_id and model_id:
      try:
        model_data = await self.ai_model_service.get_model_by_id(str(model_id), access_token=access_token)
        if model_data:
          provider_data = model_data.get("ai_providers", {})
          provider_name = provider_data.get("name", "ollama")

          # Fetch secure API key
          api_key = None
          provider_id = provider_data.get("id")
          if provider_id:
            api_key = await self.ai_model_service.get_decrypted_key(provider_id)

          base_url = provider_data.get("base_url")

          model = model_data.get("model_id")
          return LLMConfig(
              provider=provider_name,
              model=model,
              temperature=temp,
              system_prompt=system_prompt,
              api_key=api_key,
              base_url=base_url
          )
      except Exception as e:
        logger.error(f"Failed to resolve model via structured columns: {e}")
        raise ValueError(f"Failed to resolve model configuration: {e}")

  def parse_kb_config(self, kb_config: Optional[dict]) -> KBIndexConfig:
    """
    Parses KB-specific settings (embedding model, search method).
    """
    if not kb_config:
      raise ValueError("Knowledge Base configuration is missing entirely.")

    embedding_provider = None
    if kb_config.get("embedding_provider") and isinstance(kb_config["embedding_provider"], dict):
      embedding_provider = kb_config["embedding_provider"].get("name")

    if not embedding_provider:
      raise ValueError(
          "Knowledge Base is missing 'embedding_provider' configuration.")

    embedding_model = None
    if kb_config.get("embedding_model"):
      if isinstance(kb_config["embedding_model"], dict):
        embedding_model = kb_config["embedding_model"].get("model_id")
      else:
        embedding_model = kb_config.get("embedding_model")

    if not embedding_model:
      raise ValueError(
          "Knowledge Base is missing 'embedding_model' configuration.")

    # Check retrieval_model JSON for search_method/auto_merging ONLY
    search_method = "semantic"
    auto_merging = False
    if kb_config.get("retrieval_model"):
      rm_raw = kb_config["retrieval_model"]
      rm = {}
      if isinstance(rm_raw, dict):
        rm = rm_raw
      elif isinstance(rm_raw, str):
        import json
        try:
          rm = json.loads(rm_raw)
        except Exception:
          pass

      # Only extract what belongs to KB Indexing
      search_method = rm.get("search_method", "semantic")
      auto_merging = rm.get("auto_merging", False)

    return KBIndexConfig(
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        search_method=search_method,
        auto_merging=auto_merging
    )

  def parse_bot_retrieval_config(self, bot_config: Dict[str, Any]) -> BotRetrievalConfig:
    """
    Parses retrieval config from the Bot's config_model column.
    Uses flattened reranking keys.
    """
    config_model = bot_config.get("config_model") or {}

    # Defaults
    top_k = 10
    score_threshold = 0.4
    rerank = False
    rerank_model = settings.RERANKER_MODEL

    # Parse from config_model
    if config_model.get("top_k") is not None:
      top_k = int(config_model["top_k"])

    if config_model.get("score_threshold_enabled"):
      score_threshold = float(config_model.get("score_threshold", 0.4))

    # Flattened Reranking Logic
    rerank = config_model.get("reranking_enable", False)

    # Try flattened key first, fallback to legacy for safety during transition
    raw_model = config_model.get("reranking_model")
    if not raw_model:
      # Legacy fallback
      reranking_mode = config_model.get("reranking_mode", {})
      raw_model = reranking_mode.get(
          "reranking_model") or reranking_mode.get("model_name")

    if raw_model:
      if "/" in raw_model and not raw_model.startswith("cross-encoder/"):
        _, rerank_model = raw_model.split("/", 1)
      else:
        rerank_model = raw_model

    return BotRetrievalConfig(
        top_k=top_k,
        score_threshold=score_threshold,
        rerank=rerank,
        rerank_model=rerank_model
    )
