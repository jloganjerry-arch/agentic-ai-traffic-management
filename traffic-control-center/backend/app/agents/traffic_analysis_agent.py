import time
from datetime import datetime
from typing import Dict, Any, List
from app.data_providers.schemas import TrafficState

class TrafficAnalysisAgent:
    """Agent 2: Analyzes congestion patterns, density rankings, and queue severity per approach."""

    def __init__(self):
        self.id = "agent-2"
        self.name = "Traffic Analysis Agent"
        self.role = "Congestion & Pattern Analytics"

    def analyze_patterns(self, state: TrafficState, monitoring_res: Dict[str, Any] = None, decision_id: str = "DEC-LIVE-001") -> Dict[str, Any]:
        start_t = time.time()
        
        approach_list = []
        for app in state.approaches:
            est_wait = round((app.queue_len / 5.0) * 1.8, 1) if app.queue_len > 0 else 0.0
            
            if app.queue_len >= 30.0 or app.density >= 40.0:
                severity = "HIGH"
            elif app.queue_len >= 12.0 or app.density >= 20.0:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            approach_list.append({
                "approach": app.approach,
                "vehicle_count": app.vehicle_count,
                "queue_m": app.queue_len,
                "density": app.density,
                "waiting_s": est_wait,
                "speed_kmh": app.avg_speed,
                "severity": severity
            })

        sorted_ranking = sorted(approach_list, key=lambda x: (x["density"], x["queue_m"]), reverse=True)
        busiest = sorted_ranking[0] if sorted_ranking else {
            "approach": "North (N-Bound)",
            "severity": "LOW",
            "vehicle_count": 0,
            "queue_m": 0.0,
            "density": 0.0
        }

        overall_congestion = state.overview.current_congestion
        exec_ms = max(1, int((time.time() - start_t) * 1000) + 7)

        reasoning = (
            f"Approach {busiest['approach']} identified as primary bottleneck with "
            f"{busiest['vehicle_count']} vehicles, {busiest['queue_m']}m queue, and {busiest['density']} v/km density."
        )

        return {
            "agent_id": self.id,
            "status": "ACTIVE",
            "current_task": "Analyzing Approach Congestion & Density",
            "execution_time_ms": exec_ms,
            "latency_ms": exec_ms,
            "last_execution": datetime.now().strftime("%H:%M:%S"),
            "decision_id": decision_id,
            "processing_stage": "Analysis",
            "congestion_level": overall_congestion,
            "busiest_direction": busiest["approach"],
            "ranking": sorted_ranking,
            "reasoning": reasoning
        }
