"""Document processing service for text extraction and chunking."""

import fitz  # PyMuPDF
from docx import Document
from typing import List, Dict, Any
import tiktoken

from app.core.config import settings


class DocumentProcessor:
    """Service for processing documents (PDF, DOCX) into chunks."""

    def __init__(self):
        """Initialize document processor."""
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def extract_text_from_pdf(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from PDF file.

        Args:
            file_content: PDF file as bytes

        Returns:
            List of dicts with page number and text
        """
        pages = []

        try:
            doc = fitz.open(stream=file_content, filetype="pdf")

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                if text.strip():
                    pages.append({"page": page_num + 1, "text": text})

            doc.close()

        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")

        return pages

    def extract_text_from_docx(self, file_content: bytes) -> str:
        """
        Extract text from DOCX file.

        Args:
            file_content: DOCX file as bytes

        Returns:
            Extracted text
        """
        try:
            from io import BytesIO

            doc = Document(BytesIO(file_content))
            paragraphs = [para.text for para in doc.paragraphs]
            return "\n".join(paragraphs)

        except Exception as e:
            print(f"Error extracting text from DOCX: {str(e)}")
            return ""

    def chunk_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with token-based overlap.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of chunks with content and metadata
        """
        # Tokenize the text
        tokens = self.encoding.encode(text)

        chunks = []
        start = 0

        while start < len(tokens):
            # Get chunk
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            # Create chunk dict
            chunk = {
                "content": chunk_text,
                "metadata": metadata or {},
                "token_count": len(chunk_tokens),
            }

            chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks

    def process_document(
        self, file_content: bytes, file_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a document (extract text and chunk).

        Args:
            file_content: File content as bytes
            file_type: File type ("pdf", "docx", "txt")
            metadata: Optional metadata for chunks

        Returns:
            List of text chunks with metadata
        """
        all_text = ""

        if file_type.lower() == "pdf":
            pages = self.extract_text_from_pdf(file_content)
            all_text = "\n\n".join([p["text"] for p in pages])

        elif file_type.lower() == "docx":
            all_text = self.extract_text_from_docx(file_content)

        elif file_type.lower() == "txt":
            all_text = file_content.decode("utf-8")

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Chunk the text
        chunks = self.chunk_text(all_text, metadata)

        return chunks
