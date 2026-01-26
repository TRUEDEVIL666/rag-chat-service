
import logging
from typing import Optional, List, Any, Dict
from app.services.supabase.supabase_client import get_async_supabase_client
from app.schemas.course import ClassCreateRequest

logger = logging.getLogger(__name__)


class ClassRepository:
  def __init__(self, supabase_client=None):
    self.table_name = "classes"

  async def list_classes(self, tenant_id: str, semester_id: Optional[str] = None, course_id: Optional[str] = None, access_token: str = None) -> List[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)
      query = client.table("classes")\
          .select("*, courses(name, code), semesters(name)")\
          .eq("tenant_id", tenant_id)

      if semester_id:
        query = query.eq("semester_id", semester_id)

      if course_id:
        query = query.eq("course_id", course_id)

      response = await query.order("created_at", desc=True).execute()
      return response.data
    except Exception as e:
      logger.error(f"Error listing classes: {e}")
      return []

  async def get_class(self, class_id: str, tenant_id: str, access_token: str = None) -> Optional[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)
      response = await client.table("classes")\
          .select("*, courses(*), semesters(*)")\
          .eq("id", class_id)\
          .eq("tenant_id", tenant_id)\
          .single()\
          .execute()
      return response.data
    except Exception as e:
      logger.error(f"Error getting class {class_id}: {e}")
      return None

  async def create_class(self, data: ClassCreateRequest, tenant_id: str, access_token: str = None) -> Optional[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)
      payload = data.model_dump()
      payload["tenant_id"] = tenant_id

      response = await client.table(self.table_name).insert(payload).execute()
      return response.data[0] if response.data else None
    except Exception as e:
      logger.error(f"Error creating class: {e}")
      raise e

  async def enroll_student(self, class_id: str, user_id: str, tenant_id: str, access_token: str = None) -> bool:
    try:
      client = await get_async_supabase_client(access_token)
      response = await client.table("class_enrollments").insert({
          "class_id": class_id,
          "user_id": user_id,
          "tenant_id": tenant_id
      }).execute()
      return response.data[0] if response.data else None
    except Exception as e:
      logger.error(f"Error enrolling student: {e}")
      raise e

  async def get_student_enrollments(self, user_id: str, tenant_id: str, access_token: str = None) -> List[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)
      # Query enrollments, join classes -> courses, semesters
      # We want class details for the student
      response = await client.table("class_enrollments")\
          .select("*, classes(*, courses(name, code), semesters(name))")\
          .eq("user_id", user_id)\
          .eq("tenant_id", tenant_id)\
          .execute()
      return response.data
    except Exception as e:
      logger.error(f"Error listing student enrollments: {e}")
      return []

  async def get_classes_by_instructor(self, instructor_id: str, tenant_id: str, access_token: str = None) -> List[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)
      response = await client.table("classes")\
          .select("*, courses(name, code), semesters(name)")\
          .eq("instructor_id", instructor_id)\
          .eq("tenant_id", tenant_id)\
          .execute()
      return response.data or []
    except Exception as e:
      logger.error(f"Error getting classes by instructor: {e}")
      return []

  async def get_class_students(self, class_id: str, tenant_id: str, access_token: str = None) -> List[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)
      response = await client.table("class_enrollments")\
          .select("*, users!inner(*)")\
          .eq("class_id", class_id)\
          .eq("tenant_id", tenant_id)\
          .execute()
      return response.data
    except Exception as e:
      logger.error(f"Error getting class students: {e}")
      return []

  async def get_stats(self, tenant_id: str, access_token: str = None) -> Dict[str, Any]:
    try:
      client = await get_async_supabase_client(access_token)

      classes_res = await client.table("classes").select("*", count="exact", head=True)\
          .eq("tenant_id", tenant_id).execute()
      classes_count = classes_res.count if hasattr(classes_res, "count") else 0

      enrollments_res = await client.table("class_enrollments").select("*", count="exact", head=True)\
          .eq("tenant_id", tenant_id).execute()
      enrollments_count = enrollments_res.count if hasattr(
        enrollments_res, "count") else 0

      return {
          "total_classes": classes_count,
          "total_enrollments": enrollments_count
      }
    except Exception as e:
      logger.error(f"Error getting class stats: {e}")
      return {"total_classes": 0, "total_enrollments": 0}

  async def add_students_to_class(self, class_id: str, user_ids: List[str], tenant_id: str, access_token: str = None) -> bool:
    try:
      client = await get_async_supabase_client(access_token)
      if not user_ids:
        return True

      data = [
        {"class_id": class_id, "user_id": uid, "tenant_id": tenant_id}
        for uid in user_ids
      ]

      response = await client.table("class_enrollments").upsert(
        data, on_conflict="class_id,user_id").execute()
      return True
    except Exception as e:
      logger.error(f"Error adding students to class: {e}")
      return False

  async def get_class_bots(self, class_id: str, tenant_id: str, access_token: str = None) -> List[Dict[str, Any]]:
    try:
      client = await get_async_supabase_client(access_token)

      # 1. Get bot_ids from classes table
      class_res = await client.table("classes").select("bot_ids").eq(
        "id", class_id).eq("tenant_id", tenant_id).single().execute()
      bot_ids = class_res.data.get("bot_ids", []) if class_res.data else []

      if not bot_ids:
        return []

      # 2. Fetch full bot details
      bots_res = await client.table("bots").select("*").in_("id", bot_ids).execute()
      return bots_res.data or []
    except Exception as e:
      logger.error(f"Error getting class bots: {e}")
      return []

  async def get_bots_by_ids(self, bot_ids: List[str], access_token: str = None) -> List[Dict[str, Any]]:
    try:
      if not bot_ids:
        return []

      client = await get_async_supabase_client(access_token)
      bots_res = await client.table("bots").select("*").in_("id", bot_ids).execute()
      return bots_res.data or []
    except Exception as e:
      logger.error(f"Error getting bots by ids: {e}")
      return []

  async def add_bots_to_class(self, class_id: str, bot_ids: List[str], tenant_id: str, access_token: str = None) -> bool:
    try:
      client = await get_async_supabase_client(access_token)
      if not bot_ids:
        return True

      # 1. Get existing bot_ids
      class_res = await client.table("classes").select("bot_ids").eq(
        "id", class_id).eq("tenant_id", tenant_id).single().execute()
      existing_ids = class_res.data.get("bot_ids", []) if (
        class_res.data and class_res.data.get("bot_ids")) else []

      # 2. Merge unique IDs
      new_ids = list(set(existing_ids + bot_ids))

      # 3. Update classes table
      await client.table("classes").update({"bot_ids": new_ids}).eq(
        "id", class_id).eq("tenant_id", tenant_id).execute()
      return True
    except Exception as e:
      logger.error(f"Error adding bots to class: {e}")
      return False

  async def remove_bot_from_class(self, class_id: str, bot_id: str, tenant_id: str, access_token: str = None) -> bool:
    try:
      client = await get_async_supabase_client(access_token)

      # 1. Get existing bot_ids
      class_res = await client.table("classes").select("bot_ids").eq(
        "id", class_id).eq("tenant_id", tenant_id).single().execute()
      existing_ids = class_res.data.get("bot_ids", []) if (
        class_res.data and class_res.data.get("bot_ids")) else []

      # 2. Filter out the bot_id to remove
      new_ids = [bid for bid in existing_ids if str(bid) != str(bot_id)]

      # 3. Update classes table
      await client.table("classes").update({"bot_ids": new_ids}).eq(
        "id", class_id).eq("tenant_id", tenant_id).execute()
      return True
    except Exception as e:
      logger.error(f"Error removing bot from class: {e}")
      return False

  async def remove_student_from_class(self, class_id: str, user_id: str, tenant_id: str, access_token: str = None) -> bool:
    try:
      client = await get_async_supabase_client(access_token)
      await client.table("class_enrollments")\
          .delete()\
          .eq("class_id", class_id)\
          .eq("user_id", user_id)\
          .eq("tenant_id", tenant_id)\
          .execute()
      return True
    except Exception as e:
      logger.error(f"Error removing student from class: {e}")
      return False
