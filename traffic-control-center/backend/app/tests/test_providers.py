import asyncio
from app.data_providers.sumo_provider import SumoTrafficProvider
from app.data_providers.camera_provider import CameraTrafficProvider
from app.data_providers.factory import get_provider
from app.data_providers.schemas import TrafficState
from app.agents.traffic_monitoring_agent import TrafficMonitoringAgent
from app.agents.traffic_analysis_agent import TrafficAnalysisAgent
from app.agents.signal_optimization_agent import SignalOptimizationAgent
from app.agents.supervisor_agent import SupervisorAgent

def test_sumo_provider_contract():
    provider = SumoTrafficProvider()
    assert "SUMO" in provider.get_source_name()
    state = asyncio.run(provider.get_current_state())
    assert isinstance(state, TrafficState)
    assert state.overview.total_vehicle_count >= 0
    assert len(state.approaches) == 4
    assert len(state.signals) == 4

def test_camera_provider_contract():
    provider = CameraTrafficProvider()
    assert "Camera" in provider.get_source_name()
    state = asyncio.run(provider.get_current_state())
    assert isinstance(state, TrafficState)
    assert state.overview.total_vehicle_count == 0

def test_factory_switching():
    sumo_p = get_provider(force_type="sumo")
    assert isinstance(sumo_p, SumoTrafficProvider)

    cam_p = get_provider(force_type="camera")
    assert isinstance(cam_p, CameraTrafficProvider)

def test_agents_consume_traffic_state():
    sumo_p = SumoTrafficProvider()
    state = asyncio.run(sumo_p.get_current_state())

    m_agent = TrafficMonitoringAgent()
    m_res = m_agent.process_state(state)
    assert m_res["status"] in ["ACTIVE", "processed"]

    a_agent = TrafficAnalysisAgent()
    a_res = a_agent.analyze_patterns(state)
    assert "congestion_level" in a_res

    o_agent = SignalOptimizationAgent()
    o_res = o_agent.compute_timing_plan(a_res, state)
    assert "phase_durations" in o_res

    s_agent = SupervisorAgent()
    s_res = s_agent.evaluate_and_dispatch(o_res, state)
    assert s_res["decision"] == "APPROVED"

if __name__ == "__main__":
    test_sumo_provider_contract()
    test_camera_provider_contract()
    test_factory_switching()
    test_agents_consume_traffic_state()
    print("ALL TESTS PASSED SUCCESSFULLY!")
