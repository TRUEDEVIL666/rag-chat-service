# app/api/v1/root.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Health check")
def read_root():
	return {"message": "RAG API is running."}
