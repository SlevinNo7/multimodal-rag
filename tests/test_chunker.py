import io
import pytest
import fitz
from lib.chunker import chunk_text, chunk_pdf, extract_pdf_text


def make_pdf(num_pages: int) -> bytes:
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1} content")
    buf = doc.tobytes()
    doc.close()
    return buf


# ── chunk_text ────────────────────────────────────────────────────────────────

class TestChunkText:
    def test_short_text_returned_as_single_chunk(self):
        text = "Hello world"
        assert chunk_text(text) == [text]

    def test_exact_boundary_is_single_chunk(self):
        text = "a" * (100 * 4)
        chunks = chunk_text(text, max_tokens=100, overlap=0)
        assert len(chunks) == 1

    def test_long_text_splits_into_multiple_chunks(self):
        text = "a" * (100 * 4 + 1)
        chunks = chunk_text(text, max_tokens=100, overlap=0)
        assert len(chunks) > 1

    def test_chunks_cover_full_content(self):
        text = "ab" * 500
        chunks = chunk_text(text, max_tokens=100, overlap=10)
        reconstructed = chunks[0]
        for chunk in chunks[1:]:
            reconstructed += chunk[-(len(chunk) - 10 * 4):]
        assert len(reconstructed) >= len(text)

    def test_each_chunk_within_max_size(self):
        text = "x" * 2000
        max_tokens = 50
        chunks = chunk_text(text, max_tokens=max_tokens, overlap=0)
        for chunk in chunks:
            assert len(chunk) <= max_tokens * 4

    def test_overlap_makes_chunks_longer_than_stride(self):
        text = "a" * (100 * 4 * 3)
        chunks = chunk_text(text, max_tokens=100, overlap=10)
        assert len(chunks) >= 3

    def test_empty_string_returns_one_chunk(self):
        assert chunk_text("") == [""]

    def test_custom_max_tokens(self):
        text = "b" * 200
        chunks = chunk_text(text, max_tokens=10, overlap=0)
        assert len(chunks) == 5  # 200 chars / 40 chars per chunk


# ── chunk_pdf ─────────────────────────────────────────────────────────────────

class TestChunkPdf:
    def test_small_pdf_returned_as_single_chunk(self):
        pdf = make_pdf(3)
        chunks = chunk_pdf(pdf, max_pages=5)
        assert len(chunks) == 1

    def test_exact_page_limit_is_single_chunk(self):
        pdf = make_pdf(5)
        chunks = chunk_pdf(pdf, max_pages=5)
        assert len(chunks) == 1

    def test_oversized_pdf_splits_into_multiple_chunks(self):
        pdf = make_pdf(11)
        chunks = chunk_pdf(pdf, max_pages=5)
        assert len(chunks) == 3  # pages 0-4, 5-9, 10

    def test_each_chunk_is_valid_pdf(self):
        pdf = make_pdf(12)
        for chunk in chunk_pdf(pdf, max_pages=5):
            doc = fitz.open(stream=chunk, filetype="pdf")
            assert len(doc) > 0
            doc.close()

    def test_total_pages_preserved(self):
        total_pages = 13
        pdf = make_pdf(total_pages)
        chunks = chunk_pdf(pdf, max_pages=5)
        pages_in_chunks = sum(
            len(fitz.open(stream=c, filetype="pdf")) for c in chunks
        )
        assert pages_in_chunks == total_pages


# ── extract_pdf_text ──────────────────────────────────────────────────────────

class TestExtractPdfText:
    def test_extracts_text_from_pdf(self):
        pdf = make_pdf(2)
        text = extract_pdf_text(pdf)
        assert "Page 1 content" in text
        assert "Page 2 content" in text

    def test_empty_pdf_returns_empty_string(self):
        doc = fitz.open()
        doc.new_page()  # blank page
        pdf = doc.tobytes()
        doc.close()
        assert extract_pdf_text(pdf) == ""
