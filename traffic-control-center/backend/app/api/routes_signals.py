from fastapi import APIRouter, Body
from app.data_providers import get_provider
from app.core.pipeline import pipeline
from datetime import datetime
from typing import Dict, Any

router = APIRouter(tags=["Signals"])

@router.get("/signals")
@router.get("/signals/status")
@router.get("/api/signals/status")
async def get_signals():
    provider = get_provider()
    state = await provider.get_current_state()
    return {
        "timestamp": datetime.now().isoformat(),
        "source": state.source,
        "confidence": state.confidence,
        "signals": [sig.model_dump() for sig in state.signals]
    }

@router.post("/signals/emergency-corridor")
@router.post("/api/signals/emergency-corridor")
async def trigger_emergency_corridor(payload: Dict[str, Any] = Body(...)):
    """
    Activates or deactivates Emergency Green Corridor Preemption.
    Payload body: {"active": bool, "direction": "North-South" | "East-West", "vehicle_type": "ambulance" | "fire" | "police"}
    """
    provider = get_provider()
    active = payload.get("active", True)
    direction = payload.get("direction", "North-South")
    vtype = payload.get("vehicle_type", "ambulance")

    if hasattr(provider, "trigger_emergency_corridor"):
        provider.trigger_emergency_corridor(direction=direction, active=active, vehicle_type=vtype)

    # Force immediate pipeline execution step
    decision = await pipeline.run_step()

    return {
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS",
        "emergency_corridor_active": active,
        "direction": direction,
        "vehicle_type": vtype,
        "message": f"Emergency Green Corridor {'ACTIVATED' if active else 'DEACTIVATED'} for {direction} ({vtype}).",
        "decision": decision
    }

@router.get("/signals/adaptive-mode")
@router.get("/api/signals/adaptive-mode")
async def get_adaptive_mode():
    """
    Returns current AI Adaptive Signal Timing status (ENABLED vs FIXED SCHEDULE).
    """
    provider = get_provider()
    enabled = getattr(provider, "_adaptive_mode_enabled", True)
    return {
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS",
        "adaptive_mode_enabled": enabled,
        "mode_label": "Autonomous Adaptive" if enabled else "Fixed Schedule"
    }

@router.post("/signals/adaptive-mode")
@router.post("/api/signals/adaptive-mode")
async def set_adaptive_mode(payload: Dict[str, Any] = Body(...)):
    """
    Toggles between AI Adaptive Signal Timing and Fixed Schedule Mode.
    Payload body: {"enabled": bool}
    """
    provider = get_provider()
    enabled = payload.get("enabled", True)

    if hasattr(provider, "set_adaptive_mode"):
        provider.set_adaptive_mode(enabled)

    decision = await pipeline.run_step()

    return {
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS",
        "adaptive_mode_enabled": enabled,
        "message": f"Adaptive Signal Timing Mode {'ENABLED' if enabled else 'DISABLED'}.",
        "decision": decision
    }

@router.get("/signals/mode")
@router.get("/api/signals/mode")
async def get_signal_mode():
    """
    Returns current signal sequencing mode: 'paired_corridor' (2-Phase) or 'one_by_one' (4-Phase Isolated).
    """
    provider = get_provider()
    state = await provider.get_current_state()
    mode = getattr(provider, "get_signal_mode", lambda: "paired_corridor")()
    mode_label = "One-by-One (4-Phase)" if mode == "one_by_one" else "Paired Corridors (2-Phase)"
    desc = (
        "Isolated single-approach green sequencing with zero turn conflicts"
        if mode == "one_by_one"
        else "Paired bidirectional corridor flow (North+South <-> East+West)"
    )
    return {
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS",
        "signal_mode": mode,
        "mode_label": mode_label,
        "description": desc,
        "active_phase": state.overview.current_signal_phase
    }

@router.post("/signals/mode")
@router.post("/api/signals/mode")
async def set_signal_mode(payload: Dict[str, Any] = Body(...)):
    """
    Toggles between 'paired_corridor' (2-Phase) and 'one_by_one' (4-Phase Isolated) modes.
    Payload body: {"mode": "paired_corridor" | "one_by_one"} or {"signal_mode": ...}
    """
    provider = get_provider()
    mode = payload.get("mode") or payload.get("signal_mode", "paired_corridor")
    if mode not in ["paired_corridor", "one_by_one"]:
        mode = "paired_corridor"

    if hasattr(provider, "set_signal_mode"):
        provider.set_signal_mode(mode)

    # Force immediate pipeline execution step
    decision = await pipeline.run_step()
    state = await provider.get_current_state()

    mode_label = "One-by-One (4-Phase)" if mode == "one_by_one" else "Paired Corridors (2-Phase)"
    desc = (
        "Isolated single-approach green sequencing with zero turn conflicts"
        if mode == "one_by_one"
        else "Paired bidirectional corridor flow (North+South <-> East+West)"
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS",
        "signal_mode": mode,
        "mode_label": mode_label,
        "description": desc,
        "active_phase": state.overview.current_signal_phase,
        "decision": decision
    }

@router.get("/signals/glide")
@router.get("/api/signals/glide")
async def get_glide_setup():
    """
    Returns current GLIDE (Green Light Intelligent Dynamic Extension) setup,
    dynamic per-approach durations, platoon extension status, and gap-out thresholds.
    """
    provider = get_provider()
    setup = getattr(provider, "get_glide_setup", lambda: {
        "glide_enabled": True,
        "platoon_extension_s": 4,
        "gap_out_threshold_s": 2.5,
        "min_green_s": 15,
        "max_green_s": 65,
        "status": "DYNAMIC_GLIDE_OPTIMIZED"
    })()
    return {
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS",
        **setup
    }

@router.post("/signals/glide")
@router.post("/api/signals/glide")
async def set_glide_setup(payload: Dict[str, Any] = Body(...)):
    """
    Updates GLIDE dynamic timing parameters:
    Payload: {"enabled": bool, "platoon_extension_s": int, "gap_out_threshold_s": float, "min_green_s": int, "max_green_s": int, "durations": {"North": 35, "East": 25, "South": 30, "West": 25}}
    """
    provider = get_provider()
    if hasattr(provider, "set_glide_setup"):
        updated = provider.set_glide_setup(payload)
    else:
        updated = payload

    decision = await pipeline.run_step()
    return {
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS",
        "message": "GLIDE dynamic timing parameters updated successfully",
        "glide_setup": updated,
        "decision": decision
    }

