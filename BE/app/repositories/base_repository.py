from typing import Any, Dict, List, Optional

from postgrest.base_request_builder import APIResponse

from app.core.logger import get_logger
from app.core.supabase_client import get_async_supabase_client


class BaseRepository:
  """
  Generic Supabase repository with shared CRUD helpers.
  Ported from Auto_5SEval's base_repository pattern, adapted
  for RAG_Chat_Service's async supabase client.
  """

  _instances: Dict[Any, Any] = {}

  @classmethod
  def get_instance(cls, *args: Any, **kwargs: Any) -> Any:
    """Returns the singleton instance of the repository."""
    if cls not in BaseRepository._instances:
      BaseRepository._instances[cls] = cls(*args, **kwargs)
    return BaseRepository._instances[cls]

  def __init__(self, table_name: str = ""):
    self.table_name = table_name
    self.logger = get_logger(self.__class__.__name__)

  async def _get_client(self, access_token: str = None):
    """Returns the Supabase async client."""
    return await get_async_supabase_client(access_token)

  async def _execute_select(self, query: Any) -> APIResponse:
    """Executes a select query and handles exceptions."""
    try:
      return await query.execute()
    except Exception as e:
      self.logger.error(f"Error executing select on {self.table_name}: {e}")
      raise

  async def _execute_mutation(self, query: Any) -> APIResponse:
    """Executes a mutation query (insert/update/delete) and handles exceptions."""
    try:
      return await query.execute()
    except Exception as e:
      self.logger.error(f"Error executing mutation on {self.table_name}: {e}")
      raise

  async def find_all(
    self, columns: str = "*", access_token: str = None
  ) -> List[Dict[str, Any]]:
    """Fetches all records from the table."""
    client = await self._get_client(access_token)
    response = await self._execute_select(client.table(self.table_name).select(columns))
    return response.data

  async def find_by_id(
    self,
    column_name: str,
    value: Any,
    columns: str = "*",
    access_token: str = None,
  ) -> Optional[Dict[str, Any]]:
    """Fetches a single record by ID."""
    client = await self._get_client(access_token)
    response = await self._execute_select(
      client.table(self.table_name).select(columns).eq(column_name, value).single()
    )
    return response.data

  async def find_one_by_column(
    self,
    column_name: str,
    value: Any,
    columns: str = "*",
    access_token: str = None,
  ) -> Optional[Dict[str, Any]]:
    """Fetches a single record by a specific column."""
    client = await self._get_client(access_token)
    response = await self._execute_select(
      client.table(self.table_name).select(columns).eq(column_name, value).limit(1)
    )
    return response.data[0] if response.data else None

  async def find_all_ordered(
    self,
    order_by: str,
    columns: str = "*",
    access_token: str = None,
  ) -> List[Dict[str, Any]]:
    """Fetches all records ordered by a column."""
    client = await self._get_client(access_token)
    response = await self._execute_select(
      client.table(self.table_name).select(columns).order(order_by)
    )
    return response.data

  async def insert(
    self, data: Dict[str, Any], access_token: str = None
  ) -> List[Dict[str, Any]]:
    """Inserts a new record."""
    client = await self._get_client(access_token)
    response = await self._execute_mutation(client.table(self.table_name).insert(data))
    return response.data

  async def update(
    self,
    column_name: str,
    value: Any,
    data: Dict[str, Any],
    access_token: str = None,
  ) -> List[Dict[str, Any]]:
    """Updates existing records."""
    client = await self._get_client(access_token)
    response = await self._execute_mutation(
      client.table(self.table_name).update(data).eq(column_name, value)
    )
    return response.data

  async def delete(
    self, column_name: str, value: Any, access_token: str = None
  ) -> List[Dict[str, Any]]:
    """Deletes records."""
    client = await self._get_client(access_token)
    response = await self._execute_mutation(
      client.table(self.table_name).delete().eq(column_name, value)
    )
    return response.data

  async def find_by_ids(
    self,
    ids: List[Any],
    id_column: str = "id",
    columns: str = "*",
    access_token: str = None,
  ) -> List[Dict[str, Any]]:
    """Fetches records by a list of IDs."""
    if not ids:
      return []
    client = await self._get_client(access_token)
    response = await self._execute_select(
      client.table(self.table_name).select(columns).in_(id_column, ids)
    )
    return response.data or []

  async def get_max_id(self, column_name: str, access_token: str = None) -> int:
    """Returns the maximum value of a numeric column."""
    client = await self._get_client(access_token)
    response = await self._execute_select(
      client.table(self.table_name)
      .select(column_name)
      .order(column_name, desc=True)
      .limit(1)
    )
    return response.data[0][column_name] if response.data else 0
