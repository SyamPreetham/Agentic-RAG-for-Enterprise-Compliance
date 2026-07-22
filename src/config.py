import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Infrastructure targets
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    COMPLIANCE_COLLECTION_NAME: str = os.getenv("COMPLIANCE_COLLECTION_NAME", "aegis_compliance_idx")

    # Local inference bindings
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "llama3.2:3b")
    LOCAL_EMBED_MODEL: str = os.getenv("LOCAL_EMBED_MODEL", "nomic-embed-text")

    # IMPORTANT: this must match the real output dimension of LOCAL_EMBED_MODEL.
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))

    # Agent loop controls
    MAX_AUDIT_RETRIES: int = int(os.getenv("MAX_AUDIT_RETRIES", "2"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "3"))

    # 🚀 FIX: Add missing properties so main.py initialization doesn't throw AttributeErrors
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
    ARTIFACTS_DIR: str = os.getenv("ARTIFACTS_DIR", "/app/artifacts")


@lru_cache()
def get_settings() -> Settings:
    return Settings()