# app/api/v1/data_processor.py
from app.schemas.data_processor import (
    FileUploadResponse, TaskStatusResponse,
    FileUploadRequest
)
import base64
from typing import List
from fastapi import APIRouter, UploadFile, HTTPException, Depends
from celery.result import AsyncResult
from app.config.celery import celery_app
from app.core.logger import get_logger
from app.utils.auth import get_current_user
from app.task.file_processor_worker import process_uploaded_file_celery

# import asyncio
# import sys

# if sys.platform.startswith('win'):
#     print("Setting Windows event loop policy")
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

router = APIRouter()

logger = get_logger("upload")


@router.post("/upload-file", response_model=FileUploadResponse)
async def upload_file_process(
    request: FileUploadRequest = Depends(),
    auth=Depends(get_current_user)
):
  if not request.files:
    raise HTTPException(status_code=400, detail="Files is required")

  results = []
  for file in request.files:
    content = await file.read()
    encoded_content = base64.b64encode(content).decode("utf-8")
    task = process_uploaded_file_celery.delay(
        encoded_content,
        file.filename,
        request.knowledge_base_id,
        auth["tenant_id"],
        auth["user_id"],
        request.chunking_method
    )
    results.append({
        "filename": file.filename,
        "task_id": task.id,
        "status": "pending"
    })

  return {
      "files_queued": len(results),
      "results": results
  }


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
  result = AsyncResult(task_id, app=celery_app)

  if result.ready():
    if result.status == "FAILURE":
      return {
          "task_id": task_id,
          "status": result.status,
          "result": str(result.result),
          "message": "Task failed"
      }

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result
    }
  else:
    return {
        "task_id": task_id,
        "status": result.status,
        "message": "Processing..."
    }
