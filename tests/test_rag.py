import pytest
from unittest.mock import MagicMock, patch
from lib.rag import detect_content_type, ingest, query


# ── detect_content_type ───────────────────────────────────────────────────────

class TestDetectContentType:
    @pytest.mark.parametrize("mime,expected", [
        ("image/png", "image"),
        ("image/jpeg", "image"),
        ("image/webp", "image"),
        ("application/pdf", "pdf"),
        ("audio/mpeg", "audio"),
        ("audio/wav", "audio"),
        ("video/mp4", "video"),
        ("video/quicktime", "video"),
    ])
    def test_known_mime_types(self, mime, expected):
        assert detect_content_type(mime, "file") == expected

    @pytest.mark.parametrize("filename,expected", [
        ("doc.txt", "text"),
        ("photo.png", "image"),
        ("photo.jpg", "image"),
        ("report.pdf", "pdf"),
        ("song.mp3", "audio"),
        ("song.wav", "audio"),
        ("clip.mp4", "video"),
        ("clip.mov", "video"),
    ])
    def test_fallback_by_extension(self, filename, expected):
        assert detect_content_type("application/octet-stream", filename) == expected

    def test_unknown_type_defaults_to_text(self):
        assert detect_content_type("application/octet-stream", "mystery") == "text"

    def test_mime_takes_priority_over_extension(self):
        # mime says image even though extension is .pdf
        assert detect_content_type("image/png", "file.pdf") == "image"


# ── ingest (mocked) ───────────────────────────────────────────────────────────

def _fake_vec():
    return [0.0] * 3072


class TestIngest:
    def _patch_all(self):
        return [
            patch("lib.rag.embedder.embed_text", return_value=_fake_vec()),
            patch("lib.rag.embedder.embed_image", return_value=_fake_vec()),
            patch("lib.rag.embedder.embed_pdf_page_bytes", return_value=_fake_vec()),
            patch("lib.rag.db.insert_document", side_effect=lambda **kw: {"id": "abc", **kw}),
        ]

    def test_ingest_text_returns_one_result(self):
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            results = ingest(b"Hello world", "test.txt", "Test", "text/plain")
            assert len(results) == 1
        finally:
            for p in patches:
                p.stop()

    def test_ingest_text_long_creates_multiple_chunks(self):
        # default max_chars = 6000*4 = 24000; need > 24000 chars; overlap=500 < 6000 so no infinite loop
        long_text = ("word " * 5000).encode()  # 25000 chars
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            results = ingest(long_text, "big.txt", "Big", "text/plain")
            assert len(results) > 1
        finally:
            for p in patches:
                p.stop()

    def test_ingest_image_stores_base64(self):
        import base64
        patches = self._patch_all()
        for p in patches:
            p.start()
        inserted = {}
        with patch("lib.rag.db.insert_document", side_effect=lambda **kw: (inserted.update(kw) or {"id": "x", **kw})):
            try:
                ingest(b"\x89PNG\r\n", "img.png", "Img", "image/png")
            finally:
                for p in patches:
                    p.stop()
        assert inserted.get("file_data") == base64.b64encode(b"\x89PNG\r\n").decode("ascii")

    def test_ingest_unknown_mime_treated_as_text(self):
        patches = self._patch_all()
        for p in patches:
            p.start()
        try:
            results = ingest(b"some data", "data.bin", "Data", "application/octet-stream")
            assert len(results) >= 1
        finally:
            for p in patches:
                p.stop()


# ── query (mocked) ────────────────────────────────────────────────────────────

class TestQuery:
    def test_returns_answer_and_sources(self):
        fake_matches = [{"id": "1", "text_content": "foo", "similarity": 0.9}]
        with patch("lib.rag.embedder.embed_query", return_value=_fake_vec()), \
             patch("lib.rag.db.search_documents", return_value=fake_matches), \
             patch("lib.rag.codex.reason", return_value="The answer"):
            result = query("What is foo?")
        assert result["answer"] == "The answer"
        assert result["sources"] == fake_matches

    def test_no_codex_when_disabled(self):
        fake_matches = [{"id": "1", "text_content": "foo", "similarity": 0.9}]
        with patch("lib.rag.embedder.embed_query", return_value=_fake_vec()), \
             patch("lib.rag.db.search_documents", return_value=fake_matches):
            result = query("What is foo?", use_codex=False)
        assert result["answer"] is None
        assert result["sources"] == fake_matches

    def test_no_answer_when_no_matches(self):
        with patch("lib.rag.embedder.embed_query", return_value=_fake_vec()), \
             patch("lib.rag.db.search_documents", return_value=[]):
            result = query("What is foo?", use_codex=True)
        assert result["answer"] is None
        assert result["sources"] == []

    def test_uses_llm_provider_when_settings_given(self):
        fake_matches = [{"id": "1", "text_content": "bar", "similarity": 0.8}]
        mock_provider = MagicMock()
        mock_provider.reason.return_value = "LLM answer"
        with patch("lib.rag.embedder.embed_query", return_value=_fake_vec()), \
             patch("lib.rag.db.search_documents", return_value=fake_matches), \
             patch("lib.llm.get_provider", return_value=mock_provider):
            result = query("Q?", use_codex=True, llm_settings={"provider": "openai"})
        assert result["answer"] == "LLM answer"
        mock_provider.reason.assert_called_once()
