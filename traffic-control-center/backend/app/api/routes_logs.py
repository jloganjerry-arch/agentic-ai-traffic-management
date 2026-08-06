from fastapi import APIRouter
from app.core.pipeline import pipeline

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.get("/")
@router.get("")
@router.get("/api/logs")
async def get_system_logs():
    logs = pipeline.get_logs()
    if not logs:
        return [
            {"timestamp": "00:00:00", "level": "INFO", "source": "System", "message": "Pipeline initialization complete. Waiting for first telemetry cycle."}
        ]
    return logs
