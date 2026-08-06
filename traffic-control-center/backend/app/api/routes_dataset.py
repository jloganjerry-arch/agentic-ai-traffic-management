from fastapi import APIRouter, Query
from app.data_providers import get_provider
from datetime import datetime

router = APIRouter(tags=["Dataset"])

@router.get("/dataset/preview")
@router.get("/api/dataset/preview")
async def get_dataset_preview(limit: int = Query(20, description="Limit rows returned")):
    provider = get_provider()
    state = await provider.get_current_state()

    columns = [
        "Timestamp",
        "North Count",
        "South Count",
        "East Count",
        "West Count",
        "Queue Length (m)",
        "Density (v/km)",
        "Avg Speed (km/h)",
        "Waiting Time (s)",
        "Decision ID",
        "Green Time (s)"
    ]

    rows = []
    if hasattr(provider, "get_dataset_rows"):
        rows = provider.get_dataset_rows(limit)

    if not rows:
        now_str = datetime.now().strftime("%H:%M:%S")
        rows = [
            [now_str, 12, 14, 8, 9, 15.0, 36.0, 38.5, 4.2, "DEC-LIVE-0001", 45]
        ]

    return {
        "timestamp": datetime.now().isoformat(),
        "source": state.source,
        "confidence": state.confidence,
        "limit": limit,
        "columns": columns,
        "rows": rows[:limit]
    }
