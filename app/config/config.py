from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	secret_key: str
	algorithm: str

	supabase_url: str
	supabase_key: str

	celery_broker: str
	celery_backend: str

	ollama_url: str
	embedding_api_url: str
	embedding_model: str

	qdrant_host: str
	qdrant_port: int
	qdrant_collection: str

	minio_endpoint: str
	minio_access_key: str
	minio_secret_key: str

	class Config:
		env_file = ".env"


settings = Settings()
