# app/api/v1/__init__.py
from fastapi import APIRouter
from .root_api import router as root_router
from .auth_api import router as auth_router
from .data_processor_api import router as data_processor_router
from .knowledge_base_api import router as knowledge_base_router
from .chatbot_api import router as chatbot_router
from .system_api import router as system_router
from .workspaces_api import router as workspaces_router

router = APIRouter()

from .users_api import router as users_router

from .session_api import router as session_router

router.include_router(root_router, tags=["Root"])
router.include_router(auth_router, tags=["Auth"])
router.include_router(users_router, tags=["Users"])
router.include_router(router=knowledge_base_router, tags=["Knowledge Base"])
router.include_router(data_processor_router, tags=["Data Processor"])
router.include_router(session_router, tags=["Sessions"])
router.include_router(router=chatbot_router, tags=["Chatbot"])
