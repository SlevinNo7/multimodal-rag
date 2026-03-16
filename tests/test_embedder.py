import math
import pytest
from unittest.mock import MagicMock, patch
from lib.embedder import _normalize, embed_text, embed_query, embed_image


# ── _normalize ────────────────────────────────────────────────────────────────

class TestNormalize:
    def test_unit_vector_unchanged(self):
        vec = [1.0, 0.0, 0.0]
        result = _normalize(vec)
        assert abs(result[0] - 1.0) < 1e-9
        assert abs(result[1]) < 1e-9

    def test_output_has_unit_length(self):
        vec = [3.0, 4.0]
        result = _normalize(vec)
        norm = math.sqrt(sum(x ** 2 for x in result))
        assert abs(norm - 1.0) < 1e-9

    def test_zero_vector_unchanged(self):
        vec = [0.0, 0.0, 0.0]
        result = _normalize(vec)
        assert result == [0.0, 0.0, 0.0]

    def test_negative_values(self):
        vec = [-3.0, 4.0]
        result = _normalize(vec)
        norm = math.sqrt(sum(x ** 2 for x in result))
        assert abs(norm - 1.0) < 1e-9

    def test_returns_list(self):
        assert isinstance(_normalize([1.0, 2.0]), list)

    def test_single_element(self):
        result = _normalize([5.0])
        assert abs(result[0] - 1.0) < 1e-9


# ── embed_text / embed_query (mocked API) ─────────────────────────────────────

def _mock_client(vec: list[float]):
    embedding = MagicMock()
    embedding.values = vec
    response = MagicMock()
    response.embeddings = [embedding]
    client = MagicMock()
    client.models.embed_content.return_value = response
    return client


class TestEmbedText:
    def test_returns_normalized_vector(self):
        raw = [3.0, 4.0] + [0.0] * 3070
        with patch("lib.embedder.get_client", return_value=_mock_client(raw)):
            result = embed_text("hello")
        norm = math.sqrt(sum(x ** 2 for x in result))
        assert abs(norm - 1.0) < 1e-6

    def test_uses_retrieval_document_task_type_by_default(self):
        raw = [1.0] + [0.0] * 3071
        client = _mock_client(raw)
        with patch("lib.embedder.get_client", return_value=client):
            embed_text("hello")
        call_kwargs = client.models.embed_content.call_args
        # config is passed as keyword arg; inspect the EmbedContentConfig constructor call
        config_call = client.models.embed_content.call_args
        # task_type is passed to types.EmbedContentConfig; verify via the call args directly
        from google.genai import types as genai_types
        ctor_calls = genai_types.EmbedContentConfig.call_args_list
        assert any(
            c.kwargs.get("task_type") == "RETRIEVAL_DOCUMENT"
            or (c.args and c.args[0] == "RETRIEVAL_DOCUMENT")
            for c in ctor_calls
        )

    def test_embed_query_uses_retrieval_query_task_type(self):
        raw = [1.0] + [0.0] * 3071
        client = _mock_client(raw)
        with patch("lib.embedder.get_client", return_value=client):
            embed_query("what is rag?")
        from google.genai import types as genai_types
        ctor_calls = genai_types.EmbedContentConfig.call_args_list
        assert any(
            c.kwargs.get("task_type") == "RETRIEVAL_QUERY"
            or (c.args and c.args[0] == "RETRIEVAL_QUERY")
            for c in ctor_calls
        )

    def test_returns_list_of_floats(self):
        raw = [0.5, 0.5] + [0.0] * 3070
        with patch("lib.embedder.get_client", return_value=_mock_client(raw)):
            result = embed_text("test")
        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)
