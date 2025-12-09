import re
import uuid
from typing import List, Tuple, Optional, Any

from llama_index.core import Document, Settings
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser import (
	SentenceSplitter,
	SemanticSplitterNodeParser,
	NodeParser,
	LangchainNodeParser,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logger import get_logger
from app.services.supabase.supabase_client import supabase
from app.config.config import settings as AppSettings

logger = get_logger("chunker")


# ------------------CHUNKING STRATEGY IDENTIFIER------------------
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
			# Extract semantic-specific params from kwargs with defaults
			buffer_size = kwargs.get("buffer_size", AppSettings.buffer_size)
			threshold_percentage = kwargs.get(
				"threshold_percentage", AppSettings.threshold_percentage
			)
			embed_model = kwargs.get("embed_model", Settings.embed_model)

			return semantic_chunk_documents(
				documents,
				filename,
				buffer_size=buffer_size,
				threshold_percentage=threshold_percentage,
				embed_model=embed_model,
			)

		case "fixed":
			# Extract fixed-size specific params
			chunk_size = kwargs.get("chunk_size")
			chunk_overlap = kwargs.get("chunk_overlap")

			return fixed_chunk_documents(
				documents,
				filename,
				chunk_size=chunk_size,
				chunk_overlap=chunk_overlap,
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
				f"Unknown chunking method '{chunking_method}', defaulting to fixed chunking."
			)
			return fixed_chunk_documents(documents, filename)


# ------------------CHUNKING STRATEGIES------------------
def semantic_chunk_documents(
		documents: List[Document],
		filename: str,
		buffer_size: int = AppSettings.buffer_size,
		threshold_percentage: int = AppSettings.threshold_percentage,
		embed_model: Optional[Any] = None,
) -> List[BaseNode]:
	"""
		Chunk documents semantically using embedding-based similarity.
	"""
	splitter = SemanticSplitterNodeParser(
		embed_model=embed_model or Settings.embed_model,
		buffer_size=buffer_size,
		breakpoint_percentile_threshold=threshold_percentage,
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


def fixed_chunk_documents(
		documents: List[Document],
		filename: str,
		chunk_size: Optional[int] = None,
		chunk_overlap: Optional[int] = None,
) -> List[BaseNode]:
	"""
		Chunk documents by sentence with optional adaptive chunk size and overlap.
	"""
	total_len = sum(len(doc.text) for doc in documents)
	if chunk_size is None or chunk_overlap is None:
		chunk_size, chunk_overlap = adaptive_chunk_params(total_len)

	splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
	return apply_chunking_logic(documents, splitter, filename)


# ------------------HELPER FUNCTIONS------------------
def clean_text(text: str) -> str:
	"""Clean extra whitespace and trim the text."""
	return re.sub(r"\s+", " ", text).strip()


def adaptive_chunk_params(length: int) -> Tuple[int, int]:
	"""Determine chunk size and overlap based on total text length."""
	if length < 1000:
		size = 200
	elif length < 5000:
		size = 400
	else:
		size = 600
	overlap = int(size * 0.25)
	return size, overlap


def _detect_or_create_document_id(file_name: str) -> str:
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
	"""Clean, split, and enrich nodes with metadata."""
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

		logger.info(f"[Chunker] Generated {len(chunks)} chunks from file: {filename}")
		return chunks
