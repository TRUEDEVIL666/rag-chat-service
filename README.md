# RAG Chatbot Project

A complete framework for building and configuring a **Retrieval-Augmented Generation (RAG)** chatbot system with FastAPI (backend) and Next.js (frontend).

---

## Getting Started — Backend (BE)

### 1. Prerequisites

Ensure the following are installed on your system:

* **Python 3.11**
* **Docker** and **Docker Compose**
* **Redis**, **Qdrant**, **MinIO**, **RabbitMQ** (auto-started via Docker)
* **Hugging Face CLI** (`pip install huggingface_hub`)
* **Celery** (`pip install celery`)

---

### 2. Environment Setup

Create a `.env` file in the backend root directory with the following variables:

```env
# ===== Security =====
secret_key="a-string-secret-at-least-256-bits-long"
algorithm=HS256

# ===== Supabase =====
supabase_url=https://ilwtdmnadioboiffqohs.supabase.co
supabase_key=

# ===== Celery =====
celery_broker=redis://localhost:6379/0
celery_backend=redis://localhost:6379/0

# ===== Embedding Service =====
embedding_api_url=http://localhost:8000/embed
embedding_model=

# ===== Qdrant Vector DB =====
qdrant_host=localhost
qdrant_port=6333
qdrant_collection=documents

# ===== MinIO Storage =====
minio_endpoint=localhost:9000
minio_access_key=minioadmin
minio_secret_key=minioadmin
```

---

### 3. Installation

Navigate to the `BE` directory:

```bash
cd BE
```

1. **Create a virtual environment**

   ```bash
   python -m venv .venv
   ```

   or using `uv`:

   ```bash
   uv venv
   ```

2. **Install dependencies**

   ```bash
   pip install .
   ```

   or using `uv`:

   ```bash
   uv pip install .
   ```

---

### 4. Start Required Services

Use Docker Compose to launch all backend dependencies:

```bash
docker compose up -d
```

This will start Redis, Qdrant, MinIO, and RabbitMQ containers in detached mode.

---

### 5. Run the Backend

You will need two terminals:

**Terminal 1 — Main Application**

```bash
.venv\Scripts\activate
python -m main
```

**Terminal 2 — Celery Worker**

```bash
.venv\Scripts\activate
celery -A app.config worker --pool=solo --loglevel=info
```

---

### 6. Access the API

Once everything is running:

* API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Getting Started — Frontend (FE)

### 1. Prerequisites

Make sure the backend (`localhost:8000`) is running.

Install Node.js 22 and **pnpm** globally if you haven’t already:

```bash
npm install -g pnpm
```

---

### 2. Environment Setup

Create a `.env` file in the frontend root directory with:

```env
# ===== Frontend =====
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```


### 3. Installation & Run

```bash
pnpm install
pnpm dev
```

The app will start at [http://localhost:3000](http://localhost:3000)


---

## Quick Commands

| Task                   | Command                                                   |
| ---------------------- | --------------------------------------------------------- |
| Start backend services | `docker compose up -d`                                    |
| Run backend API        | `python -m main`                                          |
| Run Celery worker      | `celery -A app.config worker --pool=solo --loglevel=info` |
| Run frontend           | `pnpm dev`                                                |

---

## Notes

* Ensure Redis, Qdrant, RabbitMQ, and MinIO containers are healthy before running.
* Make sure all `.env` files are correctly configured before startup.
* Hugging Face login is required for embedding models:

  ```bash
  hf auth login
  ```

---

## Access Points

| Service             | URL                                                                |
| ------------------- | ------------------------------------------------------------------ |
| Backend API Docs    | [http://localhost:8000/docs](http://localhost:8000/docs)           |
| Frontend UI         | [http://localhost:3000](http://localhost:3000)                     |
| Qdrant UI           | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) |
| MinIO Console       | [http://localhost:9001](http://localhost:9001)                     |
| RabbitMQ Management | [http://localhost:15672](http://localhost:15672)                   |

# RAG Chatbot Project

A complete framework for building and configuring a **Retrieval-Augmented Generation (RAG)** chatbot system with FastAPI (backend) and Next.js (frontend).

---

## Getting Started — Backend (BE)

### 1. Prerequisites

Ensure the following are installed on your system:

* **Python 3.11**
* **Docker** and **Docker Compose**
* **Redis**, **Qdrant**, **MinIO**, **RabbitMQ** (auto-started via Docker)
* **Hugging Face CLI** (`pip install huggingface_hub`)
* **Celery** (`pip install celery`)

---

### 2. Environment Setup

Create a `.env` file in the backend root directory with the following variables:

```env
# ===== Security =====
secret_key=a-string-secret-at-least-256-bits-long
algorithm=HS256

# ===== Supabase =====
supabase_url=https://ilwtdmnadioboiffqohs.supabase.co
supabase_key=

# ===== Celery =====
celery_broker=redis://localhost:6379/0
celery_backend=redis://localhost:6379/0

# ===== Embedding Service =====
embedding_api_url=http://localhost:8000/embed
embedding_model=

# ===== Qdrant Vector DB =====
qdrant_host=localhost
qdrant_port=6333
qdrant_collection=documents

# ===== MinIO Storage =====
minio_endpoint=localhost:9000
minio_access_key=minioadmin
minio_secret_key=minioadmin
```

---

### 3. Installation

1.  **Create a virtual environment**

    ```bash
    python -m venv .venv
    ```

2.  **Install dependencies**

    ```bash
    pip install .
    ```

    or using `uv`:

    ```bash
    uv pip install .
    ```

---

### 4. Start Required Services

Use Docker Compose to launch all backend dependencies:

```bash
docker compose up -d
```

This will start Redis, Qdrant, MinIO, and RabbitMQ containers in detached mode.

---

### 5. Run the Backend

You will need two terminals:

**Terminal 1 — Main Application**

```bash
.venv\Scripts\activate
python -m main
```

**Terminal 2 — Celery Worker**

```bash
.venv\Scripts\activate
celery -A app.config worker --pool=solo --loglevel=info
```

---

### 6. Access the API

Once everything is running:

*   API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Getting Started — Frontend (FE)

### 1. Prerequisites

Make sure the backend (`localhost:8000`) is running.

Install Node.js 22 and **pnpm** globally if you haven’t already:

```bash
npm install -g pnpm
```

---

### 2. Environment Setup

Create a `.env` file in the frontend root directory with:

```env
# ===== Frontend =====
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1

AUTH_SECRET=Meow

BLOB_READ_WRITE_TOKEN=
```

### 3. Installation & Run

```bash
pnpm install
pnpm dev
```

The app will start at [http://localhost:3000](http://localhost:3000)

---

## Quick Commands

| Task                   | Command                                                   |
| :--------------------- | :-------------------------------------------------------- |
| Start backend services | `docker compose up -d`                                    |
| Run backend API        | `python -m main`                                          |
| Run Celery worker      | `celery -A app.config worker --pool=solo --loglevel=info` |
| Run frontend           | `pnpm dev`                                                |

---

## Notes

*   Ensure Redis, Qdrant, RabbitMQ, and MinIO containers are healthy before running.
*   Make sure all `.env` files are correctly configured before startup.
*   Hugging Face login is required for embedding models:

    ```bash
    hf auth login
    ```

---

## Access Points

| Service             | URL                                                                |
| :------------------ | :----------------------------------------------------------------- |
| Backend API Docs    | [http://localhost:8000/docs](http://localhost:8000/docs)           |
| Frontend UI         | [http://localhost:3000](http://localhost:3000)                     |
| Qdrant UI           | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) |
| MinIO Console       | [http://localhost:9001](http://localhost:9001)                     |
| RabbitMQ Management | [http://localhost:15672](http://localhost:15672)                   |

---

## License

This project is licensed under the MIT License.