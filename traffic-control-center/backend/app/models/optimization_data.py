"""
Optimization Data Contract for Phase 6 (Traffic Optimization Agent).
Strictly advisory recommendations. Does NOT claim safety or authorize hardware actuation.
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.traffic_data import SignalPhase


class OptimizationAction(str, Enum):
    """Advisory action recommended by the Optimization Agent."""
    EXTEND_GREEN = "EXTEND_GREEN"
    SWITCH_PHASE = "SWITCH_PHASE"
    MAINTAIN_CURRENT = "MAINTAIN_CURRENT"


class RecommendationUrgency(str, Enum):
    """Priority level of the recommendation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OptimizationRationale(BaseModel):
    """
    Explainable justification for the recommendation.
    Explicitly clarifies that optimization is distinct from safety approval.
    """
    primary_factor: str = Field(..., description="Key driving factor (e.g., PLATOON_CONTINUITY, QUEUE_DISSIPATION, NOMINAL_CYCLE)")
    reasoning: str = Field(..., description="Explainable description of why this recommendation optimizes traffic flow")
    safety_disclaimer: str = Field(
        "Advisory recommendation only. Must be validated by Supervisor Agent (policy/fairness) and Safety Agent (clearance/conflicts) prior to actuation.",
        description="Explicit separation of optimization and safety approval"
    )
    metrics_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Snapshot of driving metrics at decision time")


class OptimizationRecommendation(BaseModel):
    """
    Output of the Traffic Optimization Agent (Agent 3).
    Formulates 'WHAT SHOULD WE DO?' without claiming 'THIS IS SAFE'.
    """
    junction_id: str = Field(..., description="Junction identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Recommendation timestamp")
    data_source: str = Field(..., description="Preserved data source label (e.g. TEST_SIMULATION)")
    action: OptimizationAction = Field(..., description="Recommended optimization action")
    target_phase: SignalPhase = Field(..., description="Target signal phase (e.g., NS_GREEN or EW_GREEN)")
    recommended_duration_s: float = Field(..., ge=0.0, description="Recommended phase duration in seconds")
    extension_seconds: float = Field(0.0, ge=0.0, description="Additional green seconds if action is EXTEND_GREEN")
    urgency: RecommendationUrgency = Field(..., description="Optimization urgency level")
    rationale: OptimizationRationale = Field(..., description="Structured explainable rationale")
