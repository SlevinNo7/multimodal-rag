# TESTING.md — Test Structure & Practices

## Framework

- **pytest** — primary test runner
- **unittest.mock** — mocking external dependencies
- **fitz (PyMuPDF)** — used in tests for creating real PDF fixtures

## Test File Organization

```
tests/
├── __init__.py
├── conftest.py       # Global dependency stubbing (run before all imports)
├── test_chunker.py   # Tests for lib/chunker.py
├── test_embedder.py  # Tests for lib/embedder.py
├── test_llm.py       # Tests for lib/llm.py
└── test_rag.py       # Tests for lib/rag.py
```

Mirror pattern: each `lib/<module>.py` has a corresponding `tests/test_<module>.py`.

## conftest.py Strategy

Critical: `conftest.py` stubs out broken/unavailable system-level dependencies **before any test module is imported**. This allows unit tests to run without the full environment.

```python
# Registers MagicMock for dotted module paths
_mock_module("google", "genai")
_mock_module("supabase")
_mock_module("openai")
_mock_module("anthropic")
```

This approach patches `sys.modules` directly — tests that need specific mock behavior override at the function/method level.

## Test Structure Pattern

Tests use **class-based grouping** by function under test:

```python
class TestChunkText:
    def test_short_text_returned_as_single_chunk(self): ...
    def test_long_text_splits_into_multiple_chunks(self): ...

class TestChunkPdf:
    def test_small_pdf_returned_as_single_chunk(self): ...
```

No `setUp`/`tearDown` — tests are stateless by design. Fixtures created inline using helper functions (e.g., `make_pdf(num_pages)`).

## Naming Convention

```
test_<what_it_does_in_plain_english>
```

Examples:
- `test_short_text_returned_as_single_chunk`
- `test_each_chunk_within_max_size`
- `test_total_pages_preserved`

## Mocking Pattern

External APIs mocked at the function level with `unittest.mock.patch` or via conftest stubs:

```python
from unittest.mock import MagicMock, patch

@patch("lib.embedder.genai")
def test_embed_returns_vector(mock_genai):
    mock_genai.embed_content.return_value = MagicMock(embedding=[0.1] * 3072)
    ...
```

## Fixtures & Helpers

Real data factories preferred over mock data where possible:

```python
def make_pdf(num_pages: int) -> bytes:
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1} content")
    return doc.tobytes()
```

## Test Types

| Type | Files | Description |
|------|-------|-------------|
| Unit | `test_chunker.py`, `test_embedder.py`, `test_llm.py` | Isolated function tests, no external calls |
| Integration | `test_rag.py` | Pipeline flow with mocked API calls |
| E2E | None | No E2E tests — Streamlit UI not tested |

## Coverage Summary

- **62 passing tests** across 4 test modules
- Chunker: fully covered (text splitting, PDF splitting, PDF text extraction)
- Embedder: covered with mocked `google-genai` SDK
- LLM: covered with mocked `openai`
- RAG: pipeline integration with mocked embedder + DB

## Running Tests

```bash
pytest tests/
pytest tests/test_chunker.py -v   # specific module
pytest -k "TestChunkPdf"          # specific class
```

## Known Constraints

- `conftest.py` global stubs mean `google.genai`, `supabase`, `openai`, and `anthropic` are always mocked — tests cannot hit live APIs
- Audio/video chunking (pydub, moviepy) have no dedicated test coverage
- Database layer (`lib/db.py`) has no unit tests — tested implicitly via RAG integration tests
