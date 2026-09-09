from fastapi import APIRouter
from app.data_providers import get_provider
from app.core.prediction_service import prediction_service

router = APIRouter(tags=["Prediction"])

@router.get("/predictions")
@router.get("/traffic/predictions")
@router.get("/api/traffic/predictions")
async def get_ai_predictions():
    """
    Returns AI traffic forecasting metrics for +15m, +30m, and +60m horizons.
    """
    provider = get_provider()
    state = await provider.get_current_state()
    return prediction_service.generate_predictions(state)
