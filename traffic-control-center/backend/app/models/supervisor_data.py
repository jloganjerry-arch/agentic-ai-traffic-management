"""
Supervisor Data Contract for Phase 7 (Traffic Supervisor Agent).
Defines policy governance verdicts and granular rule check diagnostics.
Strictly distinct from physical safety validation.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.traffic_data import SignalPhase


class SupervisorDecisionStatus(str, Enum):
    """Verdicts rendered by the Policy Supervisor Agent."""
    APPROVED = "APPROVED"      # Satisfies all regulatory and fairness policies
    MODIFIED = "MODIFIED"      # Acceptable but adjusted (e.g., truncated extension) to fit policy
    OVERRULED = "OVERRULED"    # Violates an essential policy and cannot proceed as requested


class PolicyRuleCheck(BaseModel):
    """
    Granular diagnostic output for an individual policy rule.
    Exposed for dashboard explainability (PASS/FAIL indicators).
    """
    rule_name: str = Field(..., description="Name of the evaluated policy rule")
    passed: bool = Field(..., description="True if the policy check passed, False if violated")
    limit_value: float = Field(..., description="Configured policy limit threshold")
    observed_value: float = Field(..., description="Observed operational measurement")
    detail: str = Field(..., description="Human-readable explanation of the check outcome")


class SupervisorDecision(BaseModel):
    """
    Authoritative policy governance verdict from Agent 4 (Supervisor).
    Answers: 'IS THIS RECOMMENDATION ALLOWED BY POLICY?'
    Forwarded to the downstream Safety Agent (Agent 5).
    """
    junction_id: str = Field(..., description="Physical junction identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Verdict timestamp")
    data_source: str = Field("TEST_SIMULATION", description="Preserved data source label")
    status: SupervisorDecisionStatus = Field(..., description="Policy verdict: APPROVED, MODIFIED, or OVERRULED")
    authorized_phase: SignalPhase = Field(..., description="Policy-authorized target signal phase")
    authorized_duration_s: float = Field(..., ge=0.0, description="Policy-authorized phase duration in seconds")
    authorized_extension_s: float = Field(0.0, ge=0.0, description="Policy-authorized extension in seconds")
    policy_checks: List[PolicyRuleCheck] = Field(default_factory=list, description="Granular audit of all evaluated policy rules")
    policy_rationale: str = Field(..., description="Explainable justification of the supervisor verdict")
    forward_to_safety_agent: bool = Field(..., description="True if decision is authorized to proceed to the Safety Agent")
