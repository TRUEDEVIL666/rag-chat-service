# app/services/document/document_service.py
import uuid
from typing import List, Dict, Any
from fastapi import HTTPException, UploadFile
from celery.result import AsyncResult
import asyncio

from app.core.logger import get_logger
from app.config.celery import celery_app
from app.services.supabase.document_repository import DocumentRepository
from app.services.supabase.graph_chunk_repository import GraphChunkRepository
from app.services.supabase.knowledge_base_repository import KnowledgeBaseRepository
from app.services.minio.minio_storage import MinioStorage
from app.task.file_processor_worker import (
    process_uploaded_file_celery,
    process_update_file_celery
)

logger = get_logger(__name__)


class DocumentService:
  def __init__(
      self,
      doc_repo: DocumentRepository,
      minio_storage: MinioStorage,
      graph_chunk_repo: GraphChunkRepository,
      kb_repo: KnowledgeBaseRepository
  ):
    self.doc_repo = doc_repo
    self.minio_storage = minio_storage
    self.graph_chunk_repo = graph_chunk_repo
    self.kb_repo = kb_repo

  async def upload_documents(
      self,
      kb_id: str,
      files: List[UploadFile],
      tenant_id: str,
      user_id: str,
      access_token: str = None,
      chunking_method: str = "sentence",
      enable_extraction: bool = True,
      **kwargs
  ) -> Dict[str, Any]:
    """
    Orchestrates the upload of multiple documents concurrently.
    Streams files to MinIO using a Semaphore to limit concurrency.
    """
    import os
    from app.config.config import settings

    # 1. Global Validation Phase (Fast, Synchronous)
    for file in files:
      # Check extension
      ext = os.path.splitext(file.filename)[1].lower()
      if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
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
            detail=f"File '{file.filename}' exceeds size limit of {settings.MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    # 2. Concurrent Processing Phase
    semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent uploads

    async def _bounded_process(file):
      async with semaphore:
        return await self._process_single_upload(
            file, kb_id, tenant_id, user_id, access_token,
            chunking_method, enable_extraction=enable_extraction, **kwargs
        )

    results = await asyncio.gather(*[_bounded_process(file) for file in files])

    return {
        "files_queued": len(results),
        "results": results
    }

  async def _process_single_upload(
      self,
      file: UploadFile,
      kb_id: str,
      tenant_id: str,
      user_id: str,
      access_token: str,
      chunking_method: str,
      enable_extraction: bool = True,
      **kwargs
  ) -> Dict[str, Any]:
    """
    Handles the logic for a single file upload:
    - Checks for existing document (Update flow vs New flow).
    - Uploads stream to MinIO.
    - Updates DB.
    - Dispatches Celery task.
    """
    from functools import partial
    from datetime import datetime

    loop = asyncio.get_running_loop()

    try:
      # Check Existence First
      existing_doc = await self.doc_repo.get_document_by_name(
          kb_id,
          file.filename,
          tenant_id,
          access_token
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
                self.minio_storage.stream_upload,
                file.file,
                file_size,
                file.filename,
                file.content_type or "application/octet-stream",
                custom_path
            )
        )

        # 2. Trigger Task (Immediate Status Update)
        await self.doc_repo.update_document_status(
          existing_doc["id"], "learning", access_token)
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
            **kwargs
        )
        return {
            "filename": file.filename,
            "document_id": existing_doc["id"],
            "task_id": task.id,
            "status": "updating"
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
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        created_doc = await self.doc_repo.create_document(
            doc_payload, access_token)

        if not created_doc:
          return {
              "filename": file.filename,
              "status": "failed",
              "message": "Database reservation failed"
          }

        try:
          # 2. Upload to MinIO
          custom_path = f"{tenant_id}/{kb_id}/{file.filename}"
          file_path = await loop.run_in_executor(
              None,
              partial(
                  self.minio_storage.stream_upload,
                  file.file,
                  file_size,
                  file.filename,
                  file.content_type or "application/octet-stream",
                  custom_path
              )
          )

          # 3. Commit (Update DB with real path)
          await self.doc_repo.update_document_upload_success(
              new_doc_id, file_path, access_token)

          # 4. Dispatch Task
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
              **kwargs
          )

          return {
              "filename": file.filename,
              "task_id": task.id,
              "status": "pending"
          }

        except Exception as e:
          # Rollback
          logger.error(
            f"Upload failed for {file.filename}, rolling back DB: {e}")
          await self.doc_repo.delete_document(new_doc_id, access_token)
          return {
              "filename": file.filename,
              "status": "failed",
              "message": str(e)
          }

    except Exception as e:
      logger.error(f"Error processing {file.filename}: {e}")
      return {
          "filename": file.filename,
          "status": "failed",
          "message": "Internal error"
      }

  async def update_document(
      self,
      document_id: str,
      file: UploadFile,
      tenant_id: str,
      user_id: str,
      access_token: str = None,
      chunking_method: str = "sentence",
      enable_extraction: bool = True,
      **kwargs
  ) -> Dict[str, Any]:
    """
    Updates a specific document by ID.
    Validates ownership before triggering incremental sync.
    """
    from functools import partial

    doc = await self.doc_repo.get_document_by_id(document_id, access_token)

    if not doc:
      raise HTTPException(status_code=404, detail="Document not found")

    if doc["tenant_id"] != tenant_id:
      raise HTTPException(
          status_code=403, detail="Not authorized to update this document")

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
              self.minio_storage.stream_upload,
              file.file,
              file_size,
              file.filename,
              file.content_type or "application/octet-stream",
              custom_path
          )
      )

      # IMMEDIATE STATUS UPDATE:
      # Set status to 'learning' immediately so UI reflects the change right away.
      await self.doc_repo.update_document_status(
        document_id, "learning", access_token)

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
          **kwargs
      )

      return {
          "document_id": document_id,
          "task_id": task.id,
          "status": "pending"
      }
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

  async def delete_document(self, document_id: str, tenant_id: str, user_id: str, access_token: str = None) -> dict:
    """
    Deletes a document and all associated data (File, Vectors, Metadata).
    """
    # 1. Fetch Request
    doc = await self.doc_repo.get_document_by_id(document_id, access_token)
    if not doc:
      raise HTTPException(status_code=404, detail="Document not found")

    if doc["tenant_id"] != tenant_id:
      raise HTTPException(
          status_code=403, detail="Not authorized to delete this document")

    # 2. Soft Delete (Mark as trashed)
    await self.doc_repo.update_document_status(document_id, "trashed", access_token)

    # 3. Trigger Background Cleanup
    from app.task.document_cleanup_worker import delete_document_background
    delete_document_background.delay(
        document_id=document_id,
        tenant_id=tenant_id,
        kb_id=str(doc["knowledgebase_id"]),
        access_token=access_token
    )

    return {"id": document_id, "status": "accepted_for_deletion"}

  async def batch_delete_documents(self, doc_ids: List[str], tenant_id: str, user_id: str, access_token: str = None) -> dict:
    """
    Deletes multiple documents efficiently.
    Verifies ownership and triggers background cleanup tasks for current flow.
    """
    results = {
        "success": [],
        "failed": []
    }

    # 1. Fetch all documents to verify ownership
    for doc_id in doc_ids:
      try:
        doc_id_str = str(doc_id)
        doc = await self.doc_repo.get_document_by_id(doc_id_str, access_token)
        if not doc:
          results["failed"].append({"id": doc_id_str, "reason": "Not found"})
          continue

        if doc["tenant_id"] != tenant_id:
          results["failed"].append(
            {"id": doc_id_str, "reason": "Unauthorized"})
          continue

        # 2. Soft Delete (Mark as trashed)
        await self.doc_repo.update_document_status(
          doc_id_str, "trashed", access_token)

        # 3. Trigger Background Cleanup (Async)
        from app.task.document_cleanup_worker import delete_document_background
        delete_document_background.delay(
            document_id=doc_id_str,
            tenant_id=tenant_id,
            kb_id=str(doc["knowledgebase_id"]),
            access_token=access_token
        )
        results["success"].append(doc_id_str)

      except Exception as e:
        logger.error(f"Failed to batch delete doc {doc_id}: {e}")
        results["failed"].append({"id": str(doc_id), "reason": str(e)})

    return results

  async def retry_document_processing(
      self,
      document_id: str,
      tenant_id: str,
      user_id: str,
      access_token: str
  ) -> Dict[str, Any]:
    """
    Retry processing a failed document.
    """
    # 1. Fetch Request
    document = await self.doc_repo.get_document_by_id(document_id, access_token)
    if not document:
      raise HTTPException(status_code=404, detail="Document not found")

    if document.get("status") not in ["failed", "error", "Error"]:
      # Optional: allow retrying even if not strictly failed, but useful to restrict
      # logger.warning(f"Retrying document {document_id} with status {document.get('status')}")
      pass

    # 2. Get KB to find default chunking params if not stored (Assumption: using defaults)
    # Ideally, we should have stored the params used, but for now we fallback to defaults
    # or if we can extract them from somewhere.
    # For fail-safe, we use defaults.

    # 3. Dispatch Task (Reuse existing file in MinIO)
    task = process_uploaded_file_celery.delay(
        file_path=document.get("path"),  # Expecting MinIO path here
        file_name=document.get("name"),
        kb_id=document.get("knowledgebase_id"),
        tenant_id=tenant_id,
        created_by=document.get("created_by"),
        document_id=document_id,
        access_token=access_token,
        chunking_method="sentence",  # Default
        # **kwargs # We might be missing original kwargs
    )

    # 4. Update Status
    await self.doc_repo.update_document_status(document_id, "learning", access_token)

    return {
        "document_id": document_id,
        "task_id": task.id,
        "status": "retrying"
    }

  async def get_document_file_url(self, document_id: str, tenant_id: str, access_token: str = None) -> str:
    """
    Get a presigned URL for the document file from MinIO.
    """
    doc = await self.doc_repo.get_document_by_id(document_id, access_token)
    if not doc:
      raise HTTPException(status_code=404, detail="Document not found")

    if doc["tenant_id"] != tenant_id:
      raise HTTPException(
          status_code=403, detail="Not authorized to access this document")

    file_path = doc.get("path")
    if not file_path:
      raise HTTPException(
          status_code=404, detail="File path not found for this document")

    return self.minio_storage.get_presigned_url(file_path)

  async def get_document_stream(self, document_id: str, tenant_id: str, access_token: str = None):
    """
    Get the file stream for a document.
    """
    doc = await self.doc_repo.get_document_by_id(document_id, access_token)
    if not doc:
      raise HTTPException(status_code=404, detail="Document not found")

    if doc["tenant_id"] != tenant_id:
      raise HTTPException(
          status_code=403, detail="Not authorized to access this document")

    file_path = doc.get("path")
    if not file_path:
      raise HTTPException(
          status_code=404, detail="File path not found for this document")

    # Return stream, filename, and content_type (guess if needed)
    # MinIO response has headers, we can try to use them or just octet-stream
    stream = self.minio_storage.get_file_stream(file_path)
    import mimetypes
    content_type, _ = mimetypes.guess_type(doc.get("name"))
    return stream, doc.get("name"), content_type or "application/octet-stream"
