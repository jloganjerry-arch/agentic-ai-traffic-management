"""
Live Hardware Pipeline Runner (Phase 9).
Runs the complete 5-agent multi-agent architecture connected live to the
Authoritative Python Signal Controller, Mosquitto MQTT broker, and physical ESP32.

Command:
  python -m app.core.run_live_pipeline --duration 60
"""

import time
import argparse
import sys
from datetime import datetime

from app.models.traffic_data import Direction, SignalPhase
from app.models.optimization_data import OptimizationAction
from app.models.supervisor_data import SupervisorDecisionStatus
from app.models.safety_data import SafetyStatus
from app.agents.controlled_traffic_source import ControlledTrafficSource
from app.core.signal_controller import SignalController
from app.core.agent_pipeline import IntelligentTrafficPipeline


def run_live_pipeline(duration_seconds: int = 60, broker_host: str = "127.0.0.1", broker_port: int = 1883):
    print("=" * 70)
    print(" [TRAFFIC] STARTING LIVE END-TO-END INTELLIGENT TRAFFIC PIPELINE")
    print(f" Target Duration: {duration_seconds}s | Broker: {broker_host}:{broker_port}")
    print(" Full Multi-Agent Chain:")
    print(" Monitoring -> Analysis -> Optimization -> Supervisor -> Safety -> Controller -> MQTT -> ESP32")
    print("=" * 70)

    # 1. Initialize Authoritative Signal Controller in LIVE mode
    controller = SignalController(
        mqtt_broker_host=broker_host,
        mqtt_port=broker_port,
        mqtt_topic="traffic/signal",
        ack_topic="traffic/esp32/ack",
        mock_actuation=False,
        initial_phase=SignalPhase.NS_GREEN,
    )

    time.sleep(1.0)

    # 2. Initialize Intelligent Pipeline
    pipeline = IntelligentTrafficPipeline(
        signal_controller=controller,
        mock_actuation=False,
        initial_phase=SignalPhase.NS_GREEN,
    )

    start_time = time.time()
    step_count = 0

    try:
        while time.time() - start_time < duration_seconds:
            step_count += 1
            elapsed_total = round(time.time() - start_time, 1)
            print(f"\n{'='*70}")
            print(f"--- [STEP {step_count}] | Pipeline Elapsed: {elapsed_total}s / {duration_seconds}s | Active Phase: {pipeline.active_phase.value} ---")
            print(f"{'='*70}")

            # Cycle varied realistic traffic scenarios across the 60s run
            cycle_idx = (step_count - 1) % 6
            if cycle_idx == 0:
                # Step 1: Platoon approaches on North -> triggers EXTEND_GREEN (+5s)
                raw_telemetry = ControlledTrafficSource.generate_high_speed_approaching_scenario()
                raw_telemetry["current_signal_phase"] = pipeline.active_phase.value
                raw_telemetry["remaining_green_time"] = 3.0
                raw_telemetry["junction_occupancy"] = 0.05
                scenario_label = "Scenario 1: Approaching Platoon on Active Corridor (Extension Demand)"

            elif cycle_idx == 1:
                # Step 2: Clear corridor with low remaining green, high East queue -> triggers SAFE SWITCH to EW_GREEN
                raw_telemetry = ControlledTrafficSource.generate_congested_north_queue()
                raw_telemetry["current_signal_phase"] = pipeline.active_phase.value
                raw_telemetry["remaining_green_time"] = 2.0
                raw_telemetry["junction_occupancy"] = 0.05  # Box is clear!
                # Clear North vehicles so dilemma zone doesn't block switch
                raw_telemetry["raw_corridor_data"]["NORTH"]["detected_vehicles"] = []
                raw_telemetry["raw_corridor_data"]["EAST"]["queue_length_m"] = 40.0
                scenario_label = "Scenario 2: Clear Active Corridor + Heavy East Queue (Safe Phase Switch Demand)"

            elif cycle_idx == 2:
                # Step 3: Now on EW_GREEN: Nominal balanced flow
                raw_telemetry = ControlledTrafficSource.generate_balanced_traffic()
                raw_telemetry["current_signal_phase"] = pipeline.active_phase.value
                raw_telemetry["remaining_green_time"] = 20.0
                raw_telemetry["junction_occupancy"] = 0.05
                scenario_label = "Scenario 3: Balanced Flow on EW_GREEN (Nominal Maintain)"

            elif cycle_idx == 3:
                # Step 4: High junction occupancy (0.28 > 0.15) during switch request -> Safety Agent HOLDS
                raw_telemetry = ControlledTrafficSource.generate_congested_north_queue()
                raw_telemetry["current_signal_phase"] = pipeline.active_phase.value
                raw_telemetry["remaining_green_time"] = 2.0
                raw_telemetry["junction_occupancy"] = 0.28  # Box occupied!
                scenario_label = "Scenario 4: High Box Occupancy (Safety Agent Conflict Hold)"

            elif cycle_idx == 4:
                # Step 5: Box cleared, high North queue -> triggers SAFE SWITCH back to NS_GREEN
                raw_telemetry = ControlledTrafficSource.generate_congested_north_queue()
                raw_telemetry["current_signal_phase"] = pipeline.active_phase.value
                raw_telemetry["remaining_green_time"] = 2.0
                raw_telemetry["junction_occupancy"] = 0.05
                raw_telemetry["raw_corridor_data"]["EAST"]["detected_vehicles"] = []  # Clear dilemma
                scenario_label = "Scenario 5: Clear Box + High North Queue (Safe Switch back to NS_GREEN)"

            else:
                # Step 6: Nominal hold
                raw_telemetry = ControlledTrafficSource.generate_balanced_traffic()
                raw_telemetry["current_signal_phase"] = pipeline.active_phase.value
                raw_telemetry["remaining_green_time"] = 15.0
                raw_telemetry["junction_occupancy"] = 0.05
                scenario_label = "Scenario 6: Nominal Balanced Operation"

            print(f"[ENVIRONMENT] Ingesting: {scenario_label}")

            # Execute unified pipeline step
            result = pipeline.step(raw_telemetry)

            # Display real-time explainable agent logs
            m = result.monitoring
            print("\n[MONITORING]")
            print(f"  Total Vehicles: {m.total_vehicle_count} | Total Queue: {m.total_queue_length}m")
            for d_enum, d_data in m.directions.items():
                print(f"  {d_enum.value:5s}: Count={d_data.vehicle_count} | Queue={d_data.queue_length:.1f}m | Approaching={d_data.approaching_count}")

            a = result.analysis
            print("\n[ANALYSIS]")
            print(f"  JCI Score: {a.jci.score:.2f} ({a.jci.category.value}) | Critical Corridor: {a.critical_direction.value}")
            if a.platoons_detected:
                print(f"  PLATOON DETECTED on: {[d.value for d in a.platoons_detected]}")
            else:
                print("  Platoons: None active")

            opt = result.optimization
            print("\n[OPTIMIZATION]")
            print(f"  Recommendation: {opt.action.value} -> Target: {opt.target_phase.value}")
            print(f"  Rationale: {opt.rationale.reasoning}")

            sup = result.supervisor
            print("\n[SUPERVISOR]")
            print(f"  Status: {sup.status.value}")
            print(f"  Policy Rationale: {sup.policy_rationale}")
            for check in sup.policy_checks:
                status_icon = "PASS" if check.passed else "FAIL"
                print(f"    - {check.rule_name:22s} [{status_icon}]: Obs={check.observed_value:.1f}, Limit={check.limit_value:.1f}")

            safe = result.safety
            print("\n[SAFETY]")
            print(f"  Status: {safe.status.value} (is_safe={safe.is_safe})")
            print(f"  Safety Rationale: {safe.safety_rationale}")
            for check in safe.safety_checks:
                status_icon = "PASS" if check.passed else "FAIL"
                print(f"    - {check.check_name:30s} [{status_icon}]: {check.detail}")

            print("\n[SIGNAL CONTROLLER & PHYSICAL ACTUATION]")
            if result.actuation_dispatched:
                print(f"  Action Summary: {result.final_action_summary}")
                for step in result.dispatched_sequence:
                    print(f"  --> [MQTT PUBLISHED] '{step.phase.value}' (Duration: {step.duration_s}s, Role: {step.purpose})")
            else:
                print(f"  Holding State: {result.final_action_summary} (No transition commanded)")

            # Check recent ESP32 ACKs
            if controller.received_acks:
                last_ack = controller.received_acks[-1]
                print(f"  [ESP32 ACK] {last_ack['timestamp']} -> {last_ack['payload']}")

            # Pause between pipeline cycles (3.0s per step)
            time.sleep(3.0)

    except KeyboardInterrupt:
        print("\n[LIVE PIPELINE] User interrupted execution.")
    finally:
        print("\n" + "=" * 70)
        print(" [TRAFFIC] LIVE PIPELINE COMPLETE")
        print(f" Total Steps Executed: {step_count}")
        print(f" Total Actuations Dispatched: {len(controller.actuation_history)}")
        print(f" Total ESP32 ACKs Received: {len(controller.received_acks)}")
        print(" Leaving physical junction in clean ALL_RED safe state...")
        controller.emergency_all_red()
        time.sleep(1.5)
        controller.disconnect()
        print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live Hardware Intelligent Traffic Pipeline")
    parser.add_argument("--duration", type=int, default=60, help="Pipeline run duration in seconds")
    parser.add_argument("--broker", type=str, default="127.0.0.1", help="Mosquitto broker IP/host")
    parser.add_argument("--port", type=int, default=1883, help="Mosquitto broker port")
    args = parser.parse_args()

    run_live_pipeline(duration_seconds=args.duration, broker_host=args.broker, broker_port=args.port)
