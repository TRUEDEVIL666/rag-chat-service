import pytest
from unittest.mock import MagicMock, patch
from llama_index.core import Document
from llama_index.core.schema import TextNode
from app.helper.chunker import (
    process_chunks,
    semantic_chunk_documents,
    topic_chunk_documents,
    recursive_chunk_documents,
    sentence_chunk_documents,
    token_chunk_documents,
    character_chunk_documents,
    word_chunk_documents,
    sliding_window_chunk_documents,
    hierarchical_chunk_documents,
    clean_text,
    adaptive_chunk_params,
    _detect_or_create_document_id,
    apply_chunking_logic,
)

# Mock Settings and AppSettings


@pytest.fixture(autouse=True)
def mock_settings():
  with patch("app.helper.chunker.Settings") as mock_settings:
    mock_settings.embed_model = MagicMock()
    mock_settings.llm = MagicMock()
    yield mock_settings


@pytest.fixture(autouse=True)
def mock_app_settings():
  with patch("app.helper.chunker.AppSettings") as mock_app_settings:
    mock_app_settings.BUFFER_SIZE = 1
    mock_app_settings.THRESHOLD_PERCENTAGE = 95
    yield mock_app_settings


@pytest.fixture
def mock_supabase():
  with patch("app.helper.chunker.supabase") as mock_supabase:
    yield mock_supabase


@pytest.fixture
def sample_documents():
  return [Document(text="This is a test document. It has multiple sentences.", metadata={"key": "value"})]


def test_clean_text():
  assert clean_text("  Hello   World  ") == "Hello World"
  assert clean_text("\n\nLine 1\nLine 2  ") == "Line 1 Line 2"


def test_adaptive_chunk_params():
  assert adaptive_chunk_params(500) == (200, 50)
  assert adaptive_chunk_params(2000) == (400, 100)
  assert adaptive_chunk_params(6000) == (600, 150)


def test_detect_or_create_document_id_existing(mock_supabase):
  mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
    {"document_id": "existing-id"}]
  assert _detect_or_create_document_id("test.txt") == "existing-id"


def test_detect_or_create_document_id_new(mock_supabase):
  mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
  with patch("uuid.uuid4", return_value="new-uuid"):
    assert _detect_or_create_document_id("test.txt") == "new-uuid"


def test_apply_chunking_logic(sample_documents):
  mock_splitter = MagicMock()
  mock_node = TextNode(text="This is a chunk.", metadata={})
  mock_splitter.get_nodes_from_documents.return_value = [mock_node]

  chunks = apply_chunking_logic(sample_documents, mock_splitter, "test.txt")

  assert len(chunks) == 1
  assert chunks[0].text == "This is a chunk."
  assert chunks[0].metadata["source_file"] == "test.txt"
  assert chunks[0].metadata["chunk_size"] == 16


def test_process_chunks_dispatcher(sample_documents):
  with patch("app.helper.chunker.sentence_chunk_documents") as mock_sentence:
    process_chunks(sample_documents, "sentence", "test.txt")
    mock_sentence.assert_called_once()

  with patch("app.helper.chunker.token_chunk_documents") as mock_token:
    process_chunks(sample_documents, "token", "test.txt", chunk_size=512)
    mock_token.assert_called_once()

  with patch("app.helper.chunker.logger") as mock_logger:
    process_chunks(sample_documents, "unknown", "test.txt")
    mock_logger.warning.assert_called_once()


@patch("app.helper.chunker.SemanticSplitterNodeParser")
def test_semantic_chunk_documents(mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = semantic_chunk_documents(sample_documents, "test.txt")
  assert len(chunks) == 1
  mock_parser_cls.assert_called_once()


@patch("app.helper.chunker.TopicNodeParser")
def test_topic_chunk_documents(mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = topic_chunk_documents(sample_documents, "test.txt")
  assert len(chunks) == 1
  mock_parser_cls.assert_called_once()


@patch("app.helper.chunker.LangchainNodeParser")
@patch("app.helper.chunker.RecursiveCharacterTextSplitter")
def test_recursive_chunk_documents(mock_splitter_cls, mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = recursive_chunk_documents(
    sample_documents, "test.txt", chunk_size=100, chunk_overlap=20)
  assert len(chunks) == 1
  mock_splitter_cls.assert_called_once_with(chunk_size=100, chunk_overlap=20)


@patch("app.helper.chunker.SentenceSplitter")
def test_sentence_chunk_documents(mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = sentence_chunk_documents(sample_documents, "test.txt")
  assert len(chunks) == 1
  mock_parser_cls.assert_called_once()


@patch("app.helper.chunker.TokenTextSplitter")
def test_token_chunk_documents(mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = token_chunk_documents(sample_documents, "test.txt")
  assert len(chunks) == 1
  mock_parser_cls.assert_called_once()


@patch("app.helper.chunker.LangchainNodeParser")
@patch("app.helper.chunker.CharacterTextSplitter")
def test_character_chunk_documents(mock_splitter_cls, mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = character_chunk_documents(sample_documents, "test.txt")
  assert len(chunks) == 1
  mock_splitter_cls.assert_called_once()


@patch("app.helper.chunker.LangchainNodeParser")
@patch("app.helper.chunker.RecursiveCharacterTextSplitter")
def test_word_chunk_documents(mock_splitter_cls, mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = word_chunk_documents(sample_documents, "test.txt")
  assert len(chunks) == 1
  mock_splitter_cls.assert_called_once()


@patch("app.helper.chunker.SentenceWindowNodeParser")
def test_sliding_window_chunk_documents_no_llm(mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = sliding_window_chunk_documents(
    sample_documents, "test.txt", use_llm=False)
  assert len(chunks) == 1
  mock_parser_cls.assert_called_once()


@patch("app.helper.chunker.SlideNodeParser")
def test_sliding_window_chunk_documents_with_llm(mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = sliding_window_chunk_documents(
    sample_documents, "test.txt", use_llm=True)
  assert len(chunks) == 1
  mock_parser_cls.assert_called_once()


@patch("app.helper.chunker.HierarchicalNodeParser")
def test_hierarchical_chunk_documents(mock_parser_cls, sample_documents):
  mock_parser = mock_parser_cls.from_defaults.return_value
  mock_parser.get_nodes_from_documents.return_value = [
    TextNode(text="Chunk 1 is long enough.")]

  chunks = hierarchical_chunk_documents(sample_documents, "test.txt")
  assert len(chunks) == 1
  mock_parser_cls.from_defaults.assert_called_once()
