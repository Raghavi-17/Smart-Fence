/*
  =============================================================================
  SMART FENCE - ESP32 IOT SAFETY MONITORING CONTROLLER FIRMWARE
  =============================================================================

  Hardware Connections:
  - ESP32 DevKit V1
  - Active/Passive Buzzer: GPIO 25 (via 220 ohm resistor or NPN transistor)
  - Warning LED (Red):     GPIO 26 (via 330 ohm resistor)
  - Safe Indicator (Green): GPIO 27 (optional status LED)
  - GND to common Breadboard Ground Rail

  SAFETY WARNING:
  THIS IS A PROTOTYPE WARNING SYSTEM. DO NOT CONNECT THIS MICROCONTROLLER
  DIRECTLY TO HIGH-VOLTAGE MAINS OR ELECTRIC FENCE ENERGIZERS!
  The Buzzer and LED represent safe acoustic and visual warnings.
  =============================================================================
*/

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// -----------------------------------------------------------------------------
// Wi-Fi Credentials (Configure for your local Wi-Fi router / mobile hotspot)
// -----------------------------------------------------------------------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Hardware Pin Definitions
const int PIN_BUZZER    = 25;
const int PIN_LED_RED   = 26;
const int PIN_LED_GREEN = 27;

// PWM Tone Channel for ESP32
const int BUZZER_CHANNEL = 0;
const int PWM_RESOLUTION = 8;

// HTTP Server running on standard port 80
WebServer server(80);

// Current Hardware State
String currentRisk     = "LOW";
bool   buzzerActive    = false;
bool   ledActive       = false;
String lastReason      = "System Boot";
unsigned long lastCommandTime = 0;

// Non-blocking Timing Variables
unsigned long previousBlinkMillis = 0;
bool ledState = false;

// -----------------------------------------------------------------------------
// Sound Alarm Routine (Non-Blocking)
// -----------------------------------------------------------------------------
void updateAlarmHardware() {
  unsigned long currentMillis = millis();

  if (currentRisk == "CRITICAL") {
    // Rapid alternating siren & fast strobe (100ms)
    if (currentMillis - previousBlinkMillis >= 100) {
      previousBlinkMillis = currentMillis;
      ledState = !ledState;
      digitalWrite(PIN_LED_RED, ledState);
      digitalWrite(PIN_LED_GREEN, LOW);

      if (buzzerActive) {
        ledcWriteTone(BUZZER_CHANNEL, ledState ? 2800 : 3500);
      } else {
        ledcWriteTone(BUZZER_CHANNEL, 0);
      }
    }
  } else if (currentRisk == "HIGH") {
    // Pulsing alarm & warning flash (250ms)
    if (currentMillis - previousBlinkMillis >= 250) {
      previousBlinkMillis = currentMillis;
      ledState = !ledState;
      digitalWrite(PIN_LED_RED, ledState);
      digitalWrite(PIN_LED_GREEN, LOW);

      if (buzzerActive && ledState) {
        ledcWriteTone(BUZZER_CHANNEL, 2000);
      } else {
        ledcWriteTone(BUZZER_CHANNEL, 0);
      }
    }
  } else if (currentRisk == "MEDIUM") {
    // Slow warning pulse (600ms), no loud buzzer
    if (currentMillis - previousBlinkMillis >= 600) {
      previousBlinkMillis = currentMillis;
      ledState = !ledState;
      digitalWrite(PIN_LED_RED, ledState);
      digitalWrite(PIN_LED_GREEN, LOW);
      ledcWriteTone(BUZZER_CHANNEL, 0); // Buzzer silent for medium
    }
  } else {
    // Safe / Low risk: Green LED steady, Red LED OFF, Buzzer OFF
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_LED_GREEN, HIGH);
    ledcWriteTone(BUZZER_CHANNEL, 0);
  }
}

// -----------------------------------------------------------------------------
// HTTP REST Handlers
// -----------------------------------------------------------------------------
void handleRoot() {
  server.send(200, "application/json", "{\"device\":\"ESP32_SMART_FENCE\",\"status\":\"ONLINE\"}");
}

void handleStatus() {
  StaticJsonDocument<256> doc;
  doc["status"]       = "CONNECTED";
  doc["device"]       = "ESP32_PHYSICAL_HARDWARE";
  doc["risk"]         = currentRisk;
  doc["buzzer"]       = buzzerActive;
  doc["led"]          = ledActive;
  doc["reason"]       = lastReason;
  doc["ip"]           = WiFi.localIP().toString();
  doc["rssi"]         = WiFi.RSSI();
  doc["uptime_ms"]    = millis();

  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleAlert() {
  if (server.hasArg("plain") == false) {
    server.send(400, "application/json", "{\"error\":\"Missing request body\"}");
    return;
  }

  String body = server.arg("plain");
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, body);

  if (error) {
    server.send(400, "application/json", "{\"error\":\"Invalid JSON format\"}");
    return;
  }

  // Parse command fields
  if (doc.containsKey("risk")) {
    currentRisk = doc["risk"].as<String>();
  }
  if (doc.containsKey("buzzer")) {
    buzzerActive = doc["buzzer"].as<bool>();
  }
  if (doc.containsKey("led")) {
    ledActive = doc["led"].as<bool>();
  }
  if (doc.containsKey("reason")) {
    lastReason = doc["reason"].as<String>();
  }
  lastCommandTime = millis();

  Serial.println("==========================================");
  Serial.print("NEW IOT ALERT RECEIVED: Risk=");
  Serial.print(currentRisk);
  Serial.print(" | Buzzer=");
  Serial.print(buzzerActive ? "ON" : "OFF");
  Serial.print(" | LED=");
  Serial.println(ledActive ? "ON" : "OFF");
  Serial.print("Reason: ");
  Serial.println(lastReason);
  Serial.println("==========================================");

  StaticJsonDocument<128> reply;
  reply["status"]  = "ACK";
  reply["risk"]    = currentRisk;
  reply["buzzer"]  = buzzerActive;
  reply["led"]     = ledActive;

  String jsonReply;
  serializeJson(reply, jsonReply);
  server.send(200, "application/json", jsonReply);
}

// -----------------------------------------------------------------------------
// Arduino Setup & Loop
// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n[BOOT] Initializing Smart Fence ESP32 Hardware Controller...");

  // Initialize Hardware Output Pins
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_GREEN, OUTPUT);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_LED_GREEN, LOW);

  // Initialize PWM Buzzer Channel
  ledcSetup(BUZZER_CHANNEL, 2000, PWM_RESOLUTION);
  ledcAttachPin(PIN_BUZZER, BUZZER_CHANNEL);
  ledcWrite(BUZZER_CHANNEL, 0);

  // Connect to Wi-Fi
  Serial.print("[WIFI] Connecting to SSID: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    digitalWrite(PIN_LED_RED, !digitalRead(PIN_LED_RED));
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Connected successfully!");
    Serial.print("[WIFI] ESP32 Local IP Address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_LED_GREEN, HIGH);
  } else {
    Serial.println("\n[WIFI] Wi-Fi Connection failed. Running in standalone local mode.");
  }

  // Setup HTTP Endpoints
  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/status", HTTP_GET, handleStatus);
  server.on("/api/alert", HTTP_POST, handleAlert);

  server.begin();
  Serial.println("[HTTP] REST API Server started on port 80.");
  Serial.println("[READY] Smart Fence IoT Hardware Ready for Alert Ingestion.");
}

void loop() {
  // Handle incoming HTTP client requests
  server.handleClient();

  // Update Non-blocking alarm states (Buzzer & LED)
  updateAlarmHardware();

  // Safety Timeout: Auto-downgrade to LOW risk if no update received in 15 seconds
  if (currentRisk != "LOW" && (millis() - lastCommandTime > 15000)) {
    Serial.println("[TIMEOUT] Auto-clearing alarm to LOW risk after 15s inactivity.");
    currentRisk = "LOW";
    buzzerActive = false;
    ledActive = false;
    lastReason = "Alarm automatically cleared (timeout)";
  }
}
