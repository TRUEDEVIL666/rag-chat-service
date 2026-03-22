from typing import List, Dict
from app.core.logger import get_logger
from app.services.supabase.supabase_client import get_async_supabase_client

logger = get_logger(__name__)


class GraphEntityRepository:
  """
  Handles storing and querying graph entities and their mentions in Supabase.
  Tables: "graph_entities", "graph_chunk_entity_mentions"
  """

  def __init__(self, entities_table: str = "graph_entities", mentions_table: str = "graph_chunk_entity_mentions"):
    self.entities_table = entities_table
    self.mentions_table = mentions_table

  async def store(self, entities: List[Dict], chunk_mentions: List[Dict], access_token: str = None):
    """
    Store formatted graph entities and their chunk mentions into Supabase.
    """
    if not entities and not chunk_mentions:
      return

    try:
      client = await get_async_supabase_client(access_token)

      # Upsert entities
      if entities:
        # Avoid duplicate upsert errors by grouping or relying on DB constraints,
        # but here we'll assume entities array is pre-deduplicated per batch
        response_ent = await client.table(self.entities_table).upsert(entities).execute()
        if hasattr(response_ent, "error") and response_ent.error:
          logger.error(
              f"[GraphEntityRepo]: Entities Upsert error: {response_ent.error.get('message')}")
        else:
          logger.info(
            f"[GraphEntityRepo]: Upserted {len(response_ent.data)} entities.")

      # Upsert mentions
      if chunk_mentions:
        response_mentions = await client.table(self.mentions_table).upsert(chunk_mentions).execute()
        if hasattr(response_mentions, "error") and response_mentions.error:
          logger.error(
              f"[GraphEntityRepo]: Mentions Upsert error: {response_mentions.error.get('message')}")
        else:
          logger.info(
            f"[GraphEntityRepo]: Upserted {len(response_mentions.data)} chunk-entity mentions.")

    except Exception as e:
      logger.exception(
        f"[GraphEntityRepo]: Failed to upsert entities/mentions: {e}")
      raise

  async def get_entities_by_kb(self, kb_id: str, access_token: str = None) -> List[Dict]:
    """Retrieve all entities for a specific KB."""
    try:
      client = await get_async_supabase_client(access_token)
      result = await client.table(self.entities_table).select("*").eq("kb_id", kb_id).execute()
      return result.data or []
    except Exception as e:
      logger.exception(f"[GraphEntityRepo]: Failed to fetch entities: {e}")
      return []

  async def check_existing_entities(self, names: List[str], kb_id: str, access_token: str = None) -> Dict[str, str]:
    """Return a mapping of {name: id} for existing entities in the KB to avoid duplicates."""
    if not names:
      return {}
    try:
      client = await get_async_supabase_client(access_token)
      # Lowercase for case-insensitive matching if needed, or exact matching:
      result = await client.table(self.entities_table).select("id, name").eq("kb_id", kb_id).in_("name", names).execute()
      return {row["name"]: row["id"] for row in (result.data or [])}
    except Exception as e:
      logger.exception(
        f"[GraphEntityRepo]: Failed to check existing entities: {e}")
      return {}

  async def get_entities_by_chunk_ids(self, chunk_ids: List[str], access_token: str = None) -> List[str]:
    """Retrieve all entity IDs mentioned within a list of chunks."""
    if not chunk_ids:
      return []

    try:
      client = await get_async_supabase_client(access_token)

      # Execute query to get mentions
      result = await client.table(self.mentions_table).select("entity_id").in_("chunk_id", chunk_ids).execute()

      # Extract unique entity IDs
      entity_ids = set()
      for row in (result.data or []):
        entity_ids.add(row["entity_id"])

      return list(entity_ids)
    except Exception as e:
      logger.exception(
        f"[GraphEntityRepo]: Failed to fetch entities by chunk IDs: {e}")
      return []
