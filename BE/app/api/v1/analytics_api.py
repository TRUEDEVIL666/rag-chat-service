from fastapi import APIRouter, Depends, HTTPException
from app.core.factory import get_analytics_service
from app.utils.auth import get_current_user
from fastapi_cache.decorator import cache
from fastapi.responses import StreamingResponse
import asyncio
import json
import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter()


@router.get("/analytics/stats", summary="Get dashboard stats only")
@cache(expire=60)
async def get_analytics_stats(
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return await analytics_service.get_summary_stats(auth)
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/chart", summary="Get dashboard chart data")
async def get_analytics_chart(
    time_range: str = "30days",
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return await analytics_service.get_chart_data(auth, time_range=time_range)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/activity", summary="Get recent activity feed")
async def get_recent_activity(
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return await analytics_service.get_recent_activity(auth)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/topics", summary="Get trending topics")
async def get_trending_topics(
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return await analytics_service.get_trending_topics(auth)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/engagement", summary="Get engagement stats")
async def get_engagement_stats(
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return await analytics_service.get_engagement_stats(auth)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/feedback", summary="Get feedback summary")
async def get_feedback_summary(
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return await analytics_service.get_feedback_summary(auth)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
