# app/api/v1/__init__.py
from .users_api import router as users_router
from fastapi import APIRouter
from .root_api import router as root_router
from .auth_api import router as auth_router
from .knowledge_base_api import router as knowledge_base_router
from .chatbot_api import router as chatbot_router
from .session_api import router as session_router
from .analytics_api import router as analytics_router
from .ai_model_api import router as ai_model_router
from .document_api import router as document_router

router = APIRouter()


router.include_router(root_router, tags=["Root"])
router.include_router(auth_router, tags=["Auth"])
router.include_router(users_router, tags=["Users"])
router.include_router(router=knowledge_base_router, tags=["Knowledge Base"])
router.include_router(router=chatbot_router, tags=["Chatbot"])
router.include_router(router=session_router, tags=["Sessions"])
router.include_router(router=analytics_router, tags=["Analytics"])
router.include_router(router=ai_model_router,
                      prefix="/ai-models", tags=["AI Models"])
router.include_router(router=document_router,
                      prefix="/documents", tags=["Documents"])
