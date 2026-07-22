import logging
from typing import List

from langchain_ollama import OllamaEmbeddings
from qdrant_client.http import models

from src.agents.state import ComplianceState
from src.config import get_settings
from src.database.qdrant_wrapper import get_db_client

logger = logging.getLogger("aegis.retrieval")
settings = get_settings()


class EmbeddingDimensionError(RuntimeError):
    """
    Raised when the embedding model's real output dimension doesn't match the
    configured Qdrant collection size.

    The original code silently truncated/zero-padded every vector to force it
    to 384 dims regardless of what the model actually produced. That is data
    corruption, not a fix: slicing an embedding in half (or padding it with
    zeros) destroys the geometry the similarity search depends on, so queries
    silently degrade instead of failing loudly. We raise instead, because a
    clear config error is far cheaper to fix than months of quietly bad
    retrieval.
    """


def _embed_query(text: str) -> List[float]:
    embeddings = OllamaEmbeddings(base_url=settings.OLLAMA_BASE_URL, model=settings.LOCAL_EMBED_MODEL)
    vector = embeddings.embed_query(text)
    if len(vector) != settings.EMBEDDING_DIM:
        raise EmbeddingDimensionError(
            f"Embedding model '{settings.LOCAL_EMBED_MODEL}' returned a {len(vector)}-dim vector, "
            f"but EMBEDDING_DIM is configured as {settings.EMBEDDING_DIM}. Set EMBEDDING_DIM to match "
            f"the model (e.g. 768 for nomic-embed-text, 384 for all-minilm) and recreate the Qdrant "
            f"collection — do not truncate or pad vectors."
        )
    return vector


def retrieval_node(state: ComplianceState) -> dict:
    """
    Node 2: Live Router & Vector Retrieval Agent.

    Returns `current_context` — the retrieval slice for THIS sub-task only —
    rather than appending onto a single ever-growing list. `retrieved_contexts`
    is still maintained as a full audit trail for the final report's citation
    section, but it is never re-fed into the LLM.
    """
    current_idx = state.get("current_step", 0)
    logger.info("NODE 2: retrieval agent — step %s", current_idx)

    meta = state["contract_meta"]
    plan = state["audit_plan"]

    if current_idx >= len(plan):
        logger.warning("current_step (%s) exceeds plan length (%s)", current_idx, len(plan))
        return {"current_context": []}

    target_query = plan[current_idx]
    logger.info("Vectorizing sub-query: %s", target_query)

    client = get_db_client()
    query_vector = _embed_query(target_query)

    payload_filter = models.Filter(
        must=[models.FieldCondition(key="metadata.jurisdiction", match=models.MatchValue(value=meta.get("jurisdiction")))]
    )

    search_results = client.query_points(
        collection_name=settings.COMPLIANCE_COLLECTION_NAME,
        query=query_vector,
        query_filter=payload_filter,
        limit=settings.RETRIEVAL_TOP_K,
    ).points

    step_context = []
    if search_results:
        for point in search_results:
            step_context.append({"text": point.payload["text"], "metadata": point.payload["metadata"]})
            logger.info("Hit: %s", point.payload["metadata"]["source"])
    else:
        logger.warning("No Qdrant matches for sub-query '%s'", target_query)
        step_context.append(
            {
                "text": "No matching clause was found in the indexed contract set for this sub-query.",
                "metadata": {"source": "System Index (no match)", "jurisdiction": meta.get("jurisdiction")},
            }
        )

    trail = list(state.get("retrieved_contexts", []))
    trail.extend(step_context)

    return {
        "current_context": step_context,
        "retrieved_contexts": trail,
    }
