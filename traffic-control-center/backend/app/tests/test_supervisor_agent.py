"""
Comprehensive Unit Tests for Traffic Supervisor Agent (Phase 7).
Validates Tests 1 through 11 as required by the system specification.
"""

import unittest
from datetime import datetime

from app.models.traffic_data import SignalPhase
from app.models.optimization_data import (
    OptimizationAction,
    RecommendationUrgency,
    OptimizationRationale,
    OptimizationRecommendation,
)
from app.models.supervisor_data import (
    SupervisorDecisionStatus,
    SupervisorDecision,
)
from app.agents.supervisor_agent import (
    TrafficSupervisorAgent,
    SupervisorPolicyConfig,
)


class TestTrafficSupervisorAgent(unittest.TestCase):

    def setUp(self):
        self.supervisor = TrafficSupervisorAgent()

    def _create_sample_recommendation(
        self,
        action: OptimizationAction = OptimizationAction.EXTEND_GREEN,
        target_phase: SignalPhase = SignalPhase.NS_GREEN,
        duration: float = 30.0,
        extension: float = 6.0,
    ) -> OptimizationRecommendation:
        return OptimizationRecommendation(
            junction_id="JUNCTION-01",
            data_source="TEST_SIMULATION",
            action=action,
            target_phase=target_phase,
            recommended_duration_s=duration,
            extension_seconds=extension,
            urgency=RecommendationUrgency.HIGH,
            rationale=OptimizationRationale(
                primary_factor="TEST",
                reasoning="Test recommendation",
            ),
        )

    # ------------------------------------------------------------------------
    # TEST 1: APPROVED Recommendation Within All Limits
    # ------------------------------------------------------------------------
    def test_01_approved_recommendation(self):
        """Recommendation within all regulatory and fairness limits -> APPROVED."""
        rec = self._create_sample_recommendation(
            action=OptimizationAction.EXTEND_GREEN,
            extension=6.0,
        )
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=30.0,      # Well below 60s max green cap (30 + 6 = 36s)
            consecutive_extensions_count=0,    # 1st extension (limit 2)
            opposing_red_wait_s=35.0,          # Well below 90s starvation limit
        )

        self.assertEqual(decision.status, SupervisorDecisionStatus.APPROVED)
        self.assertTrue(decision.forward_to_safety_agent)
        self.assertEqual(decision.authorized_phase, SignalPhase.NS_GREEN)
        self.assertEqual(decision.authorized_extension_s, 6.0)
        self.assertEqual(decision.policy_rationale, "All regulatory and fairness policies satisfied.")

    # ------------------------------------------------------------------------
    # TEST 2: Extension Exceeding 60s Truncated -> MODIFIED
    # ------------------------------------------------------------------------
    def test_02_max_green_extension_truncated(self):
        """
        Current green = 55s, requested extension = 10s.
        Remaining allowance = 60s - 55s = 5s.
        Expected: MODIFIED, authorized_extension_s = 5.0.
        """
        rec = self._create_sample_recommendation(
            action=OptimizationAction.EXTEND_GREEN,
            extension=10.0,
        )
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=55.0,
            consecutive_extensions_count=1,
            opposing_red_wait_s=50.0,
        )

        self.assertEqual(decision.status, SupervisorDecisionStatus.MODIFIED)
        self.assertTrue(decision.forward_to_safety_agent)
        self.assertEqual(decision.authorized_extension_s, 5.0)
        self.assertEqual(decision.authorized_duration_s, 60.0)
        self.assertIn("truncated", decision.policy_rationale.lower())

    # ------------------------------------------------------------------------
    # TEST 3: Extension When Max Green Cap Already Reached -> OVERRULED
    # ------------------------------------------------------------------------
    def test_03_max_green_cap_exhausted(self):
        """
        Current green = 60s (cap exhausted), requesting extension.
        Expected: OVERRULED.
        """
        rec = self._create_sample_recommendation(
            action=OptimizationAction.EXTEND_GREEN,
            extension=5.0,
        )
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=60.0,
            consecutive_extensions_count=1,
            opposing_red_wait_s=60.0,
        )

        self.assertEqual(decision.status, SupervisorDecisionStatus.OVERRULED)
        self.assertFalse(decision.forward_to_safety_agent)
        self.assertEqual(decision.authorized_extension_s, 0.0)
        self.assertEqual(decision.policy_rationale, "Maximum cumulative green threshold reached.")

    # ------------------------------------------------------------------------
    # TEST 4: Third Consecutive Extension -> OVERRULED
    # ------------------------------------------------------------------------
    def test_04_consecutive_extension_limit(self):
        """
        Already granted 2 consecutive extensions (consecutive_extensions_count = 2).
        Third extension request must be OVERRULED.
        """
        rec = self._create_sample_recommendation(
            action=OptimizationAction.EXTEND_GREEN,
            extension=6.0,
        )
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=40.0,
            consecutive_extensions_count=2,    # Already had 2 extensions
            opposing_red_wait_s=45.0,
        )

        self.assertEqual(decision.status, SupervisorDecisionStatus.OVERRULED)
        self.assertFalse(decision.forward_to_safety_agent)
        self.assertEqual(decision.authorized_extension_s, 0.0)
        self.assertEqual(
            decision.policy_rationale,
            "Maximum consecutive extensions limit reached for this corridor cycle."
        )

    # ------------------------------------------------------------------------
    # TEST 5: Opposing Red Wait >= 90s (Starvation) -> OVERRULED
    # ------------------------------------------------------------------------
    def test_05_starvation_prevention(self):
        """
        Opposing corridor waiting on red for 95.0s (>= 90.0s).
        Any extension request must be OVERRULED to prevent starvation.
        """
        rec = self._create_sample_recommendation(
            action=OptimizationAction.EXTEND_GREEN,
            extension=6.0,
        )
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=30.0,
            consecutive_extensions_count=0,
            opposing_red_wait_s=95.0,          # Exceeds 90.0s threshold!
        )

        self.assertEqual(decision.status, SupervisorDecisionStatus.OVERRULED)
        self.assertFalse(decision.forward_to_safety_agent)
        self.assertEqual(decision.authorized_extension_s, 0.0)
        self.assertEqual(
            decision.policy_rationale,
            "Opposing corridor exceeded maximum red waiting threshold."
        )

    # ------------------------------------------------------------------------
    # TEST 6: Phase Switch Before 15s Minimum Green -> OVERRULED
    # ------------------------------------------------------------------------
    def test_06_min_green_enforcement(self):
        """
        Optimization recommends SWITCH_PHASE when current corridor has only had 8.0s green.
        Minimum green = 15.0s.
        Expected: OVERRULED.
        """
        rec = self._create_sample_recommendation(
            action=OptimizationAction.SWITCH_PHASE,
            target_phase=SignalPhase.EW_GREEN,
            duration=25.0,
            extension=0.0,
        )
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=8.0,       # Only 8s elapsed (< 15s)
            consecutive_extensions_count=0,
            opposing_red_wait_s=8.0,
        )

        self.assertEqual(decision.status, SupervisorDecisionStatus.OVERRULED)
        self.assertFalse(decision.forward_to_safety_agent)
        self.assertEqual(decision.policy_rationale, "Minimum green requirement not satisfied.")

    # ------------------------------------------------------------------------
    # TEST 7: Granular Policy Checks Included in Output
    # ------------------------------------------------------------------------
    def test_07_granular_policy_checks_included(self):
        """Verify each of the 4 policy checks is exposed in the output with all fields."""
        rec = self._create_sample_recommendation()
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=25.0,
            consecutive_extensions_count=0,
            opposing_red_wait_s=30.0,
        )

        rule_names = [c.rule_name for c in decision.policy_checks]
        self.assertIn("MIN_GREEN", rule_names)
        self.assertIn("MAX_CUMULATIVE_GREEN", rule_names)
        self.assertIn("EXTENSION_LIMIT", rule_names)
        self.assertIn("STARVATION_PREVENTION", rule_names)

        # Inspect fields of each check
        for check in decision.policy_checks:
            self.assertIsInstance(check.rule_name, str)
            self.assertIsInstance(check.passed, bool)
            self.assertIsInstance(check.limit_value, float)
            self.assertIsInstance(check.observed_value, float)
            self.assertIsInstance(check.detail, str)

    # ------------------------------------------------------------------------
    # TEST 8: Explainable Policy Rationale
    # ------------------------------------------------------------------------
    def test_08_explainable_policy_rationale(self):
        """Verify policy rationale provides unambiguous, human-readable explanations."""
        rec = self._create_sample_recommendation(action=OptimizationAction.EXTEND_GREEN, extension=5.0)
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=58.0,
            consecutive_extensions_count=0,
            opposing_red_wait_s=20.0,
        )
        self.assertEqual(decision.status, SupervisorDecisionStatus.MODIFIED)
        self.assertTrue(len(decision.policy_rationale) > 10)
        self.assertIn("truncated", decision.policy_rationale.lower())

    # ------------------------------------------------------------------------
    # TEST 9: Preserve TEST_SIMULATION Data Source
    # ------------------------------------------------------------------------
    def test_09_preserve_test_simulation_source(self):
        """Verify data source metadata is strictly preserved."""
        rec = self._create_sample_recommendation()
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=20.0,
            consecutive_extensions_count=0,
            opposing_red_wait_s=20.0,
        )
        self.assertEqual(decision.data_source, "TEST_SIMULATION")
        summary = self.supervisor.get_summary(decision)
        self.assertEqual(summary["data_source"], "TEST_SIMULATION")

    # ------------------------------------------------------------------------
    # TEST 10: Strict Absence of Hardware / MQTT / Signal Controller Commands
    # ------------------------------------------------------------------------
    def test_10_strict_absence_of_hardware_commands(self):
        """Supervisor must NOT contain MQTT topics, hardware pins, or execution triggers."""
        rec = self._create_sample_recommendation()
        decision = self.supervisor.evaluate_recommendation(
            recommendation=rec,
            current_elapsed_green_s=20.0,
            consecutive_extensions_count=0,
            opposing_red_wait_s=20.0,
        )
        summary = self.supervisor.get_summary(decision)

        forbidden_fields = [
            "mqtt_publish",
            "mqtt_topic",
            "esp32_gpio",
            "execute_now",
            "signal_controller_call",
        ]
        for field in forbidden_fields:
            self.assertNotIn(field, summary)
            self.assertNotIn(field, decision.model_dump())

    # ------------------------------------------------------------------------
    # TEST 11: Forwards to Safety Agent (No Direct Actuation)
    # ------------------------------------------------------------------------
    def test_11_forward_to_safety_agent_flag(self):
        """Approved and Modified verdicts set forward_to_safety_agent = True, Overruled sets False."""
        rec_approved = self._create_sample_recommendation(action=OptimizationAction.EXTEND_GREEN, extension=5.0)
        dec_approved = self.supervisor.evaluate_recommendation(
            recommendation=rec_approved,
            current_elapsed_green_s=20.0,
            consecutive_extensions_count=0,
            opposing_red_wait_s=20.0,
        )
        self.assertTrue(dec_approved.forward_to_safety_agent)

        rec_modified = self._create_sample_recommendation(action=OptimizationAction.EXTEND_GREEN, extension=8.0)
        dec_modified = self.supervisor.evaluate_recommendation(
            recommendation=rec_modified,
            current_elapsed_green_s=55.0,
            consecutive_extensions_count=0,
            opposing_red_wait_s=20.0,
        )
        self.assertTrue(dec_modified.forward_to_safety_agent)

        rec_overruled = self._create_sample_recommendation(action=OptimizationAction.SWITCH_PHASE)
        dec_overruled = self.supervisor.evaluate_recommendation(
            recommendation=rec_overruled,
            current_elapsed_green_s=5.0,  # Below min green
            consecutive_extensions_count=0,
            opposing_red_wait_s=20.0,
        )
        self.assertFalse(dec_overruled.forward_to_safety_agent)


if __name__ == "__main__":
    unittest.main(verbosity=2)
