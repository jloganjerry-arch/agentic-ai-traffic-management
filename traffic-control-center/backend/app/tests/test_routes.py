import asyncio
from app.api.routes_system import get_system_status
from app.api.routes_overview import get_overview
from app.api.routes_approach import get_approaches
from app.api.routes_signals import get_signals
from app.api.routes_agents import get_agent_status
from app.api.routes_trends import get_trends
from app.api.routes_dataset import get_dataset_preview
from app.api.routes_hardware import get_hardware_status
from app.api.routes_decision import get_latest_ai_decision
from app.data_providers.factory import get_provider

async def run_route_tests():
    print("--- Testing REST endpoints under SUMO Provider ---")
    get_provider(force_type="sumo")

    sys_stat = await get_system_status()
    assert sys_stat["source"] == "sumo_simulation"
    assert sys_stat["confidence"] == "exact"
    assert "timestamp" in sys_stat

    overview = await get_overview()
    assert overview["source"] == "sumo_simulation"
    assert overview["confidence"] == "exact"
    assert overview["total_vehicle_count"] >= 0

    approaches = await get_approaches()
    assert approaches["source"] == "sumo_simulation"
    assert len(approaches["approaches"]) == 4

    signals = await get_signals()
    assert signals["source"] == "sumo_simulation"
    assert len(signals["signals"]) == 4

    agents = await get_agent_status()
    assert agents["source"] == "sumo_simulation"
    assert len(agents["agents"]) == 4
    assert "pipeline_stage" in agents

    trends = await get_trends(window="15m")
    assert trends["source"] == "sumo_simulation"
    assert trends["window"] == "15m"
    assert "volume_over_time" in trends

    dataset = await get_dataset_preview(limit=10)
    assert dataset["source"] == "sumo_simulation"
    assert dataset["limit"] == 10
    assert len(dataset["rows"]) <= 10

    hardware = await get_hardware_status()
    assert hardware["source"] == "sumo_simulation"
    assert len(hardware["hardware_status"]) == 4

    decision = await get_latest_ai_decision()
    assert decision["source"] == "sumo_simulation"
    assert decision["supervisor_status"] == "APPROVED"

    print("--- Testing REST endpoints under Camera Provider ---")
    get_provider(force_type="camera")

    sys_stat_cam = await get_system_status()
    assert sys_stat_cam["source"] == "camera_yolo"
    assert sys_stat_cam["confidence"] == "estimated"

    overview_cam = await get_overview()
    assert overview_cam["source"] == "camera_yolo"
    assert overview_cam["confidence"] == "estimated"
    assert overview_cam["total_vehicle_count"] == 0

    print("ALL REST ENDPOINT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_route_tests())
