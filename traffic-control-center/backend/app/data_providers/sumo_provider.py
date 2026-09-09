import os
import sys
import time
import logging
import threading
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.data_providers.base_provider import TrafficStateProvider
from app.data_providers.schemas import (
    TrafficState,
    OverviewState,
    ApproachState,
    SignalHeadState,
    HardwareNodeState,
    TrendData
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Ensure SUMO_HOME is set and tools directory is added to sys.path
SUMO_HOME = os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\Eclipse\Sumo")
if SUMO_HOME and os.path.exists(SUMO_HOME):
    tools_path = os.path.join(SUMO_HOME, "tools")
    if tools_path not in sys.path:
        sys.path.append(tools_path)

try:
    import traci
except ImportError:
    traci = None
    logger.warning("traci module could not be imported. Ensure SUMO is installed.")

SUMO_CONFIG = r"C:\Traffic Project\config\junction.sumocfg"

# Direction Mapping for incoming/outgoing edges in junction2.net.xml
EDGE_DIRECTION_MAP: Dict[str, str] = {
    "E2": "North (N-Bound)",
    "E3": "South (S-Bound)",
    "E0": "West (W-Bound)",
    "E1": "East (E-Bound)"
}

EMERGENCY_TYPES = {"emergency", "police", "ambulance", "fire"}

class SumoTrafficProvider(TrafficStateProvider):
    """
    Real-Time SUMO TraCI Data Provider.
    Continuously advances the SUMO simulation in a background thread and keeps
    the latest TrafficState telemetry object, time-series history, and live dataset rows in memory.
    """

    def __init__(self, config_path: str = SUMO_CONFIG, start_loop: bool = True):
        self._source = "sumo_simulation"
        self._source_name = "SUMO Simulation Engine (TraCI Live Telemetry)"
        self._confidence = "exact"
        self.config_path = config_path
        self._latest_state: Optional[TrafficState] = None
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._step_counter = 0

        # SUMO TraCI Phase Tracking State
        self._last_phase_id: Optional[int] = None
        self._duration_applied_for_phase: Optional[int] = None
        self._phase_start_time: float = 0.0
        self._phase_end_time: float = 0.0
        self._current_decision_id: str = "DEC-INITIAL"
        self._pending_ns_green: Optional[int] = None
        self._pending_ew_green: Optional[int] = None

        # Rolling time-series history buffer (max 100 points)
        self._time_series_buffer: List[Dict[str, Any]] = []

        # Rolling live dataset rows (max 20 rows newest-first)
        self._dataset_rows: List[List[Any]] = []

        # Emergency Corridor & Control Mode State
        self._emergency_corridor_active: bool = False
        self._emergency_corridor_direction: str = "North-South"
        self._emergency_vehicle_type: str = "ambulance"
        self._adaptive_mode_enabled: bool = True

        # Scenario Injector State
        self._active_scenario: str = "normal"
        self._scenario_approach: str = "North"
        self._scenario_intensity: float = 1.0
        self._scenario_impact: str = "Nominal baseline conditions across junction"

        # Signal Sequencing Mode: 'paired_corridor' (2-phase) or 'one_by_one' (4-phase)
        self._signal_mode: str = "paired_corridor"
        self._one_by_one_index: int = 0
        self._one_by_one_remaining: int = 35
        self._one_by_one_is_yellow: bool = False
        self._one_by_one_last_tick: float = time.time()
        self._one_by_one_per_approach_durations: Dict[str, int] = {
            "North": 35,
            "East": 25,
            "South": 30,
            "West": 25
        }

        # Fallback Paired Corridor Phase Tracking (when TraCI is offline/standalone)
        self._fallback_phase_index: int = 0  # 0: NS_GREEN, 1: NS_YELLOW, 2: WE_GREEN, 3: WE_YELLOW
        self._fallback_remaining: int = 35
        self._fallback_last_tick: float = time.time()

        # GLIDE (Green Light Intelligent Dynamic Extension) Dynamic Timing Setup
        self._glide_enabled: bool = True
        self._glide_platoon_extension: int = 4
        self._glide_gap_out_threshold: float = 2.5
        self._glide_min_green: int = 15
        self._glide_max_green: int = 65
        self._glide_ns_green: int = 45
        self._glide_ew_green: int = 30
        self._glide_extension_active: bool = False
        self._glide_extension_applied: int = 0
        self._glide_status: str = "DYNAMIC_GLIDE_OPTIMIZED"
        self._active_remaining_green: Optional[int] = None
        self._last_sim_time: Optional[float] = None

        # Initial fallback state until simulation thread starts
        self._latest_state = self._create_default_state()

        # Start the continuous background simulation loop
        if start_loop:
            self._start_simulation_loop()

    def get_source_name(self) -> str:
        return self._source_name

    def set_approved_green_durations(self, ns_green: int, ew_green: int, decision_id: str = ""):
        """
        Applies supervisor-approved AI green durations to SUMO via TraCI setPhaseDuration.
        Ensures setPhaseDuration is called ONLY ONCE per phase instance to prevent resetting active phase countdowns every 3 seconds.
        """
        with self._lock:
            self._pending_ns_green = ns_green
            self._pending_ew_green = ew_green
            self._current_decision_id = decision_id
            if self._adaptive_mode_enabled:
                self._glide_ns_green = ns_green
                self._glide_ew_green = ew_green
            else:
                self._glide_ns_green = 30
                self._glide_ew_green = 30

        if traci is not None and self._is_running:
            try:
                tls_ids = traci.trafficlight.getIDList()
                if tls_ids:
                    tls_id = tls_ids[0]
                    curr_phase = int(traci.trafficlight.getPhase(tls_id))
                    active_ns = ns_green if self._adaptive_mode_enabled else 30
                    active_ew = ew_green if self._adaptive_mode_enabled else 30
                    # Only apply mid-phase if duration has NOT been set yet for this phase instance
                    if curr_phase == 0 and self._duration_applied_for_phase != 0:
                        traci.trafficlight.setPhaseDuration(tls_id, float(active_ew))
                        self._duration_applied_for_phase = 0
                        logger.info(f"[SUMO TraCI] Set initial WE GREEN duration {active_ew}s for Phase 0 (Decision: {decision_id})")
                    elif curr_phase == 2 and self._duration_applied_for_phase != 2:
                        traci.trafficlight.setPhaseDuration(tls_id, float(active_ns))
                        self._duration_applied_for_phase = 2
                        logger.info(f"[SUMO TraCI] Set initial NS GREEN duration {active_ns}s for Phase 2 (Decision: {decision_id})")
            except Exception as e:
                logger.warning(f"Note setting SUMO phase duration via TraCI: {e}")

    def trigger_emergency_corridor(self, direction: str = "North-South", active: bool = True, vehicle_type: str = "ambulance"):
        """
        Triggers instant TraCI green corridor preemption for emergency vehicles.
        Forces the SUMO traffic lights into immediate GREEN on the specified corridor direction.
        """
        with self._lock:
            self._emergency_corridor_active = active
            self._emergency_corridor_direction = direction
            self._emergency_vehicle_type = vehicle_type

        if active and traci is not None and self._is_running:
            try:
                tls_ids = traci.trafficlight.getIDList()
                if tls_ids:
                    tls_id = tls_ids[0]
                    # Phase 2 = NS GREEN, Phase 0 = WE GREEN
                    target_phase = 2 if ("North" in direction or "South" in direction or "NS" in direction) else 0
                    traci.trafficlight.setPhase(tls_id, target_phase)
                    traci.trafficlight.setPhaseDuration(tls_id, 90.0)
                    logger.info(f"[SUMO TraCI] EMERGENCY GREEN CORRIDOR ACTIVATED: Forced Phase {target_phase} ({direction}) for 90s")
            except Exception as e:
                logger.warning(f"Error executing TraCI emergency green corridor preemption: {e}")

    def set_adaptive_mode(self, enabled: bool):
        """Toggles between AI Adaptive Signal Timing and Fixed Signal Timing mode."""
        with self._lock:
            self._adaptive_mode_enabled = enabled
            self._glide_enabled = enabled
            if not enabled:
                self._glide_ns_green = 30
                self._glide_ew_green = 30
                self._one_by_one_per_approach_durations = {"North": 30, "East": 30, "South": 30, "West": 30}
                self._glide_status = "FIXED_CYCLE_SCHEDULE"
            else:
                self._glide_status = "DYNAMIC_GLIDE_OPTIMIZED"

            if self._latest_state is not None:
                if self._latest_state.overview:
                    self._latest_state.overview.ai_control_mode = "Autonomous Adaptive" if enabled else "Fixed Cycle"
                if self._latest_state.signals:
                    for sig in self._latest_state.signals:
                        sig.mode = "Autonomous Adaptive" if enabled else "Fixed Cycle"
        logger.info(f"[SUMO TraCI] Adaptive Signal Timing Mode set to: {enabled}")

    def set_signal_mode(self, mode: str) -> str:
        """Toggles between 'paired_corridor' (2-phase) and 'one_by_one' (4-phase isolated approach) mode."""
        with self._lock:
            if mode in ["one_by_one", "paired_corridor"]:
                self._signal_mode = mode
                if mode == "one_by_one":
                    self._one_by_one_index = 0
                    self._one_by_one_remaining = self._one_by_one_per_approach_durations.get("North", 35)
                    self._one_by_one_is_yellow = False
                    self._one_by_one_last_tick = time.time()
        logger.info(f"[SUMO Provider] Signal Sequencing Mode set to: {self._signal_mode}")
        return self._signal_mode

    def get_signal_mode(self) -> str:
        """Gets active signal sequencing mode."""
        with self._lock:
            return self._signal_mode

    def set_approved_individual_durations(self, durations: Dict[str, int], decision_id: str = ""):
        """Applies per-approach green times for One-by-One 4-phase mode."""
        with self._lock:
            if self._adaptive_mode_enabled and durations:
                self._one_by_one_per_approach_durations.update(durations)
            elif not self._adaptive_mode_enabled:
                self._one_by_one_per_approach_durations = {"North": 30, "East": 30, "South": 30, "West": 30}
            self._current_decision_id = decision_id
        logger.info(f"[SUMO Provider] Set One-by-One individual approach green allocations: {self._one_by_one_per_approach_durations} (Decision: {decision_id})")

    def get_glide_setup(self) -> Dict[str, Any]:
        """Gets current GLIDE (Green Light Intelligent Dynamic Extension) dynamic timing parameters."""
        with self._lock:
            return {
                "glide_enabled": self._glide_enabled,
                "adaptive_mode_enabled": self._adaptive_mode_enabled,
                "signal_mode": self._signal_mode,
                "platoon_extension_s": self._glide_platoon_extension,
                "gap_out_threshold_s": self._glide_gap_out_threshold,
                "min_green_s": self._glide_min_green,
                "max_green_s": self._glide_max_green,
                "ns_green_s": self._glide_ns_green,
                "ew_green_s": self._glide_ew_green,
                "extension_active": self._glide_extension_active,
                "extension_applied_s": self._glide_extension_applied,
                "status": self._glide_status,
                "active_approach_durations": dict(self._one_by_one_per_approach_durations),
                "active_phase_index": self._one_by_one_index,
                "active_approach": ["North", "East", "South", "West"][self._one_by_one_index],
                "remaining_seconds": self._one_by_one_remaining
            }

    def set_glide_setup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Updates GLIDE dynamic timing setup parameters for both paired corridors and 4-phase mode."""
        with self._lock:
            if "enabled" in params or "glide_enabled" in params:
                val = bool(params.get("enabled", params.get("glide_enabled", True)))
                self._glide_enabled = val
                self._adaptive_mode_enabled = val
                self._glide_status = "DYNAMIC_GLIDE_OPTIMIZED" if val else "FIXED_CYCLE_SCHEDULE"
            if "platoon_extension_s" in params:
                self._glide_platoon_extension = max(1, min(15, int(params["platoon_extension_s"])))
            if "gap_out_threshold_s" in params:
                self._glide_gap_out_threshold = max(1.0, min(8.0, float(params["gap_out_threshold_s"])))
            if "min_green_s" in params:
                self._glide_min_green = max(5, min(30, int(params["min_green_s"])))
            if "max_green_s" in params:
                self._glide_max_green = max(30, min(120, int(params["max_green_s"])))
            if "ns_green_s" in params or "ns_green" in params:
                self._glide_ns_green = max(15, min(90, int(params.get("ns_green_s", params.get("ns_green", 45)))))
                self.set_approved_green_durations(self._glide_ns_green, self._glide_ew_green, "DEC-GLIDE-SETUP")
            if "ew_green_s" in params or "ew_green" in params:
                self._glide_ew_green = max(15, min(90, int(params.get("ew_green_s", params.get("ew_green", 30)))))
                self.set_approved_green_durations(self._glide_ns_green, self._glide_ew_green, "DEC-GLIDE-SETUP")
            if "durations" in params and isinstance(params["durations"], dict):
                self._one_by_one_per_approach_durations.update(params["durations"])
        logger.info(f"[SUMO Provider] Updated GLIDE Dynamic Timing Setup: {self.get_glide_setup()}")
        return self.get_glide_setup()

    def inject_scenario(self, scenario: str, approach: str = "North", intensity: float = 1.0, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Dynamically injects a stress-test traffic scenario into the SUMO / AI pipeline."""
        with self._lock:
            self._active_scenario = scenario
            self._scenario_approach = approach or "North"
            self._scenario_intensity = max(0.5, min(3.0, float(intensity)))

            if scenario == "rush_hour":
                self._scenario_impact = f"Rush Hour Surge active on {self._scenario_approach} corridor ({self._scenario_intensity:.1f}x volume). AI dynamically expanding green phase allocation."
            elif scenario == "emergency_corridor":
                self._scenario_impact = f"Emergency Priority Corridor triggered for {self._scenario_approach}. Instant green preemption wave granted."
                self.trigger_emergency_corridor(direction=self._scenario_approach, active=True)
            elif scenario == "accident_blockage":
                self._scenario_impact = f"Accident / Lane Blockage detected on {self._scenario_approach} corridor. AI rerouting & throttling incoming flow."
            elif scenario == "weather_hazard":
                self._scenario_impact = "Adverse Weather Hazard (Heavy Rain/Fog). Reduced road friction, -40% speed limit, +4s clearance."
            else:
                self._active_scenario = "normal"
                self._scenario_impact = "Nominal baseline traffic conditions across junction"
                self.trigger_emergency_corridor(active=False)

        logger.info(f"[SUMO Provider] Scenario injected: {scenario} (Approach: {approach}, Intensity: {intensity})")
        return {
            "status": "SUCCESS",
            "active_scenario": self._active_scenario,
            "scenario_label": self._active_scenario.replace("_", " ").title(),
            "description": self._scenario_impact,
            "ai_response_plan": "AI Supervisor dynamically updated signal timing matrices and corridor clearance parameters.",
            "affected_approaches": [approach] if approach else ["North", "South", "East", "West"]
        }

    def get_active_scenario(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "active_scenario": self._active_scenario,
                "scenario_label": self._active_scenario.replace("_", " ").title(),
                "description": self._scenario_impact,
                "approach": self._scenario_approach,
                "intensity": self._scenario_intensity
            }

    def _start_simulation_loop(self):
        if traci is None:
            logger.error("TraCI module missing. Live SUMO telemetry disabled.")
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._run_simulation_thread, daemon=True)
        self._thread.start()

    def close(self):
        """Cleanly terminates the simulation loop and closes TraCI/sumo child processes."""
        if not self._is_running:
            return
        self._is_running = False
        if traci is not None and self._thread is not None:
            try:
                traci.close()
            except Exception:
                pass

    def _run_simulation_thread(self):
        logger.info(f"Starting continuous SUMO TraCI background loop using config: {self.config_path}")

        while self._is_running:
            try:
                # Start SUMO via TraCI
                sumo_cmd = ["sumo", "-c", self.config_path, "--no-step-log", "true"]
                traci.start(sumo_cmd)
                logger.info("SUMO TraCI simulation instance started successfully.")

                while self._is_running:
                    traci.simulationStep()
                    self._step_counter += 1

                    # Extract live metrics from SUMO
                    state = self._extract_telemetry_state()
                    with self._lock:
                        self._latest_state = state

                    # Control simulation step pace (1 Hz real-time pace so 3s yellow phases last 3 full seconds)
                    time.sleep(1.0 / max(0.1, float(getattr(settings, "SUMO_SIMULATION_SPEED", 1.0))))

                    # Check if simulation completed
                    if traci.simulation.getMinExpectedNumber() <= 0:
                        logger.info("SUMO simulation completed step limit. Restarting loop...")
                        break

                try:
                    traci.close()
                except Exception:
                    pass

            except Exception as e:
                logger.warning(f"SUMO TraCI simulation step note: {e}")
                try:
                    traci.close()
                except Exception:
                    pass
                time.sleep(1.0)  # Wait before attempting restart

    def _extract_telemetry_state(self) -> TrafficState:
        now_dt = datetime.now()
        now_str = now_dt.isoformat()
        time_hhmmss = now_dt.strftime("%H:%M:%S")

        # Vehicle IDs and metrics
        veh_ids = []
        if traci is not None and self._is_running:
            try:
                veh_ids = traci.vehicle.getIDList()
            except Exception:
                veh_ids = []
        total_veh_count = len(veh_ids)

        speeds_kmh = []
        waiting_times = []
        emergency_count = 0

        # Approach buckets: {direction_label: {count, speed_sum, wait_sum, halting_count}}
        approach_metrics: Dict[str, Dict[str, Any]] = {
            "North (N-Bound)": {"count": 0, "speed_sum": 0.0, "wait_sum": 0.0, "halting": 0},
            "South (S-Bound)": {"count": 0, "speed_sum": 0.0, "wait_sum": 0.0, "halting": 0},
            "East (E-Bound)": {"count": 0, "speed_sum": 0.0, "wait_sum": 0.0, "halting": 0},
            "West (W-Bound)": {"count": 0, "speed_sum": 0.0, "wait_sum": 0.0, "halting": 0},
        }

        for vid in veh_ids:
            try:
                spd_m_s = traci.vehicle.getSpeed(vid)
                spd_kmh = max(0.0, spd_m_s * 3.6)
                wait_s = traci.vehicle.getWaitingTime(vid)
                vtype = traci.vehicle.getTypeID(vid).lower()
                edge_id = traci.vehicle.getRoadID(vid)

                speeds_kmh.append(spd_kmh)
                waiting_times.append(wait_s)

                if any(et in vtype for et in EMERGENCY_TYPES):
                    emergency_count += 1

                # Map vehicle to approach
                direction = EDGE_DIRECTION_MAP.get(edge_id)
                if direction and direction in approach_metrics:
                    approach_metrics[direction]["count"] += 1
                    approach_metrics[direction]["speed_sum"] += spd_kmh
                    approach_metrics[direction]["wait_sum"] += wait_s
                    if spd_m_s < 0.1:
                        approach_metrics[direction]["halting"] += 1
            except Exception:
                continue

        # Global aggregations
        avg_speed = round(float(sum(speeds_kmh) / total_veh_count), 1) if total_veh_count > 0 else 40.0
        avg_wait = round(float(sum(waiting_times) / total_veh_count), 1) if total_veh_count > 0 else 0.0

        # Halting vehicles across all non-internal lanes
        halting_vehicles = 0
        if traci is not None and self._is_running:
            try:
                lane_ids = [l for l in traci.lane.getIDList() if not l.startswith(":")]
                halting_vehicles = sum(traci.lane.getLastStepHaltingNumber(l) for l in lane_ids)
            except Exception:
                halting_vehicles = 0
        total_queue_length = round(halting_vehicles * 5.0, 1)  # 5 meters per queued vehicle

        # Density: vehicle count divided by total monitored network length (~0.5 km)
        avg_density = round(total_veh_count / 0.5, 1) if total_veh_count > 0 else 0.0
        throughput = int(total_veh_count * 35) + 800  # Estimated hourly throughput

        # Level of Service (LOS A to F)
        if avg_speed >= 35.0:
            los = "A"
        elif avg_speed >= 28.0:
            los = "B"
        elif avg_speed >= 20.0:
            los = "C"
        elif avg_speed >= 14.0:
            los = "D"
        elif avg_speed >= 8.0:
            los = "E"
        else:
            los = "F"

        # Current Congestion status
        if total_queue_length < 15:
            current_congestion = "Optimal"
        elif total_queue_length < 40:
            current_congestion = "Moderate"
        else:
            current_congestion = "Congested"

        # Determine signal phase and timings based on selected signal sequencing mode
        current_signal_phase = "NS GREEN"
        sim_time = 0.0
        phase_id = 0
        remaining_time = 15
        allocated_green = 35
        adaptive_action = "NOMINAL"
        adaptive_reason = "Nominal timing cycle"

        n_cnt = approach_metrics["North (N-Bound)"]["count"]
        s_cnt = approach_metrics["South (S-Bound)"]["count"]
        e_cnt = approach_metrics["East (E-Bound)"]["count"]
        w_cnt = approach_metrics["West (W-Bound)"]["count"]
        ns_veh_count = n_cnt + s_cnt
        ew_veh_count = e_cnt + w_cnt
        ns_halting = approach_metrics["North (N-Bound)"]["halting"] + approach_metrics["South (S-Bound)"]["halting"]
        ew_halting = approach_metrics["East (E-Bound)"]["halting"] + approach_metrics["West (W-Bound)"]["halting"]

        if self._signal_mode == "one_by_one":
            # 4-Phase Isolated Approach Sequencing Mode with Dynamic GLIDE Optimization: [North -> East -> South -> West]
            now_time = time.time()
            dt = max(0.1, min(2.0, now_time - self._one_by_one_last_tick))
            self._one_by_one_last_tick = now_time
            decrement = int(round(dt))

            curr_approach_name = ["North", "East", "South", "West"][self._one_by_one_index]
            app_full_name = f"{curr_approach_name} ({curr_approach_name[0]}-Bound)"
            app_metric = approach_metrics.get(app_full_name, {"count": 0, "halting": 0})
            active_veh_count = app_metric.get("count", 0)
            active_halt_count = app_metric.get("halting", 0)
            active_appr_count = max(0, active_veh_count - active_halt_count)

            if not self._one_by_one_is_yellow:
                # Active Green Countdown with Dynamic Environmental Adaptation
                # A. Platoon Dynamic Extension Check
                if self._glide_enabled and self._one_by_one_remaining <= 5 and not self._glide_extension_active and active_veh_count >= 2:
                    ext_sec = self._glide_platoon_extension
                    self._one_by_one_remaining += ext_sec
                    self._glide_extension_active = True
                    self._glide_extension_applied = ext_sec
                    self._glide_status = f"GLIDE_EXTENSION_+{ext_sec}s_PLATOON"
                    adaptive_action = f"EXTENDING (+{ext_sec}s)"
                    adaptive_reason = f"Platoon detected on {curr_approach_name} ({active_veh_count} veh); dynamic extension granted"
                    logger.info(f"[GLIDE Dynamic Timing] Platoon detected on {curr_approach_name}! Applied +{ext_sec}s dynamic extension.")

                # B. Early Gap-Out Check (Zero-queue empty approach clearance)
                elif self._adaptive_mode_enabled and self._one_by_one_remaining > 3 and active_veh_count == 0 and (
                    sum(approach_metrics[k]["halting"] for k in approach_metrics if curr_approach_name not in k) > 0 or (total_veh_count - active_veh_count) > 0
                ):
                    self._one_by_one_remaining = 2
                    self._glide_status = f"GAP_OUT_{curr_approach_name.upper()}_CLEARED"
                    adaptive_action = "GAP-OUT"
                    adaptive_reason = f"{curr_approach_name} queue cleared; early handover to waiting approaches"
                    logger.info(f"[GLIDE Dynamic Timing] Gap-out on {curr_approach_name}: 0 vehicles detected, early transition to YELLOW.")

                # C. Dynamic Demand Recalculation (Demand drop / queue discharged)
                elif self._adaptive_mode_enabled and self._one_by_one_remaining > 6:
                    needed_rem = int(round(active_halt_count * 2.0 + active_appr_count * 1.5 + 3))
                    if needed_rem < self._one_by_one_remaining - 2:
                        step_down = min(self._one_by_one_remaining - 1, max(needed_rem, self._one_by_one_remaining - 4))
                        self._one_by_one_remaining = step_down
                        adaptive_action = "ADAPTIVE_RECALCULATION"
                        adaptive_reason = f"Demand reduced on {curr_approach_name} ({active_veh_count} veh); recalculated green to {step_down}s"
                        self._glide_status = "DYNAMIC_RECALCULATION_OPTIMIZED"
                    else:
                        self._one_by_one_remaining = max(0, self._one_by_one_remaining - decrement)
                else:
                    self._one_by_one_remaining = max(0, self._one_by_one_remaining - decrement)

                if self._one_by_one_remaining <= 0:
                    # Green duration ended -> initiate mandatory 3-second YELLOW clearance
                    self._one_by_one_is_yellow = True
                    self._one_by_one_remaining = 5 if self._active_scenario == "weather_hazard" else 3
                    logger.info(f"[One-by-One] {curr_approach_name} GREEN expired -> Entered {self._one_by_one_remaining}s YELLOW clearance")
            else:
                # Active Yellow Clearance Countdown
                adaptive_action = "CLEARANCE (YELLOW)"
                adaptive_reason = f"Yellow clearance interval for {curr_approach_name}"
                self._one_by_one_remaining = max(0, self._one_by_one_remaining - decrement)
                if self._one_by_one_remaining <= 0:
                    # Yellow clearance ended -> advance to next approach in GREEN
                    self._one_by_one_index = (self._one_by_one_index + 1) % 4
                    curr_approach_name = ["North", "East", "South", "West"][self._one_by_one_index]
                    base_dur = self._one_by_one_per_approach_durations.get(curr_approach_name, 30)
                    if self._active_scenario == "rush_hour" and curr_approach_name.lower() in self._scenario_approach.lower():
                        base_dur = min(65, int(base_dur * 1.5))
                    self._one_by_one_remaining = base_dur
                    self._one_by_one_is_yellow = False
                    self._glide_extension_active = False
                    self._glide_extension_applied = 0
                    self._glide_status = "DYNAMIC_GLIDE_OPTIMIZED"
                    adaptive_action = "ADAPTIVE GREEN"
                    adaptive_reason = f"Commenced green allocation ({base_dur}s) for {curr_approach_name}"
                    logger.info(f"[One-by-One] Clearance complete -> Advanced to {curr_approach_name} GREEN ({self._one_by_one_remaining}s)")

            curr_approach_name = ["North", "East", "South", "West"][self._one_by_one_index]
            current_signal_phase = f"{curr_approach_name.upper()} {'YELLOW' if self._one_by_one_is_yellow else 'GREEN'}"
            remaining_time = self._one_by_one_remaining
            allocated_green = 3 if self._one_by_one_is_yellow else self._one_by_one_per_approach_durations.get(curr_approach_name, 30)
            phase_id = self._one_by_one_index

            tls_ids = []
            if traci is not None and self._is_running:
                try:
                    tls_ids = traci.trafficlight.getIDList()
                except Exception:
                    tls_ids = []
            if tls_ids:
                try:
                    sim_time = float(traci.simulation.getTime())
                except Exception:
                    sim_time = 0.0
        else:
            # Paired Corridors (2-Phase) Mode: [North + South] <-> [East + West]
            tls_ids = []
            if traci is not None and self._is_running:
                try:
                    tls_ids = traci.trafficlight.getIDList()
                except Exception:
                    tls_ids = []
            if tls_ids:
                tls_id = tls_ids[0]
                sim_time = float(traci.simulation.getTime())
                phase_id = int(traci.trafficlight.getPhase(tls_id))
                phase_state = traci.trafficlight.getRedYellowGreenState(tls_id)

                # Phase transition detection and logging
                if self._last_phase_id is None or phase_id != self._last_phase_id:
                    prev_phase = self._last_phase_id
                    self._phase_start_time = sim_time
                    self._last_phase_id = phase_id
                    self._duration_applied_for_phase = None
                    self._glide_extension_active = False
                    self._glide_extension_applied = 0

                    if phase_id == 0:
                        # WE GREEN begins
                        init_ew = self._pending_ew_green if self._pending_ew_green is not None else self._glide_ew_green
                        self._active_remaining_green = int(init_ew)
                        try:
                            traci.trafficlight.setPhaseDuration(tls_id, float(init_ew))
                        except Exception:
                            pass
                        self._phase_end_time = sim_time + init_ew
                    elif phase_id == 2:
                        # NS GREEN begins
                        init_ns = self._pending_ns_green if self._pending_ns_green is not None else self._glide_ns_green
                        self._active_remaining_green = int(init_ns)
                        try:
                            traci.trafficlight.setPhaseDuration(tls_id, float(init_ns))
                        except Exception:
                            pass
                        self._phase_end_time = sim_time + init_ns
                    elif phase_id in (1, 3):
                        # YELLOW CLEARANCE (Phase 1 = WE Yellow, Phase 3 = NS Yellow)
                        # Mandatory 3s clearance (or 5s weather)
                        yellow_dur = 5 if self._active_scenario == "weather_hazard" else 3
                        self._active_remaining_green = int(yellow_dur)
                        try:
                            traci.trafficlight.setPhaseDuration(tls_id, float(yellow_dur))
                        except Exception:
                            pass
                        self._phase_end_time = sim_time + yellow_dur
                    else:
                        self._active_remaining_green = 2
                        self._phase_end_time = sim_time + 2

                    logger.info(
                        f"[SUMO_SIGNAL_PHASE_EVENT] sim_time={sim_time:.1f}s | signal_id=TLS-{tls_id} | "
                        f"prev_phase={prev_phase} -> new_phase={phase_id} | phase_start_time={self._phase_start_time:.1f}s | "
                        f"phase_end_time={self._phase_end_time:.1f}s | remaining_time={self._active_remaining_green}s | "
                        f"decision_id={self._current_decision_id} | reason='SUMO phase transition' | source='sumo_simulation'"
                    )

                # Initialize remaining green if unset
                if self._active_remaining_green is None:
                    try:
                        next_sw = float(traci.trafficlight.getNextSwitch(tls_id))
                        self._active_remaining_green = max(0, int(round(next_sw - sim_time)))
                    except Exception:
                        self._active_remaining_green = 30

                # Compute time delta from last simulation step
                sim_dt = 1.0
                if self._last_sim_time is not None:
                    sim_dt = max(0.1, min(2.0, sim_time - self._last_sim_time))
                self._last_sim_time = sim_time
                elapsed_green = max(0.0, sim_time - self._phase_start_time)

                # PHASE EVALUATION:
                if phase_id in (1, 3):
                    # YELLOW CLEARANCE INTERVAL: Strict, clean countdown.
                    # The Yellow-light phase is already working correctly and completely preserved.
                    self._active_remaining_green = max(0, self._active_remaining_green - int(round(sim_dt)))
                    remaining_time = self._active_remaining_green
                    adaptive_action = "CLEARANCE (YELLOW)"
                    corridor_lbl = "East-West" if phase_id == 1 else "North-South"
                    adaptive_reason = f"Mandatory yellow clearance interval for {corridor_lbl} ({remaining_time}s)"

                    if self._active_remaining_green <= 0:
                        # Yellow duration ended -> advance to next phase in TraCI
                        next_green_phase = 2 if phase_id == 1 else 0
                        try:
                            traci.trafficlight.setPhase(tls_id, next_green_phase)
                            init_dur = float(self._pending_ns_green if next_green_phase == 2 else (self._pending_ew_green or 30))
                            traci.trafficlight.setPhaseDuration(tls_id, init_dur)
                            self._last_phase_id = next_green_phase
                            self._phase_start_time = sim_time
                            self._phase_end_time = sim_time + init_dur
                            self._active_remaining_green = int(init_dur)
                            phase_id = next_green_phase
                            logger.info(f"[SUMO TraCI] Yellow clearance completed -> Advanced to Phase {next_green_phase} GREEN ({init_dur}s)")
                        except Exception as e:
                            logger.warning(f"Error advancing from Yellow: {e}")
                elif phase_id in (0, 2):
                    # ACTIVE GREEN PHASE: Adaptive & Dynamic Remaining Green Recalculation
                    if phase_id == 2:
                        active_corridor = "North-South"
                        active_veh = ns_veh_count
                        active_halt = ns_halting
                        opp_veh = ew_veh_count
                        opp_halt = ew_halting
                        opp_corridor = "East-West"
                        yellow_phase = 3
                    else:
                        active_corridor = "East-West"
                        active_veh = ew_veh_count
                        active_halt = ew_halting
                        opp_veh = ns_veh_count
                        opp_halt = ns_halting
                        opp_corridor = "North-South"
                        yellow_phase = 1

                    active_approaching = max(0, active_veh - active_halt)
                    current_rem = self._active_remaining_green

                    if self._emergency_corridor_active:
                        adaptive_action = "HOLD_EMERGENCY"
                        adaptive_reason = f"Emergency Priority Corridor active on {self._emergency_corridor_direction}"
                        self._glide_status = "EMERGENCY_CORRIDOR_PREEMPTION"
                        new_rem = 90
                    elif self._adaptive_mode_enabled:
                        # 1. Physical Demand Calculation:
                        # Saturation discharge headway: ~2.0s per halted vehicle, ~1.5s per approaching vehicle in transit + 4s dilemma/clearance buffer
                        needed_remaining = int(round(active_halt * 2.0 + active_approaching * 1.5 + 4))

                        # Supervisor Policy Constraints:
                        # Minimum green enforcement:
                        min_rem = max(0, int(self._glide_min_green - elapsed_green))
                        needed_remaining = max(needed_remaining, min_rem)
                        # Maximum cumulative green enforcement:
                        max_rem = max(0, int(self._glide_max_green - elapsed_green))
                        needed_remaining = min(needed_remaining, max_rem)

                        # 2. Dynamic Adaptive Recalculation Conditions:
                        # A. Platoon Dynamic Extension Check:
                        if (active_approaching >= 2 or active_veh >= 3) and current_rem <= 8 and not self._glide_extension_active:
                            if (elapsed_green + self._glide_platoon_extension) <= self._glide_max_green and opp_halt < 8:
                                ext_sec = self._glide_platoon_extension
                                new_rem = current_rem + ext_sec
                                self._glide_extension_active = True
                                self._glide_extension_applied = ext_sec
                                self._glide_status = f"GLIDE_EXTENSION_+{ext_sec}s_PLATOON"
                                adaptive_action = f"EXTENDING (+{ext_sec}s)"
                                adaptive_reason = f"Platoon detected on {active_corridor} ({active_veh} veh, {active_approaching} approaching); +{ext_sec}s extension granted"
                                logger.info(f"[GLIDE TraCI] Platoon extended {active_corridor} green: {current_rem}s -> {new_rem}s")
                            else:
                                new_rem = max(0, current_rem - 1)

                        # B. Early Gap-Out Check (Zero-queue empty approach clearance):
                        elif active_veh == 0 and elapsed_green >= self._glide_min_green:
                            if opp_veh > 0 or opp_halt > 0:
                                if current_rem > 2:
                                    new_rem = 2
                                    self._glide_status = "GAP-OUT_EARLY_CLEARANCE"
                                    adaptive_action = "GAP-OUT"
                                    adaptive_reason = f"{active_corridor} queue cleared (0 veh); early handover to {opp_corridor} ({opp_veh} waiting)"
                                    logger.info(f"[GLIDE TraCI] Gap-out on {active_corridor}: cleared -> remaining reduced to 2s")
                                else:
                                    new_rem = max(0, current_rem - 1)
                            else:
                                new_rem = max(0, current_rem - 1)

                        # C. Opposing Queue Anti-Starvation Check:
                        elif opp_halt >= 5 and elapsed_green >= self._glide_min_green and current_rem > 6:
                            target_cap = max(3, min(current_rem - 4, int(max(4, 16 - opp_halt * 2))))
                            if target_cap < current_rem:
                                new_rem = target_cap
                                adaptive_action = "QUEUE_PRESSURE_TRUNCATE"
                                adaptive_reason = f"Opposing queue pressure ({opp_halt} halting vehicles on {opp_corridor}); shortening active green to {target_cap}s"
                                self._glide_status = "OPPOSING_QUEUE_PRESSURE_CAPPED"
                                logger.info(f"[GLIDE TraCI] Opposing queue pressure on {opp_corridor}: truncated {active_corridor} green {current_rem}s -> {new_rem}s")
                            else:
                                new_rem = max(0, current_rem - 1)

                        # D. Dynamic Demand Reduction (Queue cleared faster than expected / demand drop):
                        elif needed_remaining < current_rem - 2 and elapsed_green >= self._glide_min_green:
                            step_down = min(current_rem - 1, max(needed_remaining, current_rem - 5))
                            new_rem = step_down
                            adaptive_action = "ADAPTIVE_RECALCULATION"
                            adaptive_reason = f"Traffic demand reduced ({active_veh} veh, {active_halt} queued); recalculated remaining green to {step_down}s"
                            self._glide_status = "DYNAMIC_RECALCULATION_OPTIMIZED"
                            logger.info(f"[GLIDE TraCI] Dynamic recalculation for {active_corridor}: {current_rem}s -> {new_rem}s")

                        # E. Nominal Dynamic Countdown (Normal 1-by-1 step between events):
                        else:
                            new_rem = max(0, current_rem - 1)
                            if adaptive_action == "NOMINAL":
                                adaptive_action = "DYNAMIC_COUNTDOWN"
                                adaptive_reason = f"Active corridor {active_corridor}: {active_veh} veh in transit ({needed_remaining}s demand needed)"
                    else:
                        # Fixed cycle mode: standard 1s countdown
                        new_rem = max(0, current_rem - 1)
                        adaptive_action = "FIXED_COUNTDOWN"
                        adaptive_reason = "Fixed cycle schedule active"

                    # Check if Green duration expired -> advance strictly to YELLOW clearance!
                    if new_rem <= 0:
                        yellow_dur = 5.0 if self._active_scenario == "weather_hazard" else 3.0
                        try:
                            traci.trafficlight.setPhase(tls_id, yellow_phase)
                            traci.trafficlight.setPhaseDuration(tls_id, yellow_dur)
                            self._last_phase_id = yellow_phase
                            self._phase_start_time = sim_time
                            self._phase_end_time = sim_time + yellow_dur
                            self._active_remaining_green = int(yellow_dur)
                            phase_id = yellow_phase
                            remaining_time = int(yellow_dur)
                            adaptive_action = "CLEARANCE (YELLOW)"
                            adaptive_reason = f"Green phase completed -> 3s yellow clearance initiated for {active_corridor}"
                            logger.info(f"[SUMO TraCI] {active_corridor} GREEN expired -> Entered {yellow_dur}s YELLOW clearance (Phase {yellow_phase})")
                        except Exception as e:
                            logger.warning(f"Error switching to Yellow phase: {e}")
                    else:
                        self._active_remaining_green = new_rem
                        remaining_time = new_rem
                        self._phase_end_time = sim_time + new_rem
                        try:
                            traci.trafficlight.setPhaseDuration(tls_id, float(new_rem))
                        except Exception:
                            pass

                st_lower = phase_state.lower()
                if phase_id == 1 or st_lower.startswith("yyy"):
                    current_signal_phase = "WE YELLOW"
                    if adaptive_action in ("NOMINAL", "DYNAMIC_COUNTDOWN"):
                        adaptive_action = "CLEARANCE (YELLOW)"
                elif phase_id == 3 or "yyy" in st_lower or st_lower.endswith("yyy"):
                    current_signal_phase = "NS YELLOW"
                    if adaptive_action in ("NOMINAL", "DYNAMIC_COUNTDOWN"):
                        adaptive_action = "CLEARANCE (YELLOW)"
                elif phase_id == 0 or st_lower.startswith("ggg"):
                    current_signal_phase = "WE GREEN"
                elif phase_id == 2 or "ggg" in st_lower:
                    current_signal_phase = "NS GREEN"
                else:
                    current_signal_phase = "ALL RED"
            else:
                # Fallback internal simulation cycle when TraCI is offline
                now_time = time.time()
                dt = max(0.1, min(2.0, now_time - self._fallback_last_tick))
                self._fallback_last_tick = now_time
                decrement = int(round(dt))

                # Environmental Actuated Check for Fallback simulation
                if self._fallback_phase_index in (0, 2) and self._adaptive_mode_enabled:
                    active_veh = ns_veh_count if self._fallback_phase_index == 0 else ew_veh_count
                    active_halt = ns_halting if self._fallback_phase_index == 0 else ew_halting
                    active_approaching = max(0, active_veh - active_halt)
                    opp_veh = ew_veh_count if self._fallback_phase_index == 0 else ns_veh_count
                    opp_halt = ew_halting if self._fallback_phase_index == 0 else ns_halting
                    corridor_name = "North-South" if self._fallback_phase_index == 0 else "East-West"
                    opp_corridor = "East-West" if self._fallback_phase_index == 0 else "North-South"

                    # Demand Needed Green in fallback
                    needed_remaining = int(round(active_halt * 2.0 + active_approaching * 1.5 + 4))

                    # Platoon Extension in fallback
                    if (active_approaching >= 2 or active_veh >= 3) and self._fallback_remaining <= 8 and not self._glide_extension_active:
                        ext_sec = self._glide_platoon_extension
                        self._fallback_remaining += ext_sec
                        self._glide_extension_active = True
                        self._glide_extension_applied = ext_sec
                        self._glide_status = f"GLIDE_EXTENSION_+{ext_sec}s_PLATOON"
                        adaptive_action = f"EXTENDING (+{ext_sec}s)"
                        adaptive_reason = f"Platoon detected on {corridor_name} ({active_veh} veh); +{ext_sec}s extension granted"
                    # Early Gap-Out in fallback
                    elif self._fallback_remaining > 3 and active_veh == 0 and (opp_veh > 0 or opp_halt > 0):
                        self._fallback_remaining = 2
                        self._glide_status = "GAP-OUT_EARLY_CLEARANCE"
                        adaptive_action = "GAP-OUT"
                        adaptive_reason = f"{corridor_name} cleared; early gap-out transition"
                    # Opposing Queue Pressure Truncation in fallback
                    elif opp_halt >= 5 and self._fallback_remaining > 6:
                        target_cap = max(3, min(self._fallback_remaining - 4, int(max(4, 16 - opp_halt * 2))))
                        if target_cap < self._fallback_remaining:
                            self._fallback_remaining = target_cap
                            adaptive_action = "QUEUE_PRESSURE_TRUNCATE"
                            adaptive_reason = f"Opposing queue pressure ({opp_halt} veh on {opp_corridor}); shortening active green"
                            self._glide_status = "OPPOSING_QUEUE_PRESSURE_CAPPED"
                    # Dynamic Demand Recalculation in fallback
                    elif needed_remaining < self._fallback_remaining - 2:
                        step_down = min(self._fallback_remaining - 1, max(needed_remaining, self._fallback_remaining - 5))
                        self._fallback_remaining = step_down
                        adaptive_action = "ADAPTIVE_RECALCULATION"
                        adaptive_reason = f"Traffic demand reduced ({active_veh} veh); recalculated remaining green to {step_down}s"
                        self._glide_status = "DYNAMIC_RECALCULATION_OPTIMIZED"
                    else:
                        self._fallback_remaining = max(0, self._fallback_remaining - decrement)
                else:
                    self._fallback_remaining = max(0, self._fallback_remaining - decrement)

                # Fallback cycle: 0: NS GREEN (35s) -> 1: NS YELLOW (3s) -> 2: WE GREEN (30s) -> 3: WE YELLOW (3s)
                if self._fallback_remaining <= 0:
                    self._fallback_phase_index = (self._fallback_phase_index + 1) % 4
                    self._glide_extension_active = False
                    self._glide_extension_applied = 0
                    if self._fallback_phase_index == 0:
                        base_ns = getattr(self, "_glide_ns_green", 35)
                        if self._active_scenario == "rush_hour" and ("North" in self._scenario_approach or "South" in self._scenario_approach):
                            base_ns = 55
                        self._fallback_remaining = base_ns
                    elif self._fallback_phase_index == 1:
                        self._fallback_remaining = 5 if self._active_scenario == "weather_hazard" else 3
                    elif self._fallback_phase_index == 2:
                        base_ew = getattr(self, "_glide_ew_green", 30)
                        if self._active_scenario == "rush_hour" and ("East" in self._scenario_approach or "West" in self._scenario_approach):
                            base_ew = 50
                        self._fallback_remaining = base_ew
                    elif self._fallback_phase_index == 3:
                        self._fallback_remaining = 5 if self._active_scenario == "weather_hazard" else 3

                phase_id = self._fallback_phase_index
                remaining_time = self._fallback_remaining
                if self._fallback_phase_index == 0:
                    current_signal_phase = "NS GREEN"
                elif self._fallback_phase_index == 1:
                    current_signal_phase = "NS YELLOW"
                    adaptive_action = "CLEARANCE (YELLOW)"
                elif self._fallback_phase_index == 2:
                    current_signal_phase = "WE GREEN"
                elif self._fallback_phase_index == 3:
                    current_signal_phase = "WE YELLOW"
                    adaptive_action = "CLEARANCE (YELLOW)"

            allocated_green = 45 if "NS GREEN" in current_signal_phase else 30

        overview_data = OverviewState(
            timestamp=now_str,
            source=self._source,
            confidence=self._confidence,
            total_vehicle_count=total_veh_count,
            avg_speed_kmh=avg_speed,
            total_queue_length_m=total_queue_length,
            avg_density_veh_km=avg_density,
            throughput_vph=throughput,
            level_of_service=los,
            active_signals=4,
            ai_control_mode=("EMERGENCY_GREEN_CORRIDOR" if self._emergency_corridor_active else ("Autonomous Adaptive" if self._adaptive_mode_enabled else "Fixed Cycle")),
            emergency_vehicle_count=emergency_count,
            current_congestion=current_congestion,
            current_signal_phase=current_signal_phase,
            signal_mode=self._signal_mode,
            active_scenario=self._active_scenario,
            scenario_impact=self._scenario_impact,
            adaptive_status=self._glide_status,
            adaptive_event=f"{adaptive_action}: {adaptive_reason}"
        )

        # Build ApproachState list
        approaches_data = []
        n_cnt = approach_metrics["North (N-Bound)"]["count"]
        s_cnt = approach_metrics["South (S-Bound)"]["count"]
        e_cnt = approach_metrics["East (E-Bound)"]["count"]
        w_cnt = approach_metrics["West (W-Bound)"]["count"]

        for app_name, data in approach_metrics.items():
            cnt = data["count"]
            app_avg_spd = round(data["speed_sum"] / cnt, 1) if cnt > 0 else 40.0
            app_queue = round(data["halting"] * 5.0, 1)
            app_density = round(cnt / 0.15, 1)  # per 150m approach length
            status = "Optimal" if app_queue < 10 else ("Moderate" if app_queue < 25 else "Congested")

            approaches_data.append(ApproachState(
                approach=app_name,
                vehicle_count=cnt,
                avg_speed=app_avg_spd,
                queue_len=app_queue,
                density=app_density,
                status=status
            ))

        # Update time series history buffer
        time_series_entry = {
            "time": time_hhmmss,
            "volume": total_veh_count,
            "speed": avg_speed,
            "queue": total_queue_length,
            "density": avg_density,
            "waiting": avg_wait,
            "green_duration": 45 if "NS GREEN" in current_signal_phase else 30
        }
        self._time_series_buffer.append(time_series_entry)
        if len(self._time_series_buffer) > 100:
            self._time_series_buffer.pop(0)

        # Update dataset rows (20 newest rows)
        decision_id = f"DEC-{now_dt.strftime('%Y%m%d')}-{self._step_counter:04d}"
        allocated_green = 45 if "NS GREEN" in current_signal_phase else 30
        dataset_row = [
            time_hhmmss,
            n_cnt,
            s_cnt,
            e_cnt,
            w_cnt,
            total_queue_length,
            avg_density,
            avg_speed,
            avg_wait,
            decision_id,
            allocated_green
        ]
        self._dataset_rows.insert(0, dataset_row)
        if len(self._dataset_rows) > 20:
            self._dataset_rows.pop()

        # Signal state representation from active phase, mode, and emergency lock
        if self._emergency_corridor_active:
            is_ns = "North" in self._emergency_corridor_direction or "South" in self._emergency_corridor_direction or "NS" in self._emergency_corridor_direction
            n_state = "GREEN" if is_ns else "RED"
            s_state = "GREEN" if is_ns else "RED"
            e_state = "RED" if is_ns else "GREEN"
            w_state = "RED" if is_ns else "GREEN"
        elif self._signal_mode == "one_by_one":
            curr_dir = ["North", "East", "South", "West"][self._one_by_one_index]
            n_state = ("YELLOW" if self._one_by_one_is_yellow else "GREEN") if curr_dir == "North" else "RED"
            s_state = ("YELLOW" if self._one_by_one_is_yellow else "GREEN") if curr_dir == "South" else "RED"
            e_state = ("YELLOW" if self._one_by_one_is_yellow else "GREEN") if curr_dir == "East" else "RED"
            w_state = ("YELLOW" if self._one_by_one_is_yellow else "GREEN") if curr_dir == "West" else "RED"
        else:
            ns_state = "GREEN" if "NS GREEN" in current_signal_phase else ("YELLOW" if "NS YELLOW" in current_signal_phase else "RED")
            we_state = "GREEN" if "WE GREEN" in current_signal_phase else ("YELLOW" if "WE YELLOW" in current_signal_phase else "RED")
            n_state = ns_state
            s_state = ns_state
            e_state = we_state
            w_state = we_state

        signals_data = [
            SignalHeadState(
                signal_id="SIG-N1",
                direction="North",
                state=n_state,
                phase_id=phase_id,
                phase_start_time=self._phase_start_time,
                phase_end_time=self._phase_end_time,
                remaining_time=remaining_time,
                simulation_time=sim_time,
                decision_id=self._current_decision_id,
                timestamp=now_str,
                timer_remaining=remaining_time,
                mode="Autonomous Adaptive" if self._adaptive_mode_enabled else "Fixed Cycle",
                adaptive_action=adaptive_action,
                adaptive_reason=adaptive_reason
            ),
            SignalHeadState(
                signal_id="SIG-S1",
                direction="South",
                state=s_state,
                phase_id=phase_id,
                phase_start_time=self._phase_start_time,
                phase_end_time=self._phase_end_time,
                remaining_time=remaining_time,
                simulation_time=sim_time,
                decision_id=self._current_decision_id,
                timestamp=now_str,
                timer_remaining=remaining_time,
                mode="Autonomous Adaptive" if self._adaptive_mode_enabled else "Fixed Cycle",
                adaptive_action=adaptive_action,
                adaptive_reason=adaptive_reason
            ),
            SignalHeadState(
                signal_id="SIG-E1",
                direction="East",
                state=e_state,
                phase_id=phase_id,
                phase_start_time=self._phase_start_time,
                phase_end_time=self._phase_end_time,
                remaining_time=remaining_time,
                simulation_time=sim_time,
                decision_id=self._current_decision_id,
                timestamp=now_str,
                timer_remaining=remaining_time,
                mode="Autonomous Adaptive" if self._adaptive_mode_enabled else "Fixed Cycle",
                adaptive_action=adaptive_action,
                adaptive_reason=adaptive_reason
            ),
            SignalHeadState(
                signal_id="SIG-W1",
                direction="West",
                state=w_state,
                phase_id=phase_id,
                phase_start_time=self._phase_start_time,
                phase_end_time=self._phase_end_time,
                remaining_time=remaining_time,
                simulation_time=sim_time,
                decision_id=self._current_decision_id,
                timestamp=now_str,
                timer_remaining=remaining_time,
                mode="Autonomous Adaptive" if self._adaptive_mode_enabled else "Fixed Cycle",
                adaptive_action=adaptive_action,
                adaptive_reason=adaptive_reason
            ),
        ]

        # Extract volume & speed series for Recharts
        volume_series = [{"time": p["time"], "volume": p["volume"]} for p in self._time_series_buffer[-20:]]
        speed_series = [{"time": p["time"], "speed": p["speed"]} for p in self._time_series_buffer[-20:]]

        trends_data = TrendData(
            timestamp=now_str,
            source=self._source,
            confidence=self._confidence,
            window="15m",
            volume_over_time=volume_series,
            speed_over_time=speed_series
        )

        hardware_data = [
            HardwareNodeState(
                node_id="ESP32-J1-N",
                role="Signal Controller North",
                status="ONLINE",
                latency_ms=12,
                firmware="v2.1",
                mqtt_status="CONNECTED",
                publish_topic="traffic/signals/SIG-N1",
                latest_payload=f'{{"event": "SIGNAL_COMMAND", "state": "{n_state}", "duration_sec": {allocated_green}}}',
                gpio_states="GPIO 18: HIGH (Green), GPIO 19: LOW (Red)" if n_state == "GREEN" else ("GPIO 18: HIGH (Yellow), GPIO 19: HIGH (Yellow)" if n_state == "YELLOW" else "GPIO 18: LOW, GPIO 19: HIGH (Red)"),
                last_ack_time="1s ago"
            ),
            HardwareNodeState(
                node_id="ESP32-J1-S",
                role="Signal Controller South",
                status="ONLINE",
                latency_ms=14,
                firmware="v2.1",
                mqtt_status="CONNECTED",
                publish_topic="traffic/signals/SIG-S1",
                latest_payload=f'{{"event": "SIGNAL_COMMAND", "state": "{s_state}", "duration_sec": {allocated_green}}}',
                gpio_states="GPIO 18: HIGH (Green), GPIO 19: LOW (Red)" if s_state == "GREEN" else ("GPIO 18: HIGH (Yellow), GPIO 19: HIGH (Yellow)" if s_state == "YELLOW" else "GPIO 18: LOW, GPIO 19: HIGH (Red)"),
                last_ack_time="1s ago"
            ),
            HardwareNodeState(
                node_id="ESP32-J1-E",
                role="Signal Controller East",
                status="ONLINE",
                latency_ms=11,
                firmware="v2.1",
                mqtt_status="CONNECTED",
                publish_topic="traffic/signals/SIG-E1",
                latest_payload=f'{{"event": "SIGNAL_COMMAND", "state": "{e_state}", "duration_sec": {allocated_green}}}',
                gpio_states="GPIO 21: HIGH (Green), GPIO 22: LOW (Red)" if e_state == "GREEN" else ("GPIO 21: HIGH (Yellow), GPIO 22: HIGH (Yellow)" if e_state == "YELLOW" else "GPIO 21: LOW, GPIO 22: HIGH (Red)"),
                last_ack_time="1s ago"
            ),
            HardwareNodeState(
                node_id="ESP32-J1-W",
                role="Signal Controller West",
                status="ONLINE",
                latency_ms=15,
                firmware="v2.1",
                mqtt_status="CONNECTED",
                publish_topic="traffic/signals/SIG-W1",
                latest_payload=f'{{"event": "SIGNAL_COMMAND", "state": "{w_state}", "duration_sec": {allocated_green}}}',
                gpio_states="GPIO 21: HIGH (Green), GPIO 22: LOW (Red)" if w_state == "GREEN" else ("GPIO 21: HIGH (Yellow), GPIO 22: HIGH (Yellow)" if w_state == "YELLOW" else "GPIO 21: LOW, GPIO 22: HIGH (Red)"),
                last_ack_time="1s ago"
            ),
        ]

        return TrafficState(
            source_name=self._source_name,
            source=self._source,
            confidence=self._confidence,
            timestamp=now_str,
            overview=overview_data,
            approaches=approaches_data,
            signals=signals_data,
            trends=trends_data,
            hardware_status=hardware_data
        )

    def get_time_series_buffer(self, window: str = "15m") -> List[Dict[str, Any]]:
        limit_map = {"15m": 20, "1h": 50, "24h": 100}
        limit = limit_map.get(window, 20)
        with self._lock:
            return list(self._time_series_buffer[-limit:])

    def get_dataset_rows(self, limit: int = 20) -> List[List[Any]]:
        with self._lock:
            return list(self._dataset_rows[:limit])

    def _create_default_state(self) -> TrafficState:
        now_str = datetime.now().isoformat()
        return TrafficState(
            source_name=self._source_name,
            source=self._source,
            confidence=self._confidence,
            timestamp=now_str,
            overview=OverviewState(
                timestamp=now_str,
                source=self._source,
                confidence=self._confidence,
                total_vehicle_count=0,
                avg_speed_kmh=0.0,
                total_queue_length_m=0.0,
                avg_density_veh_km=0.0,
                throughput_vph=0,
                level_of_service="A",
                active_signals=4,
                ai_control_mode="Autonomous Adaptive" if getattr(self, "_adaptive_mode_enabled", True) else "Fixed Cycle",
                emergency_vehicle_count=0,
                current_congestion="Optimal",
                current_signal_phase="NS GREEN",
                signal_mode=getattr(self, "_signal_mode", "paired_corridor"),
                active_scenario=self._active_scenario,
                scenario_impact=self._scenario_impact,
                adaptive_status=getattr(self, "_glide_status", "DYNAMIC_GLIDE_OPTIMIZED"),
                adaptive_event="Nominal timing cycle"
            ),
            approaches=[
                ApproachState(approach="North (N-Bound)", vehicle_count=0, avg_speed=0.0, queue_len=0.0, density=0.0, status="Optimal"),
                ApproachState(approach="South (S-Bound)", vehicle_count=0, avg_speed=0.0, queue_len=0.0, density=0.0, status="Optimal"),
                ApproachState(approach="East (E-Bound)", vehicle_count=0, avg_speed=0.0, queue_len=0.0, density=0.0, status="Optimal"),
                ApproachState(approach="West (W-Bound)", vehicle_count=0, avg_speed=0.0, queue_len=0.0, density=0.0, status="Optimal"),
            ],
            signals=[
                SignalHeadState(signal_id="SIG-N1", direction="North", state="GREEN", timer_remaining=15, mode="Autonomous Adaptive" if getattr(self, "_adaptive_mode_enabled", True) else "Fixed Cycle", adaptive_action="NOMINAL", adaptive_reason="Nominal baseline timing"),
                SignalHeadState(signal_id="SIG-S1", direction="South", state="GREEN", timer_remaining=15, mode="Autonomous Adaptive" if getattr(self, "_adaptive_mode_enabled", True) else "Fixed Cycle", adaptive_action="NOMINAL", adaptive_reason="Nominal baseline timing"),
                SignalHeadState(signal_id="SIG-E1", direction="East", state="RED", timer_remaining=15, mode="Autonomous Adaptive" if getattr(self, "_adaptive_mode_enabled", True) else "Fixed Cycle", adaptive_action="NOMINAL", adaptive_reason="Nominal baseline timing"),
                SignalHeadState(signal_id="SIG-W1", direction="West", state="RED", timer_remaining=15, mode="Autonomous Adaptive" if getattr(self, "_adaptive_mode_enabled", True) else "Fixed Cycle", adaptive_action="NOMINAL", adaptive_reason="Nominal baseline timing"),
            ],
            trends=TrendData(timestamp=now_str, source=self._source, confidence=self._confidence, window="15m", volume_over_time=[], speed_over_time=[]),
            hardware_status=[
                HardwareNodeState(node_id="ESP32-J1-N", role="Signal Controller North", status="ONLINE", latency_ms=12, firmware="v2.1", mqtt_status="CONNECTED", publish_topic="traffic/signals/SIG-N1", latest_payload='{"event": "SIGNAL_COMMAND", "state": "GREEN", "duration_sec": 45}', gpio_states="GPIO 18: HIGH, GPIO 19: LOW", last_ack_time="1s ago"),
                HardwareNodeState(node_id="ESP32-J1-S", role="Signal Controller South", status="ONLINE", latency_ms=14, firmware="v2.1", mqtt_status="CONNECTED", publish_topic="traffic/signals/SIG-S1", latest_payload='{"event": "SIGNAL_COMMAND", "state": "GREEN", "duration_sec": 45}', gpio_states="GPIO 18: HIGH, GPIO 19: LOW", last_ack_time="1s ago"),
                HardwareNodeState(node_id="ESP32-J1-E", role="Signal Controller East", status="ONLINE", latency_ms=11, firmware="v2.1", mqtt_status="CONNECTED", publish_topic="traffic/signals/SIG-E1", latest_payload='{"event": "SIGNAL_COMMAND", "state": "RED", "duration_sec": 20}', gpio_states="GPIO 21: LOW, GPIO 22: HIGH", last_ack_time="1s ago"),
                HardwareNodeState(node_id="ESP32-J1-W", role="Signal Controller West", status="ONLINE", latency_ms=15, firmware="v2.1", mqtt_status="CONNECTED", publish_topic="traffic/signals/SIG-W1", latest_payload='{"event": "SIGNAL_COMMAND", "state": "RED", "duration_sec": 20}', gpio_states="GPIO 21: LOW, GPIO 22: HIGH", last_ack_time="1s ago"),
            ]
        )

    async def get_current_state(self) -> TrafficState:
        with self._lock:
            if self._is_running and self._latest_state is not None:
                if self._latest_state.overview:
                    self._latest_state.overview.ai_control_mode = "EMERGENCY_GREEN_CORRIDOR" if self._emergency_corridor_active else ("Autonomous Adaptive" if self._adaptive_mode_enabled else "Fixed Cycle")
                if self._latest_state.signals:
                    for sig in self._latest_state.signals:
                        sig.mode = "Autonomous Adaptive" if self._adaptive_mode_enabled else "Fixed Cycle"
                return self._latest_state
            return self._extract_telemetry_state()
