# CONCERNS.md — Technical Debt & Known Issues

## Security

| Issue | Location | Severity |
|-------|----------|----------|
| API keys stored in plaintext `.env` | `.env`, `lib/db.py`, `lib/embedder.py`, `lib/codex.py` | Medium |
| Base64 image storage causes memory bloat on large files | `lib/rag.py`, `lib/db.py` (`file_data` column) | Medium |
| RLS policies lack fine-grained per-user controls | Supabase `documents` table | Medium |
| Stale auth tokens never validated on reuse | `lib/auth.py` | Medium |
| `SUPABASE_SERVICE_KEY` used (bypasses RLS) — no user-scoped key | `lib/db.py` | High |

## Tech Debt

| Issue | Location | Notes |
|-------|----------|-------|
| Global client singletons initialized at module load | `lib/db.py`, `lib/embedder.py` | Hard to test; no DI |
| Broad `except Exception` swallows errors silently | Multiple `lib/` files | Obscures root causes |
| Hardcoded embedding dimensions (3072) | `lib/embedder.py`, `setup_db.py` | Breaks if model changes |
| PDF text truncation at 10k chars | `lib/chunker.py` | Loses content from large PDFs |
| No retry logic for external API calls | `lib/embedder.py`, `lib/codex.py` | Transient failures surface as errors |

## Bugs

- **Metadata inaccuracy**: chunk count reported may not match actual DB inserts on partial failures
- **Pagination off-by-one**: Browse tab pagination may skip or repeat items at boundaries
- **Auth token expiry**: Session token expiry not checked — expired sessions silently fail

## Performance

| Issue | Impact |
|-------|--------|
| Brute-force vector search (O(n)) — no HNSW index | Degrades at scale; pgvector limits HNSW to ≤2000 dims, 3072 dims forces exact search |
| Blocking DB calls in Streamlit event loop | UI freezes during large ingest operations |
| Full chunk text sent to LLM in prompt | Token bloat — no summarization or truncation of context |
| Base64 encoding for all images in DB | Large `file_data` column slows queries |

## Fragility

| Area | Risk |
|------|------|
| `moviepy` / `pydub` for audio-video chunking | Libraries load at runtime; import failures only surface when those content types are processed |
| Streamlit session state across reruns | Race conditions possible with concurrent uploads |
| Streaming LLM responses coupled to UI | `lib/codex.py` streams directly to Streamlit — hard to reuse outside UI |
| `google-genai` beta API | Breaking changes possible; `gemini-embedding-2-preview` is not GA |

## Scaling Concerns

- Single-tenant Supabase schema — all users share the `documents` table, isolated only by RLS user ID
- No embed rate-limit handling — bulk uploads can hit Gemini API rate limits with no backoff
- Streamlit designed for single-user or small-team use — not suitable for high concurrency

## Dependency Risks

| Dependency | Risk |
|------------|------|
| `google-genai` (beta) | API may change; `gemini-embedding-2-preview` model name not stable |
| `PyMuPDF (fitz)` | AGPL license — commercial use requires license compliance |
| `moviepy` | Largely unmaintained; FFmpeg dependency adds install complexity |

## Missing Features / Future Risk

- No async DB operations (all synchronous via `supabase-py`)
- No audit logging (who embedded what, when)
- No per-user quotas or rate limiting
- No document TTL / expiry mechanism
- No document versioning or deduplication

## Test Gaps

- Audio/video chunking (`chunk_audio`, `chunk_video`) — no unit tests
- Database layer (`lib/db.py`) — no isolated unit tests
- Streaming LLM response path — not tested
- RLS policy enforcement — not tested
- Token expiry / session invalidation — not tested
- Corrupted/malformed file handling — not tested
- Concurrent upload behavior — not tested
