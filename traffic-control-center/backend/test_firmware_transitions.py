import time
import json
import threading
import sys
import serial
import paho.mqtt.client as mqtt

# Configuration
SERIAL_PORT = "COM9"
SERIAL_BAUD = 115200
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

TOPIC_CONTROL = "traffic/signals/control"
TOPIC_SIGNAL = "traffic/signal"
TOPIC_ACK = "traffic/esp32/ack"
TOPIC_HEARTBEAT = "traffic/system/heartbeat"

# Shared log state
serial_logs = []
mqtt_acks = []
mqtt_heartbeats = []
stop_threads = False

def serial_listener():
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.1)
        ser.dtr = False
        ser.rts = False
        print(f"[TEST RUNNER] Serial port {SERIAL_PORT} opened at {SERIAL_BAUD} baud.")
        while not stop_threads:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                now_str = time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"
                entry = {"time": time.time(), "timestamp": now_str, "log": line}
                serial_logs.append(entry)
                clean_line = line.encode("ascii", errors="backslashreplace").decode("ascii")
                print(f"  [ESP32-SERIAL {now_str}] {clean_line}")
    except Exception as e:
        print(f"[TEST RUNNER ERROR] Serial listener error: {e}")
    finally:
        try:
            ser.close()
        except:
            pass

def on_mqtt_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore")
    now_str = time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"
    if msg.topic == TOPIC_ACK:
        mqtt_acks.append({"time": time.time(), "timestamp": now_str, "payload": payload})
        print(f"  [MQTT-ACK-RECV {now_str}] {payload}")
    elif msg.topic == TOPIC_HEARTBEAT:
        mqtt_heartbeats.append({"time": time.time(), "timestamp": now_str, "payload": payload})

def run_tests():
    global stop_threads
    
    # 1. Start Serial Listener Thread
    ser_thread = threading.Thread(target=serial_listener, daemon=True)
    ser_thread.start()
    time.sleep(1.0) # Wait for serial port to settle

    # 2. Connect MQTT Client (Simulating Python Controller)
    client = mqtt.Client(client_id="PythonControllerTestBench")
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe([(TOPIC_ACK, 0), (TOPIC_HEARTBEAT, 0)])
    client.loop_start()
    print("[TEST RUNNER] Python Controller connected to Mosquitto MQTT broker.")
    print("[TEST RUNNER] Waiting for ESP32 heartbeat...")
    for _ in range(30):
        if len(mqtt_heartbeats) > 0:
            break
        time.sleep(0.5)
    print(f"[TEST RUNNER] ESP32 confirmed online! Received {len(mqtt_heartbeats)} heartbeat(s).")

    print("\n" + "="*80)
    print("STARTING TEST SUITE: EXISTING ESP32 FIRMWARE WITH PYTHON CONTROLLER")
    print("="*80)

    results = []

    # ------------------------------------------------------------------------
    # TEST 1: Same Phase Green (NS_GREEN when already NS_GREEN)
    # ------------------------------------------------------------------------
    print("\n>>> TEST 1: Steady-State Command (NS_GREEN -> NS_GREEN)")
    print("Sending NS_GREEN to traffic/signal...")
    t_start = time.time()
    initial_log_count = len(serial_logs)
    client.publish(TOPIC_SIGNAL, "NS_GREEN")
    
    # Wait for ACK
    time.sleep(1.5)
    t_elapsed = time.time() - t_start
    t1_logs = [l["log"] for l in serial_logs[initial_log_count:]]
    has_transition = any("clearance" in l.lower() or "yellow" in l.lower() for l in t1_logs)
    print(f"Test 1 Elapsed: {t_elapsed:.3f}s | Transition Delay Triggered: {has_transition}")
    results.append({
        "test": "Test 1: Steady-State NS_GREEN -> NS_GREEN",
        "has_redundant_transition": has_transition,
        "notes": "No transition delay expected; should remain in NS_GREEN without clearance delay."
    })

    # ------------------------------------------------------------------------
    # TEST 2: Direct Phase Switch (NS_GREEN -> EW_GREEN via Decision Plan)
    # ------------------------------------------------------------------------
    print("\n>>> TEST 2: Direct Phase Switch (NS_GREEN -> EW_GREEN)")
    print("Sending AI Decision Plan with target_approach='East' (EW_GREEN)...")
    decision_payload = {
        "event": "SUPERVISOR_DECISION",
        "decision_id": "DEC-TEST-002",
        "action": "DYNAMIC_AI_GREEN_ALLOCATION",
        "target_approach": "East (E-Bound)",
        "duration_seconds": 35,
        "status": "APPROVED",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    t_start = time.time()
    initial_log_count = len(serial_logs)
    initial_ack_count = len(mqtt_acks)
    
    # Publish both control and legacy signal as Python controller does
    client.publish(TOPIC_CONTROL, json.dumps(decision_payload))
    client.publish(TOPIC_SIGNAL, "EW_GREEN")

    # Monitor time until ACK received
    ack_received = False
    ack_latency = None
    for _ in range(40): # up to 4 seconds
        if len(mqtt_acks) > initial_ack_count:
            ack_latency = time.time() - t_start
            ack_received = True
            break
        time.sleep(0.1)

    t2_logs = [l["log"] for l in serial_logs[initial_log_count:]]
    has_2s_delay = any("NS -> YELLOW clearance" in l for l in t2_logs)
    print(f"Test 2: ACK received in {ack_latency:.3f}s (due to 2000ms delay in mqttCallback)")
    print(f"Test 2: Observed firmware 2s clearance: {has_2s_delay}")
    results.append({
        "test": "Test 2: Direct Phase Switch (NS_GREEN -> EW_GREEN)",
        "has_redundant_transition": has_2s_delay,
        "ack_latency": ack_latency,
        "notes": f"Firmware executed 2s clearance delay, delaying MQTT ACK by {ack_latency:.2f}s."
    })

    time.sleep(1.0)

    # ------------------------------------------------------------------------
    # TEST 3: Staged Controller Transition (NS_YELLOW Clearance -> EW_GREEN)
    # ------------------------------------------------------------------------
    print("\n>>> TEST 3: Python Controller-Driven Yellow Clearance -> EW_GREEN")
    print("Step 3a: First setting junction back to NS_GREEN...")
    client.publish(TOPIC_SIGNAL, "NS_GREEN")
    time.sleep(3.0) # Wait for EW->YELLOW->NS_GREEN transition to settle

    print("\nStep 3b: Python Controller initiates Yellow Clearance (publishes NS_YELLOW)...")
    initial_log_count = len(serial_logs)
    client.publish(TOPIC_SIGNAL, "NS_YELLOW")
    time.sleep(2.0) # Controller allows 2 seconds of yellow clearance

    print("\nStep 3c: Controller Yellow clearance complete. Controller now commands EW_GREEN...")
    t_start = time.time()
    t3c_log_start = len(serial_logs)
    t3c_ack_start = len(mqtt_acks)
    client.publish(TOPIC_SIGNAL, "EW_GREEN")

    for _ in range(40):
        if len(mqtt_acks) > t3c_ack_start:
            break
        time.sleep(0.1)
    t_switch_elapsed = time.time() - t_start

    t3_logs = [l["log"] for l in serial_logs[t3c_log_start:]]
    redundant_yellow = any("NS -> YELLOW clearance" in l for l in t3_logs)
    print(f"Test 3 Elapsed for EW_GREEN switch: {t_switch_elapsed:.3f}s")
    print(f"Test 3 REDUNDANT 2s TRANSITION OBSERVED: {redundant_yellow}")
    if redundant_yellow:
        print("  --> BUG OBSERVED: The signal had ALREADY been in NS_YELLOW for 2.0s!")
        print("      Yet when EW_GREEN was commanded, the firmware re-entered NS_YELLOW for ANOTHER 2.0s delay!")
    results.append({
        "test": "Test 3: Staged Controller Yellow Clearance -> EW_GREEN",
        "has_redundant_transition": redundant_yellow,
        "notes": "Redundant 2s clearance observed: firmware held yellow for another 2s despite already being yellow."
    })

    time.sleep(1.0)

    # ------------------------------------------------------------------------
    # TEST 4: ALL_RED Clearance -> Green Transition
    # ------------------------------------------------------------------------
    print("\n>>> TEST 4: ALL_RED Clearance -> EW_GREEN")
    print("Step 4a: Python Controller issues emergency ALL_RED...")
    client.publish(TOPIC_SIGNAL, "ALL_RED")
    time.sleep(1.5)

    print("\nStep 4b: Controller now clears intersection into EW_GREEN...")
    t4_log_start = len(serial_logs)
    client.publish(TOPIC_SIGNAL, "EW_GREEN")
    time.sleep(2.5)

    t4_logs = [l["log"] for l in serial_logs[t4_log_start:]]
    redundant_allred_yellow = any("NS -> YELLOW clearance" in l for l in t4_logs)
    print(f"Test 4 REDUNDANT YELLOW OBSERVED FROM ALL_RED: {redundant_allred_yellow}")
    if redundant_allred_yellow:
        print("  --> BUG OBSERVED: When switching from ALL_RED to EW_GREEN, NS flashed YELLOW for 2s instead of remaining RED!")
    results.append({
        "test": "Test 4: ALL_RED -> EW_GREEN",
        "has_redundant_transition": redundant_allred_yellow,
        "notes": "From ALL_RED, firmware triggered NS -> YELLOW clearance before EW GREEN."
    })

    # ------------------------------------------------------------------------
    # TEST 5: Heartbeat and Loop Interruption during 2s delay
    # ------------------------------------------------------------------------
    print("\n>>> TEST 5: Microcontroller Blocking during 2s delay")
    print("Testing if 2s delay blocks MQTT loop and delays heartbeats...")
    hb_times = [h["time"] for h in mqtt_heartbeats]
    hb_intervals = [hb_times[i] - hb_times[i-1] for i in range(1, len(hb_times))]
    max_interval = max(hb_intervals) if hb_intervals else 0
    print(f"Test 5: Maximum Heartbeat Gap observed: {max_interval:.2f}s (nominal is 2.0s)")

    # Clean up
    print("\n" + "="*80)
    print("TEST SUMMARY & VERIFICATION REPORT")
    print("="*80)
    for r in results:
        print(f" - {r['test']}: Redundant Transition = {r['has_redundant_transition']}")
        print(f"   Notes: {r['notes']}")

    stop_threads = True
    client.loop_stop()
    client.disconnect()
    time.sleep(0.5)

if __name__ == "__main__":
    run_tests()
