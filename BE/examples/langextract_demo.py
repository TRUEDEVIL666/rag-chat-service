"""
Async LangExtract + Ollama Pipeline
Phase 2 — Improvement #1
Parallel Batch Extraction
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import langextract as lx
import langextract.factory as lx_factory
from langextract.core.data import Extraction

import logging
import sys

# ==============================================================================
# LOGGING
# ==============================================================================

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ==============================================================================
# CONFIG
# ==============================================================================

MODEL_ID = "PetrosStav/gemma3-tools:4b"
OLLAMA_BASE_URL = "http://localhost:11434"

MAX_CONCURRENT_WORKERS = 3   # Adjust per hardware

# ==============================================================================
# PROMPT + EXAMPLES
# ==============================================================================

SCHEMA_PROMPT = """
You are performing span-based information extraction.

Rules:
- Copy verbatim spans.
- No paraphrasing.
- No JSON objects.

Extract:

Person
Organization
Date
Payment Amount
Delivery Date
Termination Notice Period
"""

EXAMPLES = [
    lx.data.ExampleData(
        text="Acme Corp will pay $10,000 by March 1, 2025.",
        extractions=[
            Extraction("Organization", "Acme Corp"),
            Extraction("Payment Amount", "$10,000"),
            Extraction("Date", "March 1, 2025"),
        ],
    )
]

# ==============================================================================
# DEDUPE
# ==============================================================================


def dedupe_extractions(extractions):

  seen = set()
  unique = []

  for ext in extractions:
    key = (
        ext.extraction_class,
        ext.extraction_text,
        ext.char_interval.start_pos,
        ext.char_interval.end_pos,
    )

    if key not in seen:
      seen.add(key)
      unique.append(ext)

  return unique

# ==============================================================================
# SYNC EXTRACTION (Worker Task)
# ==============================================================================


def run_extraction(document):
  result = lx.extract(
    text_or_documents=[document],
    prompt_description=SCHEMA_PROMPT,
    examples=EXAMPLES,
    config=lx_factory.ModelConfig(
        model_id=MODEL_ID,
        provider="ollama",
        provider_kwargs={
            "base_url": OLLAMA_BASE_URL,
            "temperature": 0,
          },
      ),
  )

  doc = result[0]
  doc.extractions = dedupe_extractions(doc.extractions)

  return doc

# ==============================================================================
# ASYNC ORCHESTRATOR
# ==============================================================================


async def async_extract_documents(documents):

  loop = asyncio.get_event_loop()

  semaphore = asyncio.Semaphore(MAX_CONCURRENT_WORKERS)

  results = []

  def task_wrapper(doc):
    return run_extraction(doc)

  async def run_task(doc):

    async with semaphore:
      return await loop.run_in_executor(
          executor,
          task_wrapper,
          doc,
      )

  with ThreadPoolExecutor(
      max_workers=MAX_CONCURRENT_WORKERS
  ) as executor:

    tasks = [
        asyncio.create_task(run_task(doc))
        for doc in documents
    ]

    for task in asyncio.as_completed(tasks):
      result = await task
      results.append(result)

  return results

# ==============================================================================
# DEMO DATASET
# ==============================================================================


def build_demo_documents():

  texts = [
      """
        Agreement between Acme Corp and Beta Solutions
        signed on February 13, 2026.
        Payment of $50,000 due by May 1, 2026.
        """,
      """
        Gamma LLC will deliver services by
        June 30, 2026 for $75,000.
        """,
      """
        Termination requires 30 days' written notice.
        """,
  ]

  docs = []

  for i, text in enumerate(texts):
    docs.append(
        lx.data.Document(
            text=text.strip(),
            document_id=f"doc_{i}",
        )
    )

  return docs

# ==============================================================================
# RESULT PRINTER
# ==============================================================================


def print_results(results):

  for doc in results:

    print(f"\nDocument: {doc.document_id}")

    # Group by extraction_class
    for ext in doc.extractions:
      print(ext.extraction_class, ext.extraction_text)

# ==============================================================================
# MAIN
# ==============================================================================


async def main():

  documents = build_demo_documents()

  print(
      f"\nRunning async extraction "
      f"({len(documents)} docs, "
      f"{MAX_CONCURRENT_WORKERS} workers)…"
  )

  results = await async_extract_documents(documents)

  print_results(results)


if __name__ == "__main__":
  asyncio.run(main())
