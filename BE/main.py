# main.py
from fastapi import FastAPI
from app.api import router as api_router
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(api_router, prefix="/api")


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",  # optional, for local testing
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
