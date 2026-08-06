from fastapi import APIRouter, Query, HTTPException
from app.data_providers import get_provider
from app.mqtt.mqtt_client import mqtt_client
from datetime import datetime
from typing import Optional

router = APIRouter(tags=["Hardware"])

@router.get("/hardware")
@router.get("/hardware/status")
@router.get("/api/hardware/status")
async def get_hardware_status():
    provider = get_provider()
    state = await provider.get_current_state()
    latest_ack = mqtt_client.latest_ack or {}

    return {
        "timestamp": datetime.now().isoformat(),
        "source": state.source,
        "confidence": state.confidence,
        "mqtt_broker_status": "CONNECTED" if mqtt_client.connected else "SIMULATION_FALLBACK",
        "esp32_status": "ONLINE" if mqtt_client.esp32_connected else "FAILSAFE_OFFLINE",
        "wifi_rssi": "-62 dBm (Strong)",
        "last_publish_time": mqtt_client.last_publish_time,
        "latest_ack": latest_ack,
        "hardware_status": [hw.model_dump() for hw in state.hardware_status]
    }

@router.post("/hardware/override")
@router.post("/api/hardware/override")
@router.get("/hardware/test")
@router.get("/api/hardware/test")
async def manual_hardware_test(
    direction: str = Query("North", description="Approach direction (North, South, East, West)"),
    state: str = Query("GREEN", description="Signal state (GREEN, YELLOW, RED)"),
    duration: int = Query(30, description="Duration in seconds")
):
    """
    Development Test Mode: Allows manual signal testing of North Green, South Green,
    East Green, West Green, Yellow, and Red without needing SUMO simulation.
    """
    valid_dirs = ["North", "South", "East", "West"]
    valid_states = ["GREEN", "YELLOW", "RED"]

    if direction not in valid_dirs:
        raise HTTPException(status_code=400, detail=f"Invalid direction. Must be one of {valid_dirs}")
    if state not in valid_states:
        raise HTTPException(status_code=400, detail=f"Invalid state. Must be one of {valid_states}")

    res = mqtt_client.publish_manual_override(direction, state, duration)
    return {
        "status": "SUCCESS",
        "message": f"Manual test command dispatched to ESP32 for {direction} {state} ({duration}s)",
        "payload": res
    }
