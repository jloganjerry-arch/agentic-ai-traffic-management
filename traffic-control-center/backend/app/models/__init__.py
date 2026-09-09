"""
Common Traffic Data, Analysis, Optimization, Supervisor, and Safety Models package.
"""

from app.models.traffic_data import (
    Direction,
    SignalPhase,
    TrafficRegime,
    SpeedTrend,
    ApproachingVehicle,
    DirectionTrafficData,
    JunctionTrafficState,
    create_test_junction_state,
)

from app.models.analysis_data import (
    CongestionCategory,
    AnalysisSpeedTrend,
    FactorContribution,
    JciFactorBreakdown,
    JunctionCongestionIndex,
    PlatoonDetail,
    DirectionAnalysis,
    JunctionAnalysisState,
)

from app.models.optimization_data import (
    OptimizationAction,
    RecommendationUrgency,
    OptimizationRationale,
    OptimizationRecommendation,
)

from app.models.supervisor_data import (
    SupervisorDecisionStatus,
    PolicyRuleCheck,
    SupervisorDecision,
)

from app.models.safety_data import (
    SafetyStatus,
    PhaseTransitionStep,
    SafetyCheckResult,
    SafetyVerdict,
)

__all__ = [
    # Traffic Data Models (Phase 2 & 3)
    "Direction",
    "SignalPhase",
    "TrafficRegime",
    "SpeedTrend",
    "ApproachingVehicle",
    "DirectionTrafficData",
    "JunctionTrafficState",
    "create_test_junction_state",
    # Analysis Models (Phase 4 & 5)
    "CongestionCategory",
    "AnalysisSpeedTrend",
    "FactorContribution",
    "JciFactorBreakdown",
    "JunctionCongestionIndex",
    "PlatoonDetail",
    "DirectionAnalysis",
    "JunctionAnalysisState",
    # Optimization Models (Phase 6)
    "OptimizationAction",
    "RecommendationUrgency",
    "OptimizationRationale",
    "OptimizationRecommendation",
    # Supervisor Models (Phase 7)
    "SupervisorDecisionStatus",
    "PolicyRuleCheck",
    "SupervisorDecision",
    # Safety Models (Phase 8)
    "SafetyStatus",
    "PhaseTransitionStep",
    "SafetyCheckResult",
    "SafetyVerdict",
]
