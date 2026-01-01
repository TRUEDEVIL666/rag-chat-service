import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  # ------------------
  # SECURITY
  # ------------------
  SECRET_KEY: str = os.getenv("SECRET_KEY", "")
  ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

  # ------------------
  # DATABASE
  # ------------------
  SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
  SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

  QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
  QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
  QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "rag_collection")

  # ------------------
  # STORAGE
  # ------------------
  MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
  MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
  MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")

  # ------------------
  # CELERY & REDIS
  # ------------------
  CELERY_BROKER: str = os.getenv(
    "CELERY_BROKER", "amqp://guest:guest@localhost:5672//")
  REDIS_BACKEND: str = os.getenv("REDIS_BACKEND", "redis://localhost:6379/0")

  # ------------------
  # GENERIC EMBEDDINGS (Fallback)
  # ------------------
  RERANKER_MODEL: str = os.getenv(
      "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
  DEFAULT_CHAT_MODEL: str = os.getenv("DEFAULT_CHAT_MODEL", "ollama/gemma3:4b")
  DEFAULT_CHAT_TEMPERATURE: float = float(
      os.getenv("DEFAULT_CHAT_TEMPERATURE", 0.7))

  # ------------------
  # OLLAMA DEFAULTS
  # ------------------
  OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434/api")
  OLLAMA_EMBEDDING_API_URL: str = os.getenv(
      "OLLAMA_EMBEDDING_API_URL", "http://localhost:11434/api/embed")

  # ------------------
  # APP SETTINGS
  # ------------------
  BUFFER_SIZE: int = int(os.getenv("BUFFER_SIZE", 500))
  THRESHOLD_PERCENTAGE: int = int(os.getenv("THRESHOLD_PERCENTAGE", 10))
  MAX_FILE_SIZE: int = int(
    os.getenv("MAX_FILE_SIZE", 200 * 1024 * 1024))  # 200MB default
  ALLOWED_EXTENSIONS: set = {'.pdf', '.docx', '.txt', '.md', '.csv', '.pptx'}

  class Config:
    env_file = ".env"
    extra = "ignore"


settings = Settings()
