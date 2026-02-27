# app/core/logger.py
import logging
from pathlib import Path


def setup_logging():
  """
  Configure the root logger to output to both console and file.
  This should be called once at application startup.
  """
  # Create logs directory if it doesn't exist
  log_path = Path("logs/app.log")
  log_path.parent.mkdir(parents=True, exist_ok=True)

  # Configure root logger
  logging.basicConfig(
      level=logging.INFO,
      format="[%(asctime)s][%(levelname)s][%(name)s]%(message)s",
      handlers=[
          logging.StreamHandler(),
          logging.FileHandler(log_path, mode="a", encoding="utf-8")
      ]
  )

  # Quiet down some noisy libraries if needed
  logging.getLogger("httpx").setLevel(logging.WARNING)
  logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str = "rag_app") -> logging.Logger:
  return logging.getLogger(name)
