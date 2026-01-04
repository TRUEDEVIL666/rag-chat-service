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

  def upload_file(self, file_bytes: bytes, filename: str, custom_path: str = None) -> str:
    file_ext = Path(filename).suffix
    if custom_path:
      unique_key = custom_path
    else:
      unique_key = f"{datetime.utcnow().strftime('%Y%m%d')}/{uuid4().hex}{file_ext}"

    minio_client.put_object(
        bucket_name=self.bucket_name,
        object_name=unique_key,
        data=io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type="application/octet-stream"
    )

    logger.info(
      f"Uploaded file '{filename}' to MinIO at: {self.bucket_name}/{unique_key}")
    return f"{self.bucket_name}/{unique_key}"

  def upload_stream(self, file_stream, length: int, filename: str, content_type: str = "application/octet-stream", custom_path: str = None) -> str:
    """Upload a file stream to MinIO."""
    file_ext = Path(filename).suffix
    if custom_path:
      unique_key = custom_path
    else:
      unique_key = f"{datetime.utcnow().strftime('%Y%m%d')}/{uuid4().hex}{file_ext}"

    minio_client.put_object(
        bucket_name=self.bucket_name,
        object_name=unique_key,
        data=file_stream,
        length=length,
        content_type=content_type
    )

    logger.info(
        f"Stream uploaded file '{filename}' to MinIO at: {self.bucket_name}/{unique_key}")
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
          # Remove bucket prefix if exists
          object_name=object_name.split(self.bucket_name + "/")[-1],
          expires=timedelta(seconds=expires_seconds)
      )
      logger.info(f"Generated presigned URL for: {object_name}")
      return url
    except S3Error as e:
      logger.error(f"Error generating presigned URL: {e}")
      raise RuntimeError("Unable to create download file.")

  def delete_file(self, object_name: str) -> bool:
    """
    Delete a file from MinIO.

    Args:
        object_name (str): Full object name (e.g., "bucket/path/to/file")
    """
    try:
      # Remove bucket prefix if it exists in the object_name
      clean_object_name = object_name
      if object_name.startswith(f"{self.bucket_name}/"):
        clean_object_name = object_name.split(f"{self.bucket_name}/", 1)[1]

      minio_client.remove_object(self.bucket_name, clean_object_name)
      logger.info(f"Deleted file from MinIO: {clean_object_name}")
      return True
    except S3Error as e:
      logger.error(f"Error deleting file from MinIO: {e}")
      return False

  def download_file(self, object_name: str, file_path: str):
    """Download an object to a local file path."""
    clean_object_name = object_name
    if object_name.startswith(f"{self.bucket_name}/"):
      clean_object_name = object_name.split(f"{self.bucket_name}/", 1)[1]

    minio_client.fget_object(
        bucket_name=self.bucket_name,
        object_name=clean_object_name,
        file_path=file_path
    )

  def get_file_stream(self, object_name: str):
    """
    Get a file as a stream (response object) from MinIO.
    Caller is responsible for closing the stream.
    """
    clean_object_name = object_name
    if object_name.startswith(f"{self.bucket_name}/"):
      clean_object_name = object_name.split(f"{self.bucket_name}/", 1)[1]

    # get_object returns a urllib3.response.HTTPResponse object which is a file-like object
    return minio_client.get_object(
        bucket_name=self.bucket_name,
        object_name=clean_object_name
    )
