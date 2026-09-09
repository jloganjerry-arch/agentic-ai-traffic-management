"""
Controlled Traffic Telemetry Source (Test & Simulation Feeder).
Generates realistic, deterministic raw traffic observations tagged explicitly
as TEST_SIMULATION without requiring external simulators or YOLO.
"""

from typing import Dict, Any, List
from datetime import datetime


class ControlledTrafficSource:
    """
    Generates synthetic raw observation telemetry representing camera/radar detector feeds.
    Strictly tagged as TEST_SIMULATION.
    """

    @staticmethod
    def generate_balanced_traffic() -> Dict[str, Any]:
        """Scenario 1: Balanced nominal flow across all 4 corridors."""
        return {
            "source_type": "TEST_SIMULATION",
            "timestamp": datetime.now().isoformat(),
            "junction_id": "JUNCTION-01",
            "current_signal_phase": "NS_GREEN",
            "remaining_green_time": 20.0,
            "junction_occupancy": 0.12,
            "traffic_state": "NON_PEAK",
            "raw_corridor_data": {
                "NORTH": {
                    "detected_vehicles": [
                        {"id": "V-N-01", "distance_m": 45.0, "speed_kmh": 48.0, "acceleration": 0.0},
                        {"id": "V-N-02", "distance_m": 75.0, "speed_kmh": 50.0, "acceleration": 0.5},
                        {"id": "V-N-03", "distance_m": 110.0, "speed_kmh": 52.0, "acceleration": 0.0},
                    ],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
                "SOUTH": {
                    "detected_vehicles": [
                        {"id": "V-S-01", "distance_m": 35.0, "speed_kmh": 46.0, "acceleration": 0.0},
                        {"id": "V-S-02", "distance_m": 80.0, "speed_kmh": 47.0, "acceleration": -0.2},
                    ],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
                "EAST": {
                    "detected_vehicles": [
                        {"id": "V-E-01", "distance_m": 25.0, "speed_kmh": 0.0, "acceleration": 0.0},
                        {"id": "V-E-02", "distance_m": 32.0, "speed_kmh": 0.0, "acceleration": 0.0},
                    ],
                    "queued_count": 2,
                    "queue_length_m": 14.0,
                },
                "WEST": {
                    "detected_vehicles": [
                        {"id": "V-W-01", "distance_m": 60.0, "speed_kmh": 42.0, "acceleration": 0.0},
                    ],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
            },
        }

    @staticmethod
    def generate_congested_north_queue() -> Dict[str, Any]:
        """Scenario 2: Congested North corridor with a heavy queue waiting at the signal."""
        return {
            "source_type": "TEST_SIMULATION",
            "timestamp": datetime.now().isoformat(),
            "junction_id": "JUNCTION-01",
            "current_signal_phase": "EW_GREEN",
            "remaining_green_time": 15.0,
            "junction_occupancy": 0.28,
            "traffic_state": "PEAK",
            "raw_corridor_data": {
                "NORTH": {
                    "detected_vehicles": [
                        {"id": "V-N-01", "distance_m": 5.0, "speed_kmh": 0.0, "acceleration": 0.0},
                        {"id": "V-N-02", "distance_m": 12.0, "speed_kmh": 0.0, "acceleration": 0.0},
                        {"id": "V-N-03", "distance_m": 19.0, "speed_kmh": 0.0, "acceleration": 0.0},
                        {"id": "V-N-04", "distance_m": 26.0, "speed_kmh": 0.0, "acceleration": 0.0},
                        {"id": "V-N-05", "distance_m": 33.0, "speed_kmh": 0.0, "acceleration": 0.0},
                        {"id": "V-N-06", "distance_m": 45.0, "speed_kmh": 12.0, "acceleration": -1.5},
                        {"id": "V-N-07", "distance_m": 60.0, "speed_kmh": 22.0, "acceleration": -1.0},
                    ],
                    "queued_count": 5,
                    "queue_length_m": 35.0,
                },
                "SOUTH": {
                    "detected_vehicles": [
                        {"id": "V-S-01", "distance_m": 30.0, "speed_kmh": 0.0, "acceleration": 0.0},
                        {"id": "V-S-02", "distance_m": 50.0, "speed_kmh": 15.0, "acceleration": -0.8},
                    ],
                    "queued_count": 1,
                    "queue_length_m": 7.0,
                },
                "EAST": {
                    "detected_vehicles": [
                        {"id": "V-E-01", "distance_m": 15.0, "speed_kmh": 40.0, "acceleration": 0.0},
                        {"id": "V-E-02", "distance_m": 40.0, "speed_kmh": 45.0, "acceleration": 0.0},
                    ],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
                "WEST": {
                    "detected_vehicles": [
                        {"id": "V-W-01", "distance_m": 20.0, "speed_kmh": 38.0, "acceleration": 0.0},
                    ],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
            },
        }

    @staticmethod
    def generate_high_speed_approaching_scenario() -> Dict[str, Any]:
        """Scenario 3: Fast vehicles approaching East corridor with short ETAs."""
        return {
            "source_type": "TEST_SIMULATION",
            "timestamp": datetime.now().isoformat(),
            "junction_id": "JUNCTION-01",
            "current_signal_phase": "NS_GREEN",
            "remaining_green_time": 8.0,
            "junction_occupancy": 0.08,
            "traffic_state": "TRANSITION",
            "raw_corridor_data": {
                "NORTH": {
                    "detected_vehicles": [
                        {"id": "V-N-01", "distance_m": 50.0, "speed_kmh": 35.0, "acceleration": 0.0}
                    ],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
                "SOUTH": {
                    "detected_vehicles": [],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
                "EAST": {
                    "detected_vehicles": [
                        {"id": "V-E-FAST-01", "distance_m": 80.0, "speed_kmh": 65.0, "acceleration": 0.2},
                        {"id": "V-E-FAST-02", "distance_m": 110.0, "speed_kmh": 64.0, "acceleration": 0.0},
                    ],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
                "WEST": {
                    "detected_vehicles": [
                        {"id": "V-W-01", "distance_m": 70.0, "speed_kmh": 30.0, "acceleration": 0.0}
                    ],
                    "queued_count": 0,
                    "queue_length_m": 0.0,
                },
            },
        }
