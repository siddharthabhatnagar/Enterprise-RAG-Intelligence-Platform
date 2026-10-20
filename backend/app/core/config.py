import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "Enterprise RAG Intelligence Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Groq Model Configuration
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_FALLBACK_MODEL: str = "llama-3.3-70b-versatile"

    # NVIDIA Embeddings Configuration
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_EMBED_MODEL: str = "baai/bge-m3"
    NVIDIA_FALLBACK_MODEL: str = "nvidia/llama-nemotron-embed-1b-v2"

    # Vector Store & Paths
    FAISS_INDEX_PATH: str = str(BASE_DIR / "backend" / "data" / "vector_index")
    UPLOAD_DIR: str = str(BASE_DIR / "backend" / "data" / "uploads")

    # Retrieval & Guardrails
    TOP_K_RETRIEVAL: int = 10
    TOP_N_RERANK: int = 4
    MIN_RELEVANCE_SCORE: float = 0.25

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    def ensure_directories(self):
        """Ensure necessary storage directories exist."""
        os.makedirs(self.FAISS_INDEX_PATH, exist_ok=True)
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

settings = Settings()
settings.ensure_directories()
