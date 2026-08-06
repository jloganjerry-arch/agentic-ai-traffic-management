from fastapi import APIRouter
from app.data_providers import get_provider

router = APIRouter(tags=["Overview"])

@router.get("/overview")
@router.get("/traffic/overview")
@router.get("/api/traffic/overview")
async def get_overview():
    provider = get_provider()
    return await provider.get_overview()
