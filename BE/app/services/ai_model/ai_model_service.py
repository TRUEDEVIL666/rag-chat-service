from typing import List, Dict, Any, Optional
from app.schemas.ai_model import AiModelCreate, AiModelUpdate
from app.config.config import settings
from app.services.supabase.ai_model_repository import AiModelRepository
import logging
import httpx
import json
import openai
from google import genai

logger = logging.getLogger(__name__)


class AiModelService:
  def __init__(self, repo: AiModelRepository):
    self.repo = repo

  def validate_model_type(self, provider_id: str, model_type: str, access_token: str = None):
    """
    Validates if a model type is supported by the provider.
    """
    provider_id = str(provider_id)
    provider = self.repo.get_provider_by_id(
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

  def list_providers(self, access_token: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves all active AI providers.
    """
    try:
      return self.repo.list_providers(access_token=access_token)
    except Exception as e:
      logger.error(f"Error listing providers: {e}")
      raise

  def get_models_by_provider(self, provider_id: str, model_type: Optional[str] = None, access_token: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves all active models for a specific provider, optionally filtered by type.
    """
    try:
      return self.repo.get_models_by_provider(provider_id, model_type=model_type, access_token=access_token)
    except Exception as e:
      logger.error(
        f"Error listing models for provider {provider_id} with type {model_type}: {e}")
      raise

  def list_models_by_type(self, model_type: str, access_token: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves all active models of a specific type (e.g. 'chat', 'reranker').
    """
    try:
      return self.repo.list_models_by_type(model_type, access_token=access_token)
    except Exception as e:
      logger.error(f"Error listing models of type {model_type}: {e}")
      raise

  def list_all_models(self, access_token: str = None) -> List[Dict[str, Any]]:
    try:
      return self.repo.list_all_models(access_token=access_token)
    except Exception as e:
      logger.error(f"Error listing all models: {e}")
      raise

  def get_model_by_id(self, model_id: str, access_token: str = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves details for a specific model including its provider.
    """
    try:
      return self.repo.get_model_by_id(model_id, access_token=access_token)
    except Exception as e:
      logger.error(f"Error fetching model {model_id}: {e}")
      raise

  def create_provider(self, provider_data: dict, access_token: str = None) -> Dict[str, Any]:
    try:
      return self.repo.create_provider(provider_data, access_token=access_token)
    except Exception as e:
      logger.error(f"Error creating provider: {e}")
      raise

  def update_provider(self, provider_id: str, update_data: dict, access_token: str = None) -> Dict[str, Any]:
    try:
      return self.repo.update_provider(provider_id, update_data, access_token=access_token)
    except Exception as e:
      logger.error(f"Error updating provider {provider_id}: {e}")
      raise

  def delete_provider(self, provider_id: str, access_token: str = None) -> bool:
    try:
      self.repo.delete_provider(provider_id, access_token=access_token)
      return True
    except Exception as e:
      logger.error(f"Error deleting provider {provider_id}: {e}")
      raise

  def create_model(self, model_data: dict, access_token: str = None) -> Dict[str, Any]:
    try:
      self.validate_model_type(model_data.get(
        "provider_id"), model_data.get("model_type"), access_token=access_token)
      # Ensure provider_id is string after validation
      model_data["provider_id"] = str(model_data["provider_id"])
      return self.repo.create_model(model_data, access_token=access_token)
    except Exception as e:
      logger.error(f"Error creating model: {e}")
      raise

  def update_model(self, model_id: str, update_data: dict, access_token: str = None) -> Dict[str, Any]:
    try:
      if "provider_id" in update_data or "model_type" in update_data:
        # Get current model to fill in missing pieces for validation
        current_model = self.get_model_by_id(
          model_id, access_token=access_token)
        p_id = update_data.get("provider_id", current_model.get("provider_id"))
        m_type = update_data.get("model_type", current_model.get("model_type"))
        self.validate_model_type(p_id, m_type, access_token=access_token)

      if "provider_id" in update_data:
        update_data["provider_id"] = str(update_data["provider_id"])

      return self.repo.update_model(model_id, update_data, access_token=access_token)
    except Exception as e:
      logger.error(f"Error updating model {model_id}: {e}")
      raise

  def delete_model(self, model_id: str, access_token: str = None) -> bool:
    try:
      self.repo.delete_model(model_id, access_token=access_token)
      return True
    except Exception as e:
      logger.error(f"Error deleting model {model_id}: {e}")
      raise

  def get_decrypted_key(self, provider_id: str, access_token: str = None) -> Optional[str]:
    try:
      return self.repo.get_decrypted_key(provider_id, access_token=access_token)
    except Exception as e:
      logger.error(
          f"Error fetching decrypted key for provider {provider_id}: {e}")
      return None

  def fetch_external_models(self, provider_id: str, model_type: str = None, access_token: str = None) -> List[str]:
    """
    Fetches available models from the external provider's API using official SDKs.
    """
    try:
      # 1. Get provider details
      provider = self.repo.get_provider_by_id(
        provider_id, access_token=access_token)
      if not provider:
        raise ValueError(f"Provider with ID {provider_id} not found")

      base_url = provider.get("base_url")
      provider_name = provider.get("name", "").lower()

      # Decrypt API key if it exists
      api_key = self.repo.get_decrypted_key(
        provider_id, access_token=access_token)

      models = []

      # --- Logic: OpenAI & Compatible (also handles Ollama with /v1) ---
      # If provider is OpenAI OR (Ollama AND base_url ends with /v1)
      is_ollama_v1 = "ollama" in provider_name and base_url and base_url.rstrip(
        "/").endswith("/v1")

      if "openai" in provider_name or is_ollama_v1:
        # Use OpenAI SDK
        target_url = base_url.rstrip(
          "/") if base_url else "https://api.openai.com/v1"
        client = openai.Client(api_key=api_key or "dummy", base_url=target_url)

        try:
          response = client.models.list()
          models = [model.id for model in response.data]
        except openai.APIError as e:
          raise ValueError(f"OpenAI API Error: {e}")

      # --- Logic: Google Gemini ---
      elif "google" in provider_name:
        if not api_key:
          raise ValueError("Google API Key is required for fetching models.")

        try:
          client = genai.Client(api_key=api_key)
          # List models using the new GenAI SDK
          response = client.models.list()

          models = []
          for m in response:
            name = getattr(m, "name", "")
            if name:
              models.append(name.replace("models/", ""))
        except Exception as e:
          raise ValueError(f"Google GenAI Error: {e}")

      # --- Logic: Ollama (Native) ---
      elif "ollama" in provider_name:
        # User requested "correct library". Ollama has a python library, but it connects
        # to localhost by default. If base_url is custom, we need to configure it.
        # Fallback to simple request if library not preferred for native, OR use ollama lib.
        # Since 'ollama' package is installed (based on llm_service imports), let's use it.
        # But ollama python client uses OLLAMA_HOST env var usually.
        # It accepts 'host' in Client.
        import ollama
        target_url = base_url.rstrip(
          "/") if base_url else "http://localhost:11434"

        try:
          client = ollama.Client(host=target_url)
          response = client.list()
          if hasattr(response, 'models'):
            models = [m.model for m in response.models]
          else:
            models = [m['name'] for m in response.get('models', [])]
        except Exception as e:
          raise ValueError(f"Ollama Error: {e}")

      return sorted(models)

    except ValueError as e:
      raise e  # Re-raise known value errors
    except Exception as e:
      logger.error(
        f"Unexpected error in fetch_external_models: {e}", exc_info=True)
      raise ValueError(f"Internal service error: {str(e)}")
