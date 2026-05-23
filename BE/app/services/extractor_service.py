from typing import Any, List, Optional

import langextract as lx
import langextract.providers.ollama  # Registers the "ollama" string provider

from app.config.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

try:
  from langextract.core.data import Document, ExampleData, Extraction
except ImportError:
  # Try alternate location if direct import fails
  import langextract.data as lx_data

  Document = lx_data.Document
  ExampleData = lx_data.ExampleData
  Extraction = lx_data.Extraction

SCHEMA_PROMPT = """
You are performing span-based information extraction.

Rules:
- Copy verbatim spans.
- No paraphrasing.
- No JSON objects.
- Every source and target node in a Relationship MUST be extracted as an individual entity first.

Extract:

Concept
Person
Event
Date
Location
Formula
Quote
Relationship
"""

EXAMPLES = [
  ExampleData(
    text="Chiến dịch Điện Biên Phủ kết thúc thắng lợi vào năm 1954, do Đại tướng Võ Nguyên Giáp chỉ huy.",
    extractions=[
      Extraction("Event", "Chiến dịch Điện Biên Phủ"),
      Extraction("Date", "năm 1954"),
      Extraction("Person", "Đại tướng Võ Nguyên Giáp"),
      Extraction(
        "Relationship",
        "Đại tướng Võ Nguyên Giáp || chỉ huy || Chiến dịch Điện Biên Phủ",
      ),
      Extraction(
        "Relationship",
        "Chiến dịch Điện Biên Phủ || kết thúc thắng lợi vào || năm 1954",
      ),
    ],
  ),
  ExampleData(
    text="Quang hợp là quá trình thực vật sử dụng năng lượng ánh sáng chuyển hóa thành năng lượng hóa học.",
    extractions=[
      Extraction("Concept", "Quang hợp"),
      Extraction(
        "Concept",
        "quá trình thực vật sử dụng năng lượng ánh sáng chuyển hóa thành năng lượng hóa học",
      ),
      Extraction(
        "Relationship",
        "thực vật || sử dụng năng lượng ánh sáng || chuyển hóa thành năng lượng hóa học",
      ),
    ],
  ),
  ExampleData(
    text="Theo định luật II Newton, gia tốc của một vật cùng hướng với lực tác dụng lên vật, công thức F=ma.",
    extractions=[
      Extraction("Person", "Newton"),
      Extraction("Concept", "định luật II Newton"),
      Extraction("Formula", "F=ma"),
      Extraction("Relationship", "định luật || có công thức || F=ma"),
    ],
  ),
]


def dedupe_extractions(extractions):
  seen = set()
  unique = []
  for ext in extractions:
    start_pos = (
      getattr(ext.char_interval, "start_pos", 0) if hasattr(ext, "char_interval") else 0
    )
    end_pos = (
      getattr(ext.char_interval, "end_pos", 0) if hasattr(ext, "char_interval") else 0
    )

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
  _instance = None

  @classmethod
  def get_instance(cls) -> "ExtractorService":
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
    self.model_name = model_name or settings.EXTRACTION_LLM_MODEL
    self.base_url = base_url or settings.EXTRACTION_LLM_HOST

    logger.info(
      f"ExtractorService initialized with model={self.model_name} at {self.base_url}"
    )

  def extract(self, text: str) -> List[Any]:
    """
    Extracts structured data from text using LangExtract with prompt/examples.
    Returns a list of deduplicated Extraction objects.
    """
    try:
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
          },
        ),
      )

      if results and len(results) > 0:
        doc = results[0]
        if hasattr(doc, "extractions"):
          return dedupe_extractions(doc.extractions)

      return []

    except Exception as e:
      logger.error(f"Extraction failed: {e}")
      return []
