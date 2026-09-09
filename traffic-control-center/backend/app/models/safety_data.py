"""
Safety Data Contract for Phase 8 (Traffic Safety Agent).
Defines physical clearance checks, dilemma-zone evaluations, mutual-exclusion safeguards,
and deterministic execution sequences.
Strictly an analytical prototype safety decision model. Does NOT claim real-world accident prevention.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.traffic_data import SignalPhase


class SafetyStatus(str, Enum):
    """Authoritative safety statuses rendered by the Safety Agent."""
    SAFE_TO_EXECUTE = "SAFE_TO_EXECUTE"
    HOLD_CURRENT_PHASE = "HOLD_CURRENT_PHASE"
    EMERGENCY_CLEARANCE_REQUIRED = "EMERGENCY_CLEARANCE_REQUIRED"


class PhaseTransitionStep(BaseModel):
    """
    A single deterministic step in an approved physical signal transition sequence.
    Executed by the Python Signal Controller.
    """
    phase: SignalPhase = Field(..., description="Signal phase to actuate")
    duration_s: float = Field(..., ge=0.0, description="Duration in seconds for this step")
    purpose: str = Field(..., description="Role of step (e.g. YELLOW_CLEARANCE, ALL_RED_CLEARANCE, TARGET_GREEN)")


class SafetyCheckResult(BaseModel):
    """
    Granular diagnostic output for an individual physical safety check.
    Exposed for dashboard explainability.
    """
    check_name: str = Field(..., description="Name of the safety check (e.g. DILEMMA_ZONE, MUTUAL_EXCLUSION)")
    passed: bool = Field(..., description="True if the physical clearance check passed, False if hazardous")
    observed_value: float = Field(..., description="Measured physical observation (e.g. distance, speed, occupancy)")
    safe_threshold: float = Field(..., description="Calculated safe threshold")
    detail: str = Field(..., description="Explainable diagnostic detail")


class SafetyVerdict(BaseModel):
    """
    Authoritative safety verdict produced by the Safety Agent (Agent 5).
    Answers: 'IS IT SAFE TO PERFORM THIS TRANSITION RIGHT NOW?'
    Forwarded to the Python Signal Controller for physical actuation.
    """
    junction_id: str = Field(..., description="Junction identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Verdict timestamp")
    data_source: str = Field("TEST_SIMULATION", description="Preserved data source label")
    status: SafetyStatus = Field(..., description="Safety status: SAFE_TO_EXECUTE, HOLD_CURRENT_PHASE, EMERGENCY_CLEARANCE_REQUIRED")
    is_safe: bool = Field(..., description="True if transition is cleared to execute; False if held or in emergency")
    execution_sequence: List[PhaseTransitionStep] = Field(default_factory=list, description="Ordered physical clearance steps for Signal Controller")
    safety_checks: List[SafetyCheckResult] = Field(default_factory=list, description="Granular audit of all evaluated safety rules")
    safety_rationale: str = Field(..., description="Explainable justification of the safety verdict")
    prototype_disclaimer: str = Field(
        "Analytical prototype safety decision model. Does not claim real-world accident prevention.",
        description="Explicit limitation disclaimer"
    )
