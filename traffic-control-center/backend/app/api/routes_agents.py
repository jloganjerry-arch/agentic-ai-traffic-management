from fastapi import APIRouter
from app.core.pipeline import pipeline

router = APIRouter(tags=["Agents"])

@router.get("/agents")
@router.get("/agents/status")
@router.get("/api/agents/status")
async def get_agent_status():
    return pipeline.get_agent_status()
