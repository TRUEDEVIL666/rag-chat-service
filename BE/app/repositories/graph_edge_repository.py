from datetime import datetime
from typing import Dict, List

from app.repositories.base_repository import BaseRepository


class GraphEdgeRepository(BaseRepository):
  """
  Handles storing and querying graph edges (relationships) in Supabase.
  Table: "graph_edges"
  """

  def __init__(self):
    super().__init__(table_name="graph_edges")

  async def store(self, edges: List[Dict], access_token: str = None):
    """
    Store formatted graph edges into Supabase (Upsert).
    Expected edge format:
    {
      "source_entity_id": <uuid>,
      "target_entity_id": <uuid>,
      "relationship_type": <str>,
      "properties": <dict>
    }
    """
    if not edges:
      return

    try:
      client = await self._get_client(access_token)
      for edge in edges:
        # Add timestamp if missing
        if "created_at" not in edge:
          edge["created_at"] = datetime.utcnow().isoformat()

      response = await client.table(self.table_name).upsert(edges).execute()
      if hasattr(response, "error") and response.error:
        self.logger.error(
          f"[GraphEdgeRepo]: Upsert error: {response.error.get('message')}"
        )
      else:
        self.logger.info(f"[GraphEdgeRepo]: Upserted {len(response.data)} edges.")
    except Exception as e:
      self.logger.exception(f"[GraphEdgeRepo]: Failed to upsert edges: {e}")
      raise

  async def get_edges_by_entity_ids(
    self, entity_ids: List[str], access_token: str = None
  ) -> List[Dict]:
    """
    Retrieve all edges where the source or target matches the provided entity IDs.
    """
    if not entity_ids:
      return []

    try:
      client = await self._get_client(access_token)

      # Format IDs for PostgREST: (id1,id2,id3)
      ids_param = f"({','.join(str(cid) for cid in entity_ids)})"

      # Query where source OR target is in the list
      # Supabase OR syntax: or=(source_entity_id.in.(...),(target_entity_id.in.(...))
      or_filter = f"source_entity_id.in.{ids_param},target_entity_id.in.{ids_param}"

      result = await client.table(self.table_name).select("*").or_(or_filter).execute()
      return result.data or []
    except Exception as e:
      self.logger.exception(
        f"[GraphEdgeRepo]: Failed to fetch edges by entity IDs: {e}"
      )
      return []

  async def delete_edges(
    self,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    access_token: str = None,
  ) -> bool:
    """
    Delete a specific edge (used for cleanup or syncing).
    """
    try:
      client = await self._get_client(access_token)
      await (
        client.table(self.table_name)
        .delete()
        .eq("source_entity_id", source_entity_id)
        .eq("target_entity_id", target_entity_id)
        .eq("relationship_type", relationship_type)
        .execute()
      )
      return True
    except Exception as e:
      self.logger.exception(f"[GraphEdgeRepo]: Failed to delete edge: {e}")
      return False
