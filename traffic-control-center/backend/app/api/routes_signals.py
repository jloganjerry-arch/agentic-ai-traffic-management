from fastapi import APIRouter
from app.data_providers import get_provider
from datetime import datetime

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
