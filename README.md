# RAG Chat Service 🤖

Welcome! This includes a **FastAPI** backend and a **Next.js** frontend for a Retrieval-Augmented Generation (RAG) system.

If you just downloaded this project, follow the steps below to get it running.

---

| Service                          | URL                                                                | Default Creds               |
| :------------------------------- | :----------------------------------------------------------------- | :-------------------------- |
| **Frontend UI**                  | [http://localhost:3000](http://localhost:3000)                     | -                           |
| **Backend API Docs**             | [http://localhost:8000/docs](http://localhost:8000/docs)           | -                           |
| **MinIO Console** (Storage)      | [http://localhost:9001](http://localhost:9001)                     | `minioadmin` / `minioadmin` |
| **RabbitMQ** (Queue)             | [http://localhost:15672](http://localhost:15672)                   | `guest` / `guest`           |

## 🚀 Quick Start Guide

### 1. Prerequisites

Ensure you have these installed:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Required for DB, MinIO, Redis)
- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/) & `pnpm` (`npm install -g pnpm`)

### 2. First-Time Setup

#### Step A: Start Core Infrastructure

We use Docker to run the databases (Postgres/Supabase, Redis, MinIO).

```bash
# In project root
docker compose up -d
```

_Wait ~30 seconds for all containers to be healthy._

#### Step B: Backend Setup

1.  Navigate to the `BE` folder:
    ```bash
    cd BE
    ```
2.  Create your environment file:
    - Copy `.env.example` to `.env` (if provided) or create a new `.env`.
    - **Minimal Config** (See `BE/config.py` for full list):
      ```env
      secret_key=YOUR_SECRET_KEY
      algorithm=HS256
      celery_broker=redis://localhost:6379/0
      celery_backend=redis://localhost:6379/0
      minio_endpoint=localhost:9000
      minio_access_key=minioadmin
      minio_secret_key=minioadmin
      ```
3.  Install dependencies:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    pip install .
    # OR using uv
    uv pip install .
    ```

#### Step C: Frontend Setup

1.  Navigate to the `FE_React` folder (or `FE_Dat` if legacy):
    ```bash
    cd ../FE_React
    ```
2.  Install dependencies:
    ```bash
    pnpm install
    ```
3.  Create `.env.local`:
    ```env
    NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
    ```

---

## 🏃 running the App (Daily Usage)

### Option 1: Manual Start (Recommended for Debugging)

You need **3 Terminals**:

**Terminal 1: Services (Docker)**

```bash
docker compose up -d
```

**Terminal 2: Backend & Worker**

```bash
cd BE
.venv\Scripts\activate
# Run API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Run Worker (New Terminal)
celery -A app.config worker --pool=solo --loglevel=info
```

**Terminal 3: Frontend**

```bash
cd FE_React
pnpm dev
```

### Option 2: Windows Shortcut

1.  Ensure Docker is running (`docker compose up -d`).
2.  Run `run_dev.bat` in the root folder (Starts API & Celery).
3.  Run `pnpm dev` in the Frontend folder.

---

## 🔗 Access Points

| Service                          | URL                                                                | Default Creds               |
| :------------------------------- | :----------------------------------------------------------------- | :-------------------------- |
| **Frontend UI**                  | [http://localhost:3000](http://localhost:3000)                     | -                           |
| **Backend API Docs**             | [http://localhost:8000/docs](http://localhost:8000/docs)           | -                           |
| **MinIO Console** (Storage)      | [http://localhost:9001](http://localhost:9001)                     | `minioadmin` / `minioadmin` |
| **RabbitMQ** (Queue)             | [http://localhost:15672](http://localhost:15672)                   | `guest` / `guest`           |

---

## 📂 Project Structure

- `BE/`: FastAPI Backend.
  - `app/`: Core logic (Routers, Services).
  - `main.py`: Entry point.
- `FE_React/`: Next.js Frontend.
- `docker-compose.yml`: Infrastructure definition.
