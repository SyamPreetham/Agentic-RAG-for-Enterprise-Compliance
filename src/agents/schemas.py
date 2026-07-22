"""
Structured-output schemas shared by every LLM-facing node.

The original implementation had the Auditor and Critic communicate via raw
markdown/string tokens (e.g. "VERIFICATION: PASSED" substring matching), which
is fragile: any deviation in the model's phrasing silently breaks the router.
Every node here binds its LLM call to one of these schemas via
`.with_structured_output(...)`, so downstream code works with typed Python
objects instead of parsing prose.
"""
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    COMPLIANT = "COMPLIANT_ALIGNMENT"
    NON_COMPLIANT = "NON_COMPLIANCE"
    CONTEXT_OMISSION = "CONTEXT_OMISSION"


class ComplianceFinding(BaseModel):
    parameter: str = Field(..., description="The clause, obligation, or parameter under review.")
    finding_status: FindingStatus = Field(..., description="The compliance verdict for this parameter.")
    analysis: str = Field(
        ...,
        description=(
            "Factual, source-anchored explanation. Do not flag synonymous wording "
            "(e.g. 'comply with' vs 'align with') as a contradiction."
        ),
    )
    source: str = Field(..., description="Exact source filename this finding was derived from, taken verbatim from the provided context.")


class AuditorOutput(BaseModel):
    findings: List[ComplianceFinding] = Field(default_factory=list)


class CriticVerification(BaseModel):
    passed: bool = Field(
        ...,
        description=(
            "True only if every finding is factually grounded in the provided context, cites a real "
            "source, and does not treat synonymous phrasing as a contradiction."
        ),
    )
    issues: List[str] = Field(default_factory=list, description="Specific, itemized problems. Empty if passed.")
    feedback: str = Field(..., description="Actionable correction instructions for the next attempt, or 'No issues found.' if passed.")


class AuditPlan(BaseModel):
    sub_queries: List[str] = Field(
        ..., description="2 to 4 independent, specific semantic search strings targeting conflicts, clauses, timelines, or limitations."
    )
