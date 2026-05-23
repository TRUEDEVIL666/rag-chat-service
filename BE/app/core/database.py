from typing import Optional

from langchain_postgres import PGEngine
from psycopg_pool import AsyncConnectionPool

from app.config.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class PostgresEngine:
  """
  Singleton class to manage a centralized PGEngine instance.
  Provides both the PGEngine for LangChain and URL normalization for other services.
  """

  _instance: Optional["PostgresEngine"] = None
  _engine: Optional[PGEngine] = None
  _pool: Optional[AsyncConnectionPool] = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(PostgresEngine, cls).__new__(cls)
    return cls._instance

  @staticmethod
  def get_normalized_url() -> str:
    """Centralized logic for URL normalization (SSL, dialect fixes)."""
    url = settings.DATABASE_URL
    if not url:
      return ""

    # Enforce SSL requirement
    if "sslmode=" not in url:
      separator = "&" if "?" in url else "?"
      url = f"{url}{separator}sslmode=require"

    return url

  async def get_engine(self) -> PGEngine:
    """Returns the initialized PGEngine instance."""
    if self._engine is None:
      url = self.get_normalized_url()
      # Standardize URL for sqlalchemy if needed
      if "postgresql://" in url and not url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql://", "postgresql+psycopg://")

      logger.info(f"[PostgresEngine] Initializing PGEngine (instance={id(self)})")
      self._engine = PGEngine.from_connection_string(url)
      logger.info(
        f"[PostgresEngine] PGEngine initialized successfully (instance={id(self)})"
      )
    return self._engine

  async def get_pool(self) -> AsyncConnectionPool:
    """Returns the initialized AsyncConnectionPool instance."""
    if self._pool is None:
      url = self.get_normalized_url()
      # psycopg_pool needs a raw connection string without sqlalchemy dialect prefixes
      if "postgresql+psycopg://" in url:
        url = url.replace("postgresql+psycopg://", "postgresql://")
      elif "postgresql+psycopg2://" in url:
        url = url.replace("postgresql+psycopg2://", "postgresql://")

      logger.info("[PostgresEngine] Initializing AsyncConnectionPool")
      self._pool = AsyncConnectionPool(
        conninfo=url, max_size=20, kwargs={"autocommit": True}, open=False
      )
      await self._pool.open()
      await self._pool.wait()
      logger.info("[PostgresEngine] AsyncConnectionPool initialized successfully")
    return self._pool

  async def close(self):
    """Gracefully shuts down the engine."""
    if self._engine:
      logger.info("[PostgresEngine] Closing PGEngine")
      await self._engine.close()
      self._engine = None
    if self._pool:
      logger.info("[PostgresEngine] Closing AsyncConnectionPool")
      await self._pool.close()
      self._pool = None


# Global accessible instance
postgres_engine = PostgresEngine()
