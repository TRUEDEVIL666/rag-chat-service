# app/api/v1/__init__.py
from .users_api import router as users_router
from fastapi import APIRouter
from .root_api import router as root_router
from .auth_api import router as auth_router
from .knowledge_base_api import router as knowledge_base_router
from .session_api import router as session_router
from .analytics_api import router as analytics_router
from .document_api import router as document_router
from .tenant_api import router as tenant_router
from .quiz_api import router as quiz_router
from .semester_api import router as semester_router
from .course_api import router as course_router
from .class_api import router as class_router
from .chat_api import router as chat_router
from .bots_api import router as bots_router

from app.utils.auth import get_current_user
from fastapi import Depends

router = APIRouter()

# Public Endpoints
router.include_router(root_router, tags=["Root"])
router.include_router(auth_router, tags=["Auth"])

# Protected Endpoints (Requires global auth)
protected_router = APIRouter(dependencies=[Depends(get_current_user)])

protected_router.include_router(users_router, tags=["Users"])
protected_router.include_router(router=knowledge_base_router, tags=["Knowledge Base"])
protected_router.include_router(router=session_router, tags=["Sessions"])
protected_router.include_router(router=analytics_router, tags=["Analytics"])
protected_router.include_router(
  router=document_router, prefix="/documents", tags=["Documents"]
)
protected_router.include_router(router=tenant_router, tags=["Tenants"])
protected_router.include_router(router=quiz_router, prefix="/quiz", tags=["Quiz"])

# LMS (Protected)
protected_router.include_router(router=semester_router, tags=["Semesters"])
protected_router.include_router(router=course_router, tags=["Courses"])
protected_router.include_router(router=class_router, tags=["Classes"])
protected_router.include_router(router=chat_router)
protected_router.include_router(router=bots_router)


# Combine routers
router.include_router(protected_router)
