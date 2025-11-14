from celery import Celery
from kombu import Queue
from app.config.config import settings

celery_app = Celery(
	"rag_app",
	broker=settings.celery_broker,
	backend=settings.celery_backend
)

celery_app.conf.update(
	task_default_queue="default",
	task_queues=(
		Queue("default"),
		Queue("file_process_queue"),
	),
	task_routes={
		"process_uploaded_file_celery": {"queue": "file_process_queue"}
	},
	task_serializer="json",
	result_serializer="json",
	accept_content=["json"],
	timezone="Asia/Ho_Chi_Minh",
	enable_utc=True,
)

celery_app.autodiscover_tasks(['app.task'])

__all__ = ('celery_app',)
