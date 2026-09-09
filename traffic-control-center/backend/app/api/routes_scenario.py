from fastapi import APIRouter, HTTPException
from app.data_providers import get_provider
from app.data_providers.schemas import ScenarioInjectRequest, ScenarioResponse
from app.websocket.live_feed import logs_manager
from app.core.logger import logger
from datetime import datetime
import json

router = APIRouter(tags=["Scenario Injector"])

@router.post("/simulation/scenario", response_model=ScenarioResponse)
@router.post("/scenario", response_model=ScenarioResponse)
@router.post("/api/scenario", response_model=ScenarioResponse)
async def inject_scenario(payload: ScenarioInjectRequest):
    """
    Injects an operational stress-test scenario into the autonomous simulation pipeline:
    - rush_hour: Sudden traffic volume spike on specified approach
    - emergency_corridor: High-priority ambulance dispatch with green wave preemption
    - accident_blockage: Stalled vehicle in lane causing queue buildup
    - weather_hazard: Rain/fog conditions reducing traction and speeds
    - normal: Restores nominal baseline flow
    """
    provider = get_provider()
    res = provider.inject_scenario(
        scenario=payload.scenario,
        approach=payload.approach or "North",
        intensity=payload.intensity or 1.0,
        details=payload.details or {}
    )

    # Broadcast event to real-time WebSocket log stream
    log_msg = f"[SCENARIO INJECTOR] Scenario '{payload.scenario.upper()}' activated on {payload.approach or 'all'} approach(es). {res.get('description', '')}"
    logger.info(log_msg)
    
    try:
        await logs_manager.broadcast(json.dumps({
            "event": "scenario_injected",
            "timestamp": datetime.now().isoformat(),
            "scenario": payload.scenario,
            "approach": payload.approach,
            "message": log_msg,
            "details": res
        }))
    except Exception as e:
        logger.warning(f"Note broadcasting scenario log: {e}")

    return ScenarioResponse(
        status="SUCCESS",
        timestamp=datetime.now().isoformat(),
        active_scenario=res.get("active_scenario", payload.scenario),
        scenario_label=res.get("scenario_label", payload.scenario.title()),
        description=res.get("description", "Scenario injected successfully"),
        ai_response_plan=res.get("ai_response_plan", "AI Supervisor dynamically updated decision matrices."),
        affected_approaches=res.get("affected_approaches", [payload.approach] if payload.approach else ["North"])
    )

@router.get("/simulation/scenario")
@router.get("/scenario")
@router.get("/api/scenario")
async def get_active_scenario():
    """Returns the currently active simulation scenario and impact metadata."""
    provider = get_provider()
    return provider.get_active_scenario()
