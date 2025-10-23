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
    auth=Depends(get_current_user)
):
    tenant_id = auth["tenant_id"]
    user_id = auth["user_id"]

    try:
        bot = BotService.create_bot(request, tenant_id, user_id)
        return bot
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/bots/{bot_id}/config", summary="Update bot configuration")
async def update_bot_config(
    bot_id: str,
    request: BotUpdateConfigRequest,
    auth=Depends(get_current_user)
):
    tenant_id = auth["tenant_id"]
    try:
        updated_bot = BotService.update_config(bot_id, tenant_id, request)
        return {"message": "Bot updated successfully", "bot": updated_bot}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots", response_model=List[BotResponse], summary="List all bots of current tenant")
async def list_bots(auth=Depends(get_current_user)):
    tenant_id = auth["tenant_id"]
    try:
        bots = BotService.list_bots(tenant_id)
        return bots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bots/{bot_id}", response_model=BotResponse, summary="Get detailed information about a bot")
async def get_bot(bot_id: str, auth=Depends(get_current_user)):
    tenant_id = auth["tenant_id"]
    try:
        bot = BotService.get_bot(bot_id, tenant_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return bot
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bots/{bot_id}", summary="Delete a bot", response_model=dict)
async def delete_bot(bot_id: str, auth=Depends(get_current_user)):
    tenant_id = auth["tenant_id"]
    try:
        deleted = BotService.delete_bot(bot_id, tenant_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Bot not found or not owned by tenant")
        return {"message": "Bot deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bots/{bot_id}/ask", response_model=BotAskResponse)
async def ask_bot(
    bot_id: str,
    request: BotAskRequest,
    bot_service: BotService = Depends(get_bot_service),
    auth=Depends(get_current_user)
):
    tenant_id = auth["tenant_id"]
    try:
        if request.streaming:
            async def token_stream():
                async for chunk in bot_service.ask_bot_stream(
                    bot_id=bot_id,
                    query=request.message,
                    tenant_id=tenant_id
                ):
                    if chunk:
                        yield f"data: {json.dumps({'response': chunk}, ensure_ascii=False)}\n\n"
                print("Stream finished")
            return StreamingResponse(token_stream(), media_type="text/event-stream")

        else:
            answer = await bot_service.ask_bot(
                bot_id=bot_id,
                query=request.message,
                tenant_id=tenant_id
            )
            print("No streaming, returning answer")
            return {"answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


