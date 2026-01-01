import logging
from typing import List, Optional, Dict, Any
from app.services.supabase.ai_model_repository import AiModelRepository

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
