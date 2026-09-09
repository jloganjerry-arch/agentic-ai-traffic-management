"""
Live Hardware MQTT Verification Script.
Tests individual physical signal commands:
  NS_GREEN -> NS_YELLOW -> ALL_RED -> EW_GREEN -> EW_YELLOW -> ALL_RED
Verifies ESP32 ACKs on 'traffic/esp32/ack' and monitors hardware failsafe.
"""

import time
import sys
import paho.mqtt.client as mqtt

BROKER_HOST = "127.0.0.1"  # Python laptop connects locally to Mosquitto
BROKER_PORT = 1883
TOPIC_SIGNAL = "traffic/signal"
TOPIC_ACK = "traffic/esp32/ack"
TOPIC_HEARTBEAT = "traffic/system/heartbeat"

acks_received = []
heartbeats_received = []

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[MQTT] Connected successfully to {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe([(TOPIC_ACK, 0), (TOPIC_HEARTBEAT, 0)])
    else:
        print(f"[MQTT] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8", errors="ignore")
    timestamp = time.strftime("%H:%M:%S")
    if msg.topic == TOPIC_ACK:
        acks_received.append((timestamp, payload))
        print(f"  [ESP32 ACK] {timestamp} -> {payload}")
    elif msg.topic == TOPIC_HEARTBEAT:
        heartbeats_received.append((timestamp, payload))
        print(f"  [HEARTBEAT] {timestamp} -> {payload}")

def test_hardware_commands():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="HardwareTester")
    except AttributeError:
        client = mqtt.Client(client_id="HardwareTester")

    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to broker {BROKER_HOST}:{BROKER_PORT}...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    time.sleep(1.0)

    # Sequence of individual commands to test
    commands = [
        ("NS_GREEN", 2.0),
        ("NS_YELLOW", 2.0),
        ("ALL_RED", 1.5),
        ("EW_GREEN", 2.0),
        ("EW_YELLOW", 2.0),
        ("ALL_RED", 1.5),
    ]

    print("\n--- BEGIN INDIVIDUAL PHYSICAL SIGNAL TEST ---")
    for cmd, duration in commands:
        print(f"\n[COMMAND] Publishing '{cmd}' to topic '{TOPIC_SIGNAL}'...")
        prev_acks_count = len(acks_received)
        client.publish(TOPIC_SIGNAL, cmd, qos=1)

        # Wait for duration and check for ACK
        start_t = time.time()
        ack_found = False
        while time.time() - start_t < duration:
            if len(acks_received) > prev_acks_count:
                ack_found = True
            time.sleep(0.1)

        if ack_found:
            print(f"  --> PASS: Received ACK for {cmd}")
        else:
            print(f"  --> NOTE: No immediate ACK received for {cmd} within {duration}s")

    client.loop_stop()
    client.disconnect()

    print("\n--- SUMMARY OF RECEIVED ACKS ---")
    for ts, ack in acks_received:
        print(f"  [{ts}] {ack}")

    if len(acks_received) >= 4:
        print("\n[SUCCESS] Hardware MQTT verification PASSED! Physical ESP32 is responding with ACKs.")
        return 0
    else:
        print(f"\n[WARNING] Only received {len(acks_received)} ACKs. Check ESP32 Wi-Fi / MQTT connection.")
        return 1

if __name__ == "__main__":
    sys.exit(test_hardware_commands())
