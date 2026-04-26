from enum import Enum
import sys

if sys.version_info >= (3, 11):
  from enum import StrEnum


class ErrorMessage(StrEnum):
  FAILED_MODEL_RESPONSE = "cannot connect to llm server"
  NO_FILES_UPLOADED = "No files uploaded."
  INVALID_PDF = "Invalid PDF file content."
  NO_READABLE_TEXT_PDF = "PDF contains no readable text."
  NO_CHUNKS_PRODUCED = "No chunks were produced from the text."
  CHUNKS_EMBEDDINGS_MISMATCH = "Mismatch between chunks and embeddings."
  DOCUMENT_PROCESSING_ERROR = "Document processing error"
  UNABLE_TO_EXTRACT_TEXT = "Unable to extract text from"
  UNSUPPORTED_FILE_TYPE = "Unsupported file type"
  UNABLE_TO_DECODE_TEXT = "Unable to decode text file with common encodings"
  WORD_SUPPORT_NOT_AVAILABLE = (
    "Word document support not available. Install python-docx."
  )
  UNABLE_TO_READ_DOCX = "Unable to read DOCX file"
  LEGACY_DOC_NOT_SUPPORTED = "Legacy .doc format not supported. Please convert to .docx"
  UNABLE_TO_READ_CSV = "Unable to read CSV file"
  INVALID_JSON_FORMAT = "Invalid JSON format"
  INTERNAL_ERROR = "Internal Server Error"
  UNABLE_TO_READ_JSON = "Unable to read JSON file"
  EMPTY_QUERY_OR_DOCS = "No query or documents provided for reranking."
  PROMPT_CONTEXT_MISSING = "Prompt or context is missing for LLM generation."


class HttpStatus(Enum):
  BAD_REQUEST = 400
  UNPROCESSABLE_ENTITY = 422
  INTERNAL_SERVER_ERROR = 500
