import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.agents.schemas import AuditorOutput
from src.agents.state import ComplianceState
from src.config import get_settings

logger = logging.getLogger("aegis.auditor")
settings = get_settings()

SYSTEM_PROMPT = (
    "You are an expert Regulatory Compliance Auditor specializing in enterprise contract gaps.\n"
    "Compare the retrieved contract excerpts against the audit objective with professional legal realism.\n\n"
    "Rules:\n"
    "1. Linguistic variance is NOT non-compliance. Clauses using different wording for the same "
    "obligation (e.g. 'comply with' vs 'align with') are semantically identical — never flag this as "
    "a discrepancy.\n"
    "2. If two clauses specify matching parameters (e.g. both a 90-day cycle), mark it COMPLIANT_ALIGNMENT.\n"
    "3. Every finding must cite its exact source filename, taken verbatim from the provided context.\n"
    "4. Never invent a clause, source, or figure that is not present in the provided context."
)


def _build_context_str(contexts: list[dict]) -> str:
    return "\n".join(f"- {c['text']} (Source: {c['metadata']['source']})" for c in contexts)


def auditor_node(state: ComplianceState) -> dict:
    """
    Node 3: Ground-Truth Legal Auditor Agent.

    Operates only on `current_context` (this sub-task's retrieval slice), and
    returns typed `ComplianceFinding` objects via `.with_structured_output()`
    instead of markdown prose the downstream nodes had to regex-parse.
    """
    logger.info(
        "NODE 3: auditor agent — step %s, retry %s",
        state.get("current_step", 0),
        state.get("retry_count", 0),
    )

    llm = ChatOllama(base_url=settings.OLLAMA_BASE_URL, model=settings.LOCAL_LLM_MODEL, temperature=0.0)
    structured_llm = llm.with_structured_output(AuditorOutput)

    feedback = state.get("critic_feedback") or "None. First attempt for this sub-task."

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "user",
                (
                    "Audit Objective:\n{raw_query}\n\n"
                    "Retrieved Contract Context (this sub-task only):\n{contexts}\n\n"
                    "Prior Quality-Control Feedback (fix every item below before responding, if any):\n{feedback}\n\n"
                    "Produce the findings for this sub-task."
                ),
            ),
        ]
    )

    context_str = _build_context_str(state.get("current_context", []))

    chain = prompt | structured_llm
    try:
        result: AuditorOutput = chain.invoke(
            {"raw_query": state["raw_query"], "contexts": context_str, "feedback": feedback}
        )
    except Exception as exc:
        logger.error("Auditor structured generation failed: %s", exc)
        result = AuditorOutput(findings=[])

    return {"current_findings": result.findings}
