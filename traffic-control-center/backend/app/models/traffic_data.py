from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Core Enums
# ============================================================================

class Direction(str, Enum):
    """Traffic approach directions at the junction."""
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"


class SignalPhase(str, Enum):
    """Physical signal phases executed by the Signal Controller and ESP32."""
    NS_GREEN = "NS_GREEN"
    NS_YELLOW = "NS_YELLOW"
    ALL_RED = "ALL_RED"
    EW_GREEN = "EW_GREEN"
    EW_YELLOW = "EW_YELLOW"


class TrafficRegime(str, Enum):
    """Macro-level traffic state categorization."""
    PEAK = "PEAK"
    NON_PEAK = "NON_PEAK"
    TRANSITION = "TRANSITION"


class SpeedTrend(str, Enum):
    """Vehicle dynamic acceleration / deceleration behavior."""
    ACCELERATING = "ACCELERATING"
    DECELERATING = "DECELERATING"
    CONSTANT = "CONSTANT"


# ============================================================================
# Vehicle-Level Schema
# ============================================================================

class ApproachingVehicle(BaseModel):
    """
    Telemetry and spatial parameters of an approaching vehicle.
    Does NOT contain AI decisions — purely empirical measurements.
    """
    vehicle_id: str = Field(..., description="Unique vehicle tracking identifier")
    direction: Direction = Field(..., description="Approach direction (NORTH, SOUTH, EAST, WEST)")
    distance_to_junction: float = Field(
        ..., ge=0.0, description="Current distance to intersection stop-bar in meters"
    )
    speed: float = Field(..., ge=0.0, description="Current measured speed in km/h")
    estimated_time_of_arrival: float = Field(
        ..., ge=0.0, description="Computed estimated time of arrival (ETA) at junction in seconds"
    )
    acceleration: Optional[float] = Field(
        0.0, description="Vehicle acceleration in m/s^2 (+ accelerating, - braking)"
    )
    speed_trend: Optional[SpeedTrend] = Field(
        SpeedTrend.CONSTANT, description="Observed speed trend based on acceleration"
    )

    @field_validator("speed_trend", mode="before")
    @classmethod
    def infer_speed_trend(cls, v: Any, info: Any) -> Any:
        if isinstance(v, str):
            v_upper = v.upper()
            if v_upper in SpeedTrend.__members__:
                return SpeedTrend[v_upper]
        return v

    @classmethod
    def compute_eta(cls, distance_m: float, speed_kmh: float) -> float:
        """Helper to calculate deterministic physical ETA: time = distance / velocity."""
        if speed_kmh <= 0.5:
            return 999.0  # Stationary / queued
        speed_mps = speed_kmh / 3.6
        return round(distance_m / speed_mps, 2)


# ============================================================================
# Direction-Level Schema
# ============================================================================

class DirectionTrafficData(BaseModel):
    """
    Aggregated traffic measurements for a single corridor approach.
    Does NOT contain signal recommendations or control decisions.
    """
    direction: Direction = Field(..., description="Corridor approach direction")
    vehicle_count: int = Field(0, ge=0, description="Total active vehicles in this approach corridor")
    queue_length: float = Field(0.0, ge=0.0, description="Length of stationary / queued vehicles in meters")
    average_speed: float = Field(0.0, ge=0.0, description="Mean speed of vehicles in corridor in km/h")
    approaching_count: int = Field(0, ge=0, description="Number of vehicles actively moving toward junction")
    approaching_vehicle_details: List[ApproachingVehicle] = Field(
        default_factory=list, description="Individual telemetry records for approaching vehicles"
    )
    vehicle_positions: List[float] = Field(
        default_factory=list, description="Distances of all tracked vehicles along corridor in meters"
    )
    vehicle_speeds: List[float] = Field(
        default_factory=list, description="Speed readings of all tracked vehicles in km/h"
    )
    estimated_arrival_time: Optional[float] = Field(
        None, ge=0.0, description="Earliest ETA among all approaching vehicles in seconds"
    )
    traffic_density: float = Field(
        0.0, ge=0.0, description="Corridor vehicle density in vehicles per kilometer (veh/km)"
    )

    @model_validator(mode="after")
    def sync_approaching_metrics(self) -> "DirectionTrafficData":
        """Synchronizes derived counts and earliest ETA from approaching vehicle records if present."""
        if self.approaching_vehicle_details:
            if self.approaching_count == 0:
                self.approaching_count = len(self.approaching_vehicle_details)
            if self.estimated_arrival_time is None:
                etas = [v.estimated_time_of_arrival for v in self.approaching_vehicle_details if v.estimated_time_of_arrival > 0]
                if etas:
                    self.estimated_arrival_time = min(etas)
        return self


# ============================================================================
# Junction-Level Schema
# ============================================================================

class JunctionTrafficState(BaseModel):
    """
    Authoritative common traffic-data contract across all agents.
    Represents pure physical and signal state without any fake AI decisions.
    """
    junction_id: str = Field("JUNCTION-01", description="Identifier of the physical junction")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the observation snapshot"
    )
    data_source: str = Field(
        "TEST_SIMULATION", description="Clearly labeled telemetry source: e.g. TEST_SIMULATION"
    )
    current_signal_phase: SignalPhase = Field(
        SignalPhase.NS_GREEN, description="Active physical signal phase (actuated by Signal Controller)"
    )
    remaining_green_time: float = Field(
        0.0, ge=0.0, description="Remaining seconds on the current green phase"
    )
    junction_occupancy: float = Field(
        0.0, ge=0.0, le=1.0, description="Ratio of intersection conflict box occupied (0.0 to 1.0)"
    )
    traffic_state: TrafficRegime = Field(
        TrafficRegime.NON_PEAK, description="Macro traffic state: PEAK, NON_PEAK, or TRANSITION"
    )
    directions: Dict[Direction, DirectionTrafficData] = Field(
        ..., description="Traffic telemetry mapped by approach direction"
    )

    # Convenience Properties
    @property
    def total_vehicle_count(self) -> int:
        return sum(d.vehicle_count for d in self.directions.values())

    @property
    def total_queue_length(self) -> float:
        return round(sum(d.queue_length for d in self.directions.values()), 1)

    @property
    def total_approaching_count(self) -> int:
        return sum(d.approaching_count for d in self.directions.values())

    def get_corridor_count(self, corridor: str) -> int:
        """Returns total vehicles on 'NS' (North+South) or 'EW' (East+West)."""
        c = corridor.upper()
        if c in ("NS", "NORTH_SOUTH"):
            return (
                self.directions.get(Direction.NORTH, DirectionTrafficData(direction=Direction.NORTH)).vehicle_count +
                self.directions.get(Direction.SOUTH, DirectionTrafficData(direction=Direction.SOUTH)).vehicle_count
            )
        elif c in ("EW", "EAST_WEST"):
            return (
                self.directions.get(Direction.EAST, DirectionTrafficData(direction=Direction.EAST)).vehicle_count +
                self.directions.get(Direction.WEST, DirectionTrafficData(direction=Direction.WEST)).vehicle_count
            )
        return 0


# ============================================================================
# Baseline Test State Factory
# ============================================================================

def create_test_junction_state(
    signal_phase: SignalPhase = SignalPhase.NS_GREEN,
    remaining_green: float = 25.0,
    regime: TrafficRegime = TrafficRegime.NON_PEAK,
    north_count: int = 5,
    south_count: int = 4,
    east_count: int = 2,
    west_count: int = 3,
) -> JunctionTrafficState:
    """
    Generates a realistic, deterministic test state clearly tagged as TEST_SIMULATION.
    """
    # Build sample approaching vehicles for North
    north_vehicles = [
        ApproachingVehicle(
            vehicle_id=f"VEH-N-{i+1:02d}",
            direction=Direction.NORTH,
            distance_to_junction=round(60.0 + i * 15.0, 1),
            speed=round(58.0 + (i % 3) * 2.0, 1),
            estimated_time_of_arrival=ApproachingVehicle.compute_eta(60.0 + i * 15.0, 58.0 + (i % 3) * 2.0),
            acceleration=0.0,
            speed_trend=SpeedTrend.CONSTANT,
        )
        for i in range(min(north_count, 5))
    ]

    directions_data = {
        Direction.NORTH: DirectionTrafficData(
            direction=Direction.NORTH,
            vehicle_count=north_count,
            queue_length=12.5 if north_count > 3 else 0.0,
            average_speed=52.4,
            approaching_count=len(north_vehicles),
            approaching_vehicle_details=north_vehicles,
            vehicle_positions=[v.distance_to_junction for v in north_vehicles],
            vehicle_speeds=[v.speed for v in north_vehicles],
            estimated_arrival_time=north_vehicles[0].estimated_time_of_arrival if north_vehicles else None,
            traffic_density=round(north_count * 5.2, 1),
        ),
        Direction.SOUTH: DirectionTrafficData(
            direction=Direction.SOUTH,
            vehicle_count=south_count,
            queue_length=10.0 if south_count > 2 else 0.0,
            average_speed=48.0,
            approaching_count=south_count,
            traffic_density=round(south_count * 4.8, 1),
        ),
        Direction.EAST: DirectionTrafficData(
            direction=Direction.EAST,
            vehicle_count=east_count,
            queue_length=0.0,
            average_speed=45.0,
            approaching_count=east_count,
            traffic_density=round(east_count * 4.0, 1),
        ),
        Direction.WEST: DirectionTrafficData(
            direction=Direction.WEST,
            vehicle_count=west_count,
            queue_length=5.0,
            average_speed=40.0,
            approaching_count=west_count,
            traffic_density=round(west_count * 4.5, 1),
        ),
    }

    return JunctionTrafficState(
        junction_id="JUNCTION-TEST-01",
        timestamp=datetime.now(),
        data_source="TEST_SIMULATION",
        current_signal_phase=signal_phase,
        remaining_green_time=remaining_green,
        junction_occupancy=0.15,
        traffic_state=regime,
        directions=directions_data,
    )
