from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings, BASE_DIR
from backend.app.core.logger import logger
from backend.app.services.vector_store import vector_store_service
from backend.app.api.routes_ingest import router as ingest_router
from backend.app.api.routes_query import router as query_router
from backend.app.api.routes_documents import router as documents_router
from backend.app.api.routes_users import router as users_router
from backend.app.api.routes_analytics import router as analytics_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Starting Enterprise RAG Intelligence Platform...")
    settings.ensure_directories()

    # Auto-seed sample documents if database is fresh
    docs = vector_store_service.list_documents()
    if not docs:
        logger.info("Vector database is empty. Auto-seeding enterprise sample documents...")
        try:
            from scripts.seed_database import seed_sample_documents
            seed_sample_documents()
        except Exception as e:
            logger.warning(f"Could not auto-seed sample docs: {e}")

    yield

    # Shutdown sequence
    logger.info("Shutting down Enterprise RAG Intelligence Platform...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise RAG Intelligence Platform with LangChain, FAISS, Groq LLM, NVIDIA Embeddings, RBAC, and Citation Verification.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(documents_router)
app.include_router(users_router)
app.include_router(analytics_router)

@app.get("/health", tags=["Health"])
async def health_check():
    """Lightweight health check endpoint for Render & Docker monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# Frontend Static Assets
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    async def serve_index():
        """Serves the main single page web application."""
        return FileResponse(frontend_dir / "index.html")
