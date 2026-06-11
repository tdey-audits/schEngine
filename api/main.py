import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NCERT Math Engine starting up...")
    yield
    logger.info("NCERT Math Engine shutting down...")


app = FastAPI(
    title="NCERT Class 10 Math Question Generator",
    description="RAG + Knowledge Graph powered CBSE Class 10 Math question generation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "service": "NCERT Math Engine",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "chapters": "/api/v1/chapters",
        "question_types": "/api/v1/question-types",
        "generate": "/api/v1/generate",
    }


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
