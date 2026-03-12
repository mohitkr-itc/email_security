"""
Decision Engine for the Agentic Email Security System.

Aggregates outputs from all agents and makes the final threat determination.
"""

from typing import Any

from services.logging_service import get_service_logger

logger = get_service_logger("decision_engine")


def make_decision(agent_results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate agent results and produce a final threat decision.

    Args:
        agent_results: List of standardized agent result dictionaries.

    Returns:
        Final decision with overall risk score, verdict, and recommended actions.
    """
    logger.info("Making decision", agent_count=len(agent_results))

    # Placeholder – decision logic will be implemented in later phases
    decision = {
        "overall_risk_score": 0.0,
        "verdict": "unknown",
        "recommended_actions": [],
        "agent_results": agent_results,
    }

    logger.info("Decision made", verdict=decision["verdict"])
    return decision
