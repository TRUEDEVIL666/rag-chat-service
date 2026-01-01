from app.config.celery import celery_app
from app.core.logger import get_logger


logger = get_logger("document_cleanup_worker")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def delete_document_background(self, document_id: str, tenant_id: str, kb_id: str, access_token: str):
  from app.core.factory import (
      get_document_repository,
      get_metadata_repository,
      get_vector_store,
      get_minio_storage,
      get_knowledge_base_repository
  )

  """
  Background task to cleanup all resources associated with a document.
  Steps:

  1. Delete from MinIO (File)
  2. Delete from Metadata (Chunks)
  3. Delete from Vector Store (Points)
  4. Physically Delete from Database (or keep as soft-deleted depending on policy,
     but for now we will hard delete after cleanup to maintain cleanliness as per original behavior)
  """
  logger.info(f"Starting background cleanup for document {document_id}")

  try:
    # Initialize Services
    doc_repo = get_document_repository()
    minio_storage = get_minio_storage()
    metadata_repo = get_metadata_repository()
    vector_repo = get_vector_store()
    kb_repo = get_knowledge_base_repository()

    # 1. Get Document Details (if needed for path)
    doc = doc_repo.get_document_by_id(document_id, access_token=access_token)
    if not doc:
      logger.warning(
          f"Document {document_id} not found in DB during cleanup. Already deleted?")
      return "Skipped (Not Found)"

    # 2. Delete from MinIO
    file_path = doc.get("path")
    if file_path:
      try:
        minio_storage.delete_file(file_path)
        logger.info(f"Deleted file {file_path} from MinIO")
      except Exception as e:
        logger.error(f"MinIO deletion failed: {e}")
        # We continue despite MinIO error to ensure other cleanups happen?
        # Or retry? For now, we log and continue to avoid blocking DB cleanup.

    # 3. Delete Metadata (Chunks)
    try:
      metadata_repo.delete_by_document_id(document_id)
      logger.info("Deleted metadata chunks")
    except Exception as e:
      logger.error(f"Metadata deletion failed: {e}")

    # 4. Delete Vectors
    try:
      # Pass access_token to ensure we can read all fields if RLS is enabled
      kb_data = kb_repo.get_one(kb_id, tenant_id, access_token=access_token)

      embedding_model = None
      if kb_data:
        em = kb_data.get("embedding_model")
        if isinstance(em, str):
          embedding_model = em
        elif isinstance(em, dict):
          # Fallback: if it wasn't formatted as string string, try to get model_id
          # ideally we want provider/model_id but if provider is missing, just model_id might be the best we have
          embedding_model = em.get("model_id")

      vector_repo.delete_by_doc_id(document_id, model_name=embedding_model)
      logger.info(f"Deleted vectors using model {embedding_model}")
    except Exception as e:
      logger.error(f"Vector deletion failed: {e}")

    # 5. Final DB Record Deletion
    # If we want a "Hard Delete" eventually:
    doc_repo.delete_document(document_id, access_token=access_token)
    logger.info("Deleted document record from Database")

    return "Cleanup Success"

  except Exception as e:
    logger.exception(f"Cleanup task failed for {document_id}: {e}")
    # Retry logic could go here
    raise self.retry(exc=e)
