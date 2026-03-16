# Architecture

**Analysis Date:** 2026-03-16

## Pattern Overview

**Overall:** Layered monolith with RAG (Retrieval-Augmented Generation) pipeline

**Key Characteristics:**
- Single-process Streamlit application (no separate backend)
- Multi-modal content ingestion (text, images, PDFs, audio, video)
- Vector embedding-based retrieval using Supabase pgvector
- Pluggable LLM reasoning layer (OpenAI, Anthropic, Gemini, Ollama)
- User isolation via Supabase Row-Level Security (RLS) policies
- Asynchronous progress callbacks for long-running operations

## Layers

**Presentation (UI):**
- Purpose: Render Streamlit interface with three main tabs (Upload, Search, Browse)
- Location: `app.py`
- Contains: Tab components, form handling, image/video display, pagination
- Depends on: `lib.auth`, `lib.db`, `lib.rag`, `lib.llm`
- Used by: End users via Streamlit CLI

**Orchestration/RAG:**
- Purpose: Coordinate multi-modal ingest and query workflows
- Location: `lib/rag.py`
- Contains: `ingest()` (detect type → chunk → embed → store), `query()` (embed query → vector search → optional LLM reasoning)
- Depends on: `lib.chunker`, `lib.embedder`, `lib.db`, `lib.llm`, `lib.codex`
- Used by: `app.py` for Upload and Search tabs

**Content Processing:**
- Purpose: Transform raw content into embeddable chunks
- Location: `lib/chunker.py`
- Contains: `chunk_text()`, `chunk_pdf()`, `chunk_audio()`, `chunk_video()`, `extract_pdf_text()`
- Depends on: PyMuPDF (fitz), pydub, moviepy
- Used by: `lib.rag.ingest()`

**Embedding:**
- Purpose: Generate vector embeddings for all content types
- Location: `lib/embedder.py`
- Contains: `embed_text()`, `embed_image()`, `embed_audio()`, `embed_video()`, `embed_pdf_page_bytes()`, `embed_query()`, `_normalize()`
- Depends on: `google-genai` SDK (Gemini Embedding 2 Preview)
- Used by: `lib.rag.ingest()`, `lib.rag.query()`

**Data Access:**
- Purpose: Manage Supabase database operations (CRUD, search via RPC)
- Location: `lib/db.py`
- Contains: `insert_document()`, `search_documents()`, `get_documents_page()`, `delete_document()`, `get_stats()`, `get_user_settings()`, `upsert_user_settings()`
- Depends on: Supabase Python client
- Used by: `lib.rag.ingest()`, `lib.rag.query()`, `app.py` (Browse tab, settings management)

**Authentication:**
- Purpose: Handle user login/register and JWT token management
- Location: `lib/auth.py`
- Contains: `register()`, `login()`, `logout()`, `get_authed_db_client()`
- Depends on: Supabase auth service
- Used by: `app.py` (auth gate), RLS-enabled database operations

**LLM Reasoning:**
- Purpose: Send query + retrieved context to LLM for synthesis
- Location: `lib/llm.py`
- Contains: Provider factory and implementations (OpenAIProvider, AnthropicProvider, GeminiProvider, OllamaProvider)
- Depends on: openai, anthropic, google-genai, httpx SDKs
- Used by: `app.py` (Search tab streaming), `lib.rag.query()` (optional reasoning)

**Legacy Codex Module:**
- Purpose: Deprecated reasoning module (kept for backward compatibility)
- Location: `lib/codex.py`
- Contains: Single function (no longer actively used)
- Depends on: openai
- Used by: `lib.rag.query()` fallback if no llm_settings provided

## Data Flow

**Ingest Pipeline:**
1. User uploads file via `app.py` Upload tab
2. `rag.ingest()` detects content type from MIME + filename fallback
3. Content type router (if/elif) dispatches to appropriate chunker
4. Chunker yields binary or text segments based on content type and size limits
5. Each chunk → `embedder.embed_*()` → 3072-dim L2-normalized vector
6. `db.insert_document()` stores chunk + vector + metadata in Supabase `documents` table
7. RLS policy `users_own_documents` limits data to authenticated user
8. Progress callback fires after each chunk for UI updates

**Query Pipeline:**
1. User enters query text in `app.py` Search tab
2. `rag.query()` embeds query using `embedder.embed_query()` (task_type="RETRIEVAL_QUERY")
3. `db.search_documents()` calls Supabase `match_documents()` RPC
4. RPC executes SQL: cosine similarity search across user's document vectors, filtered by content type if specified, top-k results
5. Retrieved matches returned with similarity scores
6. If `use_codex=True`, sends query + sources to LLM provider via `llm.get_provider()` factory
7. LLM streams response to UI via `st.write_stream(provider.stream())`
8. Results displayed as collapsible cards with base64-decoded images/videos

**State Management:**
- Session state stored in Streamlit `st.session_state` (ephemeral per browser session)
- User auth tokens (`access_token`, `user_id`, `user_email`) persist for Supabase JWT
- LLM settings and pagination state cached in session state
- Streamlit's `st.cache_data()` used for database stats (30-second TTL)

## Key Abstractions

**Content Type Detection:**
- Purpose: Map MIME types and file extensions to content categories (text, image, pdf, audio, video)
- Examples: `lib/rag.py` MIME_MAP, detect_content_type()
- Pattern: Priority to MIME type, fallback to extension, default to "text"

**Vector Embedding:**
- Purpose: Normalize embeddings for cosine similarity search
- Examples: `lib/embedder.py` _normalize() uses L2 norm
- Pattern: All embeddings converted to 3072-dim float lists, L2-normalized before storage

**Chunking Strategy:**
- Purpose: Split large files into embeddable segments with size/duration limits
- Examples: Text (6000 token chunks, 500-token overlap), PDFs (5-page chunks), Audio (75s segments), Video (120s segments)
- Pattern: Fallback to whole file if already within limits

**LLM Provider Factory:**
- Purpose: Instantiate correct LLM client based on user settings
- Examples: `lib/llm.py` get_provider() factory with protocol-based duck typing
- Pattern: Each provider implements `reason()` and `stream()` methods; message formatting unified in `_build_user_message()`

**Row-Level Security (RLS):**
- Purpose: Isolate users' documents in database without application-level filtering
- Examples: `setup_db.py` RLS policies; `auth.get_authed_db_client()` binds JWT to Supabase client
- Pattern: Policy rule `auth.uid() = user_id` enforced at database layer

## Entry Points

**Web UI:**
- Location: `app.py`
- Triggers: `streamlit run app.py`
- Responsibilities: Render three-tab interface (Upload & Embed, Search, Browse), manage session auth, delegate to library functions

**Database Setup:**
- Location: `setup_db.py`
- Triggers: `python setup_db.py` with DATABASE_URL env var
- Responsibilities: Create `documents` table, `user_settings` table, indexes, RLS policies, `match_documents()` RPC function

## Error Handling

**Strategy:** Try-except at UI layer with inline error messages; exceptions propagated from library functions to Streamlit display

**Patterns:**
- Auth failures (`register()`, `login()`) return error dict: `{"error": str | None, "user": ..., "session": ...}`
- Database operations wrapped in try-except, caught in `app.py` UI callbacks, displayed as `st.error()`
- Invalid queries (empty text, no sources) caught before LLM reasoning, displayed as `st.warning()` or `st.info()`
- Chunking/embedding failures caught per-file in ingest loop, partial success possible
- File upload validation at Streamlit level (accepted types: txt, png, jpg, jpeg, webp, gif, pdf, mp3, wav, mp4, mov, avi)

## Cross-Cutting Concerns

**Logging:** No structured logging framework; relies on Streamlit progress callbacks and exception messages for user feedback

**Validation:**
- Input validation at UI level: file type whitelist, non-empty query text
- Embedding validation: vector normalization ensures L2 norm = 1
- RLS at database: user_id must match auth.uid()

**Authentication:**
- Supabase email/password auth with JWT tokens
- Token stored in session state
- RLS policies prevent access to other users' documents even with valid token
- Logout clears session state

---

*Architecture analysis: 2026-03-16*
