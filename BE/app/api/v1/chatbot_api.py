# app/api/v1/chatbot.py
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.utils.auth import get_current_user
from app.core.factory import get_bot_service
from app.services.bot.bot_service import BotService
from app.schemas.bot import (
    BotAskRequest, BotAskResponse,
    BotCreateRequest, BotResponse, BotUpdateConfigRequest
)

router = APIRouter()


@router.post("/bots", response_model=BotResponse, summary="Create new bot")
async def create_bot(
    request: BotCreateRequest,
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  user_id = auth["user_id"]

  try:
    bot = await bot_service.create_bot(request, tenant_id, user_id)
    return bot
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.patch("/bots/{bot_id}/config", summary="Update bot configuration")
async def update_bot_config(
    bot_id: str,
    request: BotUpdateConfigRequest,
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  try:
    updated_bot = await bot_service.update_config(bot_id, tenant_id, request)
    return {"message": "Bot updated successfully", "bot": updated_bot}
  except ValueError as ve:
    raise HTTPException(status_code=404, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots", response_model=List[BotResponse], summary="List all bots of current tenant")
async def list_bots(
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  try:
    bots = await bot_service.list_bots(tenant_id)
    return bots
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots/{bot_id}", response_model=BotResponse, summary="Get detailed information about a bot")
async def get_bot(
    bot_id: str,
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  try:
    bot = await bot_service.get_bot(bot_id, tenant_id)
    if not bot:
      raise HTTPException(status_code=404, detail="Bot not found")
    return bot
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bots/{bot_id}", summary="Delete a bot", response_model=dict)
async def delete_bot(
    bot_id: str,
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  try:
    deleted = await bot_service.delete_bot(bot_id, tenant_id)
    if not deleted:
      raise HTTPException(
        status_code=404, detail="Bot not found or not owned by tenant")
    return {"message": "Bot deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/bots/{bot_id}/ask", response_model=BotAskResponse)
@router.post("/bots/{bot_id}/ask/{session_id}", response_model=BotAskResponse)
async def ask_bot(
    bot_id: str,
    request: BotAskRequest,
    session_id: str = "",
    bot_service: BotService = Depends(get_bot_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]
  user_id = auth["user_id"]

  try:
    if request.streaming:
      async def token_stream():
        stream_generator, new_session_id = await bot_service.ask_bot_stream(
            bot_id=bot_id,
            query=request.message,
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id
        )
        # Yield session_id event first so client knows the session
        yield f"data: {json.dumps({'session_id': new_session_id})}\n\n"

        async for chunk in stream_generator:
          if chunk:
            yield f"data: {json.dumps({'response': chunk})}\n\n"
        yield "data: [DONE]\n\n"

      return StreamingResponse(token_stream(), media_type="text/event-stream")
    else:
      response, new_session_id = await bot_service.ask_bot(
          bot_id=bot_id,
          query=request.message,
          tenant_id=tenant_id,
          user_id=user_id,
          session_id=session_id
      )
      return BotAskResponse(answer=response, session_id=new_session_id)

  except ValueError as ve:
    raise HTTPException(status_code=404, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
