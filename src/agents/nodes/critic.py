import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.agents.schemas import CriticVerification
from src.agents.state import ComplianceState
from src.config import get_settings

logger = logging.getLogger("aegis.critic")
settings = get_settings()

SYSTEM_PROMPT = (
    "You are an enterprise Legal Quality Control Inspector evaluating an auditor's findings.\n\n"
    "Enforce these criteria strictly:\n"
    "1. Did the auditor flag synonyms (e.g., 'ensure' vs 'comply') as non-compliance? -> If yes, fail.\n"
    "2. Is every finding explicitly supported by context citations? -> If missing citations, fail.\n"
    "3. Are there any fabrications or claims not present in the reference documents? -> If found, fail.\n"
    "4. If the analysis is accurate, well-grounded, and free of superficial nitpicking, pass."
)


def critic_node(state: ComplianceState) -> dict:
    """
    Evaluates the quality, citation grounding, and fidelity of the auditor findings
    against the raw extracted source contexts.
    """
    current_retry = state.get("retry_count", 0)
    current_step = state.get("current_step", 0)
    
    logger.info("Executing NODE 4 (Critic Guardrail) | Step Index: %s | Active Retry Index: %s", current_step, current_retry)

    findings = state.get("current_findings", [])
    if not findings:
        logger.warning("No findings present in the current execution state buffer.")
        return {
            "critic_feedback": "Empty findings state. Re-evaluate contexts and generate structured entries.",
            "verification_passed": False,
            "retry_count": current_retry + 1
        }

    try:
        # Initialize Local Inference Runtime with Structured Output Enforcements
        llm = ChatOllama(base_url=settings.OLLAMA_BASE_URL, model=settings.LOCAL_LLM_MODEL, temperature=0.0)
        structured_llm = llm.with_structured_output(CriticVerification)

        # Format Reference and Candidate Artifact Datasets
        context_str = "\n".join(
            f"- {c['text']} (Source: {c['metadata'].get('source', 'Unknown File')})" 
            for c in state.get("current_context", [])
        )
        findings_str = "\n".join(
            f"- [{f.finding_status.value}] {f.parameter}: {f.analysis} (Source Citation: {f.source})" 
            for f in findings
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "Raw Source Context Matrix:\n{contexts}\n\nProposed Auditor Findings:\n{findings}"),
        ])

        chain = prompt | structured_llm
        result: CriticVerification = chain.invoke({"contexts": context_str, "findings": findings_str})
        
        passed = result.passed
        feedback = result.feedback
        logger.info("Critic Node execution evaluation complete. Result Verdict passed status: %s", passed)

    except Exception as exc:
        logger.error("Structured generation exception caught within the Critic pipeline: %s", exc, exc_info=True)
        passed = False
        feedback = f"Automated structural fallback triggered due to internal processing error: {str(exc)}"

    return {
        "critic_feedback": feedback,
        "verification_passed": passed,
        "retry_count": current_retry if passed else current_retry + 1
    }