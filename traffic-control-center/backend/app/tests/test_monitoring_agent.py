"""
Automated Unit Tests for Traffic Monitoring Agent (Phase 3).
Verifies pure observation, telemetry measurement, and lack of any decision-making.
"""

import unittest
from datetime import datetime

from app.models.traffic_data import Direction, SignalPhase, TrafficRegime, SpeedTrend
from app.agents.monitoring_agent import TrafficMonitoringAgent
from app.agents.controlled_traffic_source import ControlledTrafficSource


class TestTrafficMonitoringAgent(unittest.TestCase):

    def setUp(self):
        self.agent = TrafficMonitoringAgent()

    def test_agent_metadata_and_responsibility(self):
        """Verify agent role is strictly monitoring without decision logic."""
        self.assertEqual(self.agent.id, "agent-1")
        self.assertEqual(self.agent.name, "Traffic Monitoring Agent")
        self.assertEqual(self.agent.responsibility, "WHAT IS HAPPENING?")
        self.assertEqual(self.agent.data_source_label, "TEST_SIMULATION")

    def test_ingest_balanced_scenario(self):
        """Verify ingestion of balanced traffic scenario into structured measurements."""
        raw_data = ControlledTrafficSource.generate_balanced_traffic()
        state = self.agent.process_raw_observation(raw_data)

        # Basic metadata
        self.assertEqual(state.junction_id, "JUNCTION-01")
        self.assertEqual(state.data_source, "TEST_SIMULATION")
        self.assertEqual(state.current_signal_phase, SignalPhase.NS_GREEN)
        self.assertEqual(state.traffic_state, TrafficRegime.NON_PEAK)

        # Vehicle counts: North(3), South(2), East(2), West(1) = 8
        self.assertEqual(state.total_vehicle_count, 8)
        self.assertEqual(state.directions[Direction.NORTH].vehicle_count, 3)
        self.assertEqual(state.directions[Direction.SOUTH].vehicle_count, 2)
        self.assertEqual(state.directions[Direction.EAST].vehicle_count, 2)
        self.assertEqual(state.directions[Direction.WEST].vehicle_count, 1)

        # Queue verification: East has 2 queued vehicles (14.0m)
        self.assertEqual(state.directions[Direction.EAST].queue_length, 14.0)
        self.assertEqual(state.directions[Direction.NORTH].queue_length, 0.0)

        # Approaching count: East vehicles are stationary (speed 0), so approaching = 0
        self.assertEqual(state.directions[Direction.EAST].approaching_count, 0)
        # North vehicles are all moving, so approaching = 3
        self.assertEqual(state.directions[Direction.NORTH].approaching_count, 3)

    def test_approaching_vehicle_telemetry_and_eta(self):
        """Verify approaching vehicle telemetry details, distance, speed, and ETA."""
        raw_data = ControlledTrafficSource.generate_high_speed_approaching_scenario()
        state = self.agent.process_raw_observation(raw_data)

        east_data = state.directions[Direction.EAST]
        self.assertEqual(east_data.approaching_count, 2)
        self.assertEqual(len(east_data.approaching_vehicle_details), 2)

        v1 = east_data.approaching_vehicle_details[0]
        self.assertEqual(v1.vehicle_id, "V-E-FAST-01")
        self.assertEqual(v1.distance_to_junction, 80.0)
        self.assertEqual(v1.speed, 65.0)
        # ETA = 80 / (65 / 3.6) = 4.43 seconds
        self.assertEqual(v1.estimated_time_of_arrival, 4.43)
        self.assertEqual(v1.speed_trend, SpeedTrend.ACCELERATING)

        # Earliest ETA in East corridor should match v1's ETA
        self.assertEqual(east_data.estimated_arrival_time, 4.43)

    def test_congested_queue_measurements(self):
        """Verify queue length and vehicle position arrays on congested approach."""
        raw_data = ControlledTrafficSource.generate_congested_north_queue()
        state = self.agent.process_raw_observation(raw_data)

        north_data = state.directions[Direction.NORTH]
        self.assertEqual(north_data.vehicle_count, 7)
        self.assertEqual(north_data.queue_length, 35.0)
        # 7 positions tracked
        self.assertEqual(len(north_data.vehicle_positions), 7)
        self.assertEqual(north_data.vehicle_positions[0], 5.0)
        self.assertEqual(len(north_data.vehicle_speeds), 7)

    def test_strict_absence_of_decision_logic(self):
        """Ensure Monitoring Agent output contains ZERO signal decision or control fields."""
        raw_data = ControlledTrafficSource.generate_congested_north_queue()
        state = self.agent.process_raw_observation(raw_data)
        summary = self.agent.get_telemetry_summary(state)

        # Forbidden control decision keys
        forbidden_keys = [
            "recommended_phase",
            "recommended_green_extension",
            "decision",
            "action",
            "approved",
            "rejected",
            "control_decision",
            "target_approach",
        ]

        for key in forbidden_keys:
            self.assertNotIn(key, summary, f"Monitoring Agent leaked decision field: {key}")

        # Ensure pure telemetry fields exist
        self.assertIn("total_vehicle_count", summary)
        self.assertIn("total_queue_length_m", summary)
        self.assertIn("total_approaching_count", summary)
        self.assertIn("per_direction", summary)
        self.assertEqual(summary["question_answered"], "WHAT IS HAPPENING?")
        self.assertEqual(summary["data_source"], "TEST_SIMULATION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
