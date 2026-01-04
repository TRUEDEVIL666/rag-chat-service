from fastapi import APIRouter, Depends, HTTPException
from app.core.factory import get_analytics_service
from app.utils.auth import get_current_user
from fastapi_cache.decorator import cache
from app.schemas.analytics import AnalyticsSummaryResponse

router = APIRouter()


@router.get("/analytics/stats", summary="Get dashboard stats only")
@cache(expire=60)
async def get_analytics_stats(
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return analytics_service.get_summary_stats(auth)
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/chart", summary="Get dashboard chart data only")
@cache(expire=300)
async def get_analytics_chart(
    time_range: str = "30days",
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return analytics_service.get_chart_data(auth, time_range)
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
