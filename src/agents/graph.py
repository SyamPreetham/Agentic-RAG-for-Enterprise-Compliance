import logging
from langgraph.graph import END, StateGraph

from src.agents.nodes.auditor import auditor_node
from src.agents.nodes.critic import critic_node
from src.agents.nodes.finalize import finalize_step_node
from src.agents.nodes.planner import planner_node
from src.agents.nodes.report_generator import report_generator_node
from src.agents.nodes.retrieval import retrieval_node
from src.agents.state import ComplianceState

logger = logging.getLogger("aegis.graph")


def route_after_critic(state: ComplianceState) -> str:
    """
    Evaluates the current state metrics to determine if the active sub-query
    requires an execution retry loop or should advance to step finalization.
    """
    if state.get("verification_passed", False):
        logger.info("[ROUTER] Critic validation passed -> Proceeding to finalize_step.")
        return "finalize_step"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if retry_count >= max_retries:
        logger.warning(
            "[ROUTER] Max retries exhausted (%s/%s) for current task -> Forcing progression to finalize_step.",
            retry_count,
            max_retries
        )
        return "finalize_step"

    logger.info(
        "[ROUTER] Critic validation failed (%s/%s retries used) -> Directing retry loop back to Auditor.",
        retry_count,
        max_retries
    )
    return "retry_audit"


def route_after_finalize(state: ComplianceState) -> str:
    """
    Evaluates whether the graph has exhausted all planned compliance 
    sub-queries or needs to loop back to retrieval for the next index slice.
    """
    current_step = state.get("current_step", 0)
    audit_plan = state.get("audit_plan", [])

    logger.info("[ROUTER] Step Evaluation: index %s of %s total tasks.", current_step, len(audit_plan))

    if current_step < len(audit_plan):
        return "retrieve"
    
    logger.info("[ROUTER] All audit plan items processed -> Moving to final report generation.")
    return "generate_report"


def build_compliance_graph():
    """
    Assembles a production-grade 6-node deterministic directed state graph layout.
    """
    try:
        workflow = StateGraph(ComplianceState)

        # Register Production Execution Workers
        workflow.add_node("planner", planner_node)
        workflow.add_node("retrieve", retrieval_node)
        workflow.add_node("auditor", auditor_node)
        workflow.add_node("critic", critic_node)
        workflow.add_node("finalize_step", finalize_step_node)
        workflow.add_node("generate_report", report_generator_node)

        # Set Static Execution Paths
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "retrieve")
        workflow.add_edge("retrieve", "auditor")
        workflow.add_edge("auditor", "critic")

        # Set Conditional Core Loop Boundaries
        workflow.add_conditional_edges(
            "critic",
            route_after_critic,
            {
                "retry_audit": "auditor", 
                "finalize_step": "finalize_step"
            },
        )

        workflow.add_conditional_edges(
            "finalize_step",
            route_after_finalize,
            {
                "retrieve": "retrieve", 
                "generate_report": "generate_report"
            },
        )

        # Final Transition Path
        workflow.add_edge("generate_report", END)

        return workflow.compile()

    except Exception as exc:
        logger.critical("Critical error encountered during LangGraph compilation topology: %s", exc)
        raise RuntimeError(f"LangGraph initialization failure: {exc}") from exc