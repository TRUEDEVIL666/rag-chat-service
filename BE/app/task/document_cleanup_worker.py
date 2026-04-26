from app.config.celery import celery_app
from app.core.logger import get_logger


logger = get_logger(__name__)


def _run_async(coro):
  """Helper to run async coroutines in a synchronous context."""
  import asyncio

  try:
    loop = asyncio.get_event_loop()
  except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

  if loop.is_running():
    import nest_asyncio

    nest_asyncio.apply(loop)
    return loop.run_until_complete(coro)
  else:
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def delete_document_background(
  self, document_id: str, tenant_id: str, kb_id: str, access_token: str
):
  """
  Background task to cleanup all resources associated with a document.
  Steps:

  1. Delete from MinIO (File)
  2. Delete from Metadata (Chunks) — CASCADE auto-deletes vectors
  3. Final DB Record Deletion
  """
  from app.repositories import document_repo_instance, graph_chunk_repo_instance
  from app.services import minio_storage_instance
  logger.info(f"Starting background cleanup for document {document_id}")

  try:
    # 1. Get Document Details (if needed for path)
    doc = _run_async(
      document_repo_instance.get_document_by_id(document_id, access_token=access_token)
    )
    if not doc:
      logger.warning(
        f"Document {document_id} not found in DB during cleanup. Already deleted?"
      )
      return "Skipped (Not Found)"

    # 2. Delete from MinIO
    file_path = doc.get("path")
    if file_path:
      try:
        minio_storage_instance.delete_file(file_path)
        logger.info(f"Deleted file {file_path} from MinIO")
      except Exception as e:
        logger.error(f"MinIO deletion failed: {e}")

    # 3. Delete Metadata (Chunks) — CASCADE auto-deletes associated vectors
    try:
      _run_async(graph_chunk_repo_instance.delete_by_document_id(document_id))
      logger.info("Deleted graph chunks (CASCADE auto-deleted vectors)")
    except Exception as e:
      logger.error(f"Metadata deletion failed: {e}")

    # 4. Final DB Record Deletion
    _run_async(
      document_repo_instance.delete_document(document_id, access_token=access_token)
    )
    logger.info("Deleted document record from Database")

    return "Cleanup Success"

  except Exception as e:
    logger.exception(f"Cleanup task failed for {document_id}: {e}")
    raise self.retry(exc=e)
