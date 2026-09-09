"""
Pipeline Data Models for Phase 9 (End-to-End Multi-Agent Integration).
Encapsulates complete audit logging and serialized state across all 5 agents and the actuator.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.traffic_data import SignalPhase, JunctionTrafficState
from app.models.analysis_data import JunctionAnalysisState
from app.models.optimization_data import OptimizationRecommendation
from app.models.supervisor_data import SupervisorDecision
from app.models.safety_data import SafetyVerdict, PhaseTransitionStep


class PipelineExecutionResult(BaseModel):
    """
    Comprehensive unified snapshot produced at every step of the intelligent pipeline.
    Preserves audit trails across all 5 intelligent agents and the Signal Controller.
    """
    step_id: int = Field(..., description="Monotonically increasing step counter")
    timestamp: datetime = Field(default_factory=datetime.now, description="Execution step timestamp")
    data_source: str = Field("TEST_SIMULATION", description="Preserved data source label")
    junction_id: str = Field("JUNCTION-01", description="Junction identifier")

    active_phase_before: SignalPhase = Field(..., description="Active phase at the beginning of the step")
    active_phase_after: SignalPhase = Field(..., description="Active phase at the conclusion of the step")
    elapsed_green_s: float = Field(..., ge=0.0, description="Cumulative seconds elapsed on the active corridor")
    consecutive_extensions: int = Field(..., ge=0, description="Consecutive extensions granted during this green cycle")
    opposing_red_wait_s: float = Field(..., ge=0.0, description="Total red waiting time accumulated by opposing traffic")

    # Outputs of all 5 intelligent agents
    monitoring: JunctionTrafficState = Field(..., description="Stage 1: Observation & telemetry measurements")
    analysis: JunctionAnalysisState = Field(..., description="Stage 2: Diagnostics, JCI, and platoon analytics")
    optimization: OptimizationRecommendation = Field(..., description="Stage 3: Flow optimization recommendation")
    supervisor: SupervisorDecision = Field(..., description="Stage 4: Policy & fairness validation")
    safety: SafetyVerdict = Field(..., description="Stage 5: Physical clearance & safety verdict")

    # Authoritative Actuation Output (Signal Controller)
    actuation_dispatched: bool = Field(..., description="True if a signal transition or extension was dispatched to the controller")
    dispatched_sequence: List[PhaseTransitionStep] = Field(default_factory=list, description="Ordered physical steps dispatched to the controller")
    final_action_summary: str = Field(..., description="Human-readable audit summary of the step outcome")
