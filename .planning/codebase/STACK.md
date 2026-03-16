# Technology Stack

**Analysis Date:** 2026-03-16

## Languages

**Primary:**
- Python 3.11+ - Core application language, Streamlit frontend, all backend logic
- SQL - PostgreSQL schema and RPC functions via psycopg2

**Secondary:**
- Bash - Docker entrypoint, setup scripts

## Runtime

**Environment:**
- Python 3.11+ (Dockerfile specifies `python:3.11-slim`)
- Tested with Python 3.12.10

**Package Manager:**
- pip - Standard Python package manager
- Lockfile: Not present (uses `requirements.txt` with pinned versions)

## Frameworks

**Core:**
- Streamlit 1.40.0+ - Web UI framework (single monolith)

**Data/Vector Operations:**
- numpy 1.26.0+ - Vector normalization and numerical operations

**Media Processing:**
- PyMuPDF 1.25.0+ - PDF parsing (5-page chunks via `pymupdf`)
- pydub 0.25.1+ - Audio segmentation (75-second chunks)
- moviepy 2.1.0+ - Video frame extraction (120-second chunks)

**HTTP Client:**
- httpx 0.27.0+ - HTTP requests for Ollama API (streaming support)

**Database & ORM:**
- psycopg2-binary 2.9.9+ - PostgreSQL driver for direct schema setup
- supabase-py 2.11.0+ - Supabase client library (auth, Postgrest, RPC calls)

**Environment:**
- python-dotenv 1.0.1+ - Load `.env` configuration

## Key Dependencies

**Critical:**
- google-genai 1.0.0+ - Google Gemini API (embeddings + LLM)
  - Embedding model: `gemini-embedding-2-preview` (3072 dimensions, L2-normalized)
  - LLM model: `gemini-2.0-flash-lite` (default reasoning engine)

- openai 1.60.0+ - OpenAI API integration
  - Fallback LLM provider (supports `o4-mini` and other models)

- anthropic 0.40.0+ - Anthropic Claude API
  - Alternative LLM provider (default `claude-sonnet-4-5`)

**Infrastructure:**
- supabase-py 2.11.0+ - PostgreSQL + authentication + vector search
  - pgvector extension (exact cosine similarity search, no HNSW)
  - UUID extension for primary keys
  - Row-level security (RLS) via Postgrest auth

## Configuration

**Environment:**
- Loaded via `python-dotenv` from `.env` file (in `.gitignore`)
- Example template: `.env.example`

**Required env vars:**
- `GEMINI_API_KEY` - Google Gemini API key (for embeddings)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Service role key (admin queries)
- `SUPABASE_ANON_KEY` - Public key (authenticated user queries)
- `DATABASE_URL` - PostgreSQL connection string (setup only, via psycopg2)
- `OPENAI_API_KEY` - Optional, set in UI by users
- `ANTHROPIC_API_KEY` - Optional, set in UI by users

**Build:**
- Dockerfile: `FROM python:3.11-slim`, exposes port 8501
- docker-compose.yml: Single `app` service, mounts `.env`, restarts unless-stopped
- System packages: ffmpeg, libgl1, libglib2.0-0 (media processing dependencies)

## Platform Requirements

**Development:**
- Python 3.11 or higher
- pip (included with Python)
- FFmpeg (for audio/video processing) - `apt-get install ffmpeg`
- OpenGL libraries (libgl1, libglib2.0-0) for PDF rendering

**Production:**
- Deployment target: Docker container (Streamlit on port 8501)
- Upstream: Supabase-hosted PostgreSQL with pgvector extension enabled
- Reverse proxy: Required (Streamlit uses WebSocket; typically behind nginx/caddy)

---

*Stack analysis: 2026-03-16*
