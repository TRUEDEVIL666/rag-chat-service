from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated, Optional

from app.agent import chat_service_instance
from app.utils.auth import get_current_user
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatRequest(BaseModel):
  query: str
  session_id: str
  kb_id: Optional[str] = None


@router.post("/chat")
async def chat_endpoint(
  request: ChatRequest,
  current_user: Annotated[dict, Depends(get_current_user)],
):
  """
  Standard chat endpoint using the RAG Graph.
  """
  user_id = current_user["user_id"]

  try:
    result = await chat_service_instance.stream_chat(
      query=request.query,
      session_id=request.session_id,
      user_id=user_id,
      kb_id=request.kb_id,
    )
    return result
  except Exception as e:
    logger.error(f"Chat error: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(
  session_id: str,
  current_user: Annotated[dict, Depends(get_current_user)],
):
  return await chat_service_instance.get_history(session_id)
