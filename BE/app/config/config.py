from typing import Set
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  # ------------------
  # SECURITY
  # ------------------
  SECRET_KEY: str = ""
  ALGORITHM: str = "HS256"

  # ------------------
  # DATABASE
  # ------------------
  SUPABASE_URL: str = ""
  SUPABASE_KEY: str = ""

  # ------------------
  # STORAGE
  # ------------------
  MINIO_ENDPOINT: str = "localhost:9000"
  MINIO_ACCESS_KEY: str = "minioadmin"
  MINIO_SECRET_KEY: str = "minioadmin"

  # ------------------
  # CELERY & REDIS
  # ------------------
  CELERY_BROKER: str = "amqp://guest:guest@localhost:5672//"
  REDIS_BACKEND: str = "redis://localhost:6379/0"

  # ------------------
  # GENERIC EMBEDDINGS (Fallback)
  # ------------------
  RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
  DEFAULT_CHAT_MODEL: str = "ollama/gemma3:4b"
  DEFAULT_CHAT_TEMPERATURE: float = 0.7

  # ------------------
  # OLLAMA DEFAULTS
  # ------------------
  OLLAMA_EMBEDDING_API_URL: str = "http://localhost:11434"

  # ------------------
  # EXTRACTION LLM
  # ------------------
  EXTRACTION_LLM_HOST: str = "http://localhost:11434"
  # Requires tool calling support if using tools, but langextract handles json mode too
  EXTRACTION_LLM_MODEL: str = "gemma3:4b"

  # ------------------
  # APP SETTINGS
  # ------------------
  BUFFER_SIZE: int = 500
  THRESHOLD_PERCENTAGE: int = 10
  MAX_FILE_SIZE: int = 200 * 1024 * 1024  # 200MB default

  # Default set of extensions if not provided in env
  ALLOWED_EXTENSIONS: Set[str] = {
      '.pdf', '.txt', '.docx', '.csv', '.json',
      '.pptx', '.xlsx', '.md', '.html', '.jpg',
      '.jpeg', '.png', '.bmp', '.tiff'
  }

  QUIZ_MODE_TOP_K: int = 20
  MAX_QUIZ_QUESTIONS: int = 40

  class Config:
    env_file = ".env"
    extra = "ignore"


settings = Settings()
