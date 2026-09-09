from fastapi import APIRouter
from app.data_providers import get_provider
from datetime import datetime

router = APIRouter(tags=["Approach"])

@router.get("/approach")
@router.get("/traffic/approach")
@router.get("/api/traffic/approach")
async def get_approaches():
    provider = get_provider()
    state = await provider.get_current_state()
    
    all_vehicles = []
    for app in state.approaches:
        for v in app.vehicles:
            all_vehicles.append(v.model_dump())

    return {
        "timestamp": datetime.now().isoformat(),
        "source": state.source,
        "confidence": state.confidence,
        "approaches": [app.model_dump() for app in state.approaches],
        "vehicles": all_vehicles
    }
