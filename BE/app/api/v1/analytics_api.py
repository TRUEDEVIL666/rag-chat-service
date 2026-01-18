from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from app.core.factory import get_analytics_service
from app.utils.auth import get_current_user
from fastapi_cache.decorator import cache
from app.schemas.analytics import AnalyticsSummaryResponse
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
    return analytics_service.get_summary_stats(auth)
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/chart", summary="Get dashboard chart data (Streaming)")
async def get_analytics_chart(
    time_range: str = "30days",
    analytics_service=Depends(get_analytics_service),
    auth: dict = Depends(get_current_user)
):
  async def data_generator():
    now = datetime.datetime.now(datetime.timezone.utc)
    interval = "day"
    start_date = now - datetime.timedelta(days=30)
    end_date = now

    if time_range == "7days":
      start_date = now - datetime.timedelta(days=7)
    elif time_range == "30days":
      start_date = now - datetime.timedelta(days=30)
    elif time_range == "all":
      start_date = now - relativedelta(years=1)
      interval = "month"

    # Chunking logic
    chunk_size_days = 5
    if interval == "month":
      chunk_size_days = 30  # Approx 1 month roughly

    current_start = start_date
    while current_start < end_date.replace(microsecond=0):  # Compare properly
      current_end = current_start + datetime.timedelta(days=chunk_size_days)
      if current_end > end_date:
        current_end = end_date

      # Fetch chunk
      data_chunk = await run_in_threadpool(
          analytics_service.get_chart_data_custom,
          auth,
          start_date=current_start.isoformat(),
          end_date=current_end.isoformat(),
          interval=interval
      )

      if data_chunk:
        yield f"data: {json.dumps(data_chunk)}\n\n"

      current_start = current_end
      await asyncio.sleep(0.01)  # Yield control

  return StreamingResponse(data_generator(), media_type="text/event-stream")
