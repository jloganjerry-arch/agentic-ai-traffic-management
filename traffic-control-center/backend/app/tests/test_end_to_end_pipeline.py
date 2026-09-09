"""
Automated Integration Tests for End-to-End Multi-Agent Pipeline (Phase 9).
Validates Tests 1 through 6 in Mock/Simulation mode (no hardware required).
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
from app.models.optimization_data import OptimizationAction
from app.models.supervisor_data import SupervisorDecisionStatus
from app.models.safety_data import SafetyStatus
from app.agents.controlled_traffic_source import ControlledTrafficSource
from app.core.signal_controller import SignalController
from app.core.agent_pipeline import IntelligentTrafficPipeline


class TestEndToEndPipeline(unittest.TestCase):

    def setUp(self):
        self.mock_controller = SignalController(mock_actuation=True, initial_phase=SignalPhase.NS_GREEN)
        self.pipeline = IntelligentTrafficPipeline(
            signal_controller=self.mock_controller,
            mock_actuation=True,
            initial_phase=SignalPhase.NS_GREEN,
        )

    # ------------------------------------------------------------------------
    # TEST 1: Safe Phase Switch Flow
    # ------------------------------------------------------------------------
    def test_01_safe_phase_switch_end_to_end(self):
        """
        Clean traffic condition with low remaining green on NS_GREEN and queue on East approach:
        Optimization recommends SWITCH_PHASE -> EW_GREEN.
        Supervisor approves (elapsed green >= 15s).
        Safety approves -> SAFE_TO_EXECUTE.
        Signal Controller receives and executes sequence:
        NS_YELLOW (3s) -> ALL_RED (2s) -> EW_GREEN (duration).
        """
        self.pipeline.elapsed_green_s = 20.0  # Already met 15s min green
        raw_telemetry = ControlledTrafficSource.generate_congested_north_queue()
        # Set phase to NS_GREEN with 2s remaining green, heavy East queue
        raw_telemetry["current_signal_phase"] = "NS_GREEN"
        raw_telemetry["remaining_green_time"] = 2.0
        raw_telemetry["junction_occupancy"] = 0.05
        # Set East as congested approach
        raw_telemetry["raw_corridor_data"]["EAST"]["queue_length_m"] = 40.0
        raw_telemetry["raw_corridor_data"]["NORTH"]["detected_vehicles"] = []  # No dilemma vehicles on North

        result = self.pipeline.step(raw_telemetry)

        self.assertTrue(result.actuation_dispatched)
        self.assertEqual(result.active_phase_after, SignalPhase.EW_GREEN)
        self.assertEqual(result.safety.status, SafetyStatus.SAFE_TO_EXECUTE)
        self.assertEqual(len(result.dispatched_sequence), 3)

        # Inspect sequence received by Signal Controller
        seq_phases = [step.phase for step in result.dispatched_sequence]
        self.assertEqual(seq_phases, [SignalPhase.NS_YELLOW, SignalPhase.ALL_RED, SignalPhase.EW_GREEN])

        # Verify Mock Actuator recorded all steps
        mock_history = self.mock_controller.actuation_history
        self.assertEqual(mock_history[-1]["phase"], "EW_GREEN")

    # ------------------------------------------------------------------------
    # TEST 2: Platoon Extension Flow
    # ------------------------------------------------------------------------
    def test_02_platoon_green_extension_end_to_end(self):
        """
        Approaching North platoon (>=3 vehicles at ~60 km/h, close spacing):
        Optimization recommends EXTEND_GREEN.
        Supervisor approves (+5s or +7s within 60s max green cap).
        Safety validates continuing active green -> SAFE_TO_EXECUTE.
        Controller extends green without yellow/all-red interruption.
        """
        self.pipeline.elapsed_green_s = 25.0
        self.pipeline.consecutive_extensions = 0
        self.pipeline.opposing_red_wait_s = 25.0

        # Build raw telemetry with 5-car platoon on North
        raw_telemetry = {
            "source_type": "TEST_SIMULATION",
            "junction_id": "JUNCTION-01",
            "current_signal_phase": "NS_GREEN",
            "remaining_green_time": 3.0,
            "junction_occupancy": 0.05,
            "traffic_state": "NON_PEAK",
            "raw_corridor_data": {
                "NORTH": {
                    "detected_vehicles": [
                        {"id": "V1", "distance_m": 50.0, "speed_kmh": 60.0, "acceleration": 0.0},
                        {"id": "V2", "distance_m": 75.0, "speed_kmh": 62.0, "acceleration": 0.0},
                        {"id": "V3", "distance_m": 100.0, "speed_kmh": 59.0, "acceleration": 0.0},
                        {"id": "V4", "distance_m": 125.0, "speed_kmh": 61.0, "acceleration": 0.0},
                        {"id": "V5", "distance_m": 150.0, "speed_kmh": 60.0, "acceleration": 0.0},
                    ],
                    "queue_length_m": 0.0,
                },
                "SOUTH": {"detected_vehicles": [], "queue_length_m": 0.0},
                "EAST": {"detected_vehicles": [], "queue_length_m": 0.0},
                "WEST": {"detected_vehicles": [], "queue_length_m": 0.0},
            },
        }

        result = self.pipeline.step(raw_telemetry)

        self.assertTrue(result.actuation_dispatched)
        self.assertEqual(result.optimization.action, OptimizationAction.EXTEND_GREEN)
        self.assertEqual(result.supervisor.status, SupervisorDecisionStatus.APPROVED)
        self.assertEqual(result.safety.status, SafetyStatus.SAFE_TO_EXECUTE)
        self.assertEqual(result.active_phase_after, SignalPhase.NS_GREEN)

        # Extended green should not contain yellow or all-red steps
        for step in result.dispatched_sequence:
            self.assertEqual(step.phase, SignalPhase.NS_GREEN)
            self.assertEqual(step.purpose, "EXTENDED_GREEN")

        # Verify extension count increased
        self.assertEqual(self.pipeline.consecutive_extensions, 1)

    # ------------------------------------------------------------------------
    # TEST 3: Dilemma Zone Protection (Unsafe Transition)
    # ------------------------------------------------------------------------
    def test_03_dilemma_zone_hold_protection(self):
        """
        Fast approaching vehicle on active North corridor (65 km/h at 40m) during switch attempt:
        Safety returns HOLD_CURRENT_PHASE.
        actuation_dispatched = False, phase stays NS_GREEN, no MQTT command sent.
        """
        self.pipeline.elapsed_green_s = 20.0
        raw_telemetry = {
            "source_type": "TEST_SIMULATION",
            "junction_id": "JUNCTION-01",
            "current_signal_phase": "NS_GREEN",
            "remaining_green_time": 2.0,
            "junction_occupancy": 0.05,
            "raw_corridor_data": {
                "NORTH": {
                    "detected_vehicles": [
                        {"id": "FAST-01", "distance_m": 40.0, "speed_kmh": 65.0, "acceleration": 0.0}
                    ],
                    "queue_length_m": 0.0,
                },
                "SOUTH": {"detected_vehicles": [], "queue_length_m": 0.0},
                "EAST": {"detected_vehicles": [], "queue_length_m": 35.0},
                "WEST": {"detected_vehicles": [], "queue_length_m": 0.0},
            },
        }

        result = self.pipeline.step(raw_telemetry)

        self.assertFalse(result.actuation_dispatched)
        self.assertEqual(result.safety.status, SafetyStatus.HOLD_CURRENT_PHASE)
        self.assertEqual(result.active_phase_after, SignalPhase.NS_GREEN)
        self.assertIn("dilemma zone", result.final_action_summary.lower())

    # ------------------------------------------------------------------------
    # TEST 4: Starvation Prevention Handling
    # ------------------------------------------------------------------------
    def test_04_starvation_prevention_handling(self):
        """
        Opposing red wait >= 90s:
        Supervisor overrules any further green extension to prevent starvation.
        """
        self.pipeline.elapsed_green_s = 40.0
        self.pipeline.opposing_red_wait_s = 95.0  # Starvation threshold reached!

        # Raw telemetry with platoon attempting extension
        raw_telemetry = ControlledTrafficSource.generate_high_speed_approaching_scenario()
        raw_telemetry["current_signal_phase"] = "NS_GREEN"
        raw_telemetry["remaining_green_time"] = 3.0  # Green expiring soon, will trigger EXTEND_GREEN
        raw_telemetry["raw_corridor_data"]["NORTH"] = {
            "detected_vehicles": [
                {"id": "V1", "distance_m": 50.0, "speed_kmh": 60.0, "acceleration": 0.0},
                {"id": "V2", "distance_m": 75.0, "speed_kmh": 60.0, "acceleration": 0.0},
                {"id": "V3", "distance_m": 100.0, "speed_kmh": 60.0, "acceleration": 0.0},
            ],
            "queue_length_m": 0.0,
        }

        result = self.pipeline.step(raw_telemetry)

        self.assertEqual(result.supervisor.status, SupervisorDecisionStatus.OVERRULED)
        self.assertIn("maximum red waiting threshold", result.supervisor.policy_rationale.lower())
        self.assertFalse(result.safety.is_safe)
        self.assertIn("overruled", result.final_action_summary.lower())

    # ------------------------------------------------------------------------
    # TEST 5: Mutual Exclusion Emergency Safeguard
    # ------------------------------------------------------------------------
    def test_05_mutual_exclusion_failsafe(self):
        """
        Illegal conflicting state triggers emergency all-red clearance.
        """
        # Trigger emergency all-red directly through controller
        success = self.pipeline.controller.emergency_all_red()
        self.assertTrue(success)
        self.assertEqual(self.pipeline.controller.current_phase, SignalPhase.ALL_RED)

        last_action = self.mock_controller.actuation_history[-1]
        self.assertEqual(last_action["phase"], "ALL_RED")
        self.assertEqual(last_action["purpose"], "EMERGENCY_CLEARANCE")

    # ------------------------------------------------------------------------
    # TEST 6: Preserves TEST_SIMULATION Data Provenance
    # ------------------------------------------------------------------------
    def test_06_preserves_test_simulation_data_source(self):
        """Verify data_source = TEST_SIMULATION is preserved through all 5 agents and into result."""
        raw_telemetry = ControlledTrafficSource.generate_balanced_traffic()
        result = self.pipeline.step(raw_telemetry)

        self.assertEqual(result.data_source, "TEST_SIMULATION")
        self.assertEqual(result.monitoring.data_source, "TEST_SIMULATION")
        self.assertEqual(result.analysis.data_source, "TEST_SIMULATION")
        self.assertEqual(result.optimization.data_source, "TEST_SIMULATION")
        self.assertEqual(result.supervisor.data_source, "TEST_SIMULATION")
        self.assertEqual(result.safety.data_source, "TEST_SIMULATION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
