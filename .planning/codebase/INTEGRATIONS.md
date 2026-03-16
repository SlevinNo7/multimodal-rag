# External Integrations

**Analysis Date:** 2026-03-16

## APIs & External Services

**Embedding Model:**
- Google Gemini Embedding API (`gemini-embedding-2-preview`)
  - SDK/Client: `google-genai` (1.0.0+)
  - Auth: `GEMINI_API_KEY` env var
  - Purpose: Embed text, images, audio, video, PDF into 3072-dimensional vectors
  - All content types use `embed_content()` with `Part.from_bytes` for binary data
  - Query embeddings: `task_type="RETRIEVAL_QUERY"`
  - Document embeddings: `task_type="RETRIEVAL_DOCUMENT"`

**LLM Providers (Pluggable):**
- Google Gemini API
  - Model: `gemini-2.0-flash-lite` (default)
  - SDK: `google-genai`
  - Auth: `GEMINI_API_KEY` (from env or user-provided in UI)
  - Implementation: `lib/llm.py` → `GeminiProvider` class

- OpenAI API
  - Model: `o4-mini` (default, configurable)
  - SDK: `openai`
  - Auth: `OPENAI_API_KEY` (user-provided in UI)
  - Implementation: `lib/llm.py` → `OpenAIProvider` class
  - Streaming: Supported via `stream()` method

- Anthropic Claude API
  - Model: `claude-sonnet-4-5` (default, configurable)
  - SDK: `anthropic`
  - Auth: `ANTHROPIC_API_KEY` (user-provided in UI)
  - Implementation: `lib/llm.py` → `AnthropicProvider` class
  - Streaming: Supported via `messages.stream()`

- Ollama (Local/Self-Hosted)
  - Model: `llama3` (default, user-configurable)
  - Connection: HTTP POST to `base_url/api/chat`
  - Default URL: `http://localhost:11434` (configurable)
  - SDK: `httpx` (streaming HTTP client)
  - Auth: None (local service)
  - Implementation: `lib/llm.py` → `OllamaProvider` class

## Data Storage

**Databases:**
- Supabase PostgreSQL
  - Project: `lgllivbqhqmpkcbmacyy` (hardcoded in CLAUDE.md, environment-specific in `.env`)
  - Connection: `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` env vars
  - Client SDK: `supabase-py` (2.11.0+)
  - Authentication:
    - Service key (`SUPABASE_SERVICE_KEY`): Admin queries, database setup
    - Anon key (`SUPABASE_ANON_KEY`): Public/unauthenticated queries
    - User JWT token: Authenticated queries via RLS (postgrest.auth(access_token))

- Tables:
  - `documents`: Stores embeddings, content, file metadata, base64 image data
    - Columns: id (UUID), title, content_type, original_filename, chunk_index, chunk_total, text_content, metadata (JSONB), embedding (VECTOR(3072)), file_data (TEXT - base64), user_id (UUID FK), created_at
    - RLS: Row-level security filters by user_id

  - `user_settings`: Stores per-user LLM provider preferences
    - Columns: user_id (UUID PK), llm_provider, llm_model, llm_api_key, ollama_url
    - RLS: Scoped to authenticated user

- Extensions:
  - `pgvector`: Vector storage and cosine similarity search
    - Search method: Exact cosine similarity (no HNSW index; pgvector limit is 2000 dims, embeddings are 3072)
  - `uuid-ossp`: Generate UUID v4 for primary keys

**RPC Functions:**
- `match_documents(query_embedding, match_threshold, match_count, filter_type)`: Cosine similarity search with optional content-type filtering

**File Storage:**
- Supabase Postgrest (via TEXT column `file_data`)
  - Images: Base64-encoded and stored inline in documents table
  - Other content types: Text or metadata only

**Caching:**
- None detected (all queries hit database directly)

## Authentication & Identity

**Auth Provider:**
- Supabase Auth (built-in PostgreSQL authentication)
  - Sign up: `auth.sign_up({"email": email, "password": password})`
  - Sign in: `auth.sign_in_with_password({"email": email, "password": password})`
  - Session management: JWT access token (stored in Streamlit `st.session_state`)
  - Implementation: `lib/auth.py`
  - Login flow: Rendered in `app.py` (tabs for login and register)

**User Isolation:**
- Row-level security (RLS) on `documents` and `user_settings` tables
- All database queries use authenticated Supabase client with user JWT token
- Prevents cross-user access even if database is compromised

## Monitoring & Observability

**Error Tracking:**
- None detected (ad-hoc error handling in try/except blocks)

**Logs:**
- Streamlit native logging (stderr to console)
- No centralized logging configured
- No observability tools integrated

## CI/CD & Deployment

**Hosting:**
- Docker-based deployment
  - Base image: `python:3.11-slim`
  - Exposed port: 8501 (Streamlit default)
  - Healthcheck: `curl -f http://localhost:8501/_stcore/health`

**Docker Compose:**
- Single `app` service
- Env file injection: Loads `.env` automatically
- Restart policy: `unless-stopped`

**CI Pipeline:**
- Not detected (no GitHub Actions, CircleCI, etc.)

## Environment Configuration

**Required env vars:**
- `GEMINI_API_KEY` - Embedding + LLM API key
- `SUPABASE_URL` - Database host
- `SUPABASE_SERVICE_KEY` - Admin database access
- `SUPABASE_ANON_KEY` - Public database access
- `DATABASE_URL` - Direct PostgreSQL connection (setup only)
- `OPENAI_API_KEY` - Optional, users can set in UI
- `ANTHROPIC_API_KEY` - Optional, users can set in UI

**Secrets location:**
- `.env` file (git-ignored)
- Example provided: `.env.example`
- Supabase Dashboard: Settings → API for URL and keys

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected (RAG reasoning calls are synchronous request-response)

---

*Integration audit: 2026-03-16*
