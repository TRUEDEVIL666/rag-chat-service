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
  CELERY_BROKER: str = os.getenv("CELERY_BROKER", "redis://localhost:6379/0")
  REDIS_BACKEND: str = os.getenv("REDIS_BACKEND", "redis://localhost:6379/0")

  # ------------------
  # GENERIC EMBEDDINGS (Fallback)
  # ------------------
  EMBEDDING_API_URL: str = os.getenv(
      "EMBEDDING_API_URL", "http://localhost:11434/api/embeddings")
  EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "embeddinggemma")
  RERANKER_MODEL: str = os.getenv(
      "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
  DEFAULT_CHAT_MODEL: str = os.getenv("DEFAULT_CHAT_MODEL", "ollama/gemma3:4b")
  DEFAULT_CHAT_TEMPERATURE: float = float(
      os.getenv("DEFAULT_CHAT_TEMPERATURE", 0.7))

  # ------------------
  # OLLAMA
  # ------------------
  OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
  OLLAMA_EMBEDDING_API_URL: str = os.getenv(
      "OLLAMA_EMBEDDING_API_URL", "http://localhost:11434/api/embeddings")
  OLLAMA_EMBEDDING_MODEL: str = os.getenv(
      "OLLAMA_EMBEDDING_MODEL", "embeddinggemma")

  # ------------------
  # OPENAI
  # ------------------
  OPENAI_URL: str = os.getenv("OPENAI_URL", "https://api.openai.com/v1")
  OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
  OPENAI_EMBEDDING_MODEL: str = os.getenv(
      "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

  # ------------------
  # GEMINI
  # ------------------
  GEMINI_URL: str = os.getenv("GEMINI_URL", "")
  GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
  GEMINI_EMBEDDING_MODEL: str = os.getenv(
      "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

  # ------------------
  # APP SETTINGS
  # ------------------
  BUFFER_SIZE: int = int(os.getenv("BUFFER_SIZE", 500))
  THRESHOLD_PERCENTAGE: int = int(os.getenv("THRESHOLD_PERCENTAGE", 10))

  class Config:
    env_file = ".env"


settings = Settings()
