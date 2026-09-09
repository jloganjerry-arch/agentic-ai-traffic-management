from datetime import datetime, timedelta
from typing import Dict, Any, List
import math
from app.data_providers.schemas import TrafficState

class AIPredictionService:
    """
    AI Traffic Prediction Service:
    Forecasts expected traffic metrics (volume, speed, queue, density, congestion level, risk score)
    and recommended AI signal timing strategies for +15m, +30m, and +60m time horizons.
    """

    def generate_predictions(self, state: TrafficState) -> Dict[str, Any]:
        now_dt = datetime.now()
        overview = state.overview
        approaches = state.approaches

        curr_volume = overview.total_vehicle_count
        curr_speed = overview.avg_speed_kmh
        curr_queue = overview.total_queue_length_m
        curr_density = overview.avg_density_veh_km

        # Find current highest congested approach
        busiest_app = max(approaches, key=lambda a: a.density) if approaches else None
        busiest_name = busiest_app.approach if busiest_app else "North (N-Bound)"
        busiest_density = busiest_app.density if busiest_app else curr_density

        # Determine time-of-day factor
        hour = now_dt.hour
        is_peak = (7 <= hour <= 9) or (17 <= hour <= 19)
        trend_factor = 1.15 if is_peak else 0.95

        horizons = [15, 30, 60]
        predictions: Dict[str, Any] = {}

        for mins in horizons:
            # Model time factor & growth
            time_scale = mins / 15.0
            growth = math.sin(time_scale * 0.5) * 0.2 + (0.05 * time_scale * (1.1 if trend_factor > 1 else 0.8))

            # Projected volume
            proj_volume = max(5, int(curr_volume * (1.0 + growth * 0.8)))
            
            # Projected speed (inverse relation to volume/density)
            speed_delta = (proj_volume - curr_volume) * 0.35
            proj_speed = max(12.0, round(curr_speed - speed_delta, 1))

            # Projected queue length
            proj_queue = max(0.0, round(curr_queue * (1.0 + growth * 1.2), 1))

            # Projected density
            proj_density = max(1.0, round(curr_density * (1.0 + growth * 1.1), 1))

            # Congestion classification
            if proj_queue >= 40.0 or proj_density >= 35.0 or proj_speed < 18.0:
                level = "Congested"
                risk_score = min(98, int(65 + mins * 0.5 + busiest_density * 0.4))
                los = "E" if proj_speed > 14.0 else "F"
            elif proj_queue >= 18.0 or proj_density >= 18.0 or proj_speed < 28.0:
                level = "Moderate"
                risk_score = min(70, int(35 + mins * 0.4 + busiest_density * 0.3))
                los = "C" if proj_speed > 22.0 else "D"
            else:
                level = "Optimal"
                risk_score = max(10, int(12 + mins * 0.2))
                los = "A" if proj_speed > 35.0 else "B"

            # Confidence score decays slightly into the future
            confidence = max(0.72, round(0.95 - (mins / 60.0) * 0.18, 2))

            # AI Recommended Strategy
            if level == "Congested":
                recommendation = f"Extend {busiest_name} GREEN phase by +15s to prevent gridlock bottleneck."
                action_code = "PRIORITY_GREEN_EXTENSION"
            elif level == "Moderate":
                recommendation = f"Enable adaptive phase balancing for N-S and E-W corridors."
                action_code = "ADAPTIVE_SPLIT_BALANCING"
            else:
                recommendation = "Maintain standard dynamic equilibrium timing plan."
                action_code = "EQUILIBRIUM_HOLD"

            prediction_time_str = (now_dt + timedelta(minutes=mins)).strftime("%H:%M:%S")

            predictions[f"horizon_{mins}m"] = {
                "horizon_minutes": mins,
                "target_time": prediction_time_str,
                "projected_vehicle_count": proj_volume,
                "projected_avg_speed_kmh": proj_speed,
                "projected_queue_length_m": proj_queue,
                "projected_density_veh_km": proj_density,
                "projected_congestion_level": level,
                "projected_level_of_service": los,
                "bottleneck_risk_score": risk_score,
                "primary_risk_approach": busiest_name,
                "confidence": confidence,
                "action_code": action_code,
                "ai_recommendation": recommendation
            }

        return {
            "timestamp": now_dt.isoformat(),
            "source": state.source,
            "confidence": state.confidence,
            "horizons": predictions,
            "summary": f"AI predictions generated for +15m, +30m, and +60m. Peak congestion risk: {predictions['horizon_60m']['bottleneck_risk_score']}%."
        }

prediction_service = AIPredictionService()
