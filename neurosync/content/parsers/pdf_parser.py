"""
NeuroSync AI — PDF Parser.

Extracts text, tables, and metadata from uploaded PDF files
using pdfplumber for reliable text extraction.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from loguru import logger


@dataclass
class PDFPage:
    """Parsed content from a single PDF page."""
    page_number: int
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)
    char_count: int = 0
    word_count: int = 0

    def __post_init__(self) -> None:
        self.char_count = len(self.text)
        self.word_count = len(self.text.split()) if self.text.strip() else 0


@dataclass
class PDFDocument:
    """Complete parsed PDF document."""
    filename: str
    total_pages: int
    pages: list[PDFPage] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    total_word_count: int = 0

    def full_text(self) -> str:
        """Return all page text concatenated."""
        return "\n\n".join(p.text for p in self.pages if p.text.strip())

    def text_chunks(self, chunk_size: int = 4000, overlap: int = 200) -> list[str]:
        """Split full text into overlapping chunks for processing."""
        text = self.full_text()
        if not text:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks


class PDFParser:
    """Parse PDF files into structured PDFDocument objects."""

    def __init__(self, max_pages: int = 200, min_text_length: int = 50) -> None:
        self.max_pages = max_pages
        self.min_text_length = min_text_length

    def parse(self, pdf_path: str | Path) -> PDFDocument:
        """
        Parse a PDF file and return a PDFDocument.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            PDFDocument with extracted pages, text, and tables.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
            ValueError: If the file is not a valid PDF or is empty.
        """
        import pdfplumber

        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {path}")

        logger.info("Parsing PDF: {} (max {} pages)", path.name, self.max_pages)

        pages: list[PDFPage] = []
        metadata: dict[str, Any] = {}

        with pdfplumber.open(path) as pdf:
            metadata = dict(pdf.metadata) if pdf.metadata else {}
            total_pages = len(pdf.pages)

            for i, page in enumerate(pdf.pages[: self.max_pages]):
                text = page.extract_text() or ""
                tables: list[list[list[str]]] = []

                try:
                    raw_tables = page.extract_tables() or []
                    for table in raw_tables:
                        cleaned = [
                            [str(cell) if cell is not None else "" for cell in row]
                            for row in table
                            if row
                        ]
                        if cleaned:
                            tables.append(cleaned)
                except Exception:
                    logger.warning("Table extraction failed on page {}", i + 1)

                pages.append(PDFPage(
                    page_number=i + 1,
                    text=text.strip(),
                    tables=tables,
                ))

        # Compute content hash
        full_text = "\n".join(p.text for p in pages)
        content_hash = hashlib.sha256(full_text.encode()).hexdigest()[:16]
        total_words = sum(p.word_count for p in pages)

        doc = PDFDocument(
            filename=path.name,
            total_pages=total_pages,
            pages=pages,
            metadata=metadata,
            content_hash=content_hash,
            total_word_count=total_words,
        )

        logger.info(
            "Parsed {} pages, {} words, hash={}",
            len(pages), total_words, content_hash,
        )
        return doc

    def parse_bytes(self, data: bytes, filename: str = "upload.pdf") -> PDFDocument:
        """Parse PDF from in-memory bytes (e.g., file upload)."""
        import io
        import pdfplumber

        logger.info("Parsing PDF from bytes: {} ({} bytes)", filename, len(data))

        pages: list[PDFPage] = []
        metadata: dict[str, Any] = {}

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            metadata = dict(pdf.metadata) if pdf.metadata else {}
            total_pages = len(pdf.pages)

            for i, page in enumerate(pdf.pages[: self.max_pages]):
                text = page.extract_text() or ""
                pages.append(PDFPage(
                    page_number=i + 1,
                    text=text.strip(),
                ))

        full_text = "\n".join(p.text for p in pages)
        content_hash = hashlib.sha256(full_text.encode()).hexdigest()[:16]
        total_words = sum(p.word_count for p in pages)

        return PDFDocument(
            filename=filename,
            total_pages=total_pages,
            pages=pages,
            metadata=metadata,
            content_hash=content_hash,
            total_word_count=total_words,
        )
