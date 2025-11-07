import re
import uuid
from typing import List, Tuple, Optional
from llama_index.core import Document, Settings
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from app.core.logger import get_logger
from app.services.supabase.supabase_client import supabase

logger = get_logger("chunker")


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


def apply_chunking_logic(
		documents: List[Document],
		splitter,
		filename: str
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
				n.metadata.update({
					"chunk_size": len(n.text),
					"source_file": filename
				})
				chunks.append(n)
	logger.info(f"[Chunker] Generated {len(chunks)} chunks from file: {filename}")
	return chunks


def semantic_chunk_documents(
		documents: List[Document],
		filename: str,
		chunk_size: Optional[int] = None,
) -> List[BaseNode]:
	"""
	Chunk documents semantically using embedding-based similarity.
	"""
	splitter = SemanticSplitterNodeParser(
		embed_model=Settings.embed_model,
		breakpoint_percentile_threshold=70
	)
	return apply_chunking_logic(documents, splitter, filename)


def chunk_documents(
		documents: List[Document],
		filename: str,
		chunk_size: Optional[int] = None,
		chunk_overlap: Optional[int] = None
) -> List[BaseNode]:
	"""
	Chunk documents by sentence with optional adaptive chunk size and overlap.
	"""
	total_len = sum(len(doc.text) for doc in documents)
	if chunk_size is None or chunk_overlap is None:
		chunk_size, chunk_overlap = adaptive_chunk_params(total_len)

	splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
	return apply_chunking_logic(documents, splitter, filename)


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
