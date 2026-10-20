from typing import Dict, Any
from fastapi import APIRouter
from backend.app.services.vector_store import vector_store_service
from backend.app.core.config import settings
from backend.app.services.embeddings import EmbeddingService

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Health"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_system_analytics():
    """Returns platform metrics, vector store health, and active model providers."""
    stats = vector_store_service.get_stats()
    stats["model_config"] = {
        "groq_model": settings.GROQ_MODEL,
        "is_groq_active": bool(settings.GROQ_API_KEY and "your_groq_api_key" not in settings.GROQ_API_KEY),
        "nvidia_embed_model": settings.NVIDIA_EMBED_MODEL,
        "is_nvidia_active": EmbeddingService.is_nvidia_key_valid(),
        "top_k_retrieval": settings.TOP_K_RETRIEVAL,
        "top_n_rerank": settings.TOP_N_RERANK
    }
    stats["environment"] = settings.ENVIRONMENT
    stats["version"] = settings.VERSION
    return stats
