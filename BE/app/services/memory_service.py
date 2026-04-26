import asyncio
from typing import List, Optional

import psycopg
from memori import Memori
from psycopg_pool import AsyncConnectionPool

from app.core.database import postgres_engine
from app.core.logger import get_logger

logger = get_logger(__name__)


class MemoryService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "MemoryService":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self):
    self._mem: Optional[Memori] = None
    self._lock = asyncio.Lock()
    self._pool: Optional[AsyncConnectionPool] = None

  async def _get_pool(self) -> AsyncConnectionPool:
    if self._pool is None:
      url = postgres_engine.get_normalized_url()

      self._pool = AsyncConnectionPool(
        conninfo=url, max_size=10, kwargs={"autocommit": True}, open=False
      )
      await self._pool.open()
    return self._pool

  async def get_memori(self, force_refresh: bool = False) -> Optional[Memori]:
    async with self._lock:
      if force_refresh:
        logger.info("Refreshing Memori connection...")
        self._mem = None

      if self._mem is None:
        try:
          url = postgres_engine.get_normalized_url()

          # Memori 3.x is synchronous and expects a DBAPI or SQLAlchemy connection.
          # We provide a synchronous connection function using psycopg.
          def get_conn():
            return psycopg.connect(url)

          def _init_memori():
            mem = Memori(conn=get_conn)
            mem.config.storage.build()
            return mem

          # Run initialization in a thread to avoid blocking the event loop
          self._mem = await asyncio.to_thread(_init_memori)
          logger.info("Memori initialized")
        except Exception as e:
          logger.error(f"Memori init failed: {e}")
          return None

      return self._mem

  async def clear_cache(self):
    async with self._lock:
      self._mem = None
      logger.info("Memori cache cleared")

  async def register_llm(self, llm):
    mem = await self.get_memori()
    if mem:
      mem.llm.register(llm)

  async def set_attribution(self, entity_id: str, process_id: str):
    mem = await self.get_memori()
    if mem:
      mem.attribution(entity_id=entity_id, process_id=process_id)

  async def retrieve_memories(
    self, user_id: str, query: str, limit: int = 5
  ) -> List[str]:
    mem = await self.get_memori()

    if not mem:
      return []

    def _recall():
      mem.attribution(entity_id=user_id, process_id="rag_chat")
      return mem.recall(query, limit)

    try:
      results = await asyncio.to_thread(_recall)
      memories = []
      for r in results:
        if isinstance(r, str):
          memories.append(r)
        elif hasattr(r, "content"):
          memories.append(r.content)
      return memories
    except Exception as e:
      logger.error(f"Memory recall error {e}")
      return []

  async def process_memory(self, user_id: str):
    mem = await self.get_memori()

    if not mem:
      return

    def _process():
      mem.attribution(entity_id=user_id, process_id="rag_chat")
      mem.augmentation.wait()

    try:
      await asyncio.to_thread(_process)
      logger.info(f"Memory processed for {user_id}")
    except Exception as e:
      logger.error(f"Memory processing error {e}")

  async def close(self):
    # Use direct access to _mem to avoid triggering get_memori (which might re-open it)
    if self._mem:
      try:
        await asyncio.to_thread(self._mem.close)
        self._mem = None
      except Exception as e:
        logger.error(f"Memori close error: {e}")

    if self._pool:
      try:
        await self._pool.close()
        self._pool = None
      except Exception as e:
        logger.error(f"Pool close error: {e}")
