from app.data_providers.base_provider import TrafficStateProvider
from app.data_providers.schemas import (
    TrafficState,
    OverviewState,
    ApproachState,
    SignalHeadState,
    HardwareNodeState,
    TrendData
)
from datetime import datetime

class CameraTrafficProvider(TrafficStateProvider):
    """
    Semester 6 Data Provider stub for Live Vision / YOLOv8 Camera Pipeline.
    Source tag: 'camera_yolo', Confidence: 'estimated'
    """

    def __init__(self):
        self._source = "camera_yolo"
        self._source_name = "YOLOv8 Live Camera Feed Pipeline (Semester 6 Vision Stub)"
        self._confidence = "estimated"
        self._active_scenario = "normal"
        self._scenario_impact = "Nominal baseline conditions (Camera vision feed standby)"

    def get_source_name(self) -> str:
        return self._source_name

    def inject_scenario(self, scenario: str, approach: str = "North", intensity: float = 1.0, details=None):
        self._active_scenario = scenario
        self._scenario_impact = f"Scenario {scenario} active on {approach} (Camera Vision Mode)"
        return {
            "status": "SUCCESS",
            "active_scenario": self._active_scenario,
            "scenario_label": self._active_scenario.replace("_", " ").title(),
            "description": self._scenario_impact,
            "ai_response_plan": "AI Supervisor adapted vision detector thresholds.",
            "affected_approaches": [approach] if approach else ["North", "South", "East", "West"]
        }

    def get_active_scenario(self):
        return {
            "active_scenario": self._active_scenario,
            "scenario_label": self._active_scenario.replace("_", " ").title(),
            "description": self._scenario_impact
        }

    async def get_current_state(self) -> TrafficState:
        now_str = datetime.now().isoformat()
        overview_data = OverviewState(
            timestamp=now_str,
            source=self._source,
            confidence=self._confidence,
            total_vehicle_count=0,
            avg_speed_kmh=0.0,
            total_queue_length_m=0.0,
            avg_density_veh_km=0.0,
            throughput_vph=0,
            level_of_service="N/A (Camera Standby)",
            active_signals=0,
            ai_control_mode="Camera Ready Stub",
            signal_mode="paired_corridor",
            active_scenario=self._active_scenario,
            scenario_impact=self._scenario_impact
        )

        return TrafficState(
            source_name=self._source_name,
            source=self._source,
            confidence=self._confidence,
            timestamp=now_str,
            overview=overview_data,
            approaches=[],
            signals=[],
            trends=TrendData(
                timestamp=now_str,
                source=self._source,
                confidence=self._confidence,
                window="15m",
                volume_over_time=[],
                speed_over_time=[]
            ),
            hardware_status=[
                HardwareNodeState(node_id="CAM-J1-01", role="YOLOv8 Edge Object Detector", status="STANDBY", latency_ms=0, firmware="Sem6-Draft")
            ]
        )
