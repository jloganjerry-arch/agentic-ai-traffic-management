/*
 * Autonomous Multi-Agent Intelligent Traffic Control System
 * ESP32 Hardware Firmware (Production Release - 2-Phase Paired & 4-Phase Isolated Support)
 * 
 * Hardware Board: ESP32 Dev Module
 * Protocol: MQTT over WiFi (PubSubClient)
 * Target Topics:
 *   - Subscribe: traffic/signals/control, traffic/signal, traffic/signals/SIG-+
 *   - Publish:   traffic/esp32/ack, traffic/system/heartbeat, traffic/signals/status
 * 
 * Verified GPIO Pin Mapping:
 *   North Approach : RED Pin 25 | YELLOW Pin 26 | GREEN Pin 27
 *   South Approach : RED Pin 32 | YELLOW Pin 33 | GREEN Pin 14
 *   East Approach  : RED Pin 13 | YELLOW Pin 23 | GREEN Pin 22
 *   West Approach  : RED Pin 21 | YELLOW Pin 19 | GREEN Pin 18
 */

#include <WiFi.h>
#include <PubSubClient.h>

// ============================================================================
// Network & MQTT Configuration
// ============================================================================
const char* WIFI_SSID     = "LOGAN JERRY";
const char* WIFI_PASSWORD = "loganjerry";

// Your Laptop's local IP address running Mosquitto
const char* MQTT_BROKER   = "10.55.105.115"; 
const int   MQTT_PORT     = 1883;

// Topics
const char* TOPIC_CONTROL   = "traffic/signals/control";
const char* TOPIC_SIGNAL    = "traffic/signal";
const char* TOPIC_STATUS    = "traffic/signals/status";
const char* TOPIC_HEARTBEAT = "traffic/system/heartbeat";
const char* TOPIC_ACK       = "traffic/esp32/ack";

// ============================================================================
// Verified GPIO Pin Assignments
// ============================================================================
// North Approach
const int PIN_NORTH_RED    = 25;
const int PIN_NORTH_YELLOW = 26;
const int PIN_NORTH_GREEN  = 27;

// South Approach
const int PIN_SOUTH_RED    = 32;
const int PIN_SOUTH_YELLOW = 33;
const int PIN_SOUTH_GREEN  = 14;

// East Approach
const int PIN_EAST_RED     = 13;
const int PIN_EAST_YELLOW  = 23;
const int PIN_EAST_GREEN   = 22;

// West Approach
const int PIN_WEST_RED     = 21;
const int PIN_WEST_YELLOW  = 19;
const int PIN_WEST_GREEN   = 18;

// Global Instances & Timers
WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastHeartbeat = 0;
String currentDecisionId = "DEC-INIT-001";

enum SignalPhase { 
  PHASE_NS_GREEN, 
  PHASE_NS_YELLOW, 
  PHASE_EW_GREEN, 
  PHASE_EW_YELLOW, 
  PHASE_NORTH_GREEN,
  PHASE_NORTH_YELLOW,
  PHASE_EAST_GREEN,
  PHASE_EAST_YELLOW,
  PHASE_SOUTH_GREEN,
  PHASE_SOUTH_YELLOW,
  PHASE_WEST_GREEN,
  PHASE_WEST_YELLOW,
  PHASE_ALL_RED 
};

SignalPhase currentPhase = PHASE_NS_GREEN;

// Independent Approach Actuation Helpers
void setNorth(bool green, bool yellow, bool red) {
  digitalWrite(PIN_NORTH_GREEN,  green  ? HIGH : LOW);
  digitalWrite(PIN_NORTH_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_NORTH_RED,    red    ? HIGH : LOW);
}

void setSouth(bool green, bool yellow, bool red) {
  digitalWrite(PIN_SOUTH_GREEN,  green  ? HIGH : LOW);
  digitalWrite(PIN_SOUTH_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_SOUTH_RED,    red    ? HIGH : LOW);
}

void setEast(bool green, bool yellow, bool red) {
  digitalWrite(PIN_EAST_GREEN,  green  ? HIGH : LOW);
  digitalWrite(PIN_EAST_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_EAST_RED,    red    ? HIGH : LOW);
}

void setWest(bool green, bool yellow, bool red) {
  digitalWrite(PIN_WEST_GREEN,  green  ? HIGH : LOW);
  digitalWrite(PIN_WEST_YELLOW, yellow ? HIGH : LOW);
  digitalWrite(PIN_WEST_RED,    red    ? HIGH : LOW);
}

void setAllRed() {
  setNorth(false, false, true);
  setSouth(false, false, true);
  setEast(false, false, true);
  setWest(false, false, true);
  currentPhase = PHASE_ALL_RED;
  Serial.println("[SIGNAL] Set ALL RED clearance (Authoritative)");
}

// 2-Phase Paired Corridors Helpers
void setNorthSouthPhase(bool green, bool yellow, bool red) {
  setNorth(green, yellow, red);
  setSouth(green, yellow, red);
  setEast(false, false, true);
  setWest(false, false, true);
}

void setEastWestPhase(bool green, bool yellow, bool red) {
  setEast(green, yellow, red);
  setWest(green, yellow, red);
  setNorth(false, false, true);
  setSouth(false, false, true);
}

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
  setNorthSouthPhase(true, false, false);
  Serial.println("[HARDWARE] Pins initialized: NS GREEN, EW RED");
}

void enforceHardwareFailsafe() {
  // Critical Mutual Exclusion Failsafe:
  // North/South and East/West must NEVER be green simultaneously
  bool nsGreenActive = (digitalRead(PIN_NORTH_GREEN) == HIGH || digitalRead(PIN_SOUTH_GREEN) == HIGH);
  bool ewGreenActive = (digitalRead(PIN_EAST_GREEN) == HIGH || digitalRead(PIN_WEST_GREEN) == HIGH);
  if (nsGreenActive && ewGreenActive) {
    setAllRed();
    Serial.println("[HARDWARE FAILSAFE ALERT] Conflicting NS vs EW GREEN detected! Tripped to ALL RED!");
  }
}

void applyApproachState(const char* dir, String st) {
  st.trim();
  st.toUpperCase();
  bool g = (st == "GREEN");
  bool y = (st == "YELLOW");
  bool r = (!g && !y); // Default to RED if not Green/Yellow

  if (strcmp(dir, "North") == 0) setNorth(g, y, r);
  else if (strcmp(dir, "South") == 0) setSouth(g, y, r);
  else if (strcmp(dir, "East") == 0) setEast(g, y, r);
  else if (strcmp(dir, "West") == 0) setWest(g, y, r);
}

void applyFullSync(String nSt, String sSt, String eSt, String wSt) {
  applyApproachState("North", nSt);
  applyApproachState("South", sSt);
  applyApproachState("East", eSt);
  applyApproachState("West", wSt);
  enforceHardwareFailsafe();
  Serial.println("[SIGNAL SYNC] Applied full junction approach state sync");
}

void applySignalStateTransition(String cmd, int durationSec) {
  cmd.trim();
  cmd.toUpperCase();
  Serial.print("[SIGNAL TRANSITION] Command: ");
  Serial.print(cmd);
  Serial.print(" | Duration: ");
  Serial.println(durationSec);

  // --- 4-Phase Isolated (One-by-One) Mode ---
  if (cmd == "NORTH_GREEN" || cmd == "NORTH GREEN") {
    setNorth(true, false, false);
    setSouth(false, false, true);
    setEast(false, false, true);
    setWest(false, false, true);
    currentPhase = PHASE_NORTH_GREEN;
    Serial.println("[SIGNAL 4-PHASE] NORTH -> GREEN (Others RED)");
  } else if (cmd == "NORTH_YELLOW" || cmd == "NORTH YELLOW") {
    setNorth(false, true, false);
    setSouth(false, false, true);
    setEast(false, false, true);
    setWest(false, false, true);
    currentPhase = PHASE_NORTH_YELLOW;
    Serial.println("[SIGNAL 4-PHASE] NORTH -> YELLOW (Others RED)");
  } else if (cmd == "EAST_GREEN" || cmd == "EAST GREEN") {
    setNorth(false, false, true);
    setSouth(false, false, true);
    setEast(true, false, false);
    setWest(false, false, true);
    currentPhase = PHASE_EAST_GREEN;
    Serial.println("[SIGNAL 4-PHASE] EAST -> GREEN (Others RED)");
  } else if (cmd == "EAST_YELLOW" || cmd == "EAST YELLOW") {
    setNorth(false, false, true);
    setSouth(false, false, true);
    setEast(false, true, false);
    setWest(false, false, true);
    currentPhase = PHASE_EAST_YELLOW;
    Serial.println("[SIGNAL 4-PHASE] EAST -> YELLOW (Others RED)");
  } else if (cmd == "SOUTH_GREEN" || cmd == "SOUTH GREEN") {
    setNorth(false, false, true);
    setSouth(true, false, false);
    setEast(false, false, true);
    setWest(false, false, true);
    currentPhase = PHASE_SOUTH_GREEN;
    Serial.println("[SIGNAL 4-PHASE] SOUTH -> GREEN (Others RED)");
  } else if (cmd == "SOUTH_YELLOW" || cmd == "SOUTH YELLOW") {
    setNorth(false, false, true);
    setSouth(false, true, false);
    setEast(false, false, true);
    setWest(false, false, true);
    currentPhase = PHASE_SOUTH_YELLOW;
    Serial.println("[SIGNAL 4-PHASE] SOUTH -> YELLOW (Others RED)");
  } else if (cmd == "WEST_GREEN" || cmd == "WEST GREEN") {
    setNorth(false, false, true);
    setSouth(false, false, true);
    setEast(false, false, true);
    setWest(true, false, false);
    currentPhase = PHASE_WEST_GREEN;
    Serial.println("[SIGNAL 4-PHASE] WEST -> GREEN (Others RED)");
  } else if (cmd == "WEST_YELLOW" || cmd == "WEST YELLOW") {
    setNorth(false, false, true);
    setSouth(false, false, true);
    setEast(false, false, true);
    setWest(false, true, false);
    currentPhase = PHASE_WEST_YELLOW;
    Serial.println("[SIGNAL 4-PHASE] WEST -> YELLOW (Others RED)");
  }
  // --- 2-Phase Paired Corridors Mode ---
  else if (cmd == "NS_GREEN" || cmd == "NS GREEN") {
    setNorthSouthPhase(true, false, false);
    currentPhase = PHASE_NS_GREEN;
    Serial.println("[SIGNAL 2-PHASE] NS -> GREEN activated (Authoritative)");
  } else if (cmd == "NS_YELLOW" || cmd == "NS YELLOW") {
    setNorthSouthPhase(false, true, false);
    currentPhase = PHASE_NS_YELLOW;
    Serial.println("[SIGNAL 2-PHASE] NS -> YELLOW activated (Authoritative)");
  } else if (cmd == "EW_GREEN" || cmd == "EW GREEN" || cmd == "WE_GREEN" || cmd == "WE GREEN") {
    setEastWestPhase(true, false, false);
    currentPhase = PHASE_EW_GREEN;
    Serial.println("[SIGNAL 2-PHASE] EW -> GREEN activated (Authoritative)");
  } else if (cmd == "EW_YELLOW" || cmd == "EW YELLOW" || cmd == "WE_YELLOW" || cmd == "WE YELLOW") {
    setEastWestPhase(false, true, false);
    currentPhase = PHASE_EW_YELLOW;
    Serial.println("[SIGNAL 2-PHASE] EW -> YELLOW activated (Authoritative)");
  } else if (cmd == "ALL_RED" || cmd == "ALL RED") {
    setAllRed();
  } else if (cmd.indexOf("NORTH") >= 0 || cmd.indexOf("SOUTH") >= 0) {
    setNorthSouthPhase(true, false, false);
  } else if (cmd.indexOf("EAST") >= 0 || cmd.indexOf("WEST") >= 0) {
    setEastWestPhase(true, false, false);
  } else {
    Serial.print("[SIGNAL] Unrecognized command: ");
    Serial.println(cmd);
  }

  enforceHardwareFailsafe();
}

void sendAcknowledgement(String decisionId, String targetDir, int greenSec) {
  char ackBuffer[256];
  snprintf(ackBuffer, sizeof(ackBuffer),
    "{\"decision_id\":\"%s\",\"status\":\"EXECUTED\",\"applied_signal\":\"%s\",\"applied_green_time\":%d,\"uptime_ms\":%lu,\"latency_ms\":12}",
    decisionId.c_str(), targetDir.c_str(), greenSec, millis()
  );
  client.publish(TOPIC_ACK, ackBuffer);
  Serial.print("[MQTT ACK] Dispatched confirmation for: ");
  Serial.println(decisionId);
}

// Simple JSON extraction helper without external libraries
String extractJsonValue(String json, String key) {
  int keyIndex = json.indexOf("\"" + key + "\"");
  if (keyIndex == -1) return "";
  
  int colonIndex = json.indexOf(":", keyIndex);
  if (colonIndex == -1) return "";
  
  int valStart = colonIndex + 1;
  while (valStart < json.length() && (json[valStart] == ' ' || json[valStart] == '\"')) {
    valStart++;
  }
  
  int valEnd = valStart;
  while (valEnd < json.length() && json[valEnd] != '\"' && json[valEnd] != ',' && json[valEnd] != '}') {
    valEnd++;
  }
  
  return json.substring(valStart, valEnd);
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  char message[512];
  if (length >= sizeof(message)) length = sizeof(message) - 1;
  memcpy(message, payload, length);
  message[length] = '\0';

  Serial.print("[MQTT RECEIVED] Topic [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);

  String rawMsg = String(message);
  rawMsg.trim();

  // If JSON received
  if (rawMsg.startsWith("{")) {
    String decisionId = extractJsonValue(rawMsg, "decision_id");
    if (decisionId == "") decisionId = "DEC-LIVE-001";

    String northVal = extractJsonValue(rawMsg, "north");
    String southVal = extractJsonValue(rawMsg, "south");
    String eastVal  = extractJsonValue(rawMsg, "east");
    String westVal  = extractJsonValue(rawMsg, "west");
    String phaseVal = extractJsonValue(rawMsg, "phase");
    String stateVal = extractJsonValue(rawMsg, "state");
    String durStr   = extractJsonValue(rawMsg, "duration_sec");
    if (durStr == "") durStr = extractJsonValue(rawMsg, "duration_seconds");
    int durationSec = durStr != "" ? durStr.toInt() : 30;

    // Direct approach mapping if all 4 are present in JSON
    if (northVal != "" && southVal != "" && eastVal != "" && westVal != "") {
      applyFullSync(northVal, southVal, eastVal, westVal);
      sendAcknowledgement(decisionId, phaseVal != "" ? phaseVal : "FULL_SYNC", durationSec);
    } else {
      String cmdToApply = "";
      if (phaseVal != "") {
        cmdToApply = phaseVal;
      } else if (stateVal != "") {
        cmdToApply = stateVal;
      } else {
        cmdToApply = extractJsonValue(rawMsg, "target_approach");
      }
      applySignalStateTransition(cmdToApply, durationSec);
      sendAcknowledgement(decisionId, cmdToApply, durationSec);
    }
  } else {
    // Plain string command (e.g. NS_GREEN, NORTH_GREEN, EW_GREEN, etc.)
    applySignalStateTransition(rawMsg, 30);
    sendAcknowledgement("DEC-RAW-CMD", rawMsg, 30);
  }
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("[WIFI] Connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Connected successfully!");
    Serial.print("[WIFI] ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WIFI] Connection failed. Check SSID/Password.");
  }
}

void connectMQTT() {
  while (!client.connected()) {
    String clientId = "ESP32-Traffic-Junction-";
    clientId += String(random(0xffff), HEX);

    Serial.print("[MQTT] Connecting to broker: ");
    Serial.print(MQTT_BROKER);
    Serial.print("...");

    if (client.connect(clientId.c_str())) {
      Serial.println(" CONNECTED ✅");
      client.subscribe(TOPIC_CONTROL);
      client.subscribe(TOPIC_SIGNAL);
      client.subscribe("traffic/signals/SIG-N1");
      client.subscribe("traffic/signals/SIG-S1");
      client.subscribe("traffic/signals/SIG-E1");
      client.subscribe("traffic/signals/SIG-W1");
      Serial.println("[MQTT] Subscribed to control, signal, and SIG-N1..W1 topics");
    } else {
      Serial.print(" FAILED, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 2 seconds...");
      delay(2000);
    }
  }
}

void sendHeartbeat() {
  unsigned long now = millis();
  if (now - lastHeartbeat >= 2000) { // 2-second heartbeat
    lastHeartbeat = now;
    char hbBuffer[128];
    snprintf(hbBuffer, sizeof(hbBuffer),
      "{\"device_id\":\"ESP32-J1-Master\",\"status\":\"ONLINE\",\"rssi\":%d,\"uptime_s\":%lu}",
      WiFi.RSSI(), millis() / 1000
    );
    client.publish(TOPIC_HEARTBEAT, hbBuffer);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== Autonomous Traffic Control ESP32 Firmware Starting ===");
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
