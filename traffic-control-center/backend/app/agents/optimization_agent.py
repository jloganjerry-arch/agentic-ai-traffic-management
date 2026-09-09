"""
Traffic Optimization Agent (Agent 3 - Phase 6).
Responsibility: "WHAT SHOULD WE DO?"

Synthesizes measurements from the Monitoring Agent (JunctionTrafficState)
and diagnostics from the Analysis Agent (JunctionAnalysisState) to formulate
advisory signal optimization recommendations.

STRICT ARCHITECTURAL RULE:
Optimization is NOT Safety.
The Optimization Agent recommends:
    "I recommend extending North green by 7 seconds."
It must NOT conclude:
    "This is safe."
Safety validation belongs strictly to the downstream Safety Agent (Phase 8).
Policy and fairness checks belong to the Supervisor Agent (Phase 7).
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models.traffic_data import (
    Direction,
    SignalPhase,
    JunctionTrafficState,
)

from app.models.analysis_data import (
    CongestionCategory,
    JunctionAnalysisState,
)

from app.models.optimization_data import (
    OptimizationAction,
    RecommendationUrgency,
    OptimizationRationale,
    OptimizationRecommendation,
)


class TrafficOptimizationAgent:
    """
    Agent 3: Flow optimization engine.
    Answers: "WHAT SHOULD WE DO?"
    Produces advisory recommendations without claiming safety or executing hardware actuations.
    """

    # Baseline Timing Parameters
    MIN_EXTENSION_S: float = 5.0
    MAX_EXTENSION_S: float = 10.0
    DEFAULT_CYCLE_GREEN_S: float = 25.0
    MAX_GREEN_DURATION_S: float = 60.0
    MIN_GREEN_DURATION_S: float = 20.0

    def __init__(self, agent_id: str = "agent-3"):
        self.id = agent_id
        self.name = "Traffic Optimization Agent"
        self.role = "Signal Policy Recommendation & Flow Optimization"
        self.responsibility = "WHAT SHOULD WE DO?"

    # ========================================================================
    # Corridor Phase Mapping Helpers
    # ========================================================================

    @staticmethod
    def get_active_corridor_directions(phase: SignalPhase) -> List[Direction]:
        """Returns directions currently served by the active phase."""
        if phase in (SignalPhase.NS_GREEN, SignalPhase.NS_YELLOW):
            return [Direction.NORTH, Direction.SOUTH]
        elif phase in (SignalPhase.EW_GREEN, SignalPhase.EW_YELLOW):
            return [Direction.EAST, Direction.WEST]
        return []

    @staticmethod
    def get_opposing_green_phase(phase: SignalPhase) -> SignalPhase:
        """Returns the opposing green signal phase."""
        if phase in (SignalPhase.NS_GREEN, SignalPhase.NS_YELLOW):
            return SignalPhase.EW_GREEN
        return SignalPhase.NS_GREEN

    # ========================================================================
    # Master Optimization Evaluation
    # ========================================================================

    def optimize(
        self,
        monitoring_state: JunctionTrafficState,
        analysis_state: JunctionAnalysisState,
    ) -> OptimizationRecommendation:
        """
        Formulates an optimization recommendation based on traffic state and diagnostics.
        Evaluates:
          1. Platoon Continuity Extension (Priority 1)
          2. Opposing Heavy Queue Relief Switch (Priority 2)
          3. Nominal Balanced Cycling (Priority 3)
        """
        curr_phase = monitoring_state.current_signal_phase
        active_dirs = self.get_active_corridor_directions(curr_phase)
        opposing_phase = self.get_opposing_green_phase(curr_phase)

        # --------------------------------------------------------------------
        # Priority 1: Platoon Continuity Extension
        # --------------------------------------------------------------------
        # Check if any direction on the active green corridor has a detected platoon
        for dir_enum in active_dirs:
            dir_analysis = analysis_state.directions.get(dir_enum)
            if dir_analysis and dir_analysis.platoon.platoon_detected:
                platoon = dir_analysis.platoon
                lead_eta = platoon.lead_vehicle_eta_s
                rem_green = monitoring_state.remaining_green_time

                # If the platoon will arrive within 12s and remaining green is insufficient
                # to guarantee full clearance (lead_eta + 3.0s margin)
                needed_green = lead_eta + 3.5
                if rem_green < needed_green:
                    raw_ext = round(needed_green - rem_green, 1)
                    extension = round(min(self.MAX_EXTENSION_S, max(self.MIN_EXTENSION_S, raw_ext)), 1)
                    new_duration = round(rem_green + extension, 1)

                    return OptimizationRecommendation(
                        junction_id=monitoring_state.junction_id,
                        timestamp=datetime.now(),
                        data_source=monitoring_state.data_source,
                        action=OptimizationAction.EXTEND_GREEN,
                        target_phase=curr_phase,
                        recommended_duration_s=new_duration,
                        extension_seconds=extension,
                        urgency=RecommendationUrgency.HIGH,
                        rationale=OptimizationRationale(
                            primary_factor="PLATOON_CONTINUITY",
                            reasoning=(
                                f"Approaching platoon detected on {dir_enum.value} "
                                f"({platoon.vehicle_count} vehicles at ~{platoon.average_speed_kmh} km/h, "
                                f"lead ETA: {lead_eta}s). Recommending +{extension}s green extension "
                                f"to optimize throughput and prevent abrupt convoy stoppage."
                            ),
                            metrics_snapshot={
                                "corridor": dir_enum.value,
                                "platoon_size": platoon.vehicle_count,
                                "lead_eta_s": lead_eta,
                                "remaining_green_s": rem_green,
                                "proposed_extension_s": extension,
                            },
                        ),
                    )

        # --------------------------------------------------------------------
        # Priority 2: Opposing Heavy Queue Relief Switch
        # --------------------------------------------------------------------
        critical_dir = analysis_state.critical_direction
        critical_analysis = analysis_state.directions.get(critical_dir)
        opposing_dirs = [Direction.EAST, Direction.WEST] if curr_phase in (SignalPhase.NS_GREEN, SignalPhase.NS_YELLOW) else [Direction.NORTH, Direction.SOUTH]

        if critical_dir in opposing_dirs and critical_analysis:
            queue_len = critical_analysis.queue_severity_score * 50.0  # de-normalize queue estimate
            is_heavy = (
                critical_analysis.congestion_level in (CongestionCategory.HIGH, CongestionCategory.SEVERE)
                or queue_len >= 25.0
            )
            # Check if active approach is relatively clear or remaining green is low
            if is_heavy and monitoring_state.remaining_green_time <= 8.0:
                # Compute recommended duration proportional to queue length
                calc_duration = round(
                    min(
                        self.MAX_GREEN_DURATION_S,
                        max(self.MIN_GREEN_DURATION_S, 20.0 + (queue_len * 0.5)),
                    ),
                    1,
                )
                urgency = (
                    RecommendationUrgency.CRITICAL
                    if critical_analysis.congestion_level == CongestionCategory.SEVERE
                    else RecommendationUrgency.HIGH
                )

                return OptimizationRecommendation(
                    junction_id=monitoring_state.junction_id,
                    timestamp=datetime.now(),
                    data_source=monitoring_state.data_source,
                    action=OptimizationAction.SWITCH_PHASE,
                    target_phase=opposing_phase,
                    recommended_duration_s=calc_duration,
                    extension_seconds=0.0,
                    urgency=urgency,
                    rationale=OptimizationRationale(
                        primary_factor="QUEUE_DISSIPATION",
                        reasoning=(
                            f"Opposing corridor {critical_dir.value} experiencing high congestion "
                            f"(Queue: ~{queue_len:.1f}m, Severity: {critical_analysis.congestion_level.value}). "
                            f"Recommending phase switch to {opposing_phase.value} with {calc_duration}s duration."
                        ),
                        metrics_snapshot={
                            "critical_corridor": critical_dir.value,
                            "estimated_queue_m": round(queue_len, 1),
                            "target_phase": opposing_phase.value,
                            "recommended_duration_s": calc_duration,
                        },
                    ),
                )

        # --------------------------------------------------------------------
        # Priority 3: Nominal Balanced Cycling
        # --------------------------------------------------------------------
        if monitoring_state.remaining_green_time > 3.0:
            return OptimizationRecommendation(
                junction_id=monitoring_state.junction_id,
                timestamp=datetime.now(),
                data_source=monitoring_state.data_source,
                action=OptimizationAction.MAINTAIN_CURRENT,
                target_phase=curr_phase,
                recommended_duration_s=monitoring_state.remaining_green_time,
                extension_seconds=0.0,
                urgency=RecommendationUrgency.LOW,
                rationale=OptimizationRationale(
                    primary_factor="NOMINAL_FLOW",
                    reasoning=(
                        f"Current phase {curr_phase.value} has {monitoring_state.remaining_green_time:.1f}s "
                        "remaining with nominal conditions. Recommending maintaining current phase."
                    ),
                    metrics_snapshot={
                        "phase": curr_phase.value,
                        "remaining_green_s": monitoring_state.remaining_green_time,
                    },
                ),
            )
        else:
            # Green expired in nominal condition -> recommend standard switch
            return OptimizationRecommendation(
                junction_id=monitoring_state.junction_id,
                timestamp=datetime.now(),
                data_source=monitoring_state.data_source,
                action=OptimizationAction.SWITCH_PHASE,
                target_phase=opposing_phase,
                recommended_duration_s=self.DEFAULT_CYCLE_GREEN_S,
                extension_seconds=0.0,
                urgency=RecommendationUrgency.MEDIUM,
                rationale=OptimizationRationale(
                    primary_factor="NOMINAL_CYCLE",
                    reasoning=(
                        f"Green interval for {curr_phase.value} is concluding. "
                        f"Recommending standard cycle rotation to {opposing_phase.value} "
                        f"for {self.DEFAULT_CYCLE_GREEN_S}s."
                    ),
                    metrics_snapshot={
                        "target_phase": opposing_phase.value,
                        "duration_s": self.DEFAULT_CYCLE_GREEN_S,
                    },
                ),
            )

    def get_summary(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """Serializes recommendation for downstream agents (Supervisor/Safety) and dashboard."""
        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "stage": "Optimization",
            "question_answered": self.responsibility,
            "junction_id": recommendation.junction_id,
            "data_source": recommendation.data_source,
            "timestamp": recommendation.timestamp.isoformat(),
            "action": recommendation.action.value,
            "target_phase": recommendation.target_phase.value,
            "recommended_duration_s": recommendation.recommended_duration_s,
            "extension_seconds": recommendation.extension_seconds,
            "urgency": recommendation.urgency.value,
            "rationale": recommendation.rationale.model_dump(),
        }
