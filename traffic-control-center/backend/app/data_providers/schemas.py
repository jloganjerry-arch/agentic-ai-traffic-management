from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class OverviewState(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str = Field("sumo_simulation", description="Data source identifier")
    confidence: str = Field("exact", description="Confidence tag: 'exact' or 'estimated'")
    total_vehicle_count: int = Field(..., description="Total active vehicles detected")
    avg_speed_kmh: float = Field(..., description="Average traffic speed in km/h")
    total_queue_length_m: float = Field(..., description="Total queue length in meters across all approaches")
    avg_density_veh_km: float = Field(..., description="Average vehicle density per km")
    throughput_vph: int = Field(..., description="Vehicle throughput per hour")
    level_of_service: str = Field(..., description="Junction Level of Service (A to F)")
    active_signals: int = Field(..., description="Number of active physical signal controllers")
    ai_control_mode: str = Field(..., description="Current AI operating mode")
    emergency_vehicle_count: int = Field(0, description="Total active emergency vehicles")
    current_congestion: str = Field("Low", description="Overall junction congestion status")
    current_signal_phase: str = Field("NS GREEN", description="Active traffic signal phase")

class ApproachState(BaseModel):
    approach: str = Field(..., description="Approach identifier (North, South, East, West)")
    vehicle_count: int = Field(..., description="Vehicle count on approach")
    avg_speed: float = Field(..., description="Average vehicle speed in km/h")
    queue_len: float = Field(..., description="Queue length in meters")
    density: float = Field(..., description="Density in veh/km")
    status: str = Field(..., description="Operational status (Optimal, Moderate, Congested)")

class ApproachListResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str = Field("sumo_simulation")
    confidence: str = Field("exact")
    approaches: List[ApproachState]

class SignalHeadState(BaseModel):
    signal_id: str = Field(..., description="Signal head hardware ID")
    direction: str = Field(..., description="Direction served")
    state: str = Field(..., description="Signal state (GREEN, YELLOW, RED)")
    phase_id: int = Field(0, description="Active TLS phase index")
    phase_start_time: float = Field(0.0, description="Phase start simulation time")
    phase_end_time: float = Field(0.0, description="Phase end simulation time")
    remaining_time: int = Field(0, description="Remaining seconds in phase")
    simulation_time: float = Field(0.0, description="Current SUMO simulation time")
    decision_id: Optional[str] = Field(None, description="Associated decision ID")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    timer_remaining: int = Field(0, description="Remaining seconds in phase")
    mode: str = Field("AI-Adaptive", description="Control mode (AI-Optimized, Manual, Fixed)")

class SignalListResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str = Field("sumo_simulation")
    confidence: str = Field("exact")
    signals: List[SignalHeadState]

class HardwareNodeState(BaseModel):
    node_id: str = Field(..., description="Hardware unit ID")
    role: str = Field(..., description="Node role/description")
    status: str = Field(..., description="Status (ONLINE, STANDBY, OFFLINE)")
    latency_ms: int = Field(..., description="Communication latency in milliseconds")
    firmware: str = Field(..., description="Firmware / software version")
    mqtt_status: str = Field("CONNECTED", description="MQTT Broker connection status")
    publish_topic: str = Field("traffic/signals", description="MQTT Publish Topic")
    latest_payload: str = Field('{"event": "SIGNAL_COMMAND"}', description="Latest MQTT Payload")
    gpio_states: str = Field("GPIO 18: HIGH, GPIO 19: LOW", description="ESP32 GPIO pin states")
    last_ack_time: str = Field("1s ago", description="Last ACK time")

class HardwareListResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str = Field("sumo_simulation")
    confidence: str = Field("exact")
    hardware_status: List[HardwareNodeState]

class TrendData(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str = Field("sumo_simulation")
    confidence: str = Field("exact")
    window: str = Field("15m", description="Time window for trends (e.g. 15m, 1h)")
    volume_over_time: List[Dict[str, Any]] = Field(default_factory=list)
    speed_over_time: List[Dict[str, Any]] = Field(default_factory=list)

class TrafficState(BaseModel):
    source_name: str = Field(..., description="Identifies the data provider (e.g. sumo_simulation or camera_yolo)")
    source: str = Field("sumo_simulation")
    confidence: str = Field("exact")
    timestamp: str = Field(..., description="ISO timestamp of state snapshot")
    overview: OverviewState
    approaches: List[ApproachState]
    signals: List[SignalHeadState]
    trends: TrendData
    hardware_status: List[HardwareNodeState]
