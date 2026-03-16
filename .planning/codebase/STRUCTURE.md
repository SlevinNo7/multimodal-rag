# STRUCTURE.md — Directory Layout & Organization

## Root Directory

```
multimodal-rag/
├── app.py                  # Streamlit entry point — all UI tabs
├── CLAUDE.md               # Claude Code instructions
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── setup_db.py             # One-time DB setup script (Supabase DDL)
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Docker Compose config
├── .env                    # Secrets (not committed)
├── .env.example            # Secrets template (committed)
├── .dockerignore
├── .gitignore
├── lib/                    # Core library modules
└── tests/                  # Unit tests
```

## lib/ — Core Modules

```
lib/
├── __init__.py
├── auth.py       # Supabase auth (login, logout, session management)
├── chunker.py    # Content splitting (text, PDF, audio, video)
├── codex.py      # OpenAI o4-mini LLM reasoning + citation
├── db.py         # Supabase client, vector insert/search/delete/stats
├── embedder.py   # Gemini embedding-2-preview (3072 dims)
├── llm.py        # LLM abstraction/factory layer
└── rag.py        # Ingest + query orchestration
```

### Key File Responsibilities

| File | Responsibility |
|------|---------------|
| `app.py` | Streamlit UI: Upload & Embed, Search, Browse tabs |
| `lib/rag.py` | Orchestrates full ingest pipeline and query pipeline |
| `lib/embedder.py` | Wraps `google-genai` SDK, handles all content types via `Part.from_bytes` |
| `lib/chunker.py` | Splits oversized content: text (~6000 tokens), PDF (5 pages), audio (75s), video (120s) |
| `lib/db.py` | Supabase CRUD: insert documents, `match_documents()` RPC, stats, delete |
| `lib/codex.py` | Sends query + retrieved context to OpenAI o4-mini with citation instructions |
| `lib/auth.py` | Supabase Auth session handling for multi-user isolation |
| `lib/llm.py` | LLM factory/abstraction (used by codex) |
| `setup_db.py` | Creates Supabase tables, pgvector extension, `match_documents()` RPC |

## tests/ — Test Suite

```
tests/
├── __init__.py
├── conftest.py       # Shared pytest fixtures and mocks
├── test_chunker.py   # Chunker unit tests
├── test_embedder.py  # Embedder unit tests (mocked API)
├── test_llm.py       # LLM abstraction tests
└── test_rag.py       # RAG pipeline integration tests
```

## .planning/ — GSD Planning Artifacts

```
.planning/
└── codebase/         # Codebase mapping documents (this directory)
```

## Naming Conventions

- **Modules**: `snake_case.py` under `lib/`
- **Test files**: `test_<module>.py` mirroring `lib/<module>.py`
- **Functions**: `snake_case` throughout
- **Classes**: `PascalCase` (e.g., `Embedder`, `Chunker`)
- **Constants/env vars**: `UPPER_SNAKE_CASE`
- **Database columns**: `snake_case` (e.g., `file_data`, `content_type`, `embedding`)

## Adding New Code

### New content type support
1. Add detection logic in `lib/rag.py` (type detection block)
2. Add chunking strategy in `lib/chunker.py`
3. Ensure `lib/embedder.py` handles the MIME type via `Part.from_bytes`

### New UI tab
1. Add tab in `app.py` alongside existing `tab1`, `tab2`, `tab3`

### New database operation
1. Add method to `lib/db.py` Supabase client wrapper
2. Add corresponding SQL migration to `setup_db.py`

### New LLM provider
1. Add provider in `lib/llm.py` factory
2. Update `lib/codex.py` if reasoning prompt changes

## Configuration & Secrets

All runtime config lives in `.env` (never committed):

```
GEMINI_API_KEY=...
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
```

Template available at `.env.example`.
