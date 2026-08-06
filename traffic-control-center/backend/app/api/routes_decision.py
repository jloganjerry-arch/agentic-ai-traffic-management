from fastapi import APIRouter
from app.core.pipeline import pipeline

router = APIRouter(tags=["Decision"])

@router.get("/decision")
@router.get("/decision/current")
@router.get("/api/decision/current")
async def get_latest_ai_decision():
    # If a decision has already been computed by background loop, return cached decision instantly
    # Otherwise run a pipeline step to guarantee fresh state
    if pipeline.latest_decision is not None:
        return pipeline.get_latest_decision()
    
    return await pipeline.run_step()
