# app/services/document/document_service_instance.py
import asyncio
import uuid
from datetime import timezone
from typing import Any, Dict, List

from celery.result import AsyncResult
from fastapi import HTTPException, UploadFile

from app.config.celery import celery_app
from app.core.context import (
  get_current_tenant_id,
  get_current_token,
  get_current_user_id,
)
from app.core.logger import get_logger
from app.repositories import (
  DocumentRepository,
  GraphChunkRepository,
  KnowledgeBaseRepository,
)
from app.services.minio_storage_service import MinioStorageService

logger = get_logger(__name__)


class DocumentService:
  _instance = None

  @classmethod
  def get_instance(cls) -> "DocumentService":
    if cls._instance is None:
      from app.repositories import (
        DocumentRepository,
        GraphChunkRepository,
        KnowledgeBaseRepository,
      )

      cls._instance = cls(
        document_repo_instance=DocumentRepository.get_instance(),
        minio_storage_instance=MinioStorageService.get_instance(),
        graph_chunk_repo_instance=GraphChunkRepository.get_instance(),
        kb_repo_instance=KnowledgeBaseRepository.get_instance(),
      )
    return cls._instance

  def __init__(
    self,
    document_repo_instance: DocumentRepository,
    minio_storage_instance: MinioStorageService,
    graph_chunk_repo_instance: GraphChunkRepository,
    kb_repo_instance: KnowledgeBaseRepository,
  ):
    self.document_repo_instance = document_repo_instance
    self.minio_storage_instance = minio_storage_instance
    self.graph_chunk_repo_instance = graph_chunk_repo_instance
    self.kb_repo_instance = kb_repo_instance

  async def upload_documents(
    self,
    kb_id: str,
    files: List[UploadFile],
    chunking_method: str = "sentence",
    enable_extraction: bool = True,
    **kwargs,
  ) -> Dict[str, Any]:
    """
    Orchestrates the upload of multiple documents concurrently.
    Streams files to MinIO using a Semaphore to limit concurrency.
    """
    import os

    from app.config.config import settings

    # Resolve from context
    tenant_id = get_current_tenant_id()
    user_id = get_current_user_id()
    access_token = get_current_token()

    # 1. Global Validation Phase (Fast, Synchronous)
    for file in files:
      # Check extension
      ext = os.path.splitext(file.filename)[1].lower()
      if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
          status_code=400,
          detail=f"File type '{ext}' not supported. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

      # Check size
      file_size = file.size
      if not file_size:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

      if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
          status_code=400,
          detail=f"File '{file.filename}' exceeds size limit of {settings.MAX_FILE_SIZE / 1024 / 1024:.0f}MB",
        )

    # 2. Concurrent Processing Phase
    semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent uploads

    async def _bounded_process(file):
      async with semaphore:
        return await self._process_single_upload(
          file,
          kb_id,
          tenant_id,
          user_id,
          access_token,
          chunking_method,
          enable_extraction=enable_extraction,
          **kwargs,
        )

    results = await asyncio.gather(*[_bounded_process(file) for file in files])

    return {"files_queued": len(results), "results": results}

  async def _process_single_upload(
    self,
    file: UploadFile,
    kb_id: str,
    tenant_id: str,
    user_id: str,
    access_token: str,
    chunking_method: str,
    enable_extraction: bool = True,
    **kwargs,
  ) -> Dict[str, Any]:
    """
    Handles the logic for a single file upload:
    - Checks for existing document (Update flow vs New flow).
    - Uploads stream to MinIO.
    - Updates DB.
    - Dispatches Celery task.
    """
    from datetime import datetime
    from functools import partial

    loop = asyncio.get_running_loop()

    try:
      # Check Existence First
      existing_doc = await self.document_repo_instance.get_document_by_name(
        kb_id, file.filename
      )

      file_size = file.size or 0
      if not file_size:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

      if existing_doc:
        # --- EXISTING FILE UPDATE FLOW ---
        # 1. Upload to MinIO
        custom_path = f"{tenant_id}/{kb_id}/{file.filename}"
        file_path = await loop.run_in_executor(
          None,
          partial(
            self.minio_storage_instance.stream_upload,
            file.file,
            file_size,
            file.filename,
            file.content_type or "application/octet-stream",
            custom_path,
          ),
        )

        # 2. Trigger Task (Immediate Status Update)
        await self.document_repo_instance.update_document_status(
          existing_doc["id"], "learning"
        )
        from app.worker.file_processor_worker import process_update_file_celery

        task = process_update_file_celery.delay(
          document_id=existing_doc["id"],
          file_path=file_path,
          file_name=file.filename,
          kb_id=kb_id,
          tenant_id=tenant_id,
          created_by=user_id,
          access_token=access_token,
          chunking_method=chunking_method,
          enable_extraction=enable_extraction,
          **kwargs,
        )
        return {
          "filename": file.filename,
          "document_id": existing_doc["id"],
          "task_id": task.id,
          "status": "updating",
        }

      else:
        # --- NEW FILE FLOW ---
        new_doc_id = str(uuid.uuid4())

        # 1. Reserve DB Record
        doc_payload = {
          "id": new_doc_id,
          "name": file.filename,
          "path": "PENDING_UPLOAD",
          "knowledgebase_id": kb_id,
          "tenant_id": tenant_id,
          "created_by": user_id,
          "status": "learning",
          "created_at": datetime.now(timezone.utc).isoformat(),
          "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        created_doc = await self.document_repo_instance.create_document(doc_payload)

        if not created_doc:
          return {
            "filename": file.filename,
            "status": "failed",
            "message": "Database reservation failed",
          }

        try:
          # 2. Upload to MinIO
          custom_path = f"{tenant_id}/{kb_id}/{file.filename}"
          file_path = await loop.run_in_executor(
            None,
            partial(
              self.minio_storage_instance.stream_upload,
              file.file,
              file_size,
              file.filename,
              file.content_type or "application/octet-stream",
              custom_path,
            ),
          )

          # 3. Commit (Update DB with real path)
          await self.document_repo_instance.update_document_upload_success(
            new_doc_id, file_path
          )

          # 4. Dispatch Task
          from app.worker.file_processor_worker import process_uploaded_file_celery

          task = process_uploaded_file_celery.delay(
            file_path,
            file.filename,
            kb_id,
            tenant_id,
            user_id,
            new_doc_id,
            access_token,
            chunking_method,
            enable_extraction=enable_extraction,
            **kwargs,
          )

          return {
            "filename": file.filename,
            "task_id": task.id,
            "status": "pending",
          }

        except Exception as e:
          # Rollback
          logger.error(f"Upload failed for {file.filename}, rolling back DB: {e}")
          await self.document_repo_instance.delete_document(new_doc_id)
          return {
            "filename": file.filename,
            "status": "failed",
            "message": str(e),
          }

    except Exception as e:
      logger.error(f"Error processing {file.filename}: {e}")
      return {
        "filename": file.filename,
        "status": "failed",
        "message": "Internal error",
      }

  async def update_document(
    self,
    document_id: str,
    file: UploadFile,
    chunking_method: str = "sentence",
    enable_extraction: bool = True,
    **kwargs,
  ) -> Dict[str, Any]:
    from functools import partial

    tenant_id = get_current_tenant_id()
    user_id = get_current_user_id()
    access_token = get_current_token()

    doc = await self.document_repo_instance.get_document_by_id(document_id)

    if not doc:
      raise HTTPException(status_code=404, detail="Document not found")

    if doc["tenant_id"] != tenant_id:
      raise HTTPException(
        status_code=403, detail="Not authorized to update this document"
      )

    try:
      file_size = file.size
      if not file_size:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

      loop = asyncio.get_running_loop()
      custom_path = f"{tenant_id}/{doc['knowledgebase_id']}/{file.filename}"
      file_path = await loop.run_in_executor(
        None,
        partial(
          self.minio_storage_instance.stream_upload,
          file.file,
          file_size,
          file.filename,
          file.content_type or "application/octet-stream",
          custom_path,
        ),
      )

      await self.document_repo_instance.update_document_status(document_id, "learning")

      from app.worker.file_processor_worker import process_update_file_celery

      task = process_update_file_celery.delay(
        document_id=document_id,
        file_path=file_path,
        file_name=file.filename,
        kb_id=str(doc["knowledgebase_id"]),
        tenant_id=tenant_id,
        created_by=user_id,
        access_token=access_token,
        chunking_method=chunking_method,
        enable_extraction=enable_extraction,
        **kwargs,
      )

      return {"document_id": document_id, "task_id": task.id, "status": "pending"}
    except HTTPException:
      raise
    except Exception as e:
      logger.exception(f"Failed to initiate document update for {document_id}")
      raise HTTPException(status_code=500, detail=str(e))

  async def get_task_status(self, task_id: str) -> Dict[str, Any]:
    """
    Checks the status of a Celery processing task.
    """
    result = AsyncResult(task_id, app=celery_app)

    if result.ready():
      if result.status == "FAILURE":
        return {
          "task_id": task_id,
          "status": result.status,
          "result": str(result.result),
          "message": "Task failed",
        }

      return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result,
      }
    else:
      return {
        "task_id": task_id,
        "status": result.status,
        "message": "Processing...",
      }

  async def delete_document(self, document_id: str) -> dict:
    """
    Deletes a document and all associated data (File, Vectors, Metadata).
    """
    tenant_id = get_current_tenant_id()
    access_token = get_current_token()

    # 1. Fetch Request
    doc = await self.document_repo_instance.get_document_by_id(document_id)
    if not doc:
      raise HTTPException(status_code=404, detail="Document not found")

    if doc["tenant_id"] != tenant_id:
      raise HTTPException(
        status_code=403, detail="Not authorized to delete this document"
      )

    # 2. Soft Delete
    await self.document_repo_instance.update_document_status(document_id, "trashed")

    # 3. Trigger Background Cleanup
    from app.worker.document_cleanup_worker import delete_document_background

    delete_document_background.delay(
      document_id=document_id,
      tenant_id=tenant_id,
      kb_id=str(doc["knowledgebase_id"]),
      access_token=access_token,
    )

    return {"id": document_id, "status": "accepted_for_deletion"}

  async def batch_delete_documents(self, doc_ids: List[str]) -> dict:
    """
    Deletes multiple documents efficiently.
    Verifies ownership and triggers background cleanup tasks for current flow.
    """
    tenant_id = get_current_tenant_id()
    access_token = get_current_token()

    results = {"success": [], "failed": []}

    # 1. Fetch all documents to verify ownership
    for doc_id in doc_ids:
      try:
        doc_id_str = str(doc_id)
        doc = await self.document_repo_instance.get_document_by_id(doc_id_str)
        if not doc:
          results["failed"].append({"id": doc_id_str, "reason": "Not found"})
          continue

        if doc["tenant_id"] != tenant_id:
          results["failed"].append({"id": doc_id_str, "reason": "Unauthorized"})
          continue

        # 2. Soft Delete (Mark as trashed)
        await self.document_repo_instance.update_document_status(doc_id_str, "trashed")

        # 3. Trigger Background Cleanup (Async)
        from app.worker.document_cleanup_worker import delete_document_background

        delete_document_background.delay(
          document_id=doc_id_str,
          tenant_id=tenant_id,
          kb_id=str(doc["knowledgebase_id"]),
          access_token=access_token,
        )
        results["success"].append(doc_id_str)

      except Exception as e:
        logger.error(f"Failed to batch delete doc {doc_id}: {e}")
        results["failed"].append({"id": str(doc_id), "reason": str(e)})

    return results

  async def retry_document_processing(self, document_id: str) -> Dict[str, Any]:
    """
    Retry processing a failed document.
    """
    tenant_id = get_current_tenant_id()
    access_token = get_current_token()

    # 1. Fetch Request
    document = await self.document_repo_instance.get_document_by_id(document_id)
    if not document:
      raise HTTPException(status_code=404, detail="Document not found")

    # 2. Dispatch Task (Reuse existing file in MinIO)
    from app.worker.file_processor_worker import process_uploaded_file_celery

    task = process_uploaded_file_celery.delay(
      file_path=document.get("path"),
      file_name=document.get("name"),
      kb_id=document.get("knowledgebase_id"),
      tenant_id=tenant_id,
      created_by=document.get("created_by"),
      document_id=document_id,
      access_token=access_token,
      chunking_method="sentence",
    )

    # 3. Update Status
    await self.document_repo_instance.update_document_status(document_id, "learning")

    return {"document_id": document_id, "task_id": task.id, "status": "retrying"}

  async def get_document_stream(self, document_id: str):
    """
    Get the file stream for a document.
    """
    tenant_id = get_current_tenant_id()

    doc = await self.document_repo_instance.get_document_by_id(document_id)
    if not doc:
      raise HTTPException(status_code=404, detail="Document not found")

    if doc["tenant_id"] != tenant_id:
      raise HTTPException(
        status_code=403, detail="Not authorized to access this document"
      )

    file_path = doc.get("path")
    if not file_path:
      raise HTTPException(
        status_code=404, detail="File path not found for this document"
      )

    # Return stream, filename, and content_type (guess if needed)
    # MinIO response has headers, we can try to use them or just octet-stream
    stream = self.minio_storage_instance.get_file_stream(file_path)
    import mimetypes

    content_type, _ = mimetypes.guess_type(doc.get("name"))
    return stream, doc.get("name"), content_type or "application/octet-stream"
