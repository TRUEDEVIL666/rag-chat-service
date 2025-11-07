# app/services/supabase/kb_repository.py

from datetime import datetime, timezone
from app.services.supabase.supabase_client import supabase
from app.core.logger import get_logger
from typing import Any, Dict, Optional, List, Tuple

logger = get_logger("kb_repository")


class KnowledgeBaseRepository:
	def __init__(self):
		self.table_name = "knowledgebases"

	def check_exists(self, tenant_id: str, kb_name: str) -> bool:
		"""
		Kiểm tra knowledge base đã tồn tại theo tenant + kb_name
		"""
		try:
			response = (
				supabase.table(self.table_name)
				.select("id")
				.eq("tenant_id", tenant_id)
				.eq("name", kb_name)
				.limit(1)
				.execute()
			)
			return bool(response.data)
		except Exception as e:
			logger.exception(f"[Supabase] Error checking KB exists: {e}")
			return False

	def create(self, kb_data: dict) -> Optional[dict]:
		"""
		Tạo mới knowledge base (nếu chưa tồn tại). Trả về toàn bộ bản ghi vừa insert.
		"""
		try:
			tenant_id = kb_data["tenant_id"]
			kb_name = kb_data["name"]

			if self.check_exists(tenant_id, kb_name):
				raise ValueError(f"Knowledge base '{kb_name}' already exists.")

			kb_data.setdefault("created_at", datetime.utcnow().isoformat())

			response = supabase.table(self.table_name).insert(kb_data).execute()

			created = response.data[0] if getattr(response, "data", None) else None
			if not created:
				err = getattr(response, "error", None)
				if err:
					logger.error(f"[Supabase] Insert KB error: {getattr(err, 'message', err)}")
				else:
					logger.error("[Supabase] Insert KB returned no data")
				return None

			logger.info(f"[Supabase] Created KB: {kb_name}")
			return created

		except Exception as e:
			logger.exception(f"[Supabase] Failed to create knowledge base: {e}")
			return None

	def list_knowledge_bases(
			self,
			tenant_id: str,
			keyword: Optional[str],
			tag_ids: List[str],
			page: int,
			limit: int,
			include_all: bool,
			is_owner: bool,
	) -> Tuple[List[dict], int]:
		"""
		Trả danh sách KB theo spec /knowledge_bases, kèm total.
		- Phân trang: page, limit
		- Filter: keyword theo name, tag_ids (ALL-of)
		- include_all: chỉ hiệu lực khi is_owner=True
		"""
		try:
			offset = (page - 1) * limit
			start = offset
			end = offset + limit - 1

			q = supabase.table(self.table_name).select("*", count="exact")

			if not (include_all and is_owner):
				q = q.eq("tenant_id", tenant_id)

			if keyword:
				q = q.ilike("name", f"%{keyword}%")

			if tag_ids:
				ids_q = supabase.table("knowledge_base_tags").select("kb_id").eq("tag_id", tag_ids[0]).execute()
				if not ids_q.data:
					return [], 0
				kb_ids = {row["kb_id"] for row in ids_q.data}

				for t in tag_ids[1:]:
					t_q = supabase.table("knowledge_base_tags").select("kb_id").eq("tag_id", t).execute()
					kb_ids &= {row["kb_id"] for row in (t_q.data or [])}
					if not kb_ids:
						return [], 0

				q = q.in_("id", list(kb_ids))

			q = q.order("updated_at", desc=True).order("created_at", desc=True)

			page_res = q.range(start, end).execute()

			rows = page_res.data or []
			total = page_res.count or 0
			return rows, total
		except Exception as e:
			logger.exception(f"[Supabase] Failed to list knowledge bases: {e}")
			return [], 0

	def get_knowledge_base_detail(
			self,
			knowledge_base_id: str,
			tenant_id: str,
	) -> Tuple[Optional[dict], List[dict], Dict[str, int]]:
		"""
		Lấy chi tiết 1 KB theo id + tenant scope.
		Trả về: (row kb, tags[], counts{app_count, document_count, word_count})
		"""
		try:
			kb_q = (
				supabase.table(self.table_name)
				.select("*")
				.eq("id", knowledge_base_id)
				.eq("tenant_id", tenant_id)
				.limit(1)
				.execute()
			)
			row = (kb_q.data or [None])[0]
			if not row:
				return None, [], {"app_count": 0, "document_count": 0, "word_count": 0}

			tags: List[dict] = []
			try:
				kb_tags = (
					supabase.table("knowledge_base_tags")
					.select("tag_id")
					.eq("kb_id", knowledge_base_id)
					.execute()
				)
				tag_ids = [t["tag_id"] for t in (kb_tags.data or [])]
				if tag_ids:
					tag_rows = (
						supabase.table("tags")
						.select("*")
						.in_("id", tag_ids)
						.execute()
					)
					tags = tag_rows.data or []
			except Exception:
				tags = []

			app_count = 0
			document_count = 0
			word_count = 0

			counts = {
				"app_count": app_count,
				"document_count": document_count,
				"word_count": word_count,
			}
			return row, tags, counts

		except Exception as e:
			logger.exception(f"[Supabase] Failed to get knowledge base detail {knowledge_base_id}: {e}")
			return None, [], {"app_count": 0, "document_count": 0, "word_count": 0}

	def get_one(self, kb_id: str, tenant_id: str) -> Optional[dict]:
		res = (supabase.table(self.table_name)
		       .select("*").eq("id", kb_id).eq("tenant_id", tenant_id)
		       .limit(1).execute())
		return (res.data or [None])[0]

	def name_conflict(self, tenant_id: str, name: str, exclude_id: str) -> bool:
		res = (supabase.table(self.table_name)
		       .select("id").eq("tenant_id", tenant_id).eq("name", name)
		       .neq("id", exclude_id).limit(1).execute())
		return bool(res.data)

	def patch(self, kb_id: str, tenant_id: str, fields: Dict[str, Any]) -> Optional[dict]:
		if not fields:
			return self.get_one(kb_id, tenant_id)

		fields["updated_at"] = datetime.now(timezone.utc).isoformat()

		res = (supabase.table(self.table_name)
		       .update(fields)
		       .eq("id", kb_id).eq("tenant_id", tenant_id)
		       .execute())
		return (res.data or [None])[0]
