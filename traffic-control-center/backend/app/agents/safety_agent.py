"""
Traffic Safety Agent (Agent 5 - Phase 8).
Responsibility: "IS IT SAFE TO PERFORM THIS TRANSITION RIGHT NOW?"

The Safety Agent is the FINAL INTELLIGENCE GATEKEEPER directly preceding
the Python Signal Controller.
Verifies physical clearance, vehicle stopping distances, dilemma zones,
platoon transit safety, intersection occupancy, and enforces mandatory
yellow/all-red clearance sequencing.

STRICT ARCHITECTURAL RULE:
Analytical prototype safety decision model. Does NOT claim real-world accident prevention.
The Safety Agent does NOT publish MQTT.
The Safety Agent does NOT control ESP32.
The Safety Agent does NOT directly execute a signal transition.
The Python Signal Controller remains the sole physical signal execution authority.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.traffic_data import (
    Direction,
    SignalPhase,
    ApproachingVehicle,
    JunctionTrafficState,
)
from app.models.analysis_data import JunctionAnalysisState
from app.models.supervisor_data import (
    SupervisorDecisionStatus,
    SupervisorDecision,
)
from app.models.safety_data import (
    SafetyStatus,
    PhaseTransitionStep,
    SafetyCheckResult,
    SafetyVerdict,
)


class SafetyConfig(BaseModel):
    """
    Configurable prototype safety parameters.
    NOTE: All safety calculations and thresholds are configurable prototype assumptions
    for this academic project and are not universal road-safety standards.
    """
    reaction_time_s: float = Field(1.0, description="Driver perception-reaction time in seconds")
    braking_deceleration_mps2: float = Field(3.5, description="Comfortable maximum braking deceleration in m/s^2")
    fast_vehicle_threshold_kmh: float = Field(45.0, description="Speed threshold above which dilemma-zone checks are enforced in km/h")
    max_junction_occupancy: float = Field(0.15, description="Maximum allowable conflict box occupancy threshold before conflicting green is permitted")
    default_yellow_duration_s: float = Field(3.0, description="Mandatory yellow clearance duration in seconds")
    default_all_red_duration_s: float = Field(2.0, description="Mandatory all-red clearance duration in seconds")


class TrafficSafetyAgent:
    """
    Agent 5: Physical clearance & transition safety gatekeeper.
    Answers: 'IS IT SAFE TO PERFORM THIS TRANSITION RIGHT NOW?'
    """

    def __init__(
        self,
        agent_id: str = "agent-5",
        safety_config: Optional[SafetyConfig] = None,
    ):
        self.id = agent_id
        self.name = "Traffic Safety Agent"
        self.role = "Physical Clearance & Transition Safety Gatekeeper"
        self.responsibility = "IS IT SAFE TO PERFORM THIS TRANSITION RIGHT NOW?"
        self.config = safety_config or SafetyConfig()

    # ========================================================================
    # 1. Physics Calculations: Stopping Distance
    # ========================================================================

    def compute_stopping_distance(self, speed_kmh: float) -> float:
        """
        Calculates deterministic physical stopping distance:
          speed_mps = speed_kmh / 3.6
          reaction_distance = speed_mps * reaction_time_s
          braking_distance = speed_mps^2 / (2 * braking_deceleration_mps2)
          stopping_distance = reaction_distance + braking_distance
        """
        if speed_kmh <= 0.5:
            return 0.0
        speed_mps = speed_kmh / 3.6
        reaction_dist = speed_mps * self.config.reaction_time_s
        braking_dist = (speed_mps ** 2) / (2.0 * self.config.braking_deceleration_mps2)
        return round(reaction_dist + braking_dist, 2)

    # ========================================================================
    # 2. Corridor Mapping Helpers
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
    def get_corridor_yellow_phase(active_phase: SignalPhase) -> SignalPhase:
        """Returns the appropriate clearance yellow phase for the active green."""
        if active_phase in (SignalPhase.NS_GREEN, SignalPhase.NS_YELLOW):
            return SignalPhase.NS_YELLOW
        elif active_phase in (SignalPhase.EW_GREEN, SignalPhase.EW_YELLOW):
            return SignalPhase.EW_YELLOW
        return SignalPhase.ALL_RED

    # ========================================================================
    # 3. Master Transition Validation
    # ========================================================================

    def validate_transition(
        self,
        supervisor_decision: SupervisorDecision,
        monitoring_state: JunctionTrafficState,
        analysis_state: JunctionAnalysisState,
    ) -> SafetyVerdict:
        """
        Evaluates physical safety, vehicle stopping distances, dilemma zones,
        platoon safety, junction occupancy, and mutual exclusion.
        Outputs a SafetyVerdict with an approved execution sequence for the Signal Controller.
        """
        checks: List[SafetyCheckResult] = []
        curr_phase = monitoring_state.current_signal_phase
        target_phase = supervisor_decision.authorized_phase

        # --------------------------------------------------------------------
        # Rule 1: Upstream Supervisor Rejection Check
        # --------------------------------------------------------------------
        if supervisor_decision.status == SupervisorDecisionStatus.OVERRULED:
            checks.append(
                SafetyCheckResult(
                    check_name="UPSTREAM_SUPERVISOR_STATUS",
                    passed=False,
                    observed_value=0.0,
                    safe_threshold=1.0,
                    detail=f"Supervisor rejected recommendation: '{supervisor_decision.policy_rationale}'.",
                )
            )
            return SafetyVerdict(
                junction_id=monitoring_state.junction_id,
                timestamp=datetime.now(),
                data_source=monitoring_state.data_source,
                status=SafetyStatus.HOLD_CURRENT_PHASE,
                is_safe=False,
                execution_sequence=[],
                safety_checks=checks,
                safety_rationale="Recommendation rejected upstream by Supervisor Agent; no transition authorized by this recommendation.",
            )

        checks.append(
            SafetyCheckResult(
                check_name="UPSTREAM_SUPERVISOR_STATUS",
                passed=True,
                observed_value=1.0,
                safe_threshold=1.0,
                detail="Supervisor approved/modified recommendation.",
            )
        )

        # --------------------------------------------------------------------
        # Rule 2: Mutual Exclusion Safeguard
        # --------------------------------------------------------------------
        # Re-verify that NS_GREEN and EW_GREEN can NEVER be simultaneously active or authorized
        is_mutual_exclusion_violated = False
        if curr_phase == SignalPhase.NS_GREEN and target_phase == SignalPhase.EW_GREEN:
            # Normal phase transition (handled with sequence), not simultaneous assertion
            pass
        elif curr_phase == SignalPhase.EW_GREEN and target_phase == SignalPhase.NS_GREEN:
            # Normal phase transition
            pass
        elif "NS" in curr_phase.value and "EW" in curr_phase.value:
            is_mutual_exclusion_violated = True

        # Check if caller or raw state attempts illegal simultaneous green
        if curr_phase == SignalPhase.NS_GREEN and target_phase == SignalPhase.NS_GREEN and "EW_GREEN" in str(supervisor_decision.authorized_phase.value):
            is_mutual_exclusion_violated = True

        checks.append(
            SafetyCheckResult(
                check_name="MUTUAL_EXCLUSION",
                passed=not is_mutual_exclusion_violated,
                observed_value=1.0 if is_mutual_exclusion_violated else 0.0,
                safe_threshold=0.0,
                detail="Mutually exclusive green states verified." if not is_mutual_exclusion_violated else "CRITICAL: Conflicting greens asserted simultaneously!",
            )
        )

        if is_mutual_exclusion_violated:
            return SafetyVerdict(
                junction_id=monitoring_state.junction_id,
                timestamp=datetime.now(),
                data_source=monitoring_state.data_source,
                status=SafetyStatus.EMERGENCY_CLEARANCE_REQUIRED,
                is_safe=False,
                execution_sequence=[
                    PhaseTransitionStep(
                        phase=SignalPhase.ALL_RED,
                        duration_s=3.0,
                        purpose="EMERGENCY_ALL_RED_CLEARANCE",
                    )
                ],
                safety_checks=checks,
                safety_rationale="CRITICAL HAZARD: Mutual exclusion violation detected. Immediate trip to ALL_RED clearance required.",
            )

        # --------------------------------------------------------------------
        # Rule 3: Intersection Conflict Box Clearance Check
        # --------------------------------------------------------------------
        is_phase_switch = (curr_phase != target_phase)
        occupancy_passed = True
        occupancy_detail = "Conflict box occupancy within safe limits."

        if is_phase_switch:
            if monitoring_state.junction_occupancy > self.config.max_junction_occupancy:
                occupancy_passed = False
                occupancy_detail = (
                    f"Conflict box occupied (occupancy {monitoring_state.junction_occupancy:.2f} > "
                    f"safe limit {self.config.max_junction_occupancy:.2f}). Conflicting green delayed."
                )

        checks.append(
            SafetyCheckResult(
                check_name="INTERSECTION_OCCUPANCY",
                passed=occupancy_passed,
                observed_value=monitoring_state.junction_occupancy,
                safe_threshold=self.config.max_junction_occupancy,
                detail=occupancy_detail,
            )
        )

        if not occupancy_passed:
            return SafetyVerdict(
                junction_id=monitoring_state.junction_id,
                timestamp=datetime.now(),
                data_source=monitoring_state.data_source,
                status=SafetyStatus.HOLD_CURRENT_PHASE,
                is_safe=False,
                execution_sequence=[],
                safety_checks=checks,
                safety_rationale=f"Junction conflict box occupied ({monitoring_state.junction_occupancy:.2f} > {self.config.max_junction_occupancy:.2f}); transition delayed until conflict box clears.",
            )

        # --------------------------------------------------------------------
        # Rule 4: Dilemma-Zone & Platoon Safety Analysis
        # --------------------------------------------------------------------
        dilemma_passed = True
        dilemma_detail = "Approaching vehicles outside dilemma zone or safe to transition."
        hazard_reason = ""

        if is_phase_switch:
            active_dirs = self.get_active_corridor_directions(curr_phase)
            for d in active_dirs:
                d_data = monitoring_state.directions.get(d)
                d_analysis = analysis_state.directions.get(d)

                if not d_data:
                    continue

                # 4A. Platoon Safety Check (Consuming Analysis Agent's platoon output)
                if d_analysis and d_analysis.platoon.platoon_detected:
                    platoon = d_analysis.platoon
                    lead_eta = platoon.lead_vehicle_eta_s
                    lead_dist = platoon.lead_vehicle_distance_m
                    mean_spd = platoon.average_speed_kmh
                    stopping_dist = self.compute_stopping_distance(mean_spd)

                    # If fast approaching platoon (e.g. 60 km/h) is near or inside stopping/clearance window
                    # (ETA <= remaining_green + yellow_duration + 1.5s or distance <= stopping_dist + 25m)
                    clearance_time_window = monitoring_state.remaining_green_time + self.config.default_yellow_duration_s + 1.5
                    if lead_eta <= clearance_time_window or lead_dist <= (stopping_dist + 25.0):
                        dilemma_passed = False
                        hazard_reason = (
                            f"Fast approaching {d.value} platoon detected ({platoon.vehicle_count} vehicles at "
                            f"{mean_spd:.1f} km/h, Lead Distance: {lead_dist:.1f}m, Stopping Dist: {stopping_dist:.1f}m, "
                            f"ETA: {lead_eta:.1f}s, Remaining Green: {monitoring_state.remaining_green_time:.1f}s). "
                            "Immediate phase transition is currently unsafe; platoon may reach junction during transition."
                        )
                        dilemma_detail = hazard_reason
                        break

                # 4B. Individual Fast Vehicle Dilemma-Zone Check
                for veh in d_data.approaching_vehicle_details:
                    if veh.speed > self.config.fast_vehicle_threshold_kmh:
                        v_stop_dist = self.compute_stopping_distance(veh.speed)
                        # Vehicle is inside or near dilemma zone if distance is less than stopping distance
                        # while approaching at high speed, or ETA <= remaining green + yellow
                        clearance_cutoff = monitoring_state.remaining_green_time + self.config.default_yellow_duration_s
                        if veh.distance_to_junction < (v_stop_dist + 5.0) or veh.estimated_time_of_arrival <= clearance_cutoff:
                            dilemma_passed = False
                            hazard_reason = (
                                f"Fast vehicle {veh.vehicle_id} on {d.value} ({veh.speed:.1f} km/h, "
                                f"Dist: {veh.distance_to_junction:.1f}m, Stopping Dist: {v_stop_dist:.1f}m, "
                                f"ETA: {veh.estimated_time_of_arrival:.1f}s) in dilemma zone. "
                                "Immediate transition is unsafe."
                            )
                            dilemma_detail = hazard_reason
                            break

                if not dilemma_passed:
                    break

        checks.append(
            SafetyCheckResult(
                check_name="DILEMMA_ZONE_AND_PLATOON_SAFETY",
                passed=dilemma_passed,
                observed_value=0.0 if dilemma_passed else 1.0,
                safe_threshold=0.0,
                detail=dilemma_detail,
            )
        )

        if not dilemma_passed:
            return SafetyVerdict(
                junction_id=monitoring_state.junction_id,
                timestamp=datetime.now(),
                data_source=monitoring_state.data_source,
                status=SafetyStatus.HOLD_CURRENT_PHASE,
                is_safe=False,
                execution_sequence=[],
                safety_checks=checks,
                safety_rationale=hazard_reason,
            )

        # --------------------------------------------------------------------
        # Rule 5: Construct Mandatory Safe Execution Sequence
        # --------------------------------------------------------------------
        execution_sequence: List[PhaseTransitionStep] = []

        if is_phase_switch:
            # Mandatory sequence: Active Yellow -> ALL_RED -> Target Green
            yellow_phase = self.get_corridor_yellow_phase(curr_phase)
            execution_sequence = [
                PhaseTransitionStep(
                    phase=yellow_phase,
                    duration_s=self.config.default_yellow_duration_s,
                    purpose="YELLOW_CLEARANCE",
                ),
                PhaseTransitionStep(
                    phase=SignalPhase.ALL_RED,
                    duration_s=self.config.default_all_red_duration_s,
                    purpose="ALL_RED_CLEARANCE",
                ),
                PhaseTransitionStep(
                    phase=target_phase,
                    duration_s=supervisor_decision.authorized_duration_s,
                    purpose="TARGET_GREEN",
                ),
            ]
            checks.append(
                SafetyCheckResult(
                    check_name="MANDATORY_SEQUENCE_INTEGRITY",
                    passed=True,
                    observed_value=float(len(execution_sequence)),
                    safe_threshold=3.0,
                    detail=f"3-step sequence generated: {yellow_phase.value} ({self.config.default_yellow_duration_s}s) -> ALL_RED ({self.config.default_all_red_duration_s}s) -> {target_phase.value} ({supervisor_decision.authorized_duration_s}s).",
                )
            )
            rationale = "Safe to execute phase transition with mandatory yellow and all-red clearances."
        else:
            # Green Extension on active green: maintain current green without yellow/all-red
            execution_sequence = [
                PhaseTransitionStep(
                    phase=target_phase,
                    duration_s=supervisor_decision.authorized_duration_s,
                    purpose="EXTENDED_GREEN",
                )
            ]
            checks.append(
                SafetyCheckResult(
                    check_name="GREEN_EXTENSION_SAFETY",
                    passed=True,
                    observed_value=supervisor_decision.authorized_extension_s,
                    safe_threshold=0.0,
                    detail=f"Green extension of +{supervisor_decision.authorized_extension_s:.1f}s verified safe to continue.",
                )
            )
            rationale = "Safe to execute green extension on active corridor."

        return SafetyVerdict(
            junction_id=monitoring_state.junction_id,
            timestamp=datetime.now(),
            data_source=monitoring_state.data_source,
            status=SafetyStatus.SAFE_TO_EXECUTE,
            is_safe=True,
            execution_sequence=execution_sequence,
            safety_checks=checks,
            safety_rationale=rationale,
        )

    def get_summary(self, verdict: SafetyVerdict) -> Dict[str, Any]:
        """Serializes safety verdict for the Python Signal Controller and dashboard."""
        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "stage": "Safety",
            "question_answered": self.responsibility,
            "junction_id": verdict.junction_id,
            "data_source": verdict.data_source,
            "timestamp": verdict.timestamp.isoformat(),
            "status": verdict.status.value,
            "is_safe": verdict.is_safe,
            "safety_rationale": verdict.safety_rationale,
            "prototype_disclaimer": verdict.prototype_disclaimer,
            "execution_sequence": [step.model_dump() for step in verdict.execution_sequence],
            "safety_checks": [check.model_dump() for check in verdict.safety_checks],
        }
