from fastapi import APIRouter, Query
from app.data_providers import get_provider
from datetime import datetime

router = APIRouter(tags=["Trends"])

@router.get("/trends")
@router.get("/traffic/trends")
@router.get("/api/traffic/trends")
async def get_trends(window: str = Query("15m", description="Time window for trends (e.g. 15m, 1h, 24h)")):
    provider = get_provider()
    state = await provider.get_current_state()

    time_series = []
    if hasattr(provider, "get_time_series_buffer"):
        time_series = provider.get_time_series_buffer(window)

    volume_over_time = [{"time": p["time"], "volume": p["volume"]} for p in time_series]
    speed_over_time = [{"time": p["time"], "speed": p["speed"]} for p in time_series]
    queue_over_time = [{"time": p["time"], "queue": p["queue"]} for p in time_series]
    density_over_time = [{"time": p["time"], "density": p["density"]} for p in time_series]

    return {
        "timestamp": datetime.now().isoformat(),
        "source": state.source,
        "confidence": state.confidence,
        "window": window,
        "volume_over_time": volume_over_time,
        "speed_over_time": speed_over_time,
        "queue_over_time": queue_over_time,
        "density_over_time": density_over_time
    }
