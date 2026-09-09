"""
Comprehensive Unit Tests for Traffic Analysis Agent & Platoon Detection (Phase 4 & 5).
Validates Tests 1 through 14 as required by the system specification.
"""

import unittest
from datetime import datetime

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
    JunctionAnalysisState,
)

from app.agents.analysis_agent import TrafficAnalysisAgent


class TestTrafficAnalysisAgent(unittest.TestCase):

    def setUp(self):
        self.agent = TrafficAnalysisAgent()

    # ------------------------------------------------------------------------
    # TEST 1: JCI Mathematical Accuracy
    # ------------------------------------------------------------------------
    def test_01_jci_mathematical_accuracy(self):
        """
        Verify formula: JCI = 0.40 * NormQueue + 0.35 * NormDensity + 0.25 * NormOccupancy
        Test with deterministic exact inputs:
        Queue = 50.0m -> NormQueue = 50 / 100 = 0.50 (Contrib: 0.20)
        Avg Density = 24.0 veh/km -> NormDensity = 24 / 60 = 0.40 (Contrib: 0.14)
        Occupancy = 0.40 -> NormOccupancy = 0.40 (Contrib: 0.10)
        Expected JCI = 0.20 + 0.14 + 0.10 = 0.44
        """
        dir_data = {
            d: DirectionTrafficData(
                direction=d,
                vehicle_count=4,
                queue_length=12.5,  # 12.5 * 4 = 50.0m total queue
                traffic_density=24.0,  # avg density = 24.0 veh/km
            )
            for d in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]
        }
        state = JunctionTrafficState(
            junction_id="J1",
            data_source="TEST_SIMULATION",
            junction_occupancy=0.40,
            directions=dir_data,
        )

        jci = self.agent.compute_jci(state)
        self.assertEqual(jci.score, 0.44)
        self.assertEqual(jci.category, CongestionCategory.MODERATE)

    # ------------------------------------------------------------------------
    # TEST 2: JCI Factor Breakdown Accuracy
    # ------------------------------------------------------------------------
    def test_02_jci_factor_breakdown_accuracy(self):
        """Verify explainability breakdown components match exact formula weights and values."""
        dir_data = {
            Direction.NORTH: DirectionTrafficData(direction=Direction.NORTH, queue_length=40.0, traffic_density=20.0),
            Direction.SOUTH: DirectionTrafficData(direction=Direction.SOUTH, queue_length=20.0, traffic_density=20.0),
            Direction.EAST: DirectionTrafficData(direction=Direction.EAST, queue_length=0.0, traffic_density=10.0),
            Direction.WEST: DirectionTrafficData(direction=Direction.WEST, queue_length=0.0, traffic_density=10.0),
        }
        # Total queue = 60.0m -> NormQueue = 0.60
        # Avg density = (20+20+10+10)/4 = 15.0 -> NormDensity = 15/60 = 0.25
        # Occupancy = 0.20 -> NormOccupancy = 0.20
        state = JunctionTrafficState(
            junction_id="J1",
            data_source="TEST_SIMULATION",
            junction_occupancy=0.20,
            directions=dir_data,
        )

        jci = self.agent.compute_jci(state)
        fb = jci.factor_breakdown

        self.assertEqual(fb.queue.raw_value, 60.0)
        self.assertEqual(fb.queue.normalized_value, 0.60)
        self.assertEqual(fb.queue.weight, 0.40)
        self.assertEqual(fb.queue.contribution, 0.24)

        self.assertEqual(fb.density.raw_value, 15.0)
        self.assertEqual(fb.density.normalized_value, 0.25)
        self.assertEqual(fb.density.weight, 0.35)
        self.assertEqual(fb.density.contribution, 0.0875)

        self.assertEqual(fb.occupancy.raw_value, 0.20)
        self.assertEqual(fb.occupancy.normalized_value, 0.20)
        self.assertEqual(fb.occupancy.weight, 0.25)
        self.assertEqual(fb.occupancy.contribution, 0.05)

    # ------------------------------------------------------------------------
    # TEST 3: JCI Constrained Between 0.0 and 1.0
    # ------------------------------------------------------------------------
    def test_03_jci_boundary_constraints(self):
        """Verify extreme empty (0.0) and extreme congested (1.0) conditions stay within bounds."""
        # Empty condition
        empty_state = create_test_junction_state(
            north_count=0, south_count=0, east_count=0, west_count=0
        )
        for d in empty_state.directions.values():
            d.queue_length = 0.0
            d.traffic_density = 0.0
        empty_state.junction_occupancy = 0.0

        jci_empty = self.agent.compute_jci(empty_state)
        self.assertEqual(jci_empty.score, 0.0)
        self.assertEqual(jci_empty.category, CongestionCategory.LOW)

        # Extreme max overload condition (queue 500m, density 150, occupancy 1.0)
        overload_state = create_test_junction_state()
        for d in overload_state.directions.values():
            d.queue_length = 150.0  # 150 * 4 = 600m total queue
            d.traffic_density = 100.0
        overload_state.junction_occupancy = 1.0

        jci_overload = self.agent.compute_jci(overload_state)
        self.assertEqual(jci_overload.score, 1.0)
        self.assertEqual(jci_overload.category, CongestionCategory.SEVERE)

    # ------------------------------------------------------------------------
    # TEST 4: Exact 5-Vehicle Platoon Scenario (User Requirement)
    # ------------------------------------------------------------------------
    def test_04_exact_five_vehicle_platoon_scenario(self):
        """
        Exact scenario from prompt:
        5 vehicles approaching North: 60, 62, 59, 61, 60 km/h with close spacing.
        Expected: platoon_detected = TRUE.
        """
        vehicles = [
            ApproachingVehicle(
                vehicle_id="VEH-N-01",
                direction=Direction.NORTH,
                distance_to_junction=50.0,
                speed=60.0,
                estimated_time_of_arrival=ApproachingVehicle.compute_eta(50.0, 60.0),
            ),
            ApproachingVehicle(
                vehicle_id="VEH-N-02",
                direction=Direction.NORTH,
                distance_to_junction=75.0,
                speed=62.0,
                estimated_time_of_arrival=ApproachingVehicle.compute_eta(75.0, 62.0),
            ),
            ApproachingVehicle(
                vehicle_id="VEH-N-03",
                direction=Direction.NORTH,
                distance_to_junction=100.0,
                speed=59.0,
                estimated_time_of_arrival=ApproachingVehicle.compute_eta(100.0, 59.0),
            ),
            ApproachingVehicle(
                vehicle_id="VEH-N-04",
                direction=Direction.NORTH,
                distance_to_junction=125.0,
                speed=61.0,
                estimated_time_of_arrival=ApproachingVehicle.compute_eta(125.0, 61.0),
            ),
            ApproachingVehicle(
                vehicle_id="VEH-N-05",
                direction=Direction.NORTH,
                distance_to_junction=150.0,
                speed=60.0,
                estimated_time_of_arrival=ApproachingVehicle.compute_eta(150.0, 60.0),
            ),
        ]

        north_data = DirectionTrafficData(
            direction=Direction.NORTH,
            vehicle_count=5,
            average_speed=60.4,
            approaching_count=5,
            approaching_vehicle_details=vehicles,
            traffic_density=30.0,
        )

        platoon = self.agent.detect_platoon(north_data)

        self.assertTrue(platoon.platoon_detected)
        self.assertEqual(platoon.vehicle_count, 5)
        self.assertEqual(len(platoon.vehicle_ids), 5)
        self.assertEqual(platoon.average_speed_kmh, 60.4)
        # Sample std dev of [60, 62, 59, 61, 60] is ~1.14 km/h (<= 6.0)
        self.assertLessEqual(platoon.speed_dispersion_kmh, 6.0)
        self.assertEqual(platoon.lead_vehicle_distance_m, 50.0)
        self.assertEqual(platoon.lead_vehicle_eta_s, 3.0)  # 50 / (60 / 3.6) = 3.0s
        self.assertEqual(platoon.avg_headway_gap_m, 25.0)  # (75-50, 100-75, 125-100, 150-125) / 4 = 25.0

    # ------------------------------------------------------------------------
    # TEST 5: Platoon Rejected with Fewer than 3 Vehicles (Negative Test A)
    # ------------------------------------------------------------------------
    def test_05_platoon_rejected_fewer_than_three(self):
        """Only 2 vehicles -> platoon_detected = FALSE."""
        vehicles = [
            ApproachingVehicle(vehicle_id="V-1", direction=Direction.NORTH, distance_to_junction=40.0, speed=60.0, estimated_time_of_arrival=2.4),
            ApproachingVehicle(vehicle_id="V-2", direction=Direction.NORTH, distance_to_junction=65.0, speed=60.0, estimated_time_of_arrival=3.9),
        ]
        data = DirectionTrafficData(
            direction=Direction.NORTH, vehicle_count=2, approaching_vehicle_details=vehicles
        )
        platoon = self.agent.detect_platoon(data)
        self.assertFalse(platoon.platoon_detected)

    # ------------------------------------------------------------------------
    # TEST 6: Platoon Rejected with Slow Vehicles (Negative Test B)
    # ------------------------------------------------------------------------
    def test_06_platoon_rejected_slow_speed(self):
        """3 vehicles moving at 20 km/h (< 35 km/h) -> platoon_detected = FALSE."""
        vehicles = [
            ApproachingVehicle(vehicle_id="V-1", direction=Direction.NORTH, distance_to_junction=30.0, speed=20.0, estimated_time_of_arrival=5.4),
            ApproachingVehicle(vehicle_id="V-2", direction=Direction.NORTH, distance_to_junction=50.0, speed=22.0, estimated_time_of_arrival=8.1),
            ApproachingVehicle(vehicle_id="V-3", direction=Direction.NORTH, distance_to_junction=70.0, speed=21.0, estimated_time_of_arrival=12.0),
        ]
        data = DirectionTrafficData(
            direction=Direction.NORTH, vehicle_count=3, approaching_vehicle_details=vehicles
        )
        platoon = self.agent.detect_platoon(data)
        self.assertFalse(platoon.platoon_detected)

    # ------------------------------------------------------------------------
    # TEST 7: Platoon Rejected with Widely Spaced Vehicles (Negative Test C)
    # ------------------------------------------------------------------------
    def test_07_platoon_rejected_large_spacing(self):
        """3 vehicles with gap of 90m (> 45m and > 3s headway) -> platoon_detected = FALSE."""
        vehicles = [
            ApproachingVehicle(vehicle_id="V-1", direction=Direction.NORTH, distance_to_junction=40.0, speed=50.0, estimated_time_of_arrival=2.88),
            ApproachingVehicle(vehicle_id="V-2", direction=Direction.NORTH, distance_to_junction=130.0, speed=50.0, estimated_time_of_arrival=9.36),
            ApproachingVehicle(vehicle_id="V-3", direction=Direction.NORTH, distance_to_junction=220.0, speed=50.0, estimated_time_of_arrival=15.84),
        ]
        data = DirectionTrafficData(
            direction=Direction.NORTH, vehicle_count=3, approaching_vehicle_details=vehicles
        )
        platoon = self.agent.detect_platoon(data)
        self.assertFalse(platoon.platoon_detected)

    # ------------------------------------------------------------------------
    # TEST 8: Platoon Rejected with Inconsistent Speeds (Negative Test D)
    # ------------------------------------------------------------------------
    def test_08_platoon_rejected_inconsistent_speeds(self):
        """3 vehicles with erratic speeds: 35, 60, 80 km/h (spread=45 > 8) -> platoon_detected = FALSE."""
        vehicles = [
            ApproachingVehicle(vehicle_id="V-1", direction=Direction.NORTH, distance_to_junction=40.0, speed=35.0, estimated_time_of_arrival=4.1),
            ApproachingVehicle(vehicle_id="V-2", direction=Direction.NORTH, distance_to_junction=60.0, speed=60.0, estimated_time_of_arrival=3.6),
            ApproachingVehicle(vehicle_id="V-3", direction=Direction.NORTH, distance_to_junction=85.0, speed=80.0, estimated_time_of_arrival=3.8),
        ]
        data = DirectionTrafficData(
            direction=Direction.NORTH, vehicle_count=3, approaching_vehicle_details=vehicles
        )
        platoon = self.agent.detect_platoon(data)
        self.assertFalse(platoon.platoon_detected)

    # ------------------------------------------------------------------------
    # TEST 9: Platoon Detection is Strictly Direction-Specific (Negative Test E)
    # ------------------------------------------------------------------------
    def test_09_platoon_direction_specific(self):
        """Vehicles from different approaches (2 North, 2 East) must not be grouped together."""
        north_v = [
            ApproachingVehicle(vehicle_id="VN-1", direction=Direction.NORTH, distance_to_junction=40.0, speed=60.0, estimated_time_of_arrival=2.4),
            ApproachingVehicle(vehicle_id="VN-2", direction=Direction.NORTH, distance_to_junction=65.0, speed=60.0, estimated_time_of_arrival=3.9),
        ]
        east_v = [
            ApproachingVehicle(vehicle_id="VE-1", direction=Direction.EAST, distance_to_junction=40.0, speed=60.0, estimated_time_of_arrival=2.4),
            ApproachingVehicle(vehicle_id="VE-2", direction=Direction.EAST, distance_to_junction=65.0, speed=60.0, estimated_time_of_arrival=3.9),
        ]

        north_data = DirectionTrafficData(direction=Direction.NORTH, vehicle_count=2, approaching_vehicle_details=north_v)
        east_data = DirectionTrafficData(direction=Direction.EAST, vehicle_count=2, approaching_vehicle_details=east_v)

        platoon_north = self.agent.detect_platoon(north_data)
        platoon_east = self.agent.detect_platoon(east_data)

        # Neither has >= 3 vehicles, so neither forms a platoon
        self.assertFalse(platoon_north.platoon_detected)
        self.assertFalse(platoon_east.platoon_detected)

    # ------------------------------------------------------------------------
    # TEST 10: Deterministic ETA Calculation Accuracy
    # ------------------------------------------------------------------------
    def test_10_eta_calculation_accuracy(self):
        """Verify ETA = distance_m / (speed_kmh / 3.6) handled cleanly for all speeds."""
        # 120m at 72 km/h (20 m/s) -> exactly 6.0s
        self.assertEqual(ApproachingVehicle.compute_eta(120.0, 72.0), 6.0)

        # 90m at 54 km/h (15 m/s) -> exactly 6.0s
        self.assertEqual(ApproachingVehicle.compute_eta(90.0, 54.0), 6.0)

        # 0 km/h -> 999.0s (safe stopped value, no ZeroDivisionError)
        self.assertEqual(ApproachingVehicle.compute_eta(10.0, 0.0), 999.0)

    # ------------------------------------------------------------------------
    # TEST 11: Critical Direction Identification
    # ------------------------------------------------------------------------
    def test_11_critical_direction_identification(self):
        """Identifies corridor with highest load analytically without signal decision."""
        dir_data = {
            Direction.NORTH: DirectionTrafficData(direction=Direction.NORTH, queue_length=5.0, traffic_density=10.0),
            Direction.SOUTH: DirectionTrafficData(direction=Direction.SOUTH, queue_length=0.0, traffic_density=8.0),
            # East has huge queue and density
            Direction.EAST: DirectionTrafficData(direction=Direction.EAST, queue_length=45.0, traffic_density=38.0, vehicle_count=12),
            Direction.WEST: DirectionTrafficData(direction=Direction.WEST, queue_length=10.0, traffic_density=12.0),
        }
        state = JunctionTrafficState(junction_id="J1", data_source="TEST_SIMULATION", directions=dir_data)
        analysis = self.agent.analyze(state)

        self.assertEqual(analysis.critical_direction, Direction.EAST)
        self.assertEqual(analysis.directions[Direction.EAST].congestion_level, CongestionCategory.SEVERE)

    # ------------------------------------------------------------------------
    # TEST 12: Traffic Regime Classification
    # ------------------------------------------------------------------------
    def test_12_traffic_regime_classification(self):
        """Verifies deterministic mapping: JCI < 0.35: NON_PEAK, 0.35-0.64: TRANSITION, >= 0.65: PEAK."""
        self.assertEqual(self.agent.classify_traffic_regime(0.20), TrafficRegime.NON_PEAK)
        self.assertEqual(self.agent.classify_traffic_regime(0.45), TrafficRegime.TRANSITION)
        self.assertEqual(self.agent.classify_traffic_regime(0.70), TrafficRegime.PEAK)

    # ------------------------------------------------------------------------
    # TEST 13: Strict Absence of Signal Decision Fields
    # ------------------------------------------------------------------------
    def test_13_strict_absence_of_signal_decision_fields(self):
        """Ensure Analysis Agent output NEVER contains signal phase recommendations or commands."""
        state = create_test_junction_state()
        analysis = self.agent.analyze(state)
        summary = self.agent.get_summary(analysis)

        forbidden_keys = [
            "recommended_phase",
            "recommended_green_extension",
            "signal_command",
            "switch_to_east",
            "switch_to_north",
            "mqtt_command",
            "execute_phase",
            "action",
        ]

        for key in forbidden_keys:
            self.assertNotIn(key, summary, f"Forbidden decision field leaked in summary: {key}")
            self.assertNotIn(key, analysis.model_dump(), f"Forbidden decision field leaked in model: {key}")

    # ------------------------------------------------------------------------
    # TEST 14: TEST_SIMULATION Source Metadata Preserved
    # ------------------------------------------------------------------------
    def test_14_test_simulation_metadata_preserved(self):
        """Verify data_source is strictly preserved as TEST_SIMULATION."""
        state = create_test_junction_state()
        self.assertEqual(state.data_source, "TEST_SIMULATION")

        analysis = self.agent.analyze(state)
        self.assertEqual(analysis.data_source, "TEST_SIMULATION")

        summary = self.agent.get_summary(analysis)
        self.assertEqual(summary["data_source"], "TEST_SIMULATION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
