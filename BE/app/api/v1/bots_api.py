from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import json
from fastapi.responses import StreamingResponse
from app.agent import chat_service_instance
from app.repositories import bot_repo_instance
from app.utils.auth import get_current_user
from app.core.logger import get_logger
from app.schemas.common import BaseResponse
from app.schemas.bot import BotItem, BotKBItem

logger = get_logger(__name__)
router = APIRouter(prefix="/bots", tags=["Bots"])


class AskRequest(BaseModel):
  message: str
  streaming: Optional[bool] = False
  quiz_mode: Optional[bool] = False


@router.get("/{bot_id}", response_model=BaseResponse[BotItem])
async def get_bot(
  bot_id: str,
  current_user: Annotated[dict, Depends(get_current_user)],
):
  """
  Get bot details including linked knowledge bases.
  """
  bot = await bot_repo_instance.get_bot_with_kbs(bot_id)
  if not bot:
    raise HTTPException(status_code=404, detail="Bot not found")

  # Format KBs
  formatted_kbs = []
  for kb in bot.get("knowledge_bases", []):
    formatted_kbs.append(
      BotKBItem(
        id=str(kb["id"]),
        name=kb["name"],
        description=kb.get("description"),
      )
    )

  result = BotItem(
    id=str(bot["id"]),
    name=bot["name"],
    description=bot.get("description"),
    config_prompt=bot.get("config_prompt"),
    config_model=bot.get("config_model"),
    provider_id=str(bot["provider_id"]) if bot.get("provider_id") else None,
    model_id=str(bot["model_id"]) if bot.get("model_id") else None,
    knowledge_bases=formatted_kbs,
  )

  return BaseResponse(data=result)


@router.post("/{bot_id}/ask")
@router.post("/{bot_id}/ask/{session_id}")
async def ask_bot(
  bot_id: str,
  request: AskRequest,
  current_user: Annotated[dict, Depends(get_current_user)],
  session_id: Optional[str] = None,
):
  """
  Unified endpoint to ask a bot, with or without an existing session.
  """
  if not session_id:
    import uuid

    session_id = str(uuid.uuid4())

  return await _handle_chat(bot_id, session_id, request, current_user)


async def _handle_chat(
  bot_id: str, session_id: str, request: AskRequest, current_user: dict
):
  user_id = current_user["user_id"]

  logger.info(f"[BotsAPI] Ask request for bot {bot_id}, session {session_id}")

  try:
    kb_ids = await bot_repo_instance.get_bot_kb_ids(bot_id)
    target_kb_id = kb_ids[0] if kb_ids else None

    if not kb_ids:
      logger.info(
        f"[BotsAPI] No KB linked to bot {bot_id}. Proceeding with general chat."
      )

    # 2. Execute chat streaming
    async def event_generator():
      async for chunk in chat_service_instance.stream_chat(
        query=request.message,
        session_id=session_id,
        user_id=user_id,
        kb_id=target_kb_id,
      ):
        if chunk["type"] == "status":
          data = {"response": f"__STATUS__: {json.dumps({'text': chunk['text']})}"}
        elif chunk["type"] == "content":
          data = {
            "response": chunk["text"],
            "session_id": chunk.get("session_id"),
            "role": "assistant",
          }
        elif chunk["type"] == "error":
          data = {"response": f"Error: {chunk['text']}"}

        yield f"data: {json.dumps(data)}\n\n"

      yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

  except Exception as e:
    logger.error(f"Error in ask_bot: {e}")
    raise HTTPException(status_code=500, detail=str(e))
