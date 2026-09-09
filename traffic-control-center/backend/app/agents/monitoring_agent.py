"""
Traffic Monitoring Agent (Agent 1).
Responsibility: "WHAT IS HAPPENING?"

Ingests raw sensor/simulation observation telemetry and produces structured,
validated traffic measurements conforming to JunctionTrafficState.
Strictly contains ZERO signal decision logic.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.traffic_data import (
    Direction,
    SignalPhase,
    TrafficRegime,
    SpeedTrend,
    ApproachingVehicle,
    DirectionTrafficData,
    JunctionTrafficState,
)


class TrafficMonitoringAgent:
    """
    Agent 1: Ingests traffic observation feeds and produces empirical,
    physical measurements for the intersection.
    Does NOT recommend signals or make control decisions.
    """

    def __init__(self, agent_id: str = "agent-1"):
        self.id = agent_id
        self.name = "Traffic Monitoring Agent"
        self.role = "Traffic Observation & Telemetry Ingestion"
        self.responsibility = "WHAT IS HAPPENING?"
        self.data_source_label = "TEST_SIMULATION"

    def process_raw_observation(self, raw_data: Dict[str, Any]) -> JunctionTrafficState:
        """
        Transforms raw observation telemetry into a validated JunctionTrafficState.
        Pure empirical calculation without decision logic.
        """
        corridor_data = raw_data.get("raw_corridor_data", {})
        directions_map: Dict[Direction, DirectionTrafficData] = {}

        for dir_enum in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
            dir_key = dir_enum.value
            raw_dir = corridor_data.get(dir_key, {})
            detected_vehicles = raw_dir.get("detected_vehicles", [])

            vehicle_positions: List[float] = []
            vehicle_speeds: List[float] = []
            approaching_details: List[ApproachingVehicle] = []

            for veh in detected_vehicles:
                v_id = veh.get("id", f"V-{dir_key[:1]}-UNK")
                dist = float(veh.get("distance_m", 0.0))
                spd = float(veh.get("speed_kmh", 0.0))
                acc = float(veh.get("acceleration", 0.0))

                vehicle_positions.append(dist)
                vehicle_speeds.append(spd)

                # Determine speed trend from acceleration
                if acc > 0.1:
                    trend = SpeedTrend.ACCELERATING
                elif acc < -0.1:
                    trend = SpeedTrend.DECELERATING
                else:
                    trend = SpeedTrend.CONSTANT

                # Compute deterministic ETA
                eta = ApproachingVehicle.compute_eta(distance_m=dist, speed_kmh=spd)

                # Vehicles with speed > 5 km/h moving towards junction are considered approaching
                if spd > 5.0 and dist > 0.0:
                    approaching_details.append(
                        ApproachingVehicle(
                            vehicle_id=v_id,
                            direction=dir_enum,
                            distance_to_junction=round(dist, 1),
                            speed=round(spd, 1),
                            estimated_time_of_arrival=eta,
                            acceleration=round(acc, 2),
                            speed_trend=trend,
                        )
                    )

            # Metrics
            veh_count = len(detected_vehicles)
            queue_len = float(raw_dir.get("queue_length_m", 0.0))
            avg_speed = (
                round(sum(vehicle_speeds) / veh_count, 1) if veh_count > 0 else 0.0
            )
            # Detector zone is 150m: density = (count / 0.150 km) = count * 6.67 veh/km
            traffic_density = round(veh_count * 6.67, 1)
            earliest_eta = (
                min(v.estimated_time_of_arrival for v in approaching_details)
                if approaching_details
                else None
            )

            directions_map[dir_enum] = DirectionTrafficData(
                direction=dir_enum,
                vehicle_count=veh_count,
                queue_length=round(queue_len, 1),
                average_speed=avg_speed,
                approaching_count=len(approaching_details),
                approaching_vehicle_details=approaching_details,
                vehicle_positions=vehicle_positions,
                vehicle_speeds=vehicle_speeds,
                estimated_arrival_time=earliest_eta,
                traffic_density=traffic_density,
            )

        # Parse phase and regime with safe fallbacks
        phase_str = raw_data.get("current_signal_phase", "NS_GREEN")
        try:
            current_phase = SignalPhase[phase_str]
        except KeyError:
            current_phase = SignalPhase.NS_GREEN

        regime_str = raw_data.get("traffic_state", "NON_PEAK")
        try:
            traffic_regime = TrafficRegime[regime_str]
        except KeyError:
            traffic_regime = TrafficRegime.NON_PEAK

        # Construct validated state
        return JunctionTrafficState(
            junction_id=raw_data.get("junction_id", "JUNCTION-01"),
            timestamp=datetime.now(),
            data_source=self.data_source_label,
            current_signal_phase=current_phase,
            remaining_green_time=float(raw_data.get("remaining_green_time", 0.0)),
            junction_occupancy=float(raw_data.get("junction_occupancy", 0.0)),
            traffic_state=traffic_regime,
            directions=directions_map,
        )

    def get_telemetry_summary(self, state: JunctionTrafficState) -> Dict[str, Any]:
        """
        Formats a clean, serialized summary for the downstream Analysis Agent.
        Guaranteed to contain NO signal decisions.
        """
        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "stage": "Monitoring",
            "question_answered": self.responsibility,
            "data_source": state.data_source,
            "timestamp": state.timestamp.isoformat(),
            "total_vehicle_count": state.total_vehicle_count,
            "total_queue_length_m": state.total_queue_length,
            "total_approaching_count": state.total_approaching_count,
            "current_signal_phase": state.current_signal_phase.value,
            "remaining_green_time_s": state.remaining_green_time,
            "junction_occupancy": state.junction_occupancy,
            "traffic_state": state.traffic_state.value,
            "per_direction": {
                d.value: {
                    "vehicle_count": data.vehicle_count,
                    "queue_length_m": data.queue_length,
                    "average_speed_kmh": data.average_speed,
                    "approaching_count": data.approaching_count,
                    "earliest_eta_s": data.estimated_arrival_time,
                    "traffic_density_veh_km": data.traffic_density,
                    "approaching_vehicles": [
                        {
                            "vehicle_id": v.vehicle_id,
                            "distance_m": v.distance_to_junction,
                            "speed_kmh": v.speed,
                            "eta_s": v.estimated_time_of_arrival,
                            "trend": v.speed_trend.value if v.speed_trend else "CONSTANT",
                        }
                        for v in data.approaching_vehicle_details
                    ],
                }
                for d, data in state.directions.items()
            },
        }
