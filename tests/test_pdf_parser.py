"""
Tests for PDF parser (Step 7).

Tests parsing, text extraction, chunking, and error handling.
All tests use fixtures — no real PDF files needed for most tests.
"""

from __future__ import annotations

import pytest

from neurosync.content.parsers.pdf_parser import PDFDocument, PDFPage, PDFParser
from neurosync.content.parsers.text_cleaner import CleanedText, TextCleaner


# ── PDFPage tests ───────────────────────────────────────────────────


class TestPDFPage:
    """Test PDFPage data model."""

    def test_page_counts(self):
        """Word and char counts are computed automatically."""
        page = PDFPage(page_number=1, text="Hello world this is a test")
        assert page.char_count == 26
        assert page.word_count == 6

    def test_empty_page(self):
        """Empty pages have zero counts."""
        page = PDFPage(page_number=1, text="")
        assert page.char_count == 0
        assert page.word_count == 0


# ── PDFDocument tests ───────────────────────────────────────────────


class TestPDFDocument:
    """Test PDFDocument data model."""

    def test_full_text(self):
        """full_text() concatenates all pages."""
        doc = PDFDocument(
            filename="test.pdf",
            total_pages=2,
            pages=[
                PDFPage(page_number=1, text="Page one content"),
                PDFPage(page_number=2, text="Page two content"),
            ],
        )
        assert "Page one content" in doc.full_text()
        assert "Page two content" in doc.full_text()

    def test_text_chunks(self):
        """text_chunks() splits long text into overlapping chunks."""
        long_text = "word " * 1000  # 5000 chars
        doc = PDFDocument(
            filename="test.pdf",
            total_pages=1,
            pages=[PDFPage(page_number=1, text=long_text)],
        )
        chunks = doc.text_chunks(chunk_size=200, overlap=50)
        assert len(chunks) > 1
        # Each chunk should not exceed chunk_size
        for ch in chunks:
            assert len(ch) <= 200

    def test_empty_document(self):
        """Empty document returns empty text and no chunks."""
        doc = PDFDocument(filename="empty.pdf", total_pages=0, pages=[])
        assert doc.full_text() == ""
        assert doc.text_chunks() == []


# ── TextCleaner tests ──────────────────────────────────────────────


class TestTextCleaner:
    """Test text cleaning and normalization."""

    def test_basic_cleaning(self):
        """Cleans whitespace and returns sections."""
        cleaner = TextCleaner()
        result = cleaner.clean("   Hello   world  \n\n\n\n  Second paragraph  ")
        assert isinstance(result, CleanedText)
        assert "Hello world" in result.text
        assert len(result.sections) >= 1

    def test_removes_page_numbers(self):
        """Strips standalone page numbers."""
        cleaner = TextCleaner()
        result = cleaner.clean("Some content\nPage 1 of 10\nMore content")
        assert "Page 1 of 10" not in result.text
        assert result.removed_artifacts > 0

    def test_extracts_title(self):
        """Extracts title from first lines."""
        cleaner = TextCleaner()
        title = cleaner.extract_title("Introduction to Machine Learning\nThis chapter covers...")
        assert title == "Introduction to Machine Learning"


# ── PDFParser error handling ────────────────────────────────────────


class TestPDFParserErrors:
    """Test parser error conditions."""

    def test_file_not_found(self):
        """Raises FileNotFoundError for missing files."""
        parser = PDFParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.pdf")

    def test_not_a_pdf(self, tmp_path):
        """Raises ValueError for non-PDF files."""
        txt = tmp_path / "test.txt"
        txt.write_text("not a pdf")
        parser = PDFParser()
        with pytest.raises(ValueError, match="Not a PDF"):
            parser.parse(txt)
