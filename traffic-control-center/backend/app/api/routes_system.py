from fastapi import APIRouter
from app.data_providers import get_provider
from datetime import datetime

router = APIRouter(tags=["System Status"])

@router.get("/system/status")
@router.get("/api/system/status")
async def get_system_status():
    provider = get_provider()
    state = await provider.get_current_state()

    return {
        "timestamp": datetime.now().isoformat(),
        "source": state.source,
        "confidence": state.confidence,
        "system_status": "OPERATIONAL",
        "subsystems": {
            "sumo_engine": "HEALTHY" if state.source == "sumo_simulation" else "STANDBY",
            "fastapi_backend": "HEALTHY",
            "mqtt_broker": "HEALTHY",
            "esp32_nodes": "ONLINE"
        }
    }
