# app/api/v1/chatbot.py
from app.schemas.common import MessageResponse
from fastapi_limiter.depends import RateLimiter
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.utils.auth import get_current_user
from app.core.factory import get_bot_service, get_chat_service
from app.services.bot.bot_service import BotService
from app.services.chat.chat_service import ChatService
from app.schemas.bot import (
    BotAskIdRequest, BotAskRequest, BotAskResponse,
    BotCreateRequest, BotIdRequest, BotResponse, BotUpdateConfigIdRequest, BotUpdateConfigRequest
)

router = APIRouter()


@router.post("/bots", response_model=BotResponse, summary="Create new bot")
async def create_bot(
  request: BotCreateRequest,
  bot_service: BotService = Depends(get_bot_service),
  auth=Depends(get_current_user)
):
  bot = await bot_service.create_bot(request, auth["tenant_id"], auth["user_id"], auth.get("token"))
  return bot


@router.put("/bots/{bot_id}", response_model=BotResponse, summary="Update bot configuration")
async def update_bot_config(
  req: BotUpdateConfigIdRequest = Depends(),
  request: BotUpdateConfigRequest = None,
  bot_service: BotService = Depends(get_bot_service),
  auth=Depends(get_current_user)
):
  if request is None:
    raise HTTPException(status_code=400, detail="Request body is required")
  updated_bot = await bot_service.update_config(str(req.bot_id), auth["tenant_id"], request, auth.get("token"))
  return updated_bot


@router.get("/bots", response_model=List[BotResponse], summary="List all bots")
async def list_bots(
  bot_service: BotService = Depends(get_bot_service),
  auth=Depends(get_current_user)
):
  bots = await bot_service.list_bots(auth["tenant_id"], auth.get("token"))
  return bots


@router.get("/bots/{bot_id}", response_model=BotResponse, summary="Get bot by ID")
async def get_bot(
  req: BotIdRequest = Depends(),
  bot_service: BotService = Depends(get_bot_service),
  auth=Depends(get_current_user)
):
  bot = await bot_service.get_bot(str(req.bot_id), auth["tenant_id"], auth.get("token"))
  if not bot:
    raise HTTPException(status_code=404, detail="Bot not found")
  return bot


@router.delete("/bots/{bot_id}", response_model=MessageResponse)
async def delete_bot(
  req: BotIdRequest = Depends(),
  bot_service: BotService = Depends(get_bot_service),
  auth=Depends(get_current_user)
):
  success = await bot_service.delete_bot(str(req.bot_id), auth["tenant_id"], auth.get("token"))
  if not success:
    raise HTTPException(
      status_code=404, detail="Bot not found or could not be deleted")
  return MessageResponse(message="Bot deleted successfully")


@router.post("/bots/{bot_id}/ask", response_model=BotAskResponse, dependencies=[Depends(RateLimiter(times=50, seconds=60))])
@router.post("/bots/{bot_id}/ask/{session_id}", response_model=BotAskResponse, dependencies=[Depends(RateLimiter(times=50, seconds=60))])
async def ask_bot(
    req: BotAskIdRequest = Depends(),
    request: BotAskRequest = None,
    chat_service: ChatService = Depends(get_chat_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]
  user_id = auth["user_id"]

  try:
    # Use unified ask_bot method with stream parameter
    result, new_session_id = await chat_service.ask_bot(
        bot_id=str(req.bot_id),
        query=request.message,
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=req.session_id,
        access_token=auth.get("token"),
        quiz_mode=request.quiz_mode,
        stream=request.streaming  # ← New parameter
    )

    if request.streaming:
      # result is an AsyncGenerator
      async def token_stream():
        # Yield session_id event first so client knows the session
        yield f"data: {json.dumps({'session_id': new_session_id})}\n\n"

        async for chunk in result:
          if chunk:
            yield f"data: {json.dumps({'response': chunk})}\n\n"
        yield "data: [DONE]\n\n"

      return StreamingResponse(token_stream(), media_type="text/event-stream")
    else:
      return BotAskResponse(answer=result, session_id=new_session_id)

  except ValueError as ve:
    raise HTTPException(status_code=404, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
