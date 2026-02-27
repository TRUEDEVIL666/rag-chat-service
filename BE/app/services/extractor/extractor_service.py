from typing import List, Optional, Any
import langextract as lx
import langextract.providers.ollama  # Registers the "ollama" string provider
from app.core.logger import get_logger
from app.config.config import settings
from .schemas import SCHEMA_PROMPT, EXAMPLES

logger = get_logger(__name__)


def dedupe_extractions(extractions):
  seen = set()
  unique = []
  for ext in extractions:
    start_pos = getattr(ext.char_interval, 'start_pos',
                        0) if hasattr(ext, 'char_interval') else 0
    end_pos = getattr(ext.char_interval, 'end_pos', 0) if hasattr(
      ext, 'char_interval') else 0

    key = (
        ext.extraction_class,
        ext.extraction_text,
        start_pos,
        end_pos,
    )
    if key not in seen:
      seen.add(key)
      unique.append(ext)
  return unique


class ExtractorService:
  def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
    self.model_name = model_name or settings.EXTRACTION_LLM_MODEL
    self.base_url = base_url or settings.EXTRACTION_LLM_HOST

    logger.info(
      f"ExtractorService initialized with model={self.model_name} at {self.base_url}")

  def extract(self, text: str) -> List[Any]:
    """
    Extracts structured data from text using LangExtract with prompt/examples.
    Returns a list of deduplicated Extraction objects.
    """
    try:
      try:
        from langextract.core.data import Document
      except ImportError:
        import langextract.data as lx_data
        Document = lx_data.Document

      import langextract.factory as lx_factory

      lx_doc = Document(text=text, document_id="temp_extraction_doc")

      results = lx.extract(
          text_or_documents=[lx_doc],
          prompt_description=SCHEMA_PROMPT,
          examples=EXAMPLES,
          config=lx_factory.ModelConfig(
              model_id=self.model_name,
              provider="ollama",
              provider_kwargs={
                  "base_url": self.base_url,
                  "temperature": 0,
              }
          )
      )

      if results and len(results) > 0:
        doc = results[0]
        if hasattr(doc, 'extractions'):
          return dedupe_extractions(doc.extractions)

      return []

    except Exception as e:
      logger.error(f"Extraction failed: {e}")
      return []
