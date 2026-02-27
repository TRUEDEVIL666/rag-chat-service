from app.config.celery import celery_app


@celery_app.task(name="process_uploaded_file_celery")
def process_uploaded_file_celery(
    file_path: str,
    file_name: str,
    kb_id: str,
    tenant_id: str,
    created_by: str,
    document_id: str,
    access_token: str,
    chunking_method: str = "sentence",
    **kwargs
):
  from app.core.factory import get_file_processor_service
  file_processor = get_file_processor_service()

  return file_processor.process_file(
      file_path=file_path,
      file_name=file_name,
      kb_id=kb_id,
      tenant_id=tenant_id,
      created_by=created_by,
      document_id=document_id,
      chunking_method=chunking_method,
      access_token=access_token,
      **kwargs
  )


@celery_app.task(name="process_update_file_celery")
def process_update_file_celery(
    document_id: str,
    file_path: str,
    file_name: str,
    kb_id: str,
    tenant_id: str,
    created_by: str,
    access_token: str,
    chunking_method: str = "sentence",
    **kwargs
):
  from app.core.factory import get_file_processor_service
  file_processor = get_file_processor_service()
  return file_processor.process_file_update(
      document_id=document_id,
      file_path=file_path,
      file_name=file_name,
      kb_id=kb_id,
      tenant_id=tenant_id,
      created_by=created_by,
      chunking_method=chunking_method,
      access_token=access_token,
      **kwargs
  )
