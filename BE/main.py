from fastapi import FastAPI
from app.api import router as api_router
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from app.config.config import settings
import warnings
from pydantic.warnings import UnsupportedFieldAttributeWarning
from fastapi_limiter import FastAPILimiter

# Suppress "UnsupportedFieldAttributeWarning" from libraries (e.g. llama_index)
warnings.filterwarnings("ignore", category=UnsupportedFieldAttributeWarning)


@asynccontextmanager
async def lifespan(app: FastAPI):
  # Initialize Redis for Caching
  redis_url = settings.REDIS_BACKEND or "redis://localhost:6379/0"
  redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=False)
  FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
  await FastAPILimiter.init(redis)
  yield


app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api")


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allowed origins
    allow_credentials=True,  # if you send cookies / auth headers
    allow_methods=["*"],  # allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # allow all headers
)

if __name__ == "__main__":
  uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
