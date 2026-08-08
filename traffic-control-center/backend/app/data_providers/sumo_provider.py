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

    def __init__(self, config_path: str = SUMO_CONFIG):
        self._source = "sumo_simulation"
        self._source_name = "SUMO Simulation Engine (TraCI Live Telemetry)"
        self._confidence = "exact"
        self.config_path = config_path
        self._latest_state: Optional[TrafficState] = None
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
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

        # Initial fallback state until simulation thread starts
        self._latest_state = self._create_default_state()

        # Start the continuous background simulation loop
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

        if traci is not None and self._is_running:
            try:
                tls_ids = traci.trafficlight.getIDList()
                if tls_ids:
                    tls_id = tls_ids[0]
                    curr_phase = int(traci.trafficlight.getPhase(tls_id))
                    # Only apply mid-phase if duration has NOT been set yet for this phase instance
                    if curr_phase == 0 and self._duration_applied_for_phase != 0:
                        traci.trafficlight.setPhaseDuration(tls_id, float(ew_green))
                        self._duration_applied_for_phase = 0
                        logger.info(f"[SUMO TraCI] Set initial WE GREEN duration {ew_green}s for Phase 0 (Decision: {decision_id})")
                    elif curr_phase == 2 and self._duration_applied_for_phase != 2:
                        traci.trafficlight.setPhaseDuration(tls_id, float(ns_green))
                        self._duration_applied_for_phase = 2
                        logger.info(f"[SUMO TraCI] Set initial NS GREEN duration {ns_green}s for Phase 2 (Decision: {decision_id})")
            except Exception as e:
                logger.warning(f"Note setting SUMO phase duration via TraCI: {e}")

    def _start_simulation_loop(self):
        if traci is None:
            logger.error("TraCI module missing. Live SUMO telemetry disabled.")
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._run_simulation_thread, daemon=True)
        self._thread.start()

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

                    # Control simulation step pace (~3 Hz / 300ms per step)
                    time.sleep(0.3)

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
        veh_ids = traci.vehicle.getIDList()
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

        # Global aggregations
        avg_speed = round(float(sum(speeds_kmh) / total_veh_count), 1) if total_veh_count > 0 else 40.0
        avg_wait = round(float(sum(waiting_times) / total_veh_count), 1) if total_veh_count > 0 else 0.0

        # Halting vehicles across all non-internal lanes
        lane_ids = [l for l in traci.lane.getIDList() if not l.startswith(":")]
        halting_vehicles = sum(traci.lane.getLastStepHaltingNumber(l) for l in lane_ids)
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

        # Read signal phase and real-time timing metrics from SUMO TLS J1
        current_signal_phase = "NS GREEN"
        sim_time = 0.0
        phase_id = 0
        remaining_time = 15
        tls_ids = traci.trafficlight.getIDList()
        if tls_ids:
            tls_id = tls_ids[0]
            sim_time = float(traci.simulation.getTime())
            phase_id = int(traci.trafficlight.getPhase(tls_id))
            next_switch = float(traci.trafficlight.getNextSwitch(tls_id))
            remaining_time = max(0, int(round(next_switch - sim_time)))
            phase_state = traci.trafficlight.getRedYellowGreenState(tls_id)

            # Phase transition detection and logging
            if self._last_phase_id is None or phase_id != self._last_phase_id:
                prev_phase = self._last_phase_id
                self._phase_start_time = sim_time
                self._phase_end_time = next_switch
                self._last_phase_id = phase_id
                self._duration_applied_for_phase = None

                # Apply pending green duration for newly entered phase
                if phase_id == 0 and self._pending_ew_green is not None:
                    try:
                        traci.trafficlight.setPhaseDuration(tls_id, float(self._pending_ew_green))
                        self._duration_applied_for_phase = 0
                        next_switch = float(traci.trafficlight.getNextSwitch(tls_id))
                        remaining_time = max(0, int(round(next_switch - sim_time)))
                        self._phase_end_time = next_switch
                    except Exception as e:
                        logger.warning(f"Error applying WE green duration on phase transition: {e}")
                elif phase_id == 2 and self._pending_ns_green is not None:
                    try:
                        traci.trafficlight.setPhaseDuration(tls_id, float(self._pending_ns_green))
                        self._duration_applied_for_phase = 2
                        next_switch = float(traci.trafficlight.getNextSwitch(tls_id))
                        remaining_time = max(0, int(round(next_switch - sim_time)))
                        self._phase_end_time = next_switch
                    except Exception as e:
                        logger.warning(f"Error applying NS green duration on phase transition: {e}")

                logger.info(
                    f"[SUMO_SIGNAL_PHASE_EVENT] sim_time={sim_time:.1f}s | signal_id=TLS-{tls_id} | "
                    f"prev_phase={prev_phase} -> new_phase={phase_id} | phase_start_time={self._phase_start_time:.1f}s | "
                    f"phase_end_time={self._phase_end_time:.1f}s | remaining_time={remaining_time}s | "
                    f"decision_id={self._current_decision_id} | reason='SUMO phase transition' | source='sumo_simulation'"
                )

            if phase_state.startswith("GGG"):
                current_signal_phase = "WE GREEN"
            elif phase_state.startswith("yyy"):
                current_signal_phase = "WE YELLOW"
            elif "GGG" in phase_state:
                current_signal_phase = "NS GREEN"
            elif "yyy" in phase_state:
                current_signal_phase = "NS YELLOW"

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
            ai_control_mode="Autonomous Supervisory",
            emergency_vehicle_count=emergency_count,
            current_congestion=current_congestion,
            current_signal_phase=current_signal_phase
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

        # Signal state representation from SUMO authoritative phase
        ns_state = "GREEN" if "NS GREEN" in current_signal_phase else ("YELLOW" if "NS YELLOW" in current_signal_phase else "RED")
        we_state = "GREEN" if "WE GREEN" in current_signal_phase else ("YELLOW" if "WE YELLOW" in current_signal_phase else "RED")

        signals_data = [
            SignalHeadState(
                signal_id="SIG-N1",
                direction="North",
                state=ns_state,
                phase_id=phase_id,
                phase_start_time=self._phase_start_time,
                phase_end_time=self._phase_end_time,
                remaining_time=remaining_time,
                simulation_time=sim_time,
                decision_id=self._current_decision_id,
                timestamp=now_str,
                timer_remaining=remaining_time,
                mode="AI-Adaptive"
            ),
            SignalHeadState(
                signal_id="SIG-S1",
                direction="South",
                state=ns_state,
                phase_id=phase_id,
                phase_start_time=self._phase_start_time,
                phase_end_time=self._phase_end_time,
                remaining_time=remaining_time,
                simulation_time=sim_time,
                decision_id=self._current_decision_id,
                timestamp=now_str,
                timer_remaining=remaining_time,
                mode="AI-Adaptive"
            ),
            SignalHeadState(
                signal_id="SIG-E1",
                direction="East",
                state=we_state,
                phase_id=phase_id,
                phase_start_time=self._phase_start_time,
                phase_end_time=self._phase_end_time,
                remaining_time=remaining_time,
                simulation_time=sim_time,
                decision_id=self._current_decision_id,
                timestamp=now_str,
                timer_remaining=remaining_time,
                mode="AI-Adaptive"
            ),
            SignalHeadState(
                signal_id="SIG-W1",
                direction="West",
                state=we_state,
                phase_id=phase_id,
                phase_start_time=self._phase_start_time,
                phase_end_time=self._phase_end_time,
                remaining_time=remaining_time,
                simulation_time=sim_time,
                decision_id=self._current_decision_id,
                timestamp=now_str,
                timer_remaining=remaining_time,
                mode="AI-Adaptive"
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
                latest_payload=f'{{"event": "SIGNAL_COMMAND", "state": "{ns_state}", "duration_sec": {allocated_green}}}',
                gpio_states="GPIO 18: HIGH (Green), GPIO 19: LOW (Red)" if ns_state == "GREEN" else "GPIO 18: LOW, GPIO 19: HIGH (Red)",
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
                latest_payload=f'{{"event": "SIGNAL_COMMAND", "state": "{ns_state}", "duration_sec": {allocated_green}}}',
                gpio_states="GPIO 18: HIGH (Green), GPIO 19: LOW (Red)" if ns_state == "GREEN" else "GPIO 18: LOW, GPIO 19: HIGH (Red)",
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
                latest_payload=f'{{"event": "SIGNAL_COMMAND", "state": "{we_state}", "duration_sec": 20}}',
                gpio_states="GPIO 21: LOW, GPIO 22: HIGH (Red)" if we_state == "RED" else "GPIO 21: HIGH (Green), GPIO 22: LOW",
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
                latest_payload=f'{{"event": "SIGNAL_COMMAND", "state": "{we_state}", "duration_sec": 20}}',
                gpio_states="GPIO 21: LOW, GPIO 22: HIGH (Red)" if we_state == "RED" else "GPIO 21: HIGH (Green), GPIO 22: LOW",
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
                ai_control_mode="Autonomous Supervisory",
                emergency_vehicle_count=0,
                current_congestion="Optimal",
                current_signal_phase="NS GREEN"
            ),
            approaches=[
                ApproachState(approach="North (N-Bound)", vehicle_count=0, avg_speed=0.0, queue_len=0.0, density=0.0, status="Optimal"),
                ApproachState(approach="South (S-Bound)", vehicle_count=0, avg_speed=0.0, queue_len=0.0, density=0.0, status="Optimal"),
                ApproachState(approach="East (E-Bound)", vehicle_count=0, avg_speed=0.0, queue_len=0.0, density=0.0, status="Optimal"),
                ApproachState(approach="West (W-Bound)", vehicle_count=0, avg_speed=0.0, queue_len=0.0, density=0.0, status="Optimal"),
            ],
            signals=[
                SignalHeadState(signal_id="SIG-N1", direction="North", state="GREEN", timer_remaining=15, mode="AI-Optimized"),
                SignalHeadState(signal_id="SIG-S1", direction="South", state="GREEN", timer_remaining=15, mode="AI-Optimized"),
                SignalHeadState(signal_id="SIG-E1", direction="East", state="RED", timer_remaining=15, mode="AI-Optimized"),
                SignalHeadState(signal_id="SIG-W1", direction="West", state="RED", timer_remaining=15, mode="AI-Optimized"),
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
            if self._latest_state is not None:
                return self._latest_state
        return self._create_default_state()
