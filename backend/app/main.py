"""FastAPI application entry point for the MANGOS Tech Manual Agent."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config.settings import ALLOWED_ORIGINS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title="MANGOS Tech Manual Agent",
    description=(
        "Agent-pattern RAG chatbot for commercial Azure. "
        "Hybrid Azure AI Search + Azure OpenAI, streamed SSE with structured citations."
    ),
    version="1.0.0",
)

# CORS — configurable via ALLOWED_ORIGINS env var (comma-separated).
# Defaults to "*" so local dev and Azure dev deployments work without configuration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok"}
