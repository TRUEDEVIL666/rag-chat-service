import asyncio
from typing import Optional, List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from memori import Memori

from app.config.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class MemoryService:
  def __init__(self):
    self._mem: Optional[Memori] = None
    self._lock = asyncio.Lock()
    self._SessionLocal = None

    if settings.MEMORI_DATABASE_URL:
      db_url = settings.MEMORI_DATABASE_URL
      if "sslmode=" not in db_url:
        db_url += "&sslmode=require" if "?" in db_url else "?sslmode=require"

      engine = create_engine(
          db_url,
          pool_pre_ping=True,
          pool_recycle=300,
          pool_size=10,
          max_overflow=20
      )

      self._SessionLocal = sessionmaker(bind=engine)

  async def get_memori(self, force_refresh: bool = False) -> Optional[Memori]:
    async with self._lock:
      if force_refresh:
        logger.info("Refreshing Memori connection...")
        self._mem = None

      if self._mem is None:
        if not self._SessionLocal:
          logger.warning("Memory disabled")
          return None

        try:
          self._mem = Memori(conn=self._SessionLocal)
          self._mem.config.storage.build()
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
      self,
      user_id: str,
      query: str,
      limit: int = 5
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
    mem = await self.get_memori()
    if mem:
      try:
        mem.close()
      except Exception as e:
        logger.error(e)


memory_service = MemoryService()
