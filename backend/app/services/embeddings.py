from typing import List, Dict, Any, Optional
from langchain_core.embeddings import Embeddings
from backend.app.core.config import settings
from backend.app.core.logger import logger

class FastEmbedFallback(Embeddings):
    """
    High-speed, zero-cost on-device embedding fallback using fastembed (BGE-small-en).
    Used if NVIDIA API key is not configured, expired, or for offline evaluation.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name=model_name)
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings_gen = self.model.embed(texts)
        return [arr.tolist() for arr in embeddings_gen]

    def embed_query(self, text: str) -> List[float]:
        embeddings_gen = self.model.query_embed([text])
        return list(embeddings_gen)[0].tolist()

class ResilientNVIDIAEmbeddings(Embeddings):
    """
    Robust embedding wrapper with automatic multi-tier fallback.
    Tries primary NVIDIA model -> fallback NVIDIA model -> FastEmbed local on-device.
    """
    def __init__(self, primary_model: str, api_key: str):
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
        self.primary_model = primary_model
        self.api_key = api_key
        self.current_model = primary_model
        self._active_embedder = NVIDIAEmbeddings(model=primary_model, api_key=api_key)
        self._fallback_embedder: Optional[FastEmbedFallback] = None

    def _get_fallback_embedder(self) -> FastEmbedFallback:
        if self._fallback_embedder is None:
            self._fallback_embedder = FastEmbedFallback()
        return self._fallback_embedder

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Tier 1: Try current NVIDIA model
        try:
            return self._active_embedder.embed_documents(texts)
        except Exception as e:
            err_msg = str(e).lower()
            logger.warning(f"NVIDIA Embeddings failed with {self.current_model}: {e}")

            # Tier 2: If model was 410 Gone / deprecated / not found, try baai/bge-m3 or nemotron
            if "end of life" in err_msg or "410" in err_msg or "not found" in err_msg or "404" in err_msg:
                fallback_models = ["baai/bge-m3", "nvidia/llama-nemotron-embed-1b-v2"]
                for alt_model in fallback_models:
                    if alt_model != self.current_model:
                        try:
                            from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
                            logger.info(f"Switching NVIDIA embedding model to active alternative: {alt_model}")
                            self._active_embedder = NVIDIAEmbeddings(model=alt_model, api_key=self.api_key)
                            self.current_model = alt_model
                            return self._active_embedder.embed_documents(texts)
                        except Exception as alt_err:
                            logger.warning(f"Alternative model {alt_model} also failed: {alt_err}")

            # Tier 3: Failover to local FastEmbed so the user's PDF ingestion NEVER crashes
            logger.warning("Failing over to FastEmbed on-device local embeddings...")
            return self._get_fallback_embedder().embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        try:
            return self._active_embedder.embed_query(text)
        except Exception as e:
            err_msg = str(e).lower()
            logger.warning(f"NVIDIA EmbedQuery failed with {self.current_model}: {e}")

            if "end of life" in err_msg or "410" in err_msg or "not found" in err_msg or "404" in err_msg:
                fallback_models = ["baai/bge-m3", "nvidia/llama-nemotron-embed-1b-v2"]
                for alt_model in fallback_models:
                    if alt_model != self.current_model:
                        try:
                            from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
                            self._active_embedder = NVIDIAEmbeddings(model=alt_model, api_key=self.api_key)
                            self.current_model = alt_model
                            return self._active_embedder.embed_query(text)
                        except Exception:
                            pass

            return self._get_fallback_embedder().embed_query(text)

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
                # Sanitize model name if obsolete model was specified in older env
                model_name = settings.NVIDIA_EMBED_MODEL
                if "nv-embedqa-e5-v5" in model_name:
                    model_name = "baai/bge-m3"

                logger.info(f"Initializing Resilient NVIDIA Embeddings with model: {model_name}")
                cls._instance = ResilientNVIDIAEmbeddings(
                    primary_model=model_name,
                    api_key=settings.NVIDIA_API_KEY
                )
                cls._provider_info = f"NVIDIA NIM ({model_name})"
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
