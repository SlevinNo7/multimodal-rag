# Coding Conventions

**Analysis Date:** 2026-03-16

## Naming Patterns

**Files:**
- Module files use `snake_case`: `embedder.py`, `chunker.py`, `db.py`, `rag.py`, `llm.py`, `codex.py`, `auth.py`
- Test files follow pattern `test_<module>.py`: `test_embedder.py`, `test_chunker.py`, `test_rag.py`, `test_llm.py`
- Entry point is `app.py` (Streamlit main application)
- Setup script is `setup_db.py`

**Functions:**
- All functions use `snake_case`: `embed_text()`, `chunk_text()`, `insert_document()`, `detect_content_type()`, `embed_query()`
- Private/internal functions prefixed with single underscore: `_normalize()`, `_progress()`, `_build_user_message()`, `_mock_client()`, `_fake_vec()`, `_patch_all()`
- Helper functions for mocking/testing prefixed with underscore: `_mock_module()`, `_mock_client()`

**Variables:**
- Local variables use `snake_case`: `chunk_text`, `query_vec`, `results`, `matches`
- Configuration constants use `UPPER_CASE`: `MODEL`, `MIME_MAP`, `AUDIO_FMT`, `VIDEO_SUFFIX`, `SYSTEM_PROMPT`
- Session state keys use `snake_case`: `access_token`, `user_id`, `user_email`, `llm_settings`, `browse_page`, `pending_delete_id`
- Global module clients use `_client` pattern: `_client` in `embedder.py`, `db.py`, `auth.py`

**Types:**
- Use Python 3.10+ union syntax with `|` operator: `str | None`, `Client | None`, `list[float]`, `list[dict]`, `dict[str, int]`
- Type hints always included in function signatures
- Union types for optional values

## Code Style

**Formatting:**
- No explicit formatter configured (no `.prettierrc`, `.flake8`, or `pyproject.toml` with formatter config)
- Code follows implicit Python conventions
- Consistent indentation (4 spaces)
- Line length not strictly enforced

**Linting:**
- No explicit linter configuration found
- Code style appears to follow PEP 8 implicitly

## Import Organization

**Order:**
1. Standard library imports: `import os`, `import io`, `import sys`, `import base64`, `import tempfile`
2. Third-party framework imports: `import streamlit as st`, `from dotenv import load_dotenv`
3. Third-party SDK/client imports: `from google import genai`, `from supabase import create_client`
4. Internal library imports: `from lib import db, rag, auth, llm`, `from lib.embedder import _normalize, embed_text`

**Path Aliases:**
- Relative imports from `lib/` package: `from lib import db, rag, auth, llm`
- Specific function imports: `from lib.embedder import embed_text, embed_query`
- No path aliases configured (no `@/` or similar)

**Import style:**
- `from X import Y` for specific functions
- `from module import name as alias` when needed (e.g., `import fitz  # PyMuPDF`)
- `from __future__ import annotations` at top of modules using forward references

## Error Handling

**Patterns:**
- Try-catch blocks used for external API calls and file operations
- Return dictionaries with `error` key for propagating errors without exceptions: See `auth.login()`, `auth.register()` returning `{"user": ..., "session": ..., "error": str | None}`
- Exception messages passed directly to Streamlit UI: `st.error(f"Error: {e}")`
- Bare `except Exception:` used for logging/debugging (e.g., in `auth.logout()`)
- Broad exception catching in critical paths with error messaging

**Example from `lib/rag.py`:**
```python
def ingest(...):
    def _progress(msg: str):
        if on_progress:
            on_progress(msg)
```

**Example from `app.py`:**
```python
try:
    results = rag.ingest(...)
except Exception as e:
    file_status.update(label=f"❌ {uploaded.name} — Fehler: {e}", state="error")
```

## Logging

**Framework:** Console output via Streamlit (`st.write()`, `st.error()`, `st.success()`, `st.warning()`)

**Patterns:**
- Progress messages sent via `on_progress` callback: `on_progress(f"Embedding text chunk {i+1}/{total}")`
- Status containers show multi-line progress: `st.status()` for file upload progress
- Error messages always include exception details: `f"Fehler: {e}"`
- Success messages confirm action completion: `st.success(f"Stored {total_stored} chunk(s)...")`

**Example from `lib/rag.py`:**
```python
def ingest(..., on_progress=None, ...):
    def _progress(msg: str):
        if on_progress:
            on_progress(msg)

    _progress(f"Embedding text chunk {i+1}/{total}")
```

## Comments

**When to Comment:**
- Docstrings used for public functions: `"""Embed and store a file. Returns list of inserted document rows."""`
- Minimal inline comments; code is self-documenting via naming
- Section dividers use ASCII formatting: `# ── Section Name ──────────────────`

**JSDoc/TSDoc:**
- Not applicable (Python project)
- Function docstrings follow standard Python convention

**Example from `lib/chunker.py`:**
```python
def chunk_text(text: str, max_tokens: int = 6000, overlap: int = 500) -> list[str]:
    """Split text into chunks by approximate token count (1 token ~ 4 chars)."""
```

**Example from `lib/db.py`:**
```python
def get_documents_page(...) -> tuple[list[dict], int]:
    """Returns (rows, total_count) for the given page (0-indexed)."""
```

## Function Design

**Size:** Functions are focused and concise. Most functions under 30 lines. Larger orchestration functions like `rag.ingest()` are 120+ lines but organized by content type branches.

**Parameters:**
- Positional arguments for core inputs
- Keyword arguments with defaults for optional parameters: `max_tokens: int = 6000`, `task_type: str = "RETRIEVAL_DOCUMENT"`
- Client/context passed as `authed_client=None` or `on_progress=None`

**Return Values:**
- Explicit return types in all function signatures
- Functions return data structures (dicts, lists) rather than None
- Database functions return result dicts with full row data
- RAG pipeline returns structured dicts: `{"answer": ..., "sources": ...}`

**Example from `lib/db.py`:**
```python
def insert_document(
    title: str,
    content_type: str,
    ...,
    authed_client: Client | None = None,
) -> dict:
    client = authed_client or get_client()
    row = {...}
    result = client.table("documents").insert(row).execute()
    return result.data[0]
```

## Module Design

**Exports:**
- Modules export public functions directly
- Private functions use `_` prefix convention
- No explicit `__all__` defined

**Barrel Files:**
- `lib/__init__.py` exists but is empty (no re-exports)
- Imports use full module paths: `from lib import db, rag, auth, llm`

**Example module structure (`lib/embedder.py`):**
```python
# Private module globals and helpers
_client: genai.Client | None = None
def _normalize(vec: list[float]) -> list[float]:
    ...

# Public API functions
def embed_text(...) -> list[float]:
    ...
def embed_query(text: str) -> list[float]:
    return embed_text(text, task_type="RETRIEVAL_QUERY")
```

## Constants and Configuration

**Magic strings mapped to dictionaries:**
- MIME type mapping: `MIME_MAP` in `lib/rag.py` maps MIME strings to content type labels
- Format mapping: `AUDIO_FMT` maps MIME types to audio formats
- Video suffix mapping: `VIDEO_SUFFIX` maps video MIME types to file extensions

**Model/API constants:**
- Embedding model: `MODEL = "gemini-embedding-2-preview"` in `embedder.py`
- System prompt: `SYSTEM_PROMPT` constant in `lib/llm.py`

**Default parameters hardcoded where sensible:**
- Chunk sizes: Text 6000 tokens, PDF 5 pages, audio 75s, video 120s
- Similarity threshold: 0.5 default
- Top K results: 10 default

## Dependency Injection

**Pattern:**
- External clients passed as optional parameters with fallback to module-level singleton
- `authed_client: Client | None = None` parameter used throughout DB and auth modules
- If `authed_client` provided (user context), use it; otherwise fall back to `get_client()` (service account)

**Example from `lib/db.py`:**
```python
def search_documents(
    query_embedding: list[float],
    ...,
    authed_client: Client | None = None,
) -> list[dict]:
    client = authed_client or get_client()
    result = client.rpc(...).execute()
    return result.data
```

---

*Convention analysis: 2026-03-16*
