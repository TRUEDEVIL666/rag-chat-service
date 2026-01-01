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
from app.core.factory import get_bot_service
from app.services.bot.bot_service import BotService
from app.schemas.bot import (
    BotAskIdRequest, BotAskRequest, BotAskResponse,
    BotCreateRequest, BotIdRequest, BotResponse, BotUpdateConfigIdRequest, BotUpdateConfigRequest
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
    access_token = auth.get("token")
    bot = await bot_service.create_bot(request, tenant_id, user_id, access_token)
    # Clear cache so the new bot appears in the list
    await FastAPICache.clear(namespace="bots")
    return bot
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.patch("/bots/{bot_id}/config", summary="Update bot configuration")
async def update_bot_config(
    req: BotUpdateConfigIdRequest = Depends(),
    request: BotUpdateConfigRequest = None,
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  try:
    access_token = auth.get("token")
    updated_bot = await bot_service.update_config(str(req.bot_id), tenant_id, request, access_token)
    # Clear cache so config changes are reflected
    await FastAPICache.clear(namespace="bots")
    return {"message": "Bot updated successfully", "bot": updated_bot}
  except ValueError as ve:
    raise HTTPException(status_code=404, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots", response_model=List[BotResponse], summary="List all bots of current tenant")
@cache(expire=60, namespace="bots")
async def list_bots(
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  try:
    access_token = auth.get("token")
    bots = await bot_service.list_bots(tenant_id, access_token)
    return bots
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots/{bot_id}", response_model=BotResponse, summary="Get detailed information about a bot")
async def get_bot(
    req: BotIdRequest = Depends(),
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  try:
    access_token = auth.get("token")
    bot = await bot_service.get_bot(str(req.bot_id), tenant_id, access_token)
    if not bot:
      raise HTTPException(status_code=404, detail="Bot not found")
    return bot
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bots/{bot_id}", summary="Delete a bot", response_model=MessageResponse)
async def delete_bot(
    req: BotIdRequest = Depends(),
    auth=Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
):
  tenant_id = auth["tenant_id"]
  try:
    access_token = auth.get("token")
    deleted = await bot_service.delete_bot(str(req.bot_id), tenant_id, access_token)
    if not deleted:
      raise HTTPException(
        status_code=404, detail="Bot not found or not owned by tenant")

    # Clear cache
    await FastAPICache.clear(namespace="bots")

    return {"message": "Bot deleted successfully"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/bots/{bot_id}/ask", response_model=BotAskResponse, dependencies=[Depends(RateLimiter(times=50, seconds=60))])
@router.post("/bots/{bot_id}/ask/{session_id}", response_model=BotAskResponse, dependencies=[Depends(RateLimiter(times=50, seconds=60))])
async def ask_bot(
    req: BotAskIdRequest = Depends(),
    request: BotAskRequest = None,
    bot_service: BotService = Depends(get_bot_service),
    auth=Depends(get_current_user)
):
  tenant_id = auth["tenant_id"]
  user_id = auth["user_id"]

  try:
    if request.streaming:
      # Prepare stream immediately to catch initialization errors (e.g. 404 Session Not Found)
      stream_generator, new_session_id = await bot_service.ask_bot_stream(
          bot_id=str(req.bot_id),
          query=request.message,
          tenant_id=tenant_id,
          user_id=user_id,
          session_id=req.session_id,
          access_token=auth.get("token")
      )

      async def token_stream():
        # Yield session_id event first so client knows the session
        yield f"data: {json.dumps({'session_id': new_session_id})}\n\n"

        async for chunk in stream_generator:
          if chunk:
            yield f"data: {json.dumps({'response': chunk})}\n\n"
        yield "data: [DONE]\n\n"

      return StreamingResponse(token_stream(), media_type="text/event-stream")
    else:
      response, new_session_id = await bot_service.ask_bot(
          bot_id=str(req.bot_id),
          query=request.message,
          tenant_id=tenant_id,
          user_id=user_id,
          session_id=req.session_id,
          access_token=auth.get("token")
      )
      return BotAskResponse(answer=response, session_id=new_session_id)

  except ValueError as ve:
    raise HTTPException(status_code=404, detail=str(ve))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
