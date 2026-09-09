"""
Intelligent Traffic Pipeline Orchestrator (Phase 9).
Chains the complete 5-agent multi-agent architecture to the Authoritative Python Signal Controller:
  ControlledTrafficSource -> Monitoring -> Analysis -> Optimization -> Supervisor -> Safety -> Signal Controller -> MQTT -> ESP32
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.traffic_data import SignalPhase
from app.models.optimization_data import OptimizationAction
from app.models.supervisor_data import SupervisorDecisionStatus
from app.models.safety_data import SafetyStatus
from app.core.pipeline_data import PipelineExecutionResult
from app.core.signal_controller import SignalController

from app.agents.monitoring_agent import TrafficMonitoringAgent
from app.agents.analysis_agent import TrafficAnalysisAgent
from app.agents.optimization_agent import TrafficOptimizationAgent
from app.agents.supervisor_agent import TrafficSupervisorAgent
from app.agents.safety_agent import TrafficSafetyAgent

logger = logging.getLogger(__name__)


class IntelligentTrafficPipeline:
    """
    Unified Multi-Agent Intelligent Pipeline Orchestrator.
    Manages stateful cycle variables and executes the end-to-end intelligence loop.
    """

    def __init__(
        self,
        signal_controller: Optional[SignalController] = None,
        mock_actuation: bool = True,
        initial_phase: SignalPhase = SignalPhase.NS_GREEN,
    ):
        # 1. Initialize Intelligent Agents (Stage 1 to Stage 5)
        self.monitoring_agent = TrafficMonitoringAgent()
        self.analysis_agent = TrafficAnalysisAgent()
        self.optimization_agent = TrafficOptimizationAgent()
        self.supervisor_agent = TrafficSupervisorAgent()
        self.safety_agent = TrafficSafetyAgent()

        # 2. Authoritative Signal Controller (Stage 6)
        self.controller = signal_controller or SignalController(
            mock_actuation=mock_actuation,
            initial_phase=initial_phase,
        )

        # 3. Pipeline Operational State Tracking
        self.step_id: int = 1
        self.active_phase: SignalPhase = initial_phase
        self.elapsed_green_s: float = 0.0
        self.consecutive_extensions: int = 0
        self.opposing_red_wait_s: float = 0.0

    def step(self, raw_telemetry: Dict[str, Any]) -> PipelineExecutionResult:
        """
        Executes one synchronized step across the multi-agent pipeline.
        """
        step_id = self.step_id
        self.step_id += 1
        phase_before = self.active_phase

        # Inject current active phase and elapsed green into raw telemetry if missing
        if "current_signal_phase" not in raw_telemetry:
            raw_telemetry["current_signal_phase"] = self.active_phase.value

        # --------------------------------------------------------------------
        # Stage 1: Monitoring Agent ("WHAT IS HAPPENING?")
        # --------------------------------------------------------------------
        monitoring_state = self.monitoring_agent.process_raw_observation(raw_telemetry)

        # --------------------------------------------------------------------
        # Stage 2: Analysis Agent ("WHAT DOES IT MEAN?")
        # --------------------------------------------------------------------
        analysis_state = self.analysis_agent.analyze(monitoring_state)

        # --------------------------------------------------------------------
        # Stage 3: Optimization Agent ("WHAT SHOULD WE DO?")
        # --------------------------------------------------------------------
        opt_recommendation = self.optimization_agent.optimize(monitoring_state, analysis_state)

        # --------------------------------------------------------------------
        # Stage 4: Supervisor Agent ("IS IT ALLOWED BY POLICY?")
        # --------------------------------------------------------------------
        supervisor_decision = self.supervisor_agent.evaluate_recommendation(
            recommendation=opt_recommendation,
            current_elapsed_green_s=self.elapsed_green_s,
            consecutive_extensions_count=self.consecutive_extensions,
            opposing_red_wait_s=self.opposing_red_wait_s,
            current_active_phase=self.active_phase,
        )

        # --------------------------------------------------------------------
        # Stage 5: Safety Agent ("IS IT SAFE RIGHT NOW?")
        # --------------------------------------------------------------------
        safety_verdict = self.safety_agent.validate_transition(
            supervisor_decision=supervisor_decision,
            monitoring_state=monitoring_state,
            analysis_state=analysis_state,
        )

        # --------------------------------------------------------------------
        # Stage 6: Authoritative Signal Controller Actuation
        # --------------------------------------------------------------------
        actuation_dispatched = False
        dispatched_sequence = []
        action_summary = ""

        # Case A: Safety approves transition/extension
        if safety_verdict.status == SafetyStatus.SAFE_TO_EXECUTE and safety_verdict.is_safe:
            if opt_recommendation.action == OptimizationAction.SWITCH_PHASE:
                # Dispatch 3-step clearance sequence to Controller
                dispatched_sequence = safety_verdict.execution_sequence
                success = self.controller.execute_sequence(dispatched_sequence)
                if success:
                    actuation_dispatched = True
                    self.active_phase = supervisor_decision.authorized_phase
                    self.elapsed_green_s = 0.0
                    self.consecutive_extensions = 0
                    self.opposing_red_wait_s = 0.0
                    action_summary = f"Executed phase switch to {self.active_phase.value} via safe clearance sequence."
                else:
                    action_summary = "Actuation failed during physical execution."

            elif opt_recommendation.action == OptimizationAction.EXTEND_GREEN:
                # Dispatch green extension to Controller
                dispatched_sequence = safety_verdict.execution_sequence
                ext_seconds = supervisor_decision.authorized_extension_s
                self.controller.extend_current_phase(ext_seconds)
                actuation_dispatched = True
                self.elapsed_green_s += ext_seconds
                self.consecutive_extensions += 1
                self.opposing_red_wait_s += ext_seconds
                action_summary = f"Extended current green on {self.active_phase.value} by +{ext_seconds:.1f}s."

            else:
                # MAINTAIN_CURRENT
                self.elapsed_green_s += 1.0
                self.opposing_red_wait_s += 1.0
                action_summary = f"Maintaining current phase {self.active_phase.value}."

        # Case B: Safety orders HOLD
        elif safety_verdict.status == SafetyStatus.HOLD_CURRENT_PHASE:
            actuation_dispatched = False
            self.elapsed_green_s += 1.0
            self.opposing_red_wait_s += 1.0
            action_summary = f"Transition held by Safety Agent: {safety_verdict.safety_rationale}"

        # Case C: Emergency clearance required
        elif safety_verdict.status == SafetyStatus.EMERGENCY_CLEARANCE_REQUIRED:
            self.controller.emergency_all_red()
            self.active_phase = SignalPhase.ALL_RED
            actuation_dispatched = True
            action_summary = f"EMERGENCY CLEARANCE ACTIVATED: {safety_verdict.safety_rationale}"

        # Case D: Supervisor Overruled
        if supervisor_decision.status == SupervisorDecisionStatus.OVERRULED:
            action_summary = f"Optimization recommendation overruled by Supervisor: {supervisor_decision.policy_rationale}"

        return PipelineExecutionResult(
            step_id=step_id,
            timestamp=datetime.now(),
            data_source=monitoring_state.data_source,
            junction_id=monitoring_state.junction_id,
            active_phase_before=phase_before,
            active_phase_after=self.active_phase,
            elapsed_green_s=round(self.elapsed_green_s, 1),
            consecutive_extensions=self.consecutive_extensions,
            opposing_red_wait_s=round(self.opposing_red_wait_s, 1),
            monitoring=monitoring_state,
            analysis=analysis_state,
            optimization=opt_recommendation,
            supervisor=supervisor_decision,
            safety=safety_verdict,
            actuation_dispatched=actuation_dispatched,
            dispatched_sequence=dispatched_sequence,
            final_action_summary=action_summary,
        )

    def get_pipeline_state(self) -> Dict[str, Any]:
        """Returns snapshot of current orchestrator state."""
        return {
            "step_id": self.step_id,
            "active_phase": self.active_phase.value,
            "elapsed_green_s": self.elapsed_green_s,
            "consecutive_extensions": self.consecutive_extensions,
            "opposing_red_wait_s": self.opposing_red_wait_s,
            "controller_mode": "MOCK" if self.controller.mock_actuation else "LIVE",
            "last_actuation": self.controller.actuation_history[-1] if self.controller.actuation_history else None,
        }
