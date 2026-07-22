import asyncio
import logging
import os
import shutil
import uuid
from tempfile import NamedTemporaryFile

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.agents.graph import build_compliance_graph
from src.agents.state import ComplianceState
from src.config import get_settings
from src.database.pdf_processor import ingest_pdf_to_qdrant

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("aegis.api")
settings = get_settings()

app = FastAPI(
    title="Aegis Compliance Engine API",
    description="Production-grade multi-agent compliance audit RAG core.",
    version="2.0.0",
)

# Explicit allow-list instead of "*" — browsers reject wildcard origins combined
# with allow_credentials=True anyway, and "*" is not appropriate once this is
# reachable from anywhere but localhost. Configure via ALLOWED_ORIGINS env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile the graph once at process start rather than per-request.
_compiled_graph = build_compliance_graph()


class AuditRequest(BaseModel):
    raw_query: str = Field(..., description="The high-level compliance requirement or audit objective.")
    jurisdiction: str = Field(..., description="Target geographical or legal framework domain.")
    document_type: str = Field(..., description="The classification of target agreements to audit.")
    execution_year: int = Field(2026, description="The relevant statutory evaluation checkpoint year.")
    max_retries: int = Field(default=settings.MAX_AUDIT_RETRIES, ge=0, le=5)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def _cleanup_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as exc:
        logger.warning("Non-critical cleanup failure for %s: %s", path, exc)


@app.post("/api/v1/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    jurisdiction: str = Form(...),
    execution_year: int = Form(2026),
):
    """
    Uploads and vectorizes a PDF contract into the Qdrant compliance index.
    The original codebase only exposed ingestion via a local CLI script
    (`ingest_local.py`), which meant a browser-based front end (e.g. the
    planned Streamlit app) had no way to actually add documents.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    tmp_path = None
    try:
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Offload the CPU/IO-bound ingestion pipeline so it doesn't block the event loop.
        await asyncio.to_thread(
            ingest_pdf_to_qdrant,
            file_path=tmp_path,
            document_name=file.filename,
            jurisdiction=jurisdiction,
            execution_year=execution_year,
        )
        return {"status": "ingested", "document": file.filename, "jurisdiction": jurisdiction}
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/v1/audit")
async def execute_compliance_audit(payload: AuditRequest, background_tasks: BackgroundTasks):
    """
    Triggers the multi-agent LangGraph pipeline and streams the completed PDF.

    Two fixes versus the original:
    1. The graph's `.invoke()` is synchronous and would otherwise block the
       whole FastAPI event loop for the duration of a multi-minute audit,
       stalling every other concurrent request. It now runs in a worker
       thread via `asyncio.to_thread`.
    2. Every run gets a unique `request_id`-scoped output file, so concurrent
       requests can never overwrite or serve each other's report.
    """
    request_id = uuid.uuid4().hex
    logger.info("[%s] audit request received", request_id)

    initial_state: ComplianceState = {
        "request_id": request_id,
        "raw_query": payload.raw_query,
        "contract_meta": {
            "jurisdiction": payload.jurisdiction,
            "document_type": payload.document_type,
            "execution_year": payload.execution_year,
        },
        "audit_plan": [],
        "current_step": 0,
        "retry_count": 0,
        "max_retries": payload.max_retries,
        "current_context": [],
        "retrieved_contexts": [],
        "current_findings": [],
        "validated_drafts": [],
        "critic_feedback": None,
        "verification_passed": False,
        "final_compliance_report": {},
    }

    try:
        final_state = await asyncio.to_thread(_compiled_graph.invoke, initial_state)
    except Exception as exc:
        logger.error("[%s] graph execution crashed: %s", request_id, exc)
        raise HTTPException(status_code=500, detail=f"Aegis graph execution error: {exc}")

    report = final_state.get("final_compliance_report", {})
    file_path = report.get("generated_file_path")

    if not file_path or not os.path.exists(file_path):
        logger.error("[%s] report generation failed: %s", request_id, report.get("generation_error"))
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {report.get('generation_error', 'unknown error')}",
        )

    background_tasks.add_task(_cleanup_file, file_path)
    logger.info("[%s] audit complete, streaming %s", request_id, file_path)

    return FileResponse(path=file_path, media_type="application/pdf", filename=os.path.basename(file_path))
