from fastapi import APIRouter, HTTPException
from app.services import analytics_service_instance

from fastapi_cache.decorator import cache

router = APIRouter()


@router.get("/analytics/stats", summary="Get dashboard stats only")
@cache(expire=60)
async def get_analytics_stats():
  try:
    return await analytics_service_instance.get_summary_stats()
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/chart", summary="Get dashboard chart data")
async def get_analytics_chart(time_range: str = "30days"):
  try:
    return await analytics_service_instance.get_chart_data(time_range=time_range)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/activity", summary="Get recent activity feed")
async def get_recent_activity():
  try:
    return await analytics_service_instance.get_recent_activity()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/topics", summary="Get trending topics")
async def get_trending_topics():
  try:
    return await analytics_service_instance.get_trending_topics()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/engagement", summary="Get engagement stats")
async def get_engagement_stats():
  try:
    return await analytics_service_instance.get_engagement_stats()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/feedback", summary="Get feedback summary")
async def get_feedback_summary():
  try:
    return await analytics_service_instance.get_feedback_summary()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
