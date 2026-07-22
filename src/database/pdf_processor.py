import logging
import uuid
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http import models

from src.config import get_settings
from src.database.qdrant_wrapper import get_db_client
from src.database.vectorizer import get_embedding_engine

logger = logging.getLogger("aegis.pdf_processor")
settings = get_settings()


def _validate_dim(vector: List[float]) -> List[float]:
    if len(vector) != settings.EMBEDDING_DIM:
        raise RuntimeError(
            f"Embedding model returned {len(vector)} dims, expected {settings.EMBEDDING_DIM}. "
            "Update EMBEDDING_DIM (and recreate the Qdrant collection) to match your embedding model."
        )
    return vector


def ingest_pdf_to_qdrant(file_path: str, document_name: str, jurisdiction: str, execution_year: int) -> None:
    """Parses a multi-page PDF, splits it semantically, embeds, and upserts into Qdrant with page metadata."""
    logger.info("Extracting PDF: %s", file_path)

    loader = PyPDFLoader(file_path)
    pages = loader.load()
    logger.info("Extracted %s pages.", len(pages))

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = text_splitter.split_documents(pages)
    logger.info("Split into %s vector chunks.", len(chunks))

    client = get_db_client()
    embeddings = get_embedding_engine()
    collection_name = settings.COMPLIANCE_COLLECTION_NAME

    points = []
    for idx, chunk in enumerate(chunks):
        vector = _validate_dim(embeddings.embed_query(chunk.page_content))
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk.page_content,
                    "metadata": {
                        "source": document_name,
                        "jurisdiction": jurisdiction,
                        "year": execution_year,
                        "page_number": chunk.metadata.get("page", 0) + 1,
                        "chunk_index": idx,
                    },
                },
            )
        )

    if points:
        client.upsert(collection_name=collection_name, points=points)
    logger.info("Uploaded %s PDF vector chunks.", len(points))
