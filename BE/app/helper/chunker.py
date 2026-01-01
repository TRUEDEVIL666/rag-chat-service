import re
import uuid
import hashlib
from typing import Any, List, Optional, Tuple

from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from llama_index.core import Document, Settings
from llama_index.core.node_parser import (
    HierarchicalNodeParser,
    LangchainNodeParser,
    NodeParser,
    SemanticSplitterNodeParser,
    SentenceSplitter,
    SentenceWindowNodeParser,
    TokenTextSplitter,
)
from llama_index.node_parser.topic import TopicNodeParser
from llama_index.core.schema import BaseNode

from app.config.config import settings as AppSettings
from app.core.logger import get_logger


logger = get_logger("chunker")


# ----------------------------
# CHUNKING STRATEGY IDENTIFIER
# ----------------------------
def process_chunks(
    documents: List[Document],
    chunking_method: str,
    filename: str,
    **kwargs
) -> List[BaseNode]:
  """
  Dispatcher function to call the appropriate chunking strategy.

  Args:
      documents: List of documents to chunk
      chunking_method: Strategy name ('semantic', 'fixed', etc.)
      filename: Name of the source file
      **kwargs: Additional arguments passed to the specific chunking function
  """
  match chunking_method:
    case "semantic":
      buffer_size = kwargs.get("buffer_size", AppSettings.BUFFER_SIZE)
      threshold_percentage = kwargs.get(
          "threshold_percentage", AppSettings.THRESHOLD_PERCENTAGE
      )
      # Type coercion
      buffer_size = int(buffer_size)
      threshold_percentage = int(threshold_percentage)
      # Use lazy evaluation for embed_model to avoid triggering LlamaIndex's default (OpenAI)
      # if a custom model is already provided in kwargs.
      embed_model = kwargs.get("embed_model") or Settings.embed_model

      return semantic_chunk_documents(
          documents,
          filename,
          buffer_size=buffer_size,
          threshold_percentage=threshold_percentage,
          embed_model=embed_model,
      )

    # case "topic":
    #   chunk_size = kwargs.get("chunk_size", 1024)
    #   window_size = kwargs.get("window_size", 5)
    #   return topic_chunk_documents(
    #       documents,
    #       filename,
    #       chunk_size=chunk_size,
    #       window_size=window_size,
    #   )

    case "sentence":
      chunk_size = kwargs.get("chunk_size")
      chunk_overlap = kwargs.get("chunk_overlap")

      # Type coercion to prevent LlamaIndex TypeError
      if chunk_size is not None:
        chunk_size = int(chunk_size)
      if chunk_overlap is not None:
        chunk_overlap = int(chunk_overlap)

      return sentence_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
      )

    case "token":
      chunk_size = kwargs.get("chunk_size", 512)
      chunk_overlap = kwargs.get("chunk_overlap", 50)

      # Type coercion
      chunk_size = int(chunk_size)
      chunk_overlap = int(chunk_overlap)

      return token_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
      )

    case "character":
      chunk_size = kwargs.get("chunk_size", 1000)
      chunk_overlap = kwargs.get("chunk_overlap", 200)
      separator = kwargs.get("separator", "\n\n")

      # Type coercion
      chunk_size = int(chunk_size)
      chunk_overlap = int(chunk_overlap)

      return character_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
          separator=separator,
      )

    case "word":
      chunk_size = kwargs.get("chunk_size", 1000)
      chunk_overlap = kwargs.get("chunk_overlap", 200)

      # Type coercion
      chunk_size = int(chunk_size)
      chunk_overlap = int(chunk_overlap)

      return word_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
      )

    case "sliding":
      # Extract sliding-window specific params
      window_size = kwargs.get("window_size", 3)
      window_size = int(window_size)

      return sliding_window_chunk_documents(
          documents,
          filename,
          window_size=window_size,
      )

    case "hierarchical":
      chunk_sizes = kwargs.get("chunk_sizes", [2048, 512, 128])
      # Ensure all sizes are integers
      if isinstance(chunk_sizes, list):
        chunk_sizes = [int(s) for s in chunk_sizes]
      elif isinstance(chunk_sizes, str):
        # Handle case where it might be a comma-separated string
        chunk_sizes = [int(s.strip()) for s in chunk_sizes.split(",")]

      return hierarchical_chunk_documents(
          documents,
          filename,
          chunk_sizes=chunk_sizes,
      )

    case "recursive":
      chunk_size = kwargs.get("chunk_size")
      chunk_overlap = kwargs.get("chunk_overlap")

      # Type coercion
      if chunk_size is not None:
        chunk_size = int(chunk_size)
      if chunk_overlap is not None:
        chunk_overlap = int(chunk_overlap)

      return recursive_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
      )

    case _:
      logger.warning(
          f"Unknown chunking method '{chunking_method}', defaulting to sentence chunking."
      )
      return sentence_chunk_documents(documents, filename)


# -------------------
# CHUNKING STRATEGIES
# -------------------
def semantic_chunk_documents(
    documents: List[Document],
    filename: str,
    buffer_size: int = AppSettings.BUFFER_SIZE,
    threshold_percentage: int = AppSettings.THRESHOLD_PERCENTAGE,
    embed_model: Optional[Any] = None,
) -> List[BaseNode]:
  """
  Chunk documents semantically using embedding-based similarity.
  Suitable for documents where maintaining context is critical
    (e.g., essays, research papers).
  """
  splitter = SemanticSplitterNodeParser(
      embed_model=embed_model or Settings.embed_model,
      buffer_size=buffer_size,
      breakpoint_percentile_threshold=threshold_percentage,
  )
  return apply_chunking_logic(documents, splitter, filename)


# def topic_chunk_documents(
#     documents: List[Document],
#     filename: str,
#     chunk_size: int = 1024,
#     window_size: int = 5,
# ) -> List[BaseNode]:
#   """
#   Chunk documents using TopicNodeParser.
#   Suitable for documents with distinct topic shifts.
#   """
#   splitter = TopicNodeParser(
#       chunk_size=chunk_size,
#       window_size=window_size,
#   )
#   return apply_chunking_logic(documents, splitter, filename)


def recursive_chunk_documents(
    documents: List[Document],
    filename: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[BaseNode]:
  """
  Chunk documents recursively using LangChain's RecursiveCharacterTextSplitter.
  Suitable for documents with complex structure
    (e.g., code, markdown) where hierarchy matters.
  """
  total_len = sum(len(doc.text) for doc in documents)
  if chunk_size is None or chunk_overlap is None:
    chunk_size, chunk_overlap = adaptive_chunk_params(total_len)

  splitter = LangchainNodeParser(
      RecursiveCharacterTextSplitter(
          chunk_size=chunk_size, chunk_overlap=chunk_overlap
      )
  )
  return apply_chunking_logic(documents, splitter, filename)


def sentence_chunk_documents(
    documents: List[Document],
    filename: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[BaseNode]:
  """
  Chunk documents by sentence with optional adaptive chunk size and overlap.
  Suitable for general-purpose documents where uniform chunk size is preferred
    (e.g., news articles, simple reports).
  """
  total_len = sum(len(doc.text) for doc in documents)
  if chunk_size is None or chunk_overlap is None:
    chunk_size, chunk_overlap = adaptive_chunk_params(total_len)

  splitter = SentenceSplitter(
      chunk_size=chunk_size, chunk_overlap=chunk_overlap)
  return apply_chunking_logic(documents, splitter, filename)


def token_chunk_documents(
    documents: List[Document],
    filename: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> List[BaseNode]:
  """
  Chunk documents by fixed token count.
  Suitable for LLM context window optimization where strict token limits are required.
  """
  splitter = TokenTextSplitter(
      chunk_size=chunk_size, chunk_overlap=chunk_overlap)
  return apply_chunking_logic(documents, splitter, filename)


def character_chunk_documents(
    documents: List[Document],
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separator: str = "\n\n",
) -> List[BaseNode]:
  """
  *** NOT RECOMMENDED ***
  Chunk documents by fixed character count.
  Suitable for raw text processing where semantic structure is less important or unknown.
  """
  splitter = LangchainNodeParser(
      CharacterTextSplitter(
          separator=separator,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap
      )
  )
  return apply_chunking_logic(documents, splitter, filename)


def word_chunk_documents(
    documents: List[Document],
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[BaseNode]:
  """
  Chunk documents by word count (approximated by splitting on whitespace).
  Suitable for tasks where word count limits are strict or for simple text analysis.
  """
  splitter = LangchainNodeParser(
      RecursiveCharacterTextSplitter(
          separators=[" "],
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
          keep_separator=True
      )
  )
  return apply_chunking_logic(documents, splitter, filename)


def sliding_window_chunk_documents(
    documents: List[Document],
    filename: str,
    window_size: int = 3,
) -> List[BaseNode]:
  """
  Chunk documents using a sliding window approach.
  Suitable for documents where context retention is critical.
  """
  splitter = SentenceWindowNodeParser(
      window_size=window_size,
      window_metadata_key="window",
      original_text_metadata_key="original_text",
  )
  return apply_chunking_logic(documents, splitter, filename)


def hierarchical_chunk_documents(
    documents: List[Document],
    filename: str,
    chunk_sizes: List[int] = [2048, 512, 128],
) -> List[BaseNode]:
  """
  Chunk documents using HierarchicalNodeParser and AutoMergingRetriever to merge small context into larger parent context (Parent-Child hierarchy).
  Suitable for documents where context is too big, hence the requirement to split into smaller chunks connected to it.
  """
  splitter = HierarchicalNodeParser.from_defaults(
      chunk_sizes=chunk_sizes,
  )
  return apply_chunking_logic(documents, splitter, filename)

# ----------------
# HELPER FUNCTIONS
# ----------------


def clean_text(text: str) -> str:
  """
  Clean extra whitespace and trim the text.
  """
  return re.sub(r"\s+", " ", text).strip()


def adaptive_chunk_params(length: int) -> Tuple[int, int]:
  """
  Determine chunk size and overlap based on total text length.
  """
  if length < 1000:
    size = 200
  elif length < 5000:
    size = 400
  else:
    size = 600
  overlap = int(size * 0.25)
  return size, overlap


def apply_chunking_logic(
    documents: List[Document],
    splitter: NodeParser,
    filename: str,
  ) -> List[BaseNode]:
  """
  Clean, split, and enrich nodes with metadata.
  Processes all documents in a batch to allow the splitter to optimize (e.g. batch embeddings).
  """
  chunks: List[BaseNode] = []
  clean_docs = []

  # 1. Pre-process and clean all documents
  # Optimization: Merge small documents (like paragraphs) into one large document
  # to allow the Semantic Splitter to see the full context and batch embeddings effectively.
  full_text_list = []
  base_metadata = documents[0].metadata.copy() if documents else {}

  for doc in documents:
    cleaned = clean_text(doc.text)
    if not cleaned:
      continue
    full_text_list.append(cleaned)

  if not full_text_list:
    return []

  # Join with double newlines to preserve paragraph separation
  merged_text = "\n\n".join(full_text_list)
  # Create a single merged document
  clean_docs = [Document(text=merged_text, metadata=base_metadata)]

  # 2. Process ALL documents at once (Enables batching in LlamaIndex splitters)
  # Now the splitter receives one large doc, breaks it into sentences, and embeds them in batches.
  nodes = splitter.get_nodes_from_documents(clean_docs)

  # 3. Post-process nodes
  for n in nodes:
    if len(n.text.strip()) >= 10:
      chunk_hash = hashlib.sha256(n.text.encode("utf-8")).hexdigest()

      # Prepare metadata update
      meta_update = {
          "chunk_size": len(n.text),
          "source_file": filename,
          "chunk_hash": chunk_hash
      }

      n.metadata.update(meta_update)
      chunks.append(n)

  logger.info(
      f"[Chunker] Generated {len(chunks)} chunks from file: {filename} (Batch size: {len(documents)})")
  return chunks
