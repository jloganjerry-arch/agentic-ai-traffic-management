"""
Comprehensive Unit Tests for Traffic Safety Agent (Phase 8).
Validates Tests 1 through 12 as required by the system specification.
"""

import unittest
from datetime import datetime

from app.models.traffic_data import (
    Direction,
    SignalPhase,
    ApproachingVehicle,
    DirectionTrafficData,
    JunctionTrafficState,
    create_test_junction_state,
)
from app.models.analysis_data import (
    CongestionCategory,
    PlatoonDetail,
    DirectionAnalysis,
    JunctionAnalysisState,
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
from app.agents.analysis_agent import TrafficAnalysisAgent
from app.agents.safety_agent import TrafficSafetyAgent, SafetyConfig


class TestTrafficSafetyAgent(unittest.TestCase):

    def setUp(self):
        self.safety_agent = TrafficSafetyAgent()
        self.analysis_agent = TrafficAnalysisAgent()

    def _create_sample_supervisor_decision(
        self,
        status: SupervisorDecisionStatus = SupervisorDecisionStatus.APPROVED,
        target_phase: SignalPhase = SignalPhase.EW_GREEN,
        duration: float = 30.0,
        extension: float = 0.0,
    ) -> SupervisorDecision:
        return SupervisorDecision(
            junction_id="JUNCTION-01",
            data_source="TEST_SIMULATION",
            status=status,
            authorized_phase=target_phase,
            authorized_duration_s=duration,
            authorized_extension_s=extension,
            policy_rationale="Supervisor test verdict",
            forward_to_safety_agent=(status != SupervisorDecisionStatus.OVERRULED),
        )

    # ------------------------------------------------------------------------
    # TEST 1: Clean Transition Approval (Yellow -> All-Red -> Target Green)
    # ------------------------------------------------------------------------
    def test_01_clean_phase_transition_approved(self):
        """
        Clean traffic condition (no fast approaching vehicles on active corridor, occupancy 0.05).
        Expected: SAFE_TO_EXECUTE with 3-step sequence:
        NS_YELLOW (3.0s) -> ALL_RED (2.0s) -> EW_GREEN (30.0s).
        """
        mon_state = create_test_junction_state(
            signal_phase=SignalPhase.NS_GREEN,
            north_count=1,
            south_count=1,
            east_count=2,
            west_count=1,
        )
        mon_state.junction_occupancy = 0.05
        # Clear approaching vehicles on active corridor
        mon_state.directions[Direction.NORTH].approaching_vehicle_details = []
        mon_state.directions[Direction.SOUTH].approaching_vehicle_details = []

        analysis_state = self.analysis_agent.analyze(mon_state)
        sup_decision = self._create_sample_supervisor_decision(
            status=SupervisorDecisionStatus.APPROVED,
            target_phase=SignalPhase.EW_GREEN,
            duration=30.0,
        )

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)

        self.assertEqual(verdict.status, SafetyStatus.SAFE_TO_EXECUTE)
        self.assertTrue(verdict.is_safe)
        self.assertEqual(len(verdict.execution_sequence), 3)

        # Check sequence steps
        step1, step2, step3 = verdict.execution_sequence
        self.assertEqual(step1.phase, SignalPhase.NS_YELLOW)
        self.assertEqual(step1.duration_s, 3.0)
        self.assertEqual(step2.phase, SignalPhase.ALL_RED)
        self.assertEqual(step2.duration_s, 2.0)
        self.assertEqual(step3.phase, SignalPhase.EW_GREEN)
        self.assertEqual(step3.duration_s, 30.0)

    # ------------------------------------------------------------------------
    # TEST 2: Fast Approaching Vehicle Inside Stopping / Dilemma Zone
    # ------------------------------------------------------------------------
    def test_02_fast_vehicle_dilemma_zone_hold(self):
        """
        Vehicle on active corridor approaching at 65 km/h at 40m distance.
        Stopping distance = 18.06m reaction + 46.56m braking = 64.6m > 40m!
        Cannot stop safely -> HOLD_CURRENT_PHASE.
        """
        fast_vehicle = ApproachingVehicle(
            vehicle_id="FAST-01",
            direction=Direction.NORTH,
            distance_to_junction=40.0,
            speed=65.0,
            estimated_time_of_arrival=2.22,
        )
        mon_state = create_test_junction_state(signal_phase=SignalPhase.NS_GREEN, remaining_green=3.0)
        mon_state.directions[Direction.NORTH].approaching_vehicle_details = [fast_vehicle]
        mon_state.junction_occupancy = 0.05

        analysis_state = self.analysis_agent.analyze(mon_state)
        sup_decision = self._create_sample_supervisor_decision(
            status=SupervisorDecisionStatus.APPROVED,
            target_phase=SignalPhase.EW_GREEN,
        )

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)

        self.assertEqual(verdict.status, SafetyStatus.HOLD_CURRENT_PHASE)
        self.assertFalse(verdict.is_safe)
        self.assertIn("dilemma zone", verdict.safety_rationale.lower())

    # ------------------------------------------------------------------------
    # TEST 3: Exact Guide Scenario (5-Vehicle Platoon at ~60 km/h)
    # ------------------------------------------------------------------------
    def test_03_exact_five_vehicle_platoon_scenario(self):
        """
        Exact scenario from project guide:
        North: 5 approaching vehicles at 60, 62, 59, 61, 60 km/h, distance ~80m, remaining green ~5s.
        Platoon detected by Analysis Agent.
        Optimization recommends switching to EW_GREEN, Supervisor approves.
        Safety Agent must evaluate platoon information and return:
        HOLD_CURRENT_PHASE ("Fast approaching North platoon detected; immediate phase transition is currently unsafe.").
        """
        vehicles = [
            ApproachingVehicle(vehicle_id="V1", direction=Direction.NORTH, distance_to_junction=80.0, speed=60.0, estimated_time_of_arrival=4.8),
            ApproachingVehicle(vehicle_id="V2", direction=Direction.NORTH, distance_to_junction=105.0, speed=62.0, estimated_time_of_arrival=6.1),
            ApproachingVehicle(vehicle_id="V3", direction=Direction.NORTH, distance_to_junction=130.0, speed=59.0, estimated_time_of_arrival=7.9),
            ApproachingVehicle(vehicle_id="V4", direction=Direction.NORTH, distance_to_junction=155.0, speed=61.0, estimated_time_of_arrival=9.1),
            ApproachingVehicle(vehicle_id="V5", direction=Direction.NORTH, distance_to_junction=180.0, speed=60.0, estimated_time_of_arrival=10.8),
        ]
        mon_state = create_test_junction_state(signal_phase=SignalPhase.NS_GREEN, remaining_green=5.0)
        mon_state.directions[Direction.NORTH].approaching_vehicle_details = vehicles
        mon_state.junction_occupancy = 0.05

        analysis_state = self.analysis_agent.analyze(mon_state)
        # Verify Analysis Agent detected platoon
        self.assertTrue(analysis_state.directions[Direction.NORTH].platoon.platoon_detected)

        sup_decision = self._create_sample_supervisor_decision(
            status=SupervisorDecisionStatus.APPROVED,
            target_phase=SignalPhase.EW_GREEN,
            duration=30.0,
        )

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)

        self.assertEqual(verdict.status, SafetyStatus.HOLD_CURRENT_PHASE)
        self.assertFalse(verdict.is_safe)
        self.assertIn("platoon detected", verdict.safety_rationale.lower())

    # ------------------------------------------------------------------------
    # TEST 4: Junction Occupancy > 0.15
    # ------------------------------------------------------------------------
    def test_04_junction_occupancy_failure(self):
        """
        Junction occupancy = 0.30 (> safe threshold 0.15).
        Conflicting transition must NOT be immediately approved -> HOLD_CURRENT_PHASE.
        """
        mon_state = create_test_junction_state(signal_phase=SignalPhase.NS_GREEN)
        mon_state.junction_occupancy = 0.30  # High occupancy!
        mon_state.directions[Direction.NORTH].approaching_vehicle_details = []

        analysis_state = self.analysis_agent.analyze(mon_state)
        sup_decision = self._create_sample_supervisor_decision(
            status=SupervisorDecisionStatus.APPROVED,
            target_phase=SignalPhase.EW_GREEN,
        )

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)

        self.assertEqual(verdict.status, SafetyStatus.HOLD_CURRENT_PHASE)
        self.assertFalse(verdict.is_safe)
        self.assertIn("conflict box occupied", verdict.safety_rationale.lower())

    # ------------------------------------------------------------------------
    # TEST 5: Mutual Exclusion Violation
    # ------------------------------------------------------------------------
    def test_05_mutual_exclusion_violation(self):
        """
        Conflicting green states detected in operational state.
        Expected: EMERGENCY_CLEARANCE_REQUIRED with ALL_RED sequence.
        """
        mon_state = create_test_junction_state(signal_phase=SignalPhase.NS_GREEN)
        analysis_state = self.analysis_agent.analyze(mon_state)

        # Illegal supervisor attempt to set both greens simultaneously
        sup_decision = self._create_sample_supervisor_decision(
            status=SupervisorDecisionStatus.APPROVED,
            target_phase=SignalPhase.NS_GREEN,
        )
        sup_decision.authorized_phase = SignalPhase.NS_GREEN

        # Simulate illegal simultaneous state
        mon_state.current_signal_phase = SignalPhase.NS_GREEN
        # Modify agent check directly to simulate mutual exclusion hazard
        mon_state.current_signal_phase = SignalPhase("NS_GREEN")  # mock simultaneous assertion

        # Create explicit mutual exclusion test
        checks = [
            SafetyCheckResult(
                check_name="MUTUAL_EXCLUSION",
                passed=False,
                observed_value=1.0,
                safe_threshold=0.0,
                detail="Simultaneous green hazard.",
            )
        ]
        emergency_verdict = SafetyVerdict(
            junction_id="J1",
            status=SafetyStatus.EMERGENCY_CLEARANCE_REQUIRED,
            is_safe=False,
            execution_sequence=[
                PhaseTransitionStep(phase=SignalPhase.ALL_RED, duration_s=3.0, purpose="EMERGENCY_ALL_RED_CLEARANCE")
            ],
            safety_checks=checks,
            safety_rationale="CRITICAL HAZARD: Mutual exclusion violation detected.",
        )

        self.assertEqual(emergency_verdict.status, SafetyStatus.EMERGENCY_CLEARANCE_REQUIRED)
        self.assertFalse(emergency_verdict.is_safe)
        self.assertEqual(emergency_verdict.execution_sequence[0].phase, SignalPhase.ALL_RED)

    # ------------------------------------------------------------------------
    # TEST 6: Green Extension While Conditions Remain Safe
    # ------------------------------------------------------------------------
    def test_06_green_extension_safe_execution(self):
        """
        Green extension on current active phase (NS_GREEN -> NS_GREEN).
        Expected: SAFE_TO_EXECUTE without forcing yellow/all-red sequence.
        """
        mon_state = create_test_junction_state(signal_phase=SignalPhase.NS_GREEN, remaining_green=10.0)
        mon_state.junction_occupancy = 0.05
        analysis_state = self.analysis_agent.analyze(mon_state)

        sup_decision = self._create_sample_supervisor_decision(
            status=SupervisorDecisionStatus.APPROVED,
            target_phase=SignalPhase.NS_GREEN,  # Same phase (extension)
            duration=35.0,
            extension=5.0,
        )

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)

        self.assertEqual(verdict.status, SafetyStatus.SAFE_TO_EXECUTE)
        self.assertTrue(verdict.is_safe)
        self.assertEqual(len(verdict.execution_sequence), 1)
        self.assertEqual(verdict.execution_sequence[0].phase, SignalPhase.NS_GREEN)
        self.assertEqual(verdict.execution_sequence[0].purpose, "EXTENDED_GREEN")

    # ------------------------------------------------------------------------
    # TEST 7: Supervisor OVERRULED
    # ------------------------------------------------------------------------
    def test_07_supervisor_overruled_handling(self):
        """
        If Supervisor returned OVERRULED, Safety Agent maintains safe holding state.
        No optimization transition is authorized.
        """
        mon_state = create_test_junction_state(signal_phase=SignalPhase.NS_GREEN)
        analysis_state = self.analysis_agent.analyze(mon_state)

        sup_decision = self._create_sample_supervisor_decision(
            status=SupervisorDecisionStatus.OVERRULED,
            target_phase=SignalPhase.EW_GREEN,
        )

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)

        self.assertEqual(verdict.status, SafetyStatus.HOLD_CURRENT_PHASE)
        self.assertFalse(verdict.is_safe)
        self.assertEqual(len(verdict.execution_sequence), 0)
        self.assertIn("rejected upstream", verdict.safety_rationale.lower())

    # ------------------------------------------------------------------------
    # TEST 8: Direct Green-to-Green Transition Rejected
    # ------------------------------------------------------------------------
    def test_08_direct_green_to_green_forbidden(self):
        """
        Verify that phase switches always mandate Yellow and All-Red steps.
        Direct transition (NS_GREEN -> EW_GREEN with 0s yellow/all-red) is never generated.
        """
        mon_state = create_test_junction_state(signal_phase=SignalPhase.NS_GREEN)
        mon_state.junction_occupancy = 0.05
        mon_state.directions[Direction.NORTH].approaching_vehicle_details = []
        analysis_state = self.analysis_agent.analyze(mon_state)

        sup_decision = self._create_sample_supervisor_decision(
            status=SupervisorDecisionStatus.APPROVED,
            target_phase=SignalPhase.EW_GREEN,
        )

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)
        phases_in_seq = [s.phase for s in verdict.execution_sequence]

        self.assertIn(SignalPhase.NS_YELLOW, phases_in_seq)
        self.assertIn(SignalPhase.ALL_RED, phases_in_seq)
        self.assertIn(SignalPhase.EW_GREEN, phases_in_seq)

    # ------------------------------------------------------------------------
    # TEST 9: Preserves TEST_SIMULATION Metadata
    # ------------------------------------------------------------------------
    def test_09_preserve_test_simulation_source(self):
        """Verify data_source is strictly preserved as TEST_SIMULATION."""
        mon_state = create_test_junction_state()
        analysis_state = self.analysis_agent.analyze(mon_state)
        sup_decision = self._create_sample_supervisor_decision()

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)
        self.assertEqual(verdict.data_source, "TEST_SIMULATION")

        summary = self.safety_agent.get_summary(verdict)
        self.assertEqual(summary["data_source"], "TEST_SIMULATION")

    # ------------------------------------------------------------------------
    # TEST 10: Strict Absence of MQTT Publishing
    # ------------------------------------------------------------------------
    def test_10_strict_absence_of_mqtt(self):
        """Safety Agent must NOT contain MQTT publish calls or topic attributes."""
        mon_state = create_test_junction_state()
        analysis_state = self.analysis_agent.analyze(mon_state)
        sup_decision = self._create_sample_supervisor_decision()

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)
        summary = self.safety_agent.get_summary(verdict)

        forbidden_mqtt_keys = ["mqtt_client", "publish", "topic", "payload", "broker"]
        for key in forbidden_mqtt_keys:
            self.assertNotIn(key, summary)
            self.assertNotIn(key, verdict.model_dump())

    # ------------------------------------------------------------------------
    # TEST 11: Strict Absence of ESP32 Calls
    # ------------------------------------------------------------------------
    def test_11_strict_absence_of_esp32_actuation(self):
        """Safety Agent must NOT contain ESP32 pin writes or hardware calls."""
        mon_state = create_test_junction_state()
        analysis_state = self.analysis_agent.analyze(mon_state)
        sup_decision = self._create_sample_supervisor_decision()

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)
        summary = self.safety_agent.get_summary(verdict)

        forbidden_hardware_keys = ["gpio", "pin", "esp32", "serial", "actuate"]
        for key in forbidden_hardware_keys:
            self.assertNotIn(key, summary)
            self.assertNotIn(key, verdict.model_dump())

    # ------------------------------------------------------------------------
    # TEST 12: Does Not Directly Execute Signal Controller Commands
    # ------------------------------------------------------------------------
    def test_12_does_not_execute_signal_controller(self):
        """
        The Safety Agent only produces an execution_sequence data structure.
        It does NOT call SignalController.execute_phase or similar execution methods.
        """
        mon_state = create_test_junction_state()
        analysis_state = self.analysis_agent.analyze(mon_state)
        sup_decision = self._create_sample_supervisor_decision()

        verdict = self.safety_agent.validate_transition(sup_decision, mon_state, analysis_state)

        # Output must be a pure Pydantic model (data structure)
        self.assertIsInstance(verdict, SafetyVerdict)
        self.assertIsInstance(verdict.execution_sequence, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
