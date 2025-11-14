@echo off
cd BE
call .venv\Scripts\activate

echo Starting FastAPI application...
start cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo Starting Celery worker...
start cmd /k "celery -A app.config.celery worker --loglevel=info -P solo"

cd ..
echo Starting Frontend application...
cd FE
start cmd /k "pnpm dev"

echo All services are starting in separate windows.
