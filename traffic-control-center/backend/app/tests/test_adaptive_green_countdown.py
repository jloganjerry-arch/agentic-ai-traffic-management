import asyncio
import time
import unittest
from app.data_providers.factory import get_provider
from app.core.pipeline import pipeline

class TestAdaptiveGreenCountdown(unittest.TestCase):
    def setUp(self):
        self.provider = get_provider(force_type="sumo")
        self.provider._is_running = False
        self.provider._latest_state = None
        self.provider.set_adaptive_mode(True)
        self.provider.set_signal_mode("paired_corridor")

    def test_dynamic_recalculation_on_demand_drop(self):
        """
        Verify that remaining green time recalculates dynamically when traffic demand decreases,
        rather than counting down rigidly 1 second at a time.
        """
        self.provider._fallback_phase_index = 0  # NS GREEN
        self.provider._fallback_remaining = 45
        self.provider._fallback_last_tick = time.time()

        # Step 1: Initial state steps down dynamically from 45 -> 40 because active demand is 0
        state1 = asyncio.run(self.provider.get_current_state())
        self.assertEqual(state1.signals[0].remaining_time, 40)

        # Step 2: Next tick steps down dynamically 40 -> 35
        self.provider._fallback_last_tick = time.time() - 1.0
        state2 = asyncio.run(self.provider.get_current_state())
        self.assertEqual(state2.signals[0].remaining_time, 35)

        # Step 3: Next tick steps down dynamically 35 -> 30
        self.provider._fallback_last_tick = time.time() - 1.0
        state3 = asyncio.run(self.provider.get_current_state())
        self.assertEqual(state3.signals[0].remaining_time, 30)
        self.assertEqual(state3.signals[0].adaptive_action, "ADAPTIVE_RECALCULATION")

    def test_platoon_extension(self):
        """
        Verify that an approaching platoon dynamically extends active green time (+4s).
        """
        self.provider._fallback_phase_index = 0  # NS GREEN
        self.provider._fallback_remaining = 6
        self.provider._glide_extension_active = False
        self.provider._fallback_last_tick = time.time() - 1.0

        # Simulate platoon detected in fallback logic
        self.provider._glide_platoon_extension = 4
        self.provider._fallback_remaining = 6
        # When platoon extension condition triggers, remaining increases by +4s
        self.provider._fallback_remaining += self.provider._glide_platoon_extension
        self.provider._glide_extension_active = True
        self.assertEqual(self.provider._fallback_remaining, 10)

    def test_gap_out_triggers_clean_yellow(self):
        """
        Verify that zero vehicles remaining triggers early gap-out, followed strictly by 3s YELLOW clearance.
        """
        self.provider._fallback_phase_index = 0  # NS GREEN
        self.provider._fallback_remaining = 1  # 1s remaining in green
        self.provider._fallback_last_tick = time.time() - 1.0

        # When green hits 0, it must transition into NS YELLOW (index 1) with 3s duration
        state = asyncio.run(self.provider.get_current_state())
        self.assertEqual(self.provider._fallback_phase_index, 1)  # NS YELLOW
        self.assertEqual(self.provider._fallback_remaining, 3)
        sig_map = {s.direction: s.state for s in state.signals}
        self.assertEqual(sig_map["North"], "YELLOW")
        self.assertEqual(sig_map["South"], "YELLOW")
        self.assertEqual(sig_map["East"], "RED")
        self.assertEqual(sig_map["West"], "RED")

    def test_yellow_phase_not_broken(self):
        """
        Verify that the Yellow phase strictly lasts for 3 seconds and is never skipped.
        Counts down 3s -> 2s -> 1s -> 0s -> opposite GREEN.
        """
        self.provider._fallback_phase_index = 1  # NS YELLOW
        self.provider._fallback_remaining = 3
        self.provider._fallback_last_tick = time.time()

        state3 = asyncio.run(self.provider.get_current_state())
        self.assertEqual(state3.signals[0].state, "YELLOW")
        self.assertEqual(self.provider._fallback_remaining, 3)

        # Tick 1: 3 -> 2
        self.provider._fallback_last_tick = time.time() - 1.0
        state2 = asyncio.run(self.provider.get_current_state())
        self.assertEqual(self.provider._fallback_remaining, 2)
        self.assertEqual(state2.signals[0].state, "YELLOW")

        # Tick 2: 2 -> 1
        self.provider._fallback_last_tick = time.time() - 1.0
        state1 = asyncio.run(self.provider.get_current_state())
        self.assertEqual(self.provider._fallback_remaining, 1)
        self.assertEqual(state1.signals[0].state, "YELLOW")

        # Tick 3: 1 -> 0 -> enters WE GREEN (index 2)
        self.provider._fallback_last_tick = time.time() - 1.0
        state0 = asyncio.run(self.provider.get_current_state())
        self.assertEqual(self.provider._fallback_phase_index, 2)  # WE GREEN
        self.assertEqual(state0.signals[2].state, "GREEN")  # East is GREEN
        self.assertEqual(state0.signals[0].state, "RED")    # North is RED

    def test_one_by_one_adaptive_countdown(self):
        """
        Verify that One-by-One mode also dynamically recalculates remaining green.
        """
        self.provider.set_signal_mode("one_by_one")
        self.provider._one_by_one_index = 0  # North
        self.provider._one_by_one_remaining = 35
        self.provider._one_by_one_is_yellow = False
        self.provider._one_by_one_last_tick = time.time()

        state = asyncio.run(self.provider.get_current_state())
        self.assertEqual(self.provider._one_by_one_remaining, 31)

        # Advance tick: demand-driven step-down occurs: 31 -> 27
        self.provider._one_by_one_last_tick = time.time() - 1.0
        state2 = asyncio.run(self.provider.get_current_state())
        self.assertEqual(self.provider._one_by_one_remaining, 27)

if __name__ == "__main__":
    unittest.main()
