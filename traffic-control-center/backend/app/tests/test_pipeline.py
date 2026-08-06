import asyncio
from app.core.pipeline import pipeline
from app.data_providers.factory import get_provider
from app.mqtt.mqtt_client import mqtt_client

async def test_end_to_end_pipeline():
    print("--- Testing DataFlowPipeline under SUMO Provider ---")
    get_provider(force_type="sumo")
    
    decision = await pipeline.run_step()
    assert decision["source"] == "sumo_simulation"
    assert decision["confidence"] == "exact"
    assert decision["supervisor_status"] == "APPROVED"
    assert decision["executed_on_hardware"] is True

    # Verify Dual-Fork: State is cached instantly for UI tap
    cached = pipeline.get_latest_decision()
    assert cached["decision_id"] == decision["decision_id"]
    assert cached["source"] == "sumo_simulation"

    print("--- Testing DataFlowPipeline under Camera Provider ---")
    get_provider(force_type="camera")

    cam_decision = await pipeline.run_step()
    assert cam_decision["source"] == "camera_yolo"
    assert cam_decision["confidence"] == "estimated"
    assert cam_decision["supervisor_status"] == "APPROVED"

    cam_cached = pipeline.get_latest_decision()
    assert cam_cached["source"] == "camera_yolo"

    print("ALL DATA FLOW PIPELINE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_pipeline())
