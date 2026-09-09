"""
Authoritative Python Signal Controller.
CRITICAL ARCHITECTURAL RULE:
This module is the SOLE software component authorized to command physical signal changes
and publish to MQTT.

Supports two operational modes:
  - Mock/Simulation Mode (mock_actuation=True): Records transitions in-memory for testing.
  - Live Hardware Mode (mock_actuation=False): Connects to Mosquitto and actuates ESP32.
"""

import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.traffic_data import SignalPhase
from app.models.safety_data import PhaseTransitionStep

logger = logging.getLogger(__name__)


class SignalController:
    """
    Authoritative physical actuation layer.
    Executes approved transition sequences from the Safety Agent.
    """

    def __init__(
        self,
        mqtt_broker_host: str = "127.0.0.1",
        mqtt_port: int = 1883,
        mqtt_topic: str = "traffic/signal",
        ack_topic: str = "traffic/esp32/ack",
        mock_actuation: bool = True,
        initial_phase: SignalPhase = SignalPhase.NS_GREEN,
    ):
        self.broker_host = mqtt_broker_host
        self.broker_port = mqtt_port
        self.topic_signal = mqtt_topic
        self.topic_ack = ack_topic
        self.mock_actuation = mock_actuation
        self.current_phase = initial_phase

        # Execution Audit Records
        self.actuation_history: List[Dict[str, Any]] = []
        self.received_acks: List[Dict[str, Any]] = []

        # Live MQTT Client (only initialized if mock_actuation is False)
        self._mqtt_client = None
        self._is_connected = False

        if not self.mock_actuation:
            self._init_live_mqtt()

    def _init_live_mqtt(self):
        """Initializes connection to the Mosquitto MQTT broker for live hardware actuation."""
        try:
            import paho.mqtt.client as mqtt

            # Use modern callback API
            try:
                self._mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="PythonSignalController")
            except AttributeError:
                self._mqtt_client = mqtt.Client(client_id="PythonSignalController")

            self._mqtt_client.on_connect = self._on_connect
            self._mqtt_client.on_message = self._on_message

            logger.info(f"[SIGNAL CONTROLLER] Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            self._mqtt_client.connect(self.broker_host, self.broker_port, keepalive=60)
            self._mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"[SIGNAL CONTROLLER] Failed to connect to MQTT broker: {e}")
            self._is_connected = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        try:
            rc_int = int(rc) if hasattr(rc, "value") else int(rc)
        except Exception:
            rc_int = 0
        if rc_int == 0:
            self._is_connected = True
            logger.info(f"[SIGNAL CONTROLLER] Connected to MQTT broker. Subscribing to {self.topic_ack}...")
            client.subscribe([(self.topic_ack, 0), ("traffic/system/heartbeat", 0)])
        else:
            self._is_connected = False
            logger.error(f"[SIGNAL CONTROLLER] MQTT connection rejected with code: {rc}")

    def _on_message(self, client, userdata, msg):
        payload_str = msg.payload.decode("utf-8", errors="ignore")
        ack_entry = {
            "timestamp": datetime.now().isoformat(),
            "topic": msg.topic,
            "payload": payload_str,
        }
        self.received_acks.append(ack_entry)
        if msg.topic == self.topic_ack:
            print(f"  [ESP32] ACK: {payload_str}")
        logger.info(f"[SIGNAL CONTROLLER] Received message on {msg.topic}: {payload_str}")

    # ========================================================================
    # Core Authoritative Actuation
    # ========================================================================

    def execute_phase_command(self, target_phase: SignalPhase, duration_s: float = 0.0, purpose: str = "") -> bool:
        """
        Commands a single physical phase change.
        Publishes command to MQTT topic 'traffic/signal' and updates current_phase.
        """
        phase_str = target_phase.value
        timestamp_now = datetime.now()

        record = {
            "timestamp": timestamp_now.isoformat(),
            "phase": phase_str,
            "duration_s": duration_s,
            "purpose": purpose,
            "mode": "MOCK" if self.mock_actuation else "LIVE",
            "executed": True,
        }
        self.actuation_history.append(record)
        self.current_phase = target_phase

        if self.mock_actuation:
            logger.info(f"[SIGNAL CONTROLLER - MOCK] Actuated {phase_str} (duration: {duration_s}s, purpose: {purpose})")
            return True
        else:
            if not self._mqtt_client or not self._is_connected:
                print(f"  [SIGNAL CONTROLLER ERROR] Cannot publish {phase_str}: MQTT broker not connected!")
                logger.error(f"[SIGNAL CONTROLLER] Cannot publish {phase_str}: MQTT not connected!")
                record["executed"] = False
                return False

            print(f"  [MQTT] Published: {phase_str} (role: {purpose}, duration: {duration_s}s)")
            logger.info(f"[SIGNAL CONTROLLER - LIVE] Publishing '{phase_str}' to topic '{self.topic_signal}'...")
            res = self._mqtt_client.publish(self.topic_signal, phase_str, qos=1)
            res.wait_for_publish(timeout=2.0)

            # In live hardware, sleep for the clearance duration if duration > 0
            if duration_s > 0 and purpose in ("YELLOW_CLEARANCE", "ALL_RED_CLEARANCE"):
                time.sleep(duration_s)

            return True

    def execute_sequence(self, sequence: List[PhaseTransitionStep]) -> bool:
        """
        Executes an ordered physical clearance sequence produced by the Safety Agent.
        Example: [NS_YELLOW (3s) -> ALL_RED (2s) -> EW_GREEN (30s)]
        """
        if not sequence:
            return False

        all_succeeded = True
        for step in sequence:
            success = self.execute_phase_command(
                target_phase=step.phase,
                duration_s=step.duration_s,
                purpose=step.purpose,
            )
            if not success:
                all_succeeded = False
                break
        return all_succeeded

    def extend_current_phase(self, extension_seconds: float) -> bool:
        """Extends current green duration without interrupting with a yellow/all-red sequence."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "phase": self.current_phase.value,
            "duration_s": extension_seconds,
            "purpose": "GREEN_EXTENSION",
            "mode": "MOCK" if self.mock_actuation else "LIVE",
            "executed": True,
        }
        self.actuation_history.append(record)
        logger.info(f"[SIGNAL CONTROLLER] Extended {self.current_phase.value} by +{extension_seconds}s.")
        return True

    def emergency_all_red(self) -> bool:
        """Emergency trip to ALL_RED clearance."""
        logger.warning("[SIGNAL CONTROLLER] EMERGENCY TRIP TO ALL_RED!")
        return self.execute_phase_command(SignalPhase.ALL_RED, duration_s=3.0, purpose="EMERGENCY_CLEARANCE")

    def disconnect(self):
        """Cleanly disconnects the live MQTT client if active."""
        if self._mqtt_client:
            try:
                self._mqtt_client.loop_stop()
                self._mqtt_client.disconnect()
            except Exception:
                pass
