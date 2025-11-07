# app/core/logger.py
import logging
from pathlib import Path


def get_logger(name: str = "rag_app") -> logging.Logger:
	logger = logging.getLogger(name)
	if not logger.handlers:
		logger.setLevel(logging.INFO)

		stream_handler = logging.StreamHandler()
		stream_handler.setFormatter(logging.Formatter(
			"[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
		))
		logger.addHandler(stream_handler)

		log_path = Path("logs/app.log")
		log_path.parent.mkdir(parents=True, exist_ok=True)

		file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
		file_handler.setFormatter(logging.Formatter(
			"[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
		))
		logger.addHandler(file_handler)

	return logger
