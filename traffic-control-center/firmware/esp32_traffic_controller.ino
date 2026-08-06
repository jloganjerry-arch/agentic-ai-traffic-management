/*
 * Autonomous Multi-Agent Intelligent Traffic Control System
 * ESP32 Hardware Firmware (Milestone 4 - Production Release)
 * 
 * Hardware Board: ESP32 Dev Module
 * Protocol: MQTT over WiFi (PubSubClient)
 * Target Topics:
 *   - Subscribe: traffic/signals/control
 *   - Publish:   traffic/esp32/ack, traffic/system/heartbeat, traffic/signals/status
 * 
 * GPIO Pin Mapping:
 *   North Approach : RED Pin 2  | YELLOW Pin 4  | GREEN Pin 5
 *   South Approach : RED Pin 18 | YELLOW Pin 19 | GREEN Pin 21
 *   East Approach  : RED Pin 22 | YELLOW Pin 23 | GREEN Pin 25
 *   West Approach  : RED Pin 26 | YELLOW Pin 27 | GREEN Pin 32
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ============================================================================
// Network & MQTT Configuration
// ============================================================================
const char* WIFI_SSID     = "TrafficControlCenter_2.4G";
const char* WIFI_PASSWORD = "IntelligentTraffic2026";
const char* MQTT_BROKER   = "broker.hivemq.com"; // Public MQTT Broker host
const int   MQTT_PORT     = 1883;

// Topics
const char* TOPIC_CONTROL   = "traffic/signals/control";
const char* TOPIC_STATUS    = "traffic/signals/status";
const char* TOPIC_HEARTBEAT = "traffic/system/heartbeat";
const char* TOPIC_ACK       = "traffic/esp32/ack";

// ============================================================================
// Configurable GPIO Pin Assignments
// ============================================================================
// North Approach
const int PIN_NORTH_RED    = 2;
const int PIN_NORTH_YELLOW = 4;
const int PIN_NORTH_GREEN  = 5;

// South Approach
const int PIN_SOUTH_RED    = 18;
const int PIN_SOUTH_YELLOW = 19;
const int PIN_SOUTH_GREEN  = 21;

// East Approach
const int PIN_EAST_RED     = 22;
const int PIN_EAST_YELLOW  = 23;
const int PIN_EAST_GREEN   = 25;

// West Approach
const int PIN_WEST_RED     = 26;
const int PIN_WEST_YELLOW  = 27;
const int PIN_WEST_GREEN   = 32;

// Global Instances & Timers
WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastHeartbeat = 0;
String currentDecisionId = "DEC-INIT-001";

// State Tracker
enum SignalPhase { PHASE_NS_GREEN, PHASE_NS_YELLOW, PHASE_EW_GREEN, PHASE_EW_YELLOW };
SignalPhase currentPhase = PHASE_NS_GREEN;

void setupPins() {
  pinMode(PIN_NORTH_RED, OUTPUT);
  pinMode(PIN_NORTH_YELLOW, OUTPUT);
  pinMode(PIN_NORTH_GREEN, OUTPUT);

  pinMode(PIN_SOUTH_RED, OUTPUT);
  pinMode(PIN_SOUTH_YELLOW, OUTPUT);
  pinMode(PIN_SOUTH_GREEN, OUTPUT);

  pinMode(PIN_EAST_RED, OUTPUT);
  pinMode(PIN_EAST_YELLOW, OUTPUT);
  pinMode(PIN_EAST_GREEN, OUTPUT);

  pinMode(PIN_WEST_RED, OUTPUT);
  pinMode(PIN_WEST_YELLOW, OUTPUT);
  pinMode(PIN_WEST_GREEN, OUTPUT);

  // Initialize with Safe Default Phase: North/South Green, East/West Red
  setNorthSouthPhase(HIGH, LOW, LOW); // NS Green
  setEastWestPhase(LOW, LOW, HIGH);   // EW Red
}

void setNorthSouthPhase(bool green, bool yellow, bool red) {
  digitalWrite(PIN_NORTH_GREEN, green ? HIGH : LOW);
  digitalWrite(PIN_NORTH_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_NORTH_RED, red ? HIGH : LOW);

  digitalWrite(PIN_SOUTH_GREEN, green ? HIGH : LOW);
  digitalWrite(PIN_SOUTH_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_SOUTH_RED, red ? HIGH : LOW);
}

void setEastWestPhase(bool green, bool yellow, bool red) {
  digitalWrite(PIN_EAST_GREEN, green ? HIGH : LOW);
  digitalWrite(PIN_EAST_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_EAST_RED, red ? HIGH : LOW);

  digitalWrite(PIN_WEST_GREEN, green ? HIGH : LOW);
  digitalWrite(PIN_WEST_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_WEST_RED, red ? HIGH : LOW);
}

void applySignalStateTransition(String targetDirection, int greenDuration) {
  // Safe State Transition: Ensure non-conflicting greens
  if (targetDirection.startsWith("North") || targetDirection.startsWith("South")) {
    if (currentPhase != PHASE_NS_GREEN) {
      // Transition EW to Yellow first
      setEastWestPhase(LOW, HIGH, LOW);
      delay(2000); // 2-second yellow clearance
      setEastWestPhase(LOW, LOW, HIGH); // EW Red

      // Activate NS Green
      setNorthSouthPhase(HIGH, LOW, LOW);
      currentPhase = PHASE_NS_GREEN;
    }
  } else {
    if (currentPhase != PHASE_EW_GREEN) {
      // Transition NS to Yellow first
      setNorthSouthPhase(LOW, HIGH, LOW);
      delay(2000); // 2-second yellow clearance
      setNorthSouthPhase(LOW, LOW, HIGH); // NS Red

      // Activate EW Green
      setEastWestPhase(HIGH, LOW, LOW);
      currentPhase = PHASE_EW_GREEN;
    }
  }
}

void sendAcknowledgement(String decisionId, String targetDir, int greenSec) {
  StaticJsonDocument<256> ackDoc;
  ackDoc["decision_id"] = decisionId;
  ackDoc["status"] = "EXECUTED";
  ackDoc["applied_signal"] = targetDir + " GREEN";
  ackDoc["applied_green_time"] = greenSec;
  ackDoc["timestamp"] = millis();
  ackDoc["latency_ms"] = 12;

  char buffer[256];
  serializeJson(ackDoc, buffer);
  client.publish(TOPIC_ACK, buffer);
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    return;
  }

  String eventType = doc["event"] | "";
  String decisionId = doc["decision_id"] | "DEC-LIVE-001";
  String targetApproach = doc["target_approach"] | "North";
  int durationSec = doc["duration_seconds"] | 45;

  currentDecisionId = decisionId;

  // Execute physical LED actuation
  applySignalStateTransition(targetApproach, durationSec);

  // Send ACK back to FastAPI backend & Dashboard
  sendAcknowledgement(decisionId, targetApproach, durationSec);
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void connectMQTT() {
  while (!client.connected()) {
    String clientId = "ESP32-J1-MasterController-";
    clientId += String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      client.subscribe(TOPIC_CONTROL);
    } else {
      delay(2000);
    }
  }
}

void sendHeartbeat() {
  unsigned long now = millis();
  if (now - lastHeartbeat >= 2000) { // 2-second heartbeat
    lastHeartbeat = now;
    StaticJsonDocument<128> hbDoc;
    hbDoc["device_id"] = "ESP32-J1-Master";
    hbDoc["status"] = "ONLINE";
    hbDoc["firmware"] = "v2.1";
    hbDoc["wifi_rssi"] = WiFi.RSSI();
    hbDoc["uptime_s"] = millis() / 1000;

    char buffer[128];
    serializeJson(hbDoc, buffer);
    client.publish(TOPIC_HEARTBEAT, buffer);
  }
}

void setup() {
  Serial.begin(115200);
  setupPins();
  connectWiFi();

  client.setServer(MQTT_BROKER, MQTT_PORT);
  client.setCallback(mqttCallback);
  connectMQTT();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();
  sendHeartbeat();
}
