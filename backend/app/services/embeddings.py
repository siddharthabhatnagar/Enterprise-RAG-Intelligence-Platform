from typing import List, Dict, Any, Optional
from langchain_core.embeddings import Embeddings
from backend.app.core.config import settings
from backend.app.core.logger import logger

class FastEmbedFallback(Embeddings):
    """
    High-speed, zero-cost on-device embedding fallback using fastembed (BGE-small-en).
    Used if NVIDIA API key is not yet configured or for offline evaluation.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name)
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # FastEmbed returns a generator of numpy arrays
        embeddings_gen = self.model.embed(texts)
        return [arr.tolist() for arr in embeddings_gen]

    def embed_query(self, text: str) -> List[float]:
        embeddings_gen = self.model.query_embed([text])
        return list(embeddings_gen)[0].tolist()

class EmbeddingService:
    _instance: Optional[Embeddings] = None
    _provider_info: str = "Uninitialized"

    @classmethod
    def is_nvidia_key_valid(cls) -> bool:
        key = settings.NVIDIA_API_KEY
        if not key or key.strip() == "" or "your_nvidia_api_key" in key:
            return False
        return True

    @classmethod
    def get_embeddings(cls) -> Embeddings:
        """Returns the configured NVIDIA Embeddings model, or a local fallback if key is missing."""
        if cls._instance is not None:
            return cls._instance

        if cls.is_nvidia_key_valid():
            try:
                from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
                logger.info(f"Initializing NVIDIA Embeddings with model: {settings.NVIDIA_EMBED_MODEL}")
                cls._instance = NVIDIAEmbeddings(
                    model=settings.NVIDIA_EMBED_MODEL,
                    api_key=settings.NVIDIA_API_KEY
                )
                cls._provider_info = f"NVIDIA NIM ({settings.NVIDIA_EMBED_MODEL})"
                return cls._instance
            except Exception as e:
                logger.warning(f"Failed to initialize NVIDIA Embeddings ({str(e)}). Falling back to FastEmbed.")

        logger.info("NVIDIA API Key not provided or invalid. Engaging FastEmbed (BAAI/bge-small-en-v1.5) fallback.")
        cls._instance = FastEmbedFallback()
        cls._provider_info = "FastEmbed Local (BAAI/bge-small-en-v1.5) [Fallback]"
        return cls._instance

    @classmethod
    def get_provider_info(cls) -> Dict[str, Any]:
        cls.get_embeddings()
        return {
            "provider": cls._provider_info,
            "is_nvidia_active": cls.is_nvidia_key_valid(),
            "configured_model": settings.NVIDIA_EMBED_MODEL
        }
