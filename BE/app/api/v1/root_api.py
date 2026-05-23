# app/api/v1/root.py
from fastapi import APIRouter

from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/", summary="Health check", response_model=MessageResponse)
def read_root():
  return {"message": "RAG API is running."}
