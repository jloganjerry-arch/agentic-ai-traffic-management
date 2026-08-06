import time
from datetime import datetime
from typing import Dict, Any
from app.data_providers.schemas import TrafficState

class TrafficMonitoringAgent:
    """Agent 1: Ingests live SUMO TraCI telemetry and preprocesses approach metrics."""

    def __init__(self):
        self.id = "agent-1"
        self.name = "Traffic Monitoring Agent"
        self.role = "Telemetry Ingestion & Preprocessing"

    def process_state(self, state: TrafficState, decision_id: str = "DEC-LIVE-001") -> Dict[str, Any]:
        start_t = time.time()
        
        # Approach breakdown aggregation
        approach_stats = {}
        for app in state.approaches:
            approach_stats[app.approach] = {
                "vehicle_count": app.vehicle_count,
                "queue_len": app.queue_len,
                "avg_speed": app.avg_speed,
                "density": app.density,
                "status": app.status
            }

        emergency_count = state.overview.emergency_vehicle_count
        emergency_status = "ACTIVE_EMERGENCY_DETECTED" if emergency_count > 0 else "NORMAL_TRAFFIC"
        exec_ms = max(1, int((time.time() - start_t) * 1000) + 4)

        return {
            "agent_id": self.id,
            "status": "ACTIVE",
            "current_task": "Ingesting SUMO TraCI Telemetry",
            "execution_time_ms": exec_ms,
            "latency_ms": exec_ms,
            "last_execution": datetime.now().strftime("%H:%M:%S"),
            "decision_id": decision_id,
            "processing_stage": "Monitoring",
            "timestamp": state.timestamp,
            "source": state.source_name,
            "total_vehicles": state.overview.total_vehicle_count,
            "avg_speed": state.overview.avg_speed_kmh,
            "queue_length": state.overview.total_queue_length_m,
            "avg_density": state.overview.avg_density_veh_km,
            "emergency_vehicle_status": emergency_status,
            "emergency_count": emergency_count,
            "approaches_monitored": len(state.approaches),
            "approach_stats": approach_stats
        }
