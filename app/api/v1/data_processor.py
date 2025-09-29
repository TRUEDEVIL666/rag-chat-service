# app/api/v1/data_processor.py
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

@router.post("/upload-file")
async def upload_file_process(
    files: List[UploadFile],
    knowledge_base_id: str,
    auth=Depends(get_current_user)
):
    if not files:
        raise HTTPException(status_code=400, detail="Files is required")
          
    results = []
    for file in files:
        content = await file.read()
        encoded_content = base64.b64encode(content).decode("utf-8")
        task = process_uploaded_file_celery.delay(
            encoded_content, file.filename, auth["tenant_id"], knowledge_base_id
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

@router.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    if result.ready():
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
