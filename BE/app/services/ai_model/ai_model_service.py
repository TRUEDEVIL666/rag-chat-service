from typing import List, Dict, Any, Optional
from app.schemas.ai_model import AiModelCreate, AiModelUpdate
from app.config.config import settings
from app.services.supabase.ai_model_repository import AiModelRepository
from app.core.logger import get_logger
import httpx
import json
import openai
from google import genai

logger = get_logger(__name__)


class AiModelService:
  def __init__(self, repo: AiModelRepository):
    self.repo = repo

  async def validate_model_type(self, provider_id: str, model_type: str, access_token: str = None):
    """
    Validates if a model type is supported by the provider.
    """
    provider_id = str(provider_id)
    provider = await self.repo.get_provider_by_id(
      provider_id, access_token=access_token)
    if not provider:
      raise ValueError(f"Provider with id {provider_id} not found.")

    provider_name = provider.get("name", "").lower()

    # Define capabilities
    capabilities = {
      "openai": ["chat", "embedding"],
      "google": ["chat", "embedding"],
      "ollama": ["chat", "embedding"],
      "huggingface": ["chat", "embedding", "reranker"]
    }

    allowed = capabilities.get(
      provider_name, ["chat", "embedding", "reranker"])
    if model_type not in allowed:
      raise ValueError(
        f"Model type '{model_type}' is not supported by provider '{provider_name}'. Supported types: {', '.join(allowed)}")

  async def list_providers(self, access_token: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves all active AI providers.
    """
    try:
      return await self.repo.list_providers(access_token=access_token)
    except Exception as e:
      logger.error(f"Error listing providers: {e}")
      raise

  async def get_models_by_provider(self, provider_id: str, model_type: Optional[str] = None, access_token: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves all active models for a specific provider, optionally filtered by type.
    """
    try:
      return await self.repo.get_models_by_provider(provider_id, model_type=model_type, access_token=access_token)
    except Exception as e:
      logger.error(
        f"Error listing models for provider {provider_id} with type {model_type}: {e}")
      raise

  async def list_models_by_type(self, model_type: str, access_token: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves all active models of a specific type (e.g. 'chat', 'reranker').
    """
    try:
      return await self.repo.list_models_by_type(model_type, access_token=access_token)
    except Exception as e:
      logger.error(f"Error listing models of type {model_type}: {e}")
      raise

  async def list_all_models(self, access_token: str = None) -> List[Dict[str, Any]]:
    try:
      return await self.repo.list_all_models(access_token=access_token)
    except Exception as e:
      logger.error(f"Error listing all models: {e}")
      raise

  async def get_model_by_id(self, model_id: str, access_token: str = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves details for a specific model including its provider.
    """
    try:
      return await self.repo.get_model_by_id(model_id, access_token=access_token)
    except Exception as e:
      logger.error(f"Error fetching model {model_id}: {e}")
      raise

  async def create_provider(self, provider_data: dict, access_token: str = None) -> Dict[str, Any]:
    try:
      return await self.repo.create_provider(provider_data, access_token=access_token)
    except Exception as e:
      logger.error(f"Error creating provider: {e}")
      raise

  async def update_provider(self, provider_id: str, update_data: dict, access_token: str = None) -> Dict[str, Any]:
    try:
      return await self.repo.update_provider(provider_id, update_data, access_token=access_token)
    except Exception as e:
      logger.error(f"Error updating provider {provider_id}: {e}")
      raise

  async def delete_provider(self, provider_id: str, access_token: str = None) -> bool:
    try:
      await self.repo.delete_provider(provider_id, access_token=access_token)
      return True
    except Exception as e:
      logger.error(f"Error deleting provider {provider_id}: {e}")
      raise

  async def create_model(self, model_data: dict, access_token: str = None) -> Dict[str, Any]:
    try:
      await self.validate_model_type(model_data.get(
        "provider_id"), model_data.get("model_type"), access_token=access_token)
      # Ensure provider_id is string after validation
      model_data["provider_id"] = str(model_data["provider_id"])
      return await self.repo.create_model(model_data, access_token=access_token)
    except Exception as e:
      logger.error(f"Error creating model: {e}")
      raise

  async def update_model(self, model_id: str, update_data: dict, access_token: str = None) -> Dict[str, Any]:
    try:
      if "provider_id" in update_data or "model_type" in update_data:
        # Get current model to fill in missing pieces for validation
        current_model = await self.get_model_by_id(
          model_id, access_token=access_token)
        p_id = update_data.get("provider_id", current_model.get("provider_id"))
        m_type = update_data.get("model_type", current_model.get("model_type"))
        await self.validate_model_type(p_id, m_type, access_token=access_token)

      if "provider_id" in update_data:
        update_data["provider_id"] = str(update_data["provider_id"])

      return await self.repo.update_model(model_id, update_data, access_token=access_token)
    except Exception as e:
      logger.error(f"Error updating model {model_id}: {e}")
      raise

  async def delete_model(self, model_id: str, access_token: str = None) -> bool:
    try:
      await self.repo.delete_model(model_id, access_token=access_token)
      return True
    except Exception as e:
      logger.error(f"Error deleting model {model_id}: {e}")
      raise

  async def get_decrypted_key(self, provider_id: str, access_token: str = None) -> Optional[str]:
    try:
      return await self.repo.get_decrypted_key(provider_id, access_token=access_token)
    except Exception as e:
      logger.error(
          f"Error fetching decrypted key for provider {provider_id}: {e}")
      return None

  async def fetch_external_models(self, provider_id: str, model_type: str = None, access_token: str = None) -> List[str]:
    """
    Fetches available models from the external provider's API using official SDKs.
    """
    import asyncio
    try:
      # 1. Get provider details
      provider = await self.repo.get_provider_by_id(
        provider_id, access_token=access_token)
      if not provider:
        raise ValueError(f"Provider with ID {provider_id} not found")

      base_url = provider.get("base_url")
      provider_name = provider.get("name", "").lower()

      # Decrypt API key if it exists
      api_key = await self.repo.get_decrypted_key(
        provider_id, access_token=access_token)

      models = []

      # --- Logic: OpenAI & Compatible (also handles Ollama with /v1) ---
      # If provider is OpenAI OR (Ollama AND base_url ends with /v1)
      is_ollama_v1 = "ollama" in provider_name and base_url and base_url.rstrip(
        "/").endswith("/v1")

      if "openai" in provider_name or is_ollama_v1:
        # Use OpenAI SDK - Synchronous call wrapped in thread for safety
        def _fetch_openai():
          target_url = base_url.rstrip(
            "/") if base_url else "https://api.openai.com/v1"
          client = openai.Client(
            api_key=api_key or "dummy", base_url=target_url)
          response = client.models.list()
          return [model.id for model in response.data]

        models = await asyncio.to_thread(_fetch_openai)

      # --- Logic: Google Gemini ---
      elif "google" in provider_name:
        if not api_key:
          raise ValueError("Google API Key is required for fetching models.")

        def _fetch_google():
          client = genai.Client(api_key=api_key)
          # List models using the new GenAI SDK
          response = client.models.list()
          m_list = []
          for m in response:
            name = getattr(m, "name", "")
            if name:
              m_list.append(name.replace("models/", ""))
          return m_list

        models = await asyncio.to_thread(_fetch_google)

      # --- Logic: Ollama (Native) ---
      elif "ollama" in provider_name:
        import ollama
        target_url = base_url.rstrip(
          "/") if base_url else "http://localhost:11434"

        def _fetch_ollama():
          client = ollama.Client(host=target_url)
          response = client.list()
          if hasattr(response, 'models'):
            return [m.model for m in response.models]
          else:
            return [m['name'] for m in response.get('models', [])]

        models = await asyncio.to_thread(_fetch_ollama)

      return sorted(models)

    except ValueError as e:
      raise e  # Re-raise known value errors
    except Exception as e:
      logger.error(
        f"Unexpected error in fetch_external_models: {e}", exc_info=True)
      raise ValueError(f"Internal service error: {str(e)}")
