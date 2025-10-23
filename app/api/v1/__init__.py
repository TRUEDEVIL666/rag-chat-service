# app/api/v1/__init__.py
from fastapi import APIRouter
from .root import router as root_router
from .auth import router as auth_router
from .data_processor import router as data_processor_router
from .knowledge_base import router as knowledge_base_router
from .chatbot import router as chatbot_router

router = APIRouter()

router.include_router(root_router, tags=["Root"])
router.include_router(auth_router, tags=["Auth"])
router.include_router(data_processor_router, tags=["Data Processor"])
router.include_router(router=knowledge_base_router,tags=["Knowledge Base"])
router.include_router(router=chatbot_router,tags=["Chatbot"])