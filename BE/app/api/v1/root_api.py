# app/api/v1/root.py
from app.schemas.common import MessageResponse
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Health check", response_model=MessageResponse)
def read_root():
  return {"message": "RAG API is running."}
