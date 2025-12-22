from fastapi import APIRouter, Depends, HTTPException
from app.core.factory import get_user_service, get_session_service, get_knowledge_base_service
from app.services.users.user_service import UserService
from app.services.session.session_service import SessionService
from app.services.knowledge_base.knowledge_base_service import KnowledgeBaseService
from app.utils.auth import get_current_user
from fastapi_cache.decorator import cache

router = APIRouter()


@router.get("/analytics/summary", summary="Get dashboard summary counts")
@cache(expire=60)  # Cache for 1 minute to avoid hammering DB
async def get_analytics_summary(
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    auth: dict = Depends(get_current_user)
):
  try:
    user_id = auth["user_id"]
    tenant_id = auth["tenant_id"]
    # Assuming only admins/instructors should see this, but for now we basically allow authenticated users
    # or rely on frontend to only show to instructors.
    # If strict RBAC is needed:
    # if auth.get("role") not in ["admin", "instructor"]: ...

    # Total Students (Global or Tenant?)
    # The Supabase query provided was global 'users'. UserRepository.get_total_users() is global.
    total_users = user_service.get_total_users()

    # Total Chats (Tenant specific)
    total_chats = session_service.get_total_sessions(tenant_id)

    # Knowledge Bases (Tenant specific)
    total_kbs = kb_service.get_total_kbs(tenant_id)

    return {
        "total_students": total_users,
        "total_chats": total_chats,
        "total_kbs": total_kbs
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
