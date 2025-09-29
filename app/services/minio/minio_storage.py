import io
from datetime import datetime
from uuid import uuid4
from pathlib import Path

from datetime import timedelta
from minio.error import S3Error

from app.services.minio.minio_client import minio_client
from app.core.logger import get_logger

logger = get_logger("minio")

class MinioStorage:
    def __init__(self, bucket_name: str = "document"):
        self.bucket_name = bucket_name
        self.ensure_bucket()

    def ensure_bucket(self):
        if not minio_client.bucket_exists(self.bucket_name):
            minio_client.make_bucket(self.bucket_name)
            logger.info(f"Created MinIO bucket: {self.bucket_name}")
        else:
            logger.debug(f"MinIO bucket already exists: {self.bucket_name}")

    def upload_file(self, file_bytes: bytes, filename: str) -> str:
        file_ext = Path(filename).suffix
        unique_key = f"{datetime.utcnow().strftime('%Y%m%d')}/{uuid4().hex}{file_ext}"

        minio_client.put_object(
            bucket_name=self.bucket_name,
            object_name=unique_key,
            data=io.BytesIO(file_bytes),
            length=len(file_bytes),
            content_type="application/octet-stream"
        )

        logger.info(f"Uploaded file '{filename}' to MinIO at: {self.bucket_name}/{unique_key}")
        return f"{self.bucket_name}/{unique_key}"
    
    def list_files(self) -> list[str]:
        """List all objects in the MinIO bucket."""
        return [
            obj.object_name
            for obj in minio_client.list_objects(self.bucket_name, recursive=True)
            if obj.object_name is not None
        ]

    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """
        Generate a presigned URL to download an object from MinIO.
        
        Args:
            object_name (str): Path name in bucket (ex: "20250616/abc.pdf")
            expires_seconds (int): URL's lifetime, count by second (default: 1h)

        Returns:
            str: URL using for downloading the file.
        """
        try:
            url = minio_client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name.split(self.bucket_name + "/")[-1],  # Remove bucket prefix if exists
                expires=timedelta(seconds=expires_seconds)
            )
            logger.info(f"Generated presigned URL for: {object_name}")
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise RuntimeError("Unable to create download file.")
