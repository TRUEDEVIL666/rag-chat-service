from fastapi import APIRouter, Depends, HTTPException
from app.core.factory import get_analytics_service
from app.utils.auth import get_current_user
from fastapi_cache.decorator import cache
from app.schemas.analytics import AnalyticsSummaryResponse

router = APIRouter()


@router.get("/analytics/summary", summary="Get dashboard summary counts", response_model=AnalyticsSummaryResponse)
@cache(expire=60)  # Cache for 1 minute to avoid hammering DB
async def get_analytics_summary(
    time_range: str = "30days",
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  try:
    return analytics_service.get_summary(auth, time_range)
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
