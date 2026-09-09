import unittest
from datetime import datetime
from pydantic import ValidationError

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

class TestTrafficDataModel(unittest.TestCase):

    def test_approaching_vehicle_eta_calculation(self):
        """Verify deterministic physical ETA = distance / (speed / 3.6)."""
        # 100m at 72 km/h (20 m/s) -> 5.0 seconds
        eta = ApproachingVehicle.compute_eta(distance_m=100.0, speed_kmh=72.0)
        self.assertEqual(eta, 5.0)

        # Stationary vehicle (0 km/h) -> 999.0s (queued/stopped)
        eta_stop = ApproachingVehicle.compute_eta(distance_m=10.0, speed_kmh=0.0)
        self.assertEqual(eta_stop, 999.0)

        vehicle = ApproachingVehicle(
            vehicle_id="VEH-TEST-01",
            direction=Direction.NORTH,
            distance_to_junction=80.0,
            speed=60.0,
            estimated_time_of_arrival=ApproachingVehicle.compute_eta(80.0, 60.0),
            acceleration=-1.5,
            speed_trend=SpeedTrend.DECELERATING,
        )
        self.assertEqual(vehicle.vehicle_id, "VEH-TEST-01")
        self.assertEqual(vehicle.direction, Direction.NORTH)
        self.assertEqual(vehicle.speed, 60.0)
        self.assertEqual(vehicle.estimated_time_of_arrival, 4.8)  # 80 / (60 / 3.6) = 4.8
        self.assertEqual(vehicle.speed_trend, SpeedTrend.DECELERATING)

    def test_approaching_vehicle_validation_constraints(self):
        """Ensure negative distances or speeds trigger validation errors."""
        with self.assertRaises(ValidationError):
            ApproachingVehicle(
                vehicle_id="BAD-01",
                direction=Direction.SOUTH,
                distance_to_junction=-5.0,  # Invalid negative
                speed=50.0,
                estimated_time_of_arrival=2.0,
            )

        with self.assertRaises(ValidationError):
            ApproachingVehicle(
                vehicle_id="BAD-02",
                direction=Direction.EAST,
                distance_to_junction=50.0,
                speed=-10.0,  # Invalid negative
                estimated_time_of_arrival=2.0,
            )

    def test_direction_traffic_data_auto_sync(self):
        """Verify that DirectionTrafficData automatically infers approaching_count and earliest ETA."""
        v1 = ApproachingVehicle(
            vehicle_id="V-1",
            direction=Direction.NORTH,
            distance_to_junction=50.0,
            speed=50.0,
            estimated_time_of_arrival=3.6,
        )
        v2 = ApproachingVehicle(
            vehicle_id="V-2",
            direction=Direction.NORTH,
            distance_to_junction=120.0,
            speed=60.0,
            estimated_time_of_arrival=7.2,
        )

        direction_data = DirectionTrafficData(
            direction=Direction.NORTH,
            vehicle_count=2,
            queue_length=0.0,
            average_speed=55.0,
            approaching_vehicle_details=[v1, v2],
            traffic_density=10.4,
        )

        # Auto-synced
        self.assertEqual(direction_data.approaching_count, 2)
        self.assertEqual(direction_data.estimated_arrival_time, 3.6)  # Min of [3.6, 7.2]

    def test_junction_traffic_state_aggregations(self):
        """Verify junction-level totals and corridor counts."""
        state = create_test_junction_state(
            signal_phase=SignalPhase.NS_GREEN,
            remaining_green=30.0,
            regime=TrafficRegime.PEAK,
            north_count=8,
            south_count=6,
            east_count=3,
            west_count=4,
        )

        self.assertEqual(state.total_vehicle_count, 21)  # 8 + 6 + 3 + 4
        self.assertEqual(state.get_corridor_count("NS"), 14)  # 8 + 6
        self.assertEqual(state.get_corridor_count("EW"), 7)   # 3 + 4
        self.assertEqual(state.data_source, "TEST_SIMULATION")
        self.assertEqual(state.traffic_state, TrafficRegime.PEAK)
        self.assertEqual(state.current_signal_phase, SignalPhase.NS_GREEN)

    def test_json_serialization_roundtrip(self):
        """Ensure lossless JSON serialization and deserialization across agents."""
        original_state = create_test_junction_state()
        json_str = original_state.model_dump_json()
        self.assertIsInstance(json_str, str)
        self.assertIn("TEST_SIMULATION", json_str)

        restored_state = JunctionTrafficState.model_validate_json(json_str)
        self.assertEqual(restored_state.junction_id, original_state.junction_id)
        self.assertEqual(restored_state.total_vehicle_count, original_state.total_vehicle_count)
        self.assertEqual(restored_state.current_signal_phase, original_state.current_signal_phase)
        self.assertEqual(
            restored_state.directions[Direction.NORTH].vehicle_count,
            original_state.directions[Direction.NORTH].vehicle_count
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
