from app.core.factory import get_file_processor_service
from app.config.celery import celery_app

import base64


@celery_app.task(name="process_uploaded_file_celery")
def process_uploaded_file_celery(file_bytes, file_name, kb_id):
    file_processor = get_file_processor_service()

    decoded_bytes = base64.b64decode(file_bytes)

    return file_processor.process_file(
        file_bytes=decoded_bytes,
        file_name=file_name,
        kb_id=kb_id
    )
