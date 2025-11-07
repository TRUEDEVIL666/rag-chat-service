# RAG Chatbot Project

This project provides a framework for building and configuring a Retrieval-Augmented Generation (RAG) chatbot.

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

You need to have Docker installed and running. The following services are required:

* Redis (`redis-stack`)
* Qdrant (`qdrant/qdrant`)
* MinIO (`minio/minio`)
* RabbitMQ (`rabbitmq`)

Ensure these containers are running before proceeding.

### Installation

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

2. **Activate the environment:**
   ```bash
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install .
   ```

## Running the Project

1. **Start the application services:**

   > **Note:** You will need two separate terminals running concurrently.

    * **Terminal 1: Main Application**
      ```bash
      python -m main
      ```

    * **Terminal 2: Celery Worker**
      ```bash
      celery -A app.config worker --pool=solo --loglevel=info
      ```

2. **Access the API:**

   Once everything is running, you can access the API documentation and test the CRUD functions
   at [http://localhost:8000/docs](http://localhost:8000/docs).
