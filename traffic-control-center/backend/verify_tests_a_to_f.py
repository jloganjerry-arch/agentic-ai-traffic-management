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

serial_logs = []
mqtt_acks = []
mqtt_heartbeats = []
stop_threads = False

def serial_listener():
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=0.05)
        ser.dtr = False
        ser.rts = False
        print(f"[VERIFY RUNNER] Serial port {SERIAL_PORT} opened.")
        while not stop_threads:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                now_str = time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"
                entry = {"time": time.time(), "timestamp": now_str, "log": line}
                serial_logs.append(entry)
                clean_line = line.encode("ascii", errors="backslashreplace").decode("ascii")
                print(f"  [ESP32-LOG {now_str}] {clean_line}")
    except Exception as e:
        print(f"[VERIFY RUNNER ERROR] Serial listener: {e}")
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
        print(f"  [MQTT-ACK {now_str}] {payload}")
    elif msg.topic == TOPIC_HEARTBEAT:
        mqtt_heartbeats.append({"time": time.time(), "timestamp": now_str, "payload": payload})

def run_tests():
    global stop_threads

    # 1. Start Serial Listener
    ser_thread = threading.Thread(target=serial_listener, daemon=True)
    ser_thread.start()
    time.sleep(1.0)

    # 2. Connect MQTT Client
    client = mqtt.Client(client_id="PythonAuthoritativeVerifier")
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe([(TOPIC_ACK, 0), (TOPIC_HEARTBEAT, 0)])
    client.loop_start()

    print("[VERIFY RUNNER] Waiting for ESP32 connection & heartbeat...")
    for _ in range(30):
        if len(mqtt_heartbeats) > 0:
            break
        time.sleep(0.5)
    print(f"[VERIFY RUNNER] ESP32 confirmed online! Heartbeats: {len(mqtt_heartbeats)}")

    print("\n" + "="*80)
    print("EXECUTING TESTS A - F: AUTHORITATIVE PYTHON CONTROL")
    print("="*80)

    results = {}

    # ------------------------------------------------------------------------
    # TEST A: NS_GREEN -> EW_GREEN (Expected: No hidden 2-second yellow clearance)
    # ------------------------------------------------------------------------
    print("\n" + "-"*80)
    print(">>> TEST A: NS_GREEN -> EW_GREEN (Immediate Switch)")
    print("-" * 80)
    # Put in NS_GREEN first
    client.publish(TOPIC_SIGNAL, "NS_GREEN")
    time.sleep(1.0)
    
    # Now command EW_GREEN directly
    print("[TEST A] Publishing EW_GREEN...")
    t_start = time.time()
    t_ack_start = len(mqtt_acks)
    t_log_start = len(serial_logs)
    client.publish(TOPIC_SIGNAL, "EW_GREEN")

    # Wait for ACK
    ack_recv_time = None
    for _ in range(25): # 2.5s max
        if len(mqtt_acks) > t_ack_start:
            ack_recv_time = time.time() - t_start
            break
        time.sleep(0.05)

    t_a_logs = [l["log"] for l in serial_logs[t_log_start:]]
    has_hidden_clearance = any("YELLOW clearance" in l for l in t_a_logs)
    print(f"[TEST A RESULT] ACK Received in: {ack_recv_time:.3f}s")
    print(f"[TEST A RESULT] Hidden 2-second clearance triggered: {has_hidden_clearance}")
    
    test_a_pass = (ack_recv_time is not None and ack_recv_time < 0.5 and not has_hidden_clearance)
    results["TEST A"] = {
        "description": "NS_GREEN -> EW_GREEN: No hidden 2-second yellow clearance",
        "passed": test_a_pass,
        "ack_latency_s": ack_recv_time,
        "hidden_clearance_detected": has_hidden_clearance
    }

    time.sleep(1.0)

    # ------------------------------------------------------------------------
    # TEST B: NS_GREEN -> NS_YELLOW -> ALL_RED -> EW_GREEN
    # (Expected: Only Python-controlled yellow and all-red durations occur)
    # ------------------------------------------------------------------------
    print("\n" + "-"*80)
    print(">>> TEST B: Controller Sequence: NS_GREEN -> NS_YELLOW -> ALL_RED -> EW_GREEN")
    print("-" * 80)
    print("[TEST B] Step 1: NS_GREEN")
    client.publish(TOPIC_SIGNAL, "NS_GREEN")
    time.sleep(1.5)

    print("[TEST B] Step 2: NS_YELLOW (Python sets 1.5s yellow clearance)...")
    t_yellow_start = time.time()
    client.publish(TOPIC_SIGNAL, "NS_YELLOW")
    time.sleep(1.5)
    t_yellow_actual = time.time() - t_yellow_start

    print("[TEST B] Step 3: ALL_RED (Python sets 1.0s all-red clearance)...")
    t_allred_start = time.time()
    client.publish(TOPIC_SIGNAL, "ALL_RED")
    time.sleep(1.0)
    t_allred_actual = time.time() - t_allred_start

    print("[TEST B] Step 4: EW_GREEN (Python triggers EW green)...")
    t_ew_start = time.time()
    t_b_ack_start = len(mqtt_acks)
    t_b_log_start = len(serial_logs)
    client.publish(TOPIC_SIGNAL, "EW_GREEN")

    b_ack_time = None
    for _ in range(25):
        if len(mqtt_acks) > t_b_ack_start:
            b_ack_time = time.time() - t_ew_start
            break
        time.sleep(0.05)

    t_b_logs = [l["log"] for l in serial_logs[t_b_log_start:]]
    has_b_redundant = any("YELLOW clearance" in l for l in t_b_logs)
    print(f"[TEST B RESULT] EW_GREEN activated in {b_ack_time:.3f}s. Redundant clearance: {has_b_redundant}")
    print(f"[TEST B RESULT] Exact Python timings: Yellow={t_yellow_actual:.2f}s, AllRed={t_allred_actual:.2f}s")

    test_b_pass = (b_ack_time is not None and b_ack_time < 0.5 and not has_b_redundant)
    results["TEST B"] = {
        "description": "NS_GREEN -> NS_YELLOW -> ALL_RED -> EW_GREEN: Strictly Python-timed",
        "passed": test_b_pass,
        "ew_activate_latency_s": b_ack_time,
        "redundant_clearance": has_b_redundant
    }

    time.sleep(1.0)

    # ------------------------------------------------------------------------
    # TEST C: ALL_RED -> EW_GREEN
    # (Expected: EW_GREEN activates directly. North must NOT flash yellow.)
    # ------------------------------------------------------------------------
    print("\n" + "-"*80)
    print(">>> TEST C: ALL_RED -> EW_GREEN")
    print("-" * 80)
    print("[TEST C] Setting intersection into ALL_RED...")
    client.publish(TOPIC_SIGNAL, "ALL_RED")
    time.sleep(1.0)

    print("[TEST C] Commanding EW_GREEN from ALL_RED...")
    t_c_start = time.time()
    t_c_log_start = len(serial_logs)
    t_c_ack_start = len(mqtt_acks)
    client.publish(TOPIC_SIGNAL, "EW_GREEN")

    c_ack_time = None
    for _ in range(25):
        if len(mqtt_acks) > t_c_ack_start:
            c_ack_time = time.time() - t_c_start
            break
        time.sleep(0.05)

    t_c_logs = [l["log"] for l in serial_logs[t_c_log_start:]]
    north_flashed_yellow = any("NS -> YELLOW" in l for l in t_c_logs)
    ew_activated_directly = any("EW -> GREEN activated" in l for l in t_c_logs)
    print(f"[TEST C RESULT] EW_GREEN Activation latency: {c_ack_time:.3f}s")
    print(f"[TEST C RESULT] North flashed yellow: {north_flashed_yellow} (Must be False!)")
    print(f"[TEST C RESULT] EW activated directly: {ew_activated_directly}")

    test_c_pass = (not north_flashed_yellow and ew_activated_directly and c_ack_time < 0.5)
    results["TEST C"] = {
        "description": "ALL_RED -> EW_GREEN: Direct green, North does NOT flash yellow",
        "passed": test_c_pass,
        "north_flashed_yellow": north_flashed_yellow,
        "ew_direct_green": ew_activated_directly
    }

    time.sleep(1.0)

    # ------------------------------------------------------------------------
    # TEST D: EW_GREEN -> EW_YELLOW -> ALL_RED -> NS_GREEN
    # (Expected: No redundant clearance)
    # ------------------------------------------------------------------------
    print("\n" + "-"*80)
    print(">>> TEST D: Controller Sequence: EW_GREEN -> EW_YELLOW -> ALL_RED -> NS_GREEN")
    print("-" * 80)
    print("[TEST D] Step 1: EW_GREEN")
    client.publish(TOPIC_SIGNAL, "EW_GREEN")
    time.sleep(1.0)

    print("[TEST D] Step 2: EW_YELLOW (Python sets 1.5s yellow clearance)...")
    client.publish(TOPIC_SIGNAL, "EW_YELLOW")
    time.sleep(1.5)

    print("[TEST D] Step 3: ALL_RED (Python sets 1.0s all-red clearance)...")
    client.publish(TOPIC_SIGNAL, "ALL_RED")
    time.sleep(1.0)

    print("[TEST D] Step 4: NS_GREEN (Python triggers NS green)...")
    t_d_start = time.time()
    t_d_log_start = len(serial_logs)
    t_d_ack_start = len(mqtt_acks)
    client.publish(TOPIC_SIGNAL, "NS_GREEN")

    d_ack_time = None
    for _ in range(25):
        if len(mqtt_acks) > t_d_ack_start:
            d_ack_time = time.time() - t_d_start
            break
        time.sleep(0.05)

    t_d_logs = [l["log"] for l in serial_logs[t_d_log_start:]]
    has_d_redundant = any("YELLOW clearance" in l for l in t_d_logs)
    ns_activated_directly = any("NS -> GREEN activated" in l for l in t_d_logs)
    print(f"[TEST D RESULT] NS_GREEN Activation latency: {d_ack_time:.3f}s")
    print(f"[TEST D RESULT] Redundant clearance triggered: {has_d_redundant}")
    print(f"[TEST D RESULT] NS activated directly: {ns_activated_directly}")

    test_d_pass = (not has_d_redundant and ns_activated_directly and d_ack_time < 0.5)
    results["TEST D"] = {
        "description": "EW_GREEN -> EW_YELLOW -> ALL_RED -> NS_GREEN: No redundant clearance",
        "passed": test_d_pass,
        "redundant_clearance": has_d_redundant,
        "ns_direct_green": ns_activated_directly
    }

    # ------------------------------------------------------------------------
    # TEST E: Heartbeat Stability
    # (Expected: MQTT heartbeat remains stable and is not blocked by transitions)
    # ------------------------------------------------------------------------
    print("\n" + "-"*80)
    print(">>> TEST E: Heartbeat Stability Analysis")
    print("-" * 80)
    time.sleep(4.5) # Capture multiple heartbeats
    hb_times = [h["time"] for h in mqtt_heartbeats]
    intervals = [hb_times[i] - hb_times[i-1] for i in range(1, len(hb_times))]
    avg_interval = sum(intervals)/len(intervals) if intervals else 0
    max_interval = max(intervals) if intervals else 0
    print(f"[TEST E RESULT] Total heartbeats recorded: {len(mqtt_heartbeats)}")
    print(f"[TEST E RESULT] Heartbeat Interval: Avg = {avg_interval:.2f}s, Max Gap = {max_interval:.2f}s (Nominal: 2.0s)")

    test_e_pass = (max_interval < 2.5) # No blocking delays > 2.5s
    results["TEST E"] = {
        "description": "Heartbeat stability (not blocked by signal transition handling)",
        "passed": test_e_pass,
        "max_heartbeat_gap_s": max_interval,
        "avg_interval_s": avg_interval
    }

    # ------------------------------------------------------------------------
    # TEST F: Safety - Mutually Exclusive Green States
    # (Verify NS_GREEN and EW_GREEN can never leave conflicting greens active)
    # ------------------------------------------------------------------------
    print("\n" + "-"*80)
    print(">>> TEST F: Safety Verification (Mutual Exclusion)")
    print("-" * 80)
    # Rapid switching between NS_GREEN and EW_GREEN to verify safe atomic state transitions
    safety_violations = 0
    for i in range(4):
        target = "NS_GREEN" if i % 2 == 0 else "EW_GREEN"
        t_f_log_start = len(serial_logs)
        client.publish(TOPIC_SIGNAL, target)
        time.sleep(0.3)
        recent_logs = [l["log"] for l in serial_logs[t_f_log_start:]]
        # Check if failsafe tripped (which happens if mutual exclusion was violated)
        if any("HARDWARE FAILSAFE ALERT" in l for l in recent_logs):
            safety_violations += 1

    print(f"[TEST F RESULT] Conflicting green safety violations detected: {safety_violations}")
    test_f_pass = (safety_violations == 0)
    results["TEST F"] = {
        "description": "Safety: NS_GREEN and EW_GREEN mutually exclusive without conflicting greens",
        "passed": test_f_pass,
        "safety_violations": safety_violations
    }

    # ------------------------------------------------------------------------
    # FINAL SUMMARY REPORT
    # ------------------------------------------------------------------------
    print("\n" + "="*80)
    print("FINAL TEST REPORT (TESTS A - F)")
    print("="*80)
    all_passed = True
    for test_name, res in results.items():
        status = "PASSED" if res["passed"] else "FAILED"
        if not res["passed"]:
            all_passed = False
        print(f"[{status}] {test_name}: {res['description']}")
    
    print("\nOVERALL STATUS: " + ("ALL TESTS PASSED 100%" if all_passed else "SOME TESTS FAILED"))

    stop_threads = True
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    run_tests()
