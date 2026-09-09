"""
Automated Unit Tests for Traffic Optimization Agent (Phase 6).
Validates advisory recommendations, platoon extensions, queue dissipation,
and strict non-conclusion of safety.
"""

import unittest
from datetime import datetime

from app.models.traffic_data import (
    Direction,
    SignalPhase,
    TrafficRegime,
    ApproachingVehicle,
    DirectionTrafficData,
    JunctionTrafficState,
    create_test_junction_state,
)

from app.models.analysis_data import (
    CongestionCategory,
    JunctionCongestionIndex,
    JciFactorBreakdown,
    FactorContribution,
    PlatoonDetail,
    DirectionAnalysis,
    JunctionAnalysisState,
)

from app.models.optimization_data import (
    OptimizationAction,
    RecommendationUrgency,
    OptimizationRecommendation,
)

from app.agents.analysis_agent import TrafficAnalysisAgent
from app.agents.optimization_agent import TrafficOptimizationAgent


class TestTrafficOptimizationAgent(unittest.TestCase):

    def setUp(self):
        self.opt_agent = TrafficOptimizationAgent()
        self.analysis_agent = TrafficAnalysisAgent()

    # ------------------------------------------------------------------------
    # TEST 1: Platoon Extension Recommendation
    # ------------------------------------------------------------------------
    def test_01_platoon_green_extension_recommendation(self):
        """
        When active green corridor (NS_GREEN) has an approaching platoon (North)
        with lead ETA = 5.0s, and remaining green is only 3.0s:
        Optimization Agent should recommend EXTEND_GREEN (e.g., +5.5s to +7.0s).
        """
        vehicles = [
            ApproachingVehicle(vehicle_id="V1", direction=Direction.NORTH, distance_to_junction=60.0, speed=60.0, estimated_time_of_arrival=3.6),
            ApproachingVehicle(vehicle_id="V2", direction=Direction.NORTH, distance_to_junction=85.0, speed=61.0, estimated_time_of_arrival=5.0),
            ApproachingVehicle(vehicle_id="V3", direction=Direction.NORTH, distance_to_junction=110.0, speed=59.0, estimated_time_of_arrival=6.7),
            ApproachingVehicle(vehicle_id="V4", direction=Direction.NORTH, distance_to_junction=135.0, speed=60.0, estimated_time_of_arrival=8.1),
        ]
        north_data = DirectionTrafficData(
            direction=Direction.NORTH,
            vehicle_count=4,
            average_speed=60.0,
            approaching_count=4,
            approaching_vehicle_details=vehicles,
            traffic_density=26.7,
        )
        dir_data = {
            Direction.NORTH: north_data,
            Direction.SOUTH: DirectionTrafficData(direction=Direction.SOUTH, vehicle_count=1),
            Direction.EAST: DirectionTrafficData(direction=Direction.EAST, vehicle_count=1),
            Direction.WEST: DirectionTrafficData(direction=Direction.WEST, vehicle_count=1),
        }
        mon_state = JunctionTrafficState(
            junction_id="J1",
            data_source="TEST_SIMULATION",
            current_signal_phase=SignalPhase.NS_GREEN,
            remaining_green_time=3.0,  # Low remaining green!
            directions=dir_data,
        )

        analysis_state = self.analysis_agent.analyze(mon_state)
        self.assertIn(Direction.NORTH, analysis_state.platoons_detected)

        rec = self.opt_agent.optimize(mon_state, analysis_state)

        self.assertEqual(rec.action, OptimizationAction.EXTEND_GREEN)
        self.assertEqual(rec.target_phase, SignalPhase.NS_GREEN)
        self.assertGreater(rec.extension_seconds, 0.0)
        self.assertGreaterEqual(rec.extension_seconds, 5.0)
        self.assertLessEqual(rec.extension_seconds, 10.0)
        self.assertEqual(rec.rationale.primary_factor, "PLATOON_CONTINUITY")

    # ------------------------------------------------------------------------
    # TEST 2: Optimization is NOT Safety (Strict Separation)
    # ------------------------------------------------------------------------
    def test_02_optimization_does_not_conclude_safety(self):
        """
        The Optimization Agent recommends 'EXTEND GREEN', but NEVER claims 'THIS IS SAFE'.
        Safety validation belongs strictly to the Safety Agent.
        """
        mon_state = create_test_junction_state(signal_phase=SignalPhase.NS_GREEN, remaining_green=3.0)
        analysis_state = self.analysis_agent.analyze(mon_state)

        rec = self.opt_agent.optimize(mon_state, analysis_state)
        rec_dump = rec.model_dump()

        # Forbidden safety assertion fields
        forbidden_safety_claims = [
            "is_safe",
            "safety_verified",
            "clearance_approved",
            "conflicts_resolved",
            "failsafe_passed",
        ]
        for claim in forbidden_safety_claims:
            self.assertNotIn(claim, rec_dump)

        # Verify safety disclaimer exists
        self.assertIn("Supervisor Agent", rec.rationale.safety_disclaimer)
        self.assertIn("Safety Agent", rec.rationale.safety_disclaimer)

    # ------------------------------------------------------------------------
    # TEST 3: Opposing Heavy Queue Relief Phase Switch
    # ------------------------------------------------------------------------
    def test_03_opposing_queue_relief_switch(self):
        """
        When East approach has a 45m queue (critical direction) and active NS green
        has low remaining time without platoon, recommend SWITCH_PHASE to EW_GREEN.
        """
        dir_data = {
            Direction.NORTH: DirectionTrafficData(direction=Direction.NORTH, queue_length=0.0, traffic_density=5.0),
            Direction.SOUTH: DirectionTrafficData(direction=Direction.SOUTH, queue_length=0.0, traffic_density=5.0),
            Direction.EAST: DirectionTrafficData(direction=Direction.EAST, queue_length=45.0, traffic_density=40.0, vehicle_count=10),
            Direction.WEST: DirectionTrafficData(direction=Direction.WEST, queue_length=5.0, traffic_density=8.0),
        }
        mon_state = JunctionTrafficState(
            junction_id="J1",
            data_source="TEST_SIMULATION",
            current_signal_phase=SignalPhase.NS_GREEN,
            remaining_green_time=4.0,  # Green expiring soon
            directions=dir_data,
        )

        analysis_state = self.analysis_agent.analyze(mon_state)
        self.assertEqual(analysis_state.critical_direction, Direction.EAST)

        rec = self.opt_agent.optimize(mon_state, analysis_state)

        self.assertEqual(rec.action, OptimizationAction.SWITCH_PHASE)
        self.assertEqual(rec.target_phase, SignalPhase.EW_GREEN)
        self.assertGreaterEqual(rec.recommended_duration_s, 20.0)
        self.assertEqual(rec.rationale.primary_factor, "QUEUE_DISSIPATION")

    # ------------------------------------------------------------------------
    # TEST 4: Nominal Flow Maintenance
    # ------------------------------------------------------------------------
    def test_04_nominal_flow_maintenance(self):
        """When conditions are nominal and ample green remains, recommend MAINTAIN_CURRENT."""
        mon_state = create_test_junction_state(
            signal_phase=SignalPhase.NS_GREEN,
            remaining_green=20.0,
            north_count=2,
            south_count=2,
            east_count=1,
            west_count=1,
        )
        analysis_state = self.analysis_agent.analyze(mon_state)

        rec = self.opt_agent.optimize(mon_state, analysis_state)

        self.assertEqual(rec.action, OptimizationAction.MAINTAIN_CURRENT)
        self.assertEqual(rec.target_phase, SignalPhase.NS_GREEN)
        self.assertEqual(rec.extension_seconds, 0.0)

    # ------------------------------------------------------------------------
    # TEST 5: Strict Absence of Hardware Actuation / MQTT
    # ------------------------------------------------------------------------
    def test_05_strict_absence_of_hardware_actuation(self):
        """The Optimization Agent must NEVER contain MQTT topics, GPIO pin writes, or execution commands."""
        mon_state = create_test_junction_state()
        analysis_state = self.analysis_agent.analyze(mon_state)
        rec = self.opt_agent.optimize(mon_state, analysis_state)
        summary = self.opt_agent.get_summary(rec)

        forbidden_execution_fields = [
            "mqtt_topic",
            "mqtt_payload",
            "gpio_command",
            "execute_now",
            "actuator_command",
            "esp32_ack",
        ]
        for field in forbidden_execution_fields:
            self.assertNotIn(field, summary)
            self.assertNotIn(field, rec.model_dump())

    # ------------------------------------------------------------------------
    # TEST 6: Preserves TEST_SIMULATION Data Source
    # ------------------------------------------------------------------------
    def test_06_preserves_test_simulation_data_source(self):
        """Preserves TEST_SIMULATION metadata label."""
        mon_state = create_test_junction_state()
        analysis_state = self.analysis_agent.analyze(mon_state)
        rec = self.opt_agent.optimize(mon_state, analysis_state)

        self.assertEqual(rec.data_source, "TEST_SIMULATION")
        summary = self.opt_agent.get_summary(rec)
        self.assertEqual(summary["data_source"], "TEST_SIMULATION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
