import logging
from src.agents.state import ComplianceState

logger = logging.getLogger("aegis.finalize")


def finalize_step_node(state: ComplianceState) -> dict:
    """
    Flushes verified intermediate execution buffers into historical logs,
    increments the system task index, and clears tracking states for the next loop.
    """
    current_idx = state.get("current_step", 0)
    logger.info("Executing NODE 5 (State Finalizer Matrix) | Committing task slice index: %s", current_idx)

    # 1. Thread-safe extraction of historical trace metrics
    current_findings = state.get("current_findings", [])
    validated_drafts = list(state.get("validated_drafts", []))

    # 2. Flush current working data layer directly to the database master ledger pool
    if current_findings:
        validated_drafts.extend(current_findings)
        logger.info("Successfully committed %s findings directly into the master ledger store.", len(current_findings))
    else:
        logger.warning("Finalization step triggered with no active findings inside the state frame buffer.")

    # 3. Compile fresh configuration map to shift graph scope smoothly
    return {
        "validated_drafts": validated_drafts,
        "current_step": current_idx + 1,
        "retry_count": 0,               # Reset loop tracking completely for next task item
        "current_findings": [],         # Flush buffer clear
        "critic_feedback": None,        # Flush feedback clear
        "verification_passed": False    # Clear loop gate condition flag
    }