import re
import uuid
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
from llama_index.node_parser.slide import SlideNodeParser
from llama_index.core.schema import BaseNode

from app.config.config import settings as AppSettings
from app.core.logger import get_logger
from app.services.supabase.supabase_client import supabase

logger = get_logger("chunker")


# ----------------------------
# CHUNKING STRATEGY IDENTIFIER
# ----------------------------
def process_chunks(
    documents: List[Document], chunking_method: str, filename: str, **kwargs
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
      embed_model = kwargs.get("embed_model", Settings.embed_model)

      return semantic_chunk_documents(
          documents,
          filename,
          buffer_size=buffer_size,
          threshold_percentage=threshold_percentage,
          embed_model=embed_model,
      )

    case "topic":
      chunk_size = kwargs.get("chunk_size", 1024)
      window_size = kwargs.get("window_size", 5)
      return topic_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          window_size=window_size,
      )

    case "sentence":
      chunk_size = kwargs.get("chunk_size")
      chunk_overlap = kwargs.get("chunk_overlap")

      return sentence_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
      )

    case "token":
      chunk_size = kwargs.get("chunk_size")
      chunk_overlap = kwargs.get("chunk_overlap")
      return token_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
      )

    case "character":
      chunk_size = kwargs.get("chunk_size")
      chunk_overlap = kwargs.get("chunk_overlap")
      separator = kwargs.get("separator", "\n\n")
      return character_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
          separator=separator,
      )

    case "word":
      chunk_size = kwargs.get("chunk_size")
      chunk_overlap = kwargs.get("chunk_overlap")
      return word_chunk_documents(
          documents,
          filename,
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
      )

    case "sliding":
      # Extract sliding-window specific params
      window_size = kwargs.get("window_size", 3)
      use_llm = kwargs.get("use_llm", False)
      return sliding_window_chunk_documents(
          documents,
          filename,
          window_size=window_size,
          use_llm=use_llm,
      )

    case "hierarchical":
      chunk_sizes = kwargs.get("chunk_sizes", [2048, 512, 128])
      return hierarchical_chunk_documents(
          documents,
          filename,
          chunk_sizes=chunk_sizes,
      )

    case "recursive":
      chunk_size = kwargs.get("chunk_size")
      chunk_overlap = kwargs.get("chunk_overlap")
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


def topic_chunk_documents(
    documents: List[Document],
    filename: str,
    chunk_size: int = 1024,
    window_size: int = 5,
) -> List[BaseNode]:
  """
  Chunk documents using TopicNodeParser.
  Suitable for documents with distinct topic shifts.
  """
  splitter = TopicNodeParser(
      chunk_size=chunk_size,
      window_size=window_size,
      # FIXME: Ask about this part carefully
      llm=Settings.llm,
  )
  return apply_chunking_logic(documents, splitter, filename)


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
    use_llm: bool = False,
) -> List[BaseNode]:
  """
  Chunk documents using a sliding window approach.
  Suitable for documents where context retention is critical.
  """
  if use_llm:
    splitter = SlideNodeParser(
        # FIXME: Ask about this part carefully
        llm=Settings.llm,
        window_size=window_size,
    )
  else:
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
  Chunk documents using HierarchicalNodeParser.
  Suitable for AutoMergingRetriever to merge small context into larger parent context (Parent-Child hierarchy).
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


def _detect_or_create_document_id(file_name: str) -> str:
  """
  Detect or create a document ID based on the file name.
  """
  res = (
      supabase.table("metadata")
      .select("document_id")
      .eq("source_file", file_name)
      .limit(1)
      .execute()
  )
  if res.data:
    return res.data[0]["document_id"]
  return str(uuid.uuid4())


def apply_chunking_logic(
    documents: List[Document], splitter: NodeParser, filename: str
) -> List[BaseNode]:
  """
  Clean, split, and enrich nodes with metadata.
  """
  chunks: List[BaseNode] = []
  for doc in documents:
    cleaned = clean_text(doc.text)
    if not cleaned:
      continue
    new_doc = Document(text=cleaned, metadata=doc.metadata)
    nodes = splitter.get_nodes_from_documents([new_doc])
    for n in nodes:
      if len(n.text.strip()) >= 10:
        n.metadata.update({"chunk_size": len(n.text), "source_file": filename})
        chunks.append(n)

    logger.info(
        f"[Chunker] Generated {len(chunks)} chunks from file: {filename}")
    return chunks
