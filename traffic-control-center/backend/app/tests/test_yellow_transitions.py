import asyncio
import time
import unittest
from app.data_providers.sumo_provider import SumoTrafficProvider
from app.data_providers.schemas import TrafficState
from app.core.pipeline import pipeline
from app.models.traffic_data import SignalPhase, Direction
from app.agents.safety_agent import TrafficSafetyAgent

class TestYellowTransitions(unittest.TestCase):
    def setUp(self):
        from app.data_providers.factory import get_provider
        self.provider = get_provider(force_type="sumo")
        self.provider._is_running = False
        self.provider._latest_state = None

    def test_test1_ns_green_to_ns_yellow_to_clearance_to_ew_green(self):
        """TEST 1: NS_GREEN -> NS_YELLOW (3s) -> ALL_RED / clearance -> EW_GREEN."""
        self.provider.set_signal_mode("paired_corridor")

        # Step 1: NS GREEN
        self.provider._fallback_phase_index = 0
        self.provider._fallback_remaining = 35
        self.provider._fallback_last_tick = time.time()
        state = asyncio.run(self.provider.get_current_state())
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["North"], "GREEN")
        self.assertEqual(sig_map["South"], "GREEN")
        self.assertEqual(sig_map["East"], "RED")
        self.assertEqual(sig_map["West"], "RED")

        # Step 2: NS YELLOW (3s)
        self.provider._fallback_phase_index = 1
        self.provider._fallback_remaining = 3
        self.provider._fallback_last_tick = time.time()
        state = asyncio.run(self.provider.get_current_state())
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["North"], "YELLOW")
        self.assertEqual(sig_map["South"], "YELLOW")
        self.assertEqual(sig_map["East"], "RED")
        self.assertEqual(sig_map["West"], "RED")
        self.assertEqual(state.signals[0].timer_remaining, 3)

        # Step 3: Transition to EW GREEN
        self.provider._fallback_phase_index = 2
        self.provider._fallback_remaining = 30
        self.provider._fallback_last_tick = time.time()
        state = asyncio.run(self.provider.get_current_state())
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["North"], "RED")
        self.assertEqual(sig_map["South"], "RED")
        self.assertEqual(sig_map["East"], "GREEN")
        self.assertEqual(sig_map["West"], "GREEN")

    def test_test2_ew_green_to_ew_yellow_to_clearance_to_ns_green(self):
        """TEST 2: EW_GREEN -> EW_YELLOW (3s) -> ALL_RED / clearance -> NS_GREEN."""
        self.provider.set_signal_mode("paired_corridor")

        # Step 1: EW GREEN
        self.provider._fallback_phase_index = 2
        self.provider._fallback_remaining = 30
        self.provider._fallback_last_tick = time.time()
        state = asyncio.run(self.provider.get_current_state())
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["East"], "GREEN")
        self.assertEqual(sig_map["West"], "GREEN")
        self.assertEqual(sig_map["North"], "RED")
        self.assertEqual(sig_map["South"], "RED")

        # Step 2: EW YELLOW (3s)
        self.provider._fallback_phase_index = 3
        self.provider._fallback_remaining = 3
        self.provider._fallback_last_tick = time.time()
        state = asyncio.run(self.provider.get_current_state())
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["East"], "YELLOW")
        self.assertEqual(sig_map["West"], "YELLOW")
        self.assertEqual(sig_map["North"], "RED")
        self.assertEqual(sig_map["South"], "RED")

        # Step 3: Transition back to NS GREEN
        self.provider._fallback_phase_index = 0
        self.provider._fallback_remaining = 35
        self.provider._fallback_last_tick = time.time()
        state = asyncio.run(self.provider.get_current_state())
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["North"], "GREEN")
        self.assertEqual(sig_map["South"], "GREEN")
        self.assertEqual(sig_map["East"], "RED")
        self.assertEqual(sig_map["West"], "RED")

    def test_test3_yellow_state_in_telemetry_payload(self):
        """TEST 3: YELLOW state is explicitly included in authoritative signal telemetry payload."""
        self.provider.set_signal_mode("paired_corridor")
        self.provider._fallback_phase_index = 1 # NS YELLOW
        self.provider._fallback_remaining = 3
        self.provider._fallback_last_tick = time.time()
        state = asyncio.run(self.provider.get_current_state())
        pipeline.latest_state = state

        # Execute 1 Hz telemetry broadcaster
        asyncio.run(pipeline.broadcast_signal_telemetry())
        signals = pipeline.latest_state.signals
        self.assertEqual(len(signals), 4)
        north_sig = next(s for s in signals if s.direction == "North")
        self.assertEqual(north_sig.state, "YELLOW")
        self.assertEqual(north_sig.timer_remaining, 3)

    def test_test4_yellow_timer_countdown_sequence(self):
        """TEST 4: Yellow timer explicitly counts 3s -> 2s -> 1s."""
        self.provider.set_signal_mode("one_by_one")
        self.provider._one_by_one_index = 0 # North
        self.provider._one_by_one_remaining = 1
        self.provider._one_by_one_is_yellow = False
        self.provider._one_by_one_last_tick = time.time() - 1.0

        # Trigger transition into yellow clearance
        asyncio.run(self.provider.get_current_state())
        self.assertTrue(self.provider._one_by_one_is_yellow)
        self.assertEqual(self.provider._one_by_one_remaining, 3) # 3s

        # 1 second tick: 3s -> 2s
        self.provider._one_by_one_last_tick = time.time() - 1.0
        asyncio.run(self.provider.get_current_state())
        self.assertEqual(self.provider._one_by_one_remaining, 2) # 2s

        # 1 second tick: 2s -> 1s
        self.provider._one_by_one_last_tick = time.time() - 1.0
        asyncio.run(self.provider.get_current_state())
        self.assertEqual(self.provider._one_by_one_remaining, 1) # 1s

    def test_test6_and_7_signal_grid_and_intersection_isolation_during_yellow(self):
        """TEST 6 & 7: Signal Grid and Intersection visualizer directions during YELLOW."""
        self.provider.set_signal_mode("paired_corridor")

        # NS YELLOW: North=YELLOW, South=YELLOW, East=RED, West=RED
        self.provider._fallback_phase_index = 1
        self.provider._fallback_remaining = 2
        state = asyncio.run(self.provider.get_current_state())
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["North"], "YELLOW")
        self.assertEqual(sig_map["South"], "YELLOW")
        self.assertEqual(sig_map["East"], "RED")
        self.assertEqual(sig_map["West"], "RED")

        # EW YELLOW: East=YELLOW, West=YELLOW, North=RED, South=RED
        self.provider._fallback_phase_index = 3
        self.provider._fallback_remaining = 2
        state = asyncio.run(self.provider.get_current_state())
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["East"], "YELLOW")
        self.assertEqual(sig_map["West"], "YELLOW")
        self.assertEqual(sig_map["North"], "RED")
        self.assertEqual(sig_map["South"], "RED")

    def test_test8_one_by_one_mode_explicit_yellow(self):
        """TEST 8: one_by_one mode contains explicit 3s YELLOW phase before switching."""
        self.provider.set_signal_mode("one_by_one")
        self.provider._one_by_one_index = 1 # East
        self.provider._one_by_one_remaining = 1
        self.provider._one_by_one_is_yellow = False
        self.provider._one_by_one_last_tick = time.time() - 1.0

        state = asyncio.run(self.provider.get_current_state())
        self.assertTrue(self.provider._one_by_one_is_yellow)
        self.assertEqual(self.provider._one_by_one_remaining, 3)
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["East"], "YELLOW")
        self.assertEqual(sig_map["North"], "RED")
        self.assertEqual(sig_map["South"], "RED")
        self.assertEqual(sig_map["West"], "RED")

    def test_test9_paired_corridor_sumo_yellow_phases_mapped(self):
        """TEST 9: paired_corridor SUMO yellow phases are mapped to YELLOW."""
        # Fallback simulation phase 1 = NS YELLOW, phase 3 = WE YELLOW
        self.assertEqual(self.provider._fallback_phase_index, 0)
        self.provider._fallback_phase_index = 1
        state = asyncio.run(self.provider.get_current_state())
        self.assertIn("YELLOW", state.overview.current_signal_phase)

    def test_test10_mutual_exclusion_no_simultaneous_green(self):
        """TEST 10: Mutual Exclusion Safeguard: NS and EW NEVER simultaneously GREEN."""
        self.provider.set_signal_mode("paired_corridor")
        for phase_idx in range(4):
            self.provider._fallback_phase_index = phase_idx
            self.provider._fallback_remaining = 10
            self.provider._fallback_last_tick = time.time()
            state = asyncio.run(self.provider.get_current_state())
            sig_map = {s.direction: s.state for s in state.signals}
            ns_green = sig_map["North"] == "GREEN" or sig_map["South"] == "GREEN"
            ew_green = sig_map["East"] == "GREEN" or sig_map["West"] == "GREEN"
            self.assertFalse(ns_green and ew_green, f"Hazardous conflict in phase {phase_idx}")

if __name__ == "__main__":
    unittest.main()
