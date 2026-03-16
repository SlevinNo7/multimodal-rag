import pytest
from unittest.mock import MagicMock, patch
from lib.llm import _build_user_message, get_provider, GeminiProvider, OllamaProvider


# ── _build_user_message ───────────────────────────────────────────────────────

class TestBuildUserMessage:
    def test_includes_query(self):
        msg = _build_user_message("my question", [])
        assert "my question" in msg

    def test_includes_source_reference(self):
        chunks = [{"original_filename": "doc.txt", "content_type": "text", "similarity": 0.9, "text_content": "hello"}]
        msg = _build_user_message("q", chunks)
        assert "[Source 1]" in msg
        assert "doc.txt" in msg

    def test_non_text_content_shows_placeholder(self):
        chunks = [{"original_filename": "img.png", "content_type": "image", "similarity": 0.8, "text_content": None}]
        msg = _build_user_message("q", chunks)
        assert "(non-text content)" in msg

    def test_multiple_sources_numbered(self):
        chunks = [
            {"original_filename": "a.txt", "content_type": "text", "similarity": 0.9, "text_content": "aaa"},
            {"original_filename": "b.txt", "content_type": "text", "similarity": 0.8, "text_content": "bbb"},
        ]
        msg = _build_user_message("q", chunks)
        assert "[Source 1]" in msg
        assert "[Source 2]" in msg


# ── get_provider factory ──────────────────────────────────────────────────────

class TestGetProvider:
    def test_returns_gemini_provider(self):
        p = get_provider({"provider": "gemini", "api_key": "key", "model": ""})
        assert isinstance(p, GeminiProvider)

    def test_returns_ollama_provider(self):
        p = get_provider({"provider": "ollama", "model": "llama3", "ollama_url": "http://localhost:11434"})
        assert isinstance(p, OllamaProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_provider({"provider": "nonexistent"})

    def test_default_models_applied(self):
        p = get_provider({"provider": "gemini", "api_key": "k", "model": ""})
        assert p.model == "gemini-2.0-flash-lite"

    def test_custom_model_used(self):
        p = get_provider({"provider": "gemini", "api_key": "k", "model": "gemini-pro"})
        assert p.model == "gemini-pro"


# ── OllamaProvider.reason (mocked HTTP) ───────────────────────────────────────

class TestOllamaProvider:
    def test_reason_returns_content(self):
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3")
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "ollama answer"}}
        mock_response.raise_for_status = MagicMock()
        with patch("httpx.post", return_value=mock_response):
            result = provider.reason("q?", [{"text_content": "ctx", "original_filename": "f", "content_type": "text", "similarity": 0.9}])
        assert result == "ollama answer"

    def test_reason_raises_on_http_error(self):
        import httpx
        provider = OllamaProvider()
        with patch("httpx.post", side_effect=httpx.HTTPStatusError("err", request=MagicMock(), response=MagicMock())):
            with pytest.raises(httpx.HTTPStatusError):
                provider.reason("q?", [])
