"""Tests for document processor."""

import pytest
from app.services.document_processor import DocumentProcessor


def test_chunk_text():
    """Test text chunking."""
    processor = DocumentProcessor()
    processor.chunk_size = 100  # Small size for testing
    processor.chunk_overlap = 20

    text = "This is a test document. " * 50  # Long text
    chunks = processor.chunk_text(text)

    assert len(chunks) > 1
    assert all(chunk["token_count"] <= processor.chunk_size for chunk in chunks)


def test_chunk_text_with_metadata():
    """Test text chunking with metadata."""
    processor = DocumentProcessor()
    processor.chunk_size = 100

    text = "This is a test."
    metadata = {"page": 1, "source": "test.pdf"}

    chunks = processor.chunk_text(text, metadata)

    assert len(chunks) >= 1
    assert chunks[0]["metadata"] == metadata


def test_extract_text_from_pdf():
    """Test PDF text extraction (mock)."""
    processor = DocumentProcessor()

    # This would need a real PDF file in practice
    # For now, we test that the method exists and returns a list
    result = processor.extract_text_from_pdf(b"not a real pdf")

    assert isinstance(result, list)


def test_process_document_txt():
    """Test processing a text file."""
    processor = DocumentProcessor()
    processor.chunk_size = 50

    text_content = b"This is a plain text document. It should be chunked properly."
    chunks = processor.process_document(text_content, "txt")

    assert len(chunks) >= 1
    assert all("content" in chunk for chunk in chunks)
    assert all("metadata" in chunk for chunk in chunks)


def test_process_document_unsupported_type():
    """Test processing an unsupported file type."""
    processor = DocumentProcessor()

    with pytest.raises(ValueError, match="Unsupported file type"):
        processor.process_document(b"content", "xyz")
