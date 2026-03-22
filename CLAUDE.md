# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **RAG (Retrieval-Augmented Generation) Chat Service** with a FastAPI backend and React frontend. The system supports AI-powered chat with knowledge base document retrieval, using vector embeddings and LangGraph-based agents.

## Architecture

### Backend (BE/)
- **FastAPI** application with Python 3.11+
- **LangGraph**-based agent system for RAG workflows (`app/agent/`)
- **API v1** endpoints in `app/api/v1/`
- **Services** layer in `app/services/` handling business logic
- **Supabase** for PostgreSQL database
- **Qdrant** for vector storage
- **MinIO** for file storage (S3-compatible)
- **Redis** for caching and rate limiting
- **Celery** for background tasks (via RabbitMQ)

### Frontend (FE/)
- **React 19** with **Vite**
- **Tailwind CSS** for styling
- **React Router** for navigation
- **i18next** for internationalization

## Commands

### Backend
```bash
cd BE

# Setup virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Unix

# Install dependencies
pip install .  # or: uv pip install .

# Run API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker (separate terminal)
celery -A app.config worker --pool=solo --loglevel=info

# Run tests
pytest
pytest tests/test_file.py::test_function  # specific test
```

### Frontend
```bash
cd FE

# Install dependencies
pnpm install

# Run development server
pnpm dev

# Build for production
pnpm build

# Lint
pnpm lint
```

### Infrastructure (Docker)
```bash
cd BE
docker compose up -d  # Start Redis, Qdrant, MinIO, RabbitMQ
```

## Services & Ports

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Frontend UI | http://localhost:3000 | - |
| Backend API Docs | http://localhost:8000/docs | - |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| Qdrant Dashboard | http://localhost:6333/dashboard | - |
| RabbitMQ | http://localhost:15672 | guest / guest |

## Key Files

- `BE/main.py` - FastAPI application entry point
- `BE/app/agent/graph.py` - LangGraph agent workflow definition
- `BE/app/agent/retrieval.py` - RAG retrieval logic
- `BE/app/config/config.py` - Configuration settings
- `BE/docker-compose.yml` - Infrastructure services
- `FE/vite.config.js` - Vite configuration
- `FE/src/pages/admin/` - Admin dashboard pages

## Environment Variables

### Backend (.env)
Required variables (see `BE/app/config/config.py` for full list):
- `secret_key`
- `algorithm=HS256`
- `celery_broker=redis://localhost:6379/0`
- `celery_backend=redis://localhost:6379/0`
- `qdrant_host=localhost`
- `minio_endpoint=localhost:9000`
- `minio_access_key` / `minio_secret_key`

### Frontend (.env.local)
```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
```

# context-mode — MANDATORY routing rules

You have context-mode MCP tools available. These rules are NOT optional — they protect your context window from flooding. A single unrouted command can dump 56 KB into context and waste the entire session.

## BLOCKED commands — do NOT attempt these

### curl / wget — BLOCKED
Any Bash command containing `curl` or `wget` is intercepted and replaced with an error message. Do NOT retry.
Instead use:
- `ctx_fetch_and_index(url, source)` to fetch and index web pages
- `ctx_execute(language: "javascript", code: "const r = await fetch(...)")` to run HTTP calls in sandbox

### Inline HTTP — BLOCKED
Any Bash command containing `fetch('http`, `requests.get(`, `requests.post(`, `http.get(`, or `http.request(` is intercepted and replaced with an error message. Do NOT retry with Bash.
Instead use:
- `ctx_execute(language, code)` to run HTTP calls in sandbox — only stdout enters context

### WebFetch — BLOCKED
WebFetch calls are denied entirely. The URL is extracted and you are told to use `ctx_fetch_and_index` instead.
Instead use:
- `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` to query the indexed content

## REDIRECTED tools — use sandbox equivalents

### Bash (>20 lines output)
Bash is ONLY for: `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`, and other short-output commands.
For everything else, use:
- `ctx_batch_execute(commands, queries)` — run multiple commands + search in ONE call
- `ctx_execute(language: "shell", code: "...")` — run in sandbox, only stdout enters context

### Read (for analysis)
If you are reading a file to **Edit** it → Read is correct (Edit needs content in context).
If you are reading to **analyze, explore, or summarize** → use `ctx_execute_file(path, language, code)` instead. Only your printed summary enters context. The raw file content stays in the sandbox.

### Grep (large results)
Grep results can flood context. Use `ctx_execute(language: "shell", code: "grep ...")` to run searches in sandbox. Only your printed summary enters context.

## Tool selection hierarchy

1. **GATHER**: `ctx_batch_execute(commands, queries)` — Primary tool. Runs all commands, auto-indexes output, returns search results. ONE call replaces 30+ individual calls.
2. **FOLLOW-UP**: `ctx_search(queries: ["q1", "q2", ...])` — Query indexed content. Pass ALL questions as array in ONE call.
3. **PROCESSING**: `ctx_execute(language, code)` | `ctx_execute_file(path, language, code)` — Sandbox execution. Only stdout enters context.
4. **WEB**: `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` — Fetch, chunk, index, query. Raw HTML never enters context.
5. **INDEX**: `ctx_index(content, source)` — Store content in FTS5 knowledge base for later search.

## Subagent routing

When spawning subagents (Agent/Task tool), the routing block is automatically injected into their prompt. Bash-type subagents are upgraded to general-purpose so they have access to MCP tools. You do NOT need to manually instruct subagents about context-mode.

## Output constraints

- Keep responses under 500 words.
- Write artifacts (code, configs, PRDs) to FILES — never return them as inline text. Return only: file path + 1-line description.
- When indexing content, use descriptive source labels so others can `ctx_search(source: "label")` later.

## ctx commands

| Command | Action |
|---------|--------|
| `ctx stats` | Call the `ctx_stats` MCP tool and display the full output verbatim |
| `ctx doctor` | Call the `ctx_doctor` MCP tool, run the returned shell command, display as checklist |
| `ctx upgrade` | Call the `ctx_upgrade` MCP tool, run the returned shell command, display as checklist |
