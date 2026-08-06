from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.api import (
    routes_system,
    routes_overview,
    routes_approach,
    routes_signals,
    routes_agents,
    routes_trends,
    routes_dataset,
    routes_hardware,
    routes_logs,
    routes_decision,
)
from app.websocket.live_feed import (
    manager,
    signals_manager,
    logs_manager,
    heartbeat_manager
)
from app.data_providers import get_provider
from app.mqtt.mqtt_client import mqtt_client
from app.core.pipeline import pipeline
from datetime import datetime
import asyncio
import json

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background pipeline task runner
async def run_pipeline_loop():
    mqtt_client.connect()
    logger.info("Background DataFlowPipeline loop started.")
    while True:
        try:
            await pipeline.run_step()
        except Exception as e:
            logger.error(f"Error in pipeline loop step: {e}")
        await asyncio.sleep(3) # Periodic pipeline refresh every 3s

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_pipeline_loop())

# Include Routers under both /api/v1 and /api
for prefix in [settings.API_V1_STR, "/api"]:
    app.include_router(routes_system.router, prefix=prefix)
    app.include_router(routes_overview.router, prefix=prefix)
    app.include_router(routes_approach.router, prefix=prefix)
    app.include_router(routes_signals.router, prefix=prefix)
    app.include_router(routes_agents.router, prefix=prefix)
    app.include_router(routes_trends.router, prefix=prefix)
    app.include_router(routes_dataset.router, prefix=prefix)
    app.include_router(routes_hardware.router, prefix=prefix)
    app.include_router(routes_logs.router, prefix=prefix)
    app.include_router(routes_decision.router, prefix=prefix)

@app.get("/")
async def root():
    provider = get_provider()
    state = await provider.get_current_state()
    return {
        "system": settings.PROJECT_NAME,
        "status": "ONLINE",
        "timestamp": datetime.now().isoformat(),
        "source": state.source,
        "confidence": state.confidence,
        "data_source_type": settings.DATA_SOURCE_TYPE,
        "docs": "/docs"
    }

# ---------------------------------------------------------------------------
# WebSocket Endpoints (Section 3.2)
# ---------------------------------------------------------------------------

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    await signals_manager.connect(websocket)
    logger.info("WebSocket /ws/signals client connected")
    try:
        # Initial state push
        provider = get_provider()
        state = await provider.get_current_state()
        await websocket.send_text(json.dumps({
            "event": "signal_state_sync",
            "timestamp": datetime.now().isoformat(),
            "source": state.source,
            "confidence": state.confidence,
            "signals": [sig.model_dump() for sig in state.signals]
        }))
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        signals_manager.disconnect(websocket)
        logger.info("WebSocket /ws/signals client disconnected")

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await logs_manager.connect(websocket)
    logger.info("WebSocket /ws/logs client connected")
    try:
        await websocket.send_text(json.dumps({
            "event": "log_stream_connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to real-time system log stream"
        }))
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        logs_manager.disconnect(websocket)
        logger.info("WebSocket /ws/logs client disconnected")

@app.websocket("/ws/heartbeat")
async def websocket_heartbeat(websocket: WebSocket):
    await heartbeat_manager.connect(websocket)
    logger.info("WebSocket /ws/heartbeat client connected")
    try:
        while True:
            provider = get_provider()
            state = await provider.get_current_state()
            await websocket.send_text(json.dumps({
                "event": "heartbeat",
                "timestamp": datetime.now().isoformat(),
                "status": "ONLINE",
                "source": state.source,
                "confidence": state.confidence,
                "latency_ms": 4
            }))
            await asyncio.sleep(1) # Connection health for top nav every 1s
    except WebSocketDisconnect:
        heartbeat_manager.disconnect(websocket)
        logger.info("WebSocket /ws/heartbeat client disconnected")

@app.websocket(settings.WS_PATH)
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info("WebSocket live feed connected")
    try:
        while True:
            provider = get_provider()
            state = await provider.get_current_state()
            await websocket.send_text(json.dumps({
                "event": "telemetry_update",
                "timestamp": datetime.now().isoformat(),
                "overview": state.overview.model_dump()
            }))
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket live feed disconnected")
