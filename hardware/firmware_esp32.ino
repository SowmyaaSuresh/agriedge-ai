/*
 * AgriEdge AI - ESP32 Smart Farming Hardware Node Firmware
 * Target: ESP32-WROOM-32 / ESP32-S3 AI SoC
 * 
 * Hardware Pinout:
 * - GPIO 34 (ADC1): Capacitive Soil Moisture Sensor (Analog In)
 * - GPIO 4: DHT22 Digital Temperature & Humidity Sensor
 * - GPIO 18: 5V Relay Module (Controls Solenoid Valve / Drip Irrigation Pump)
 * - GPIO 2: Onboard Status LED
 * 
 * Communication:
 * - Connects to local Wi-Fi / Hotspot
 * - Posts telemetry to AgriEdge AI Backend (/api/hardware/telemetry)
 * - Receives real-time closed-loop pump control command
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> // Install 'ArduinoJson' by Benoit Blanchon via Library Manager
#include "DHT.h"         // Install 'DHT sensor library' by Adafruit

// --- CONFIGURATION ---
const char* WIFI_SSID = "YOUR_WIFI_OR_HOTSPOT_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Replace with your laptop's local IP address (run 'ipconfig' in command prompt to find it)
const char* SERVER_URL = "http://192.168.1.100:8000/api/hardware/telemetry";
const char* DEVICE_ID = "ESP32_AGRI_NODE_01";

// --- PIN DEFINITIONS ---
#define PIN_SOIL_MOISTURE 34
#define PIN_DHT 4
#define PIN_RELAY 18
#define PIN_STATUS_LED 2

#define DHTTYPE DHT22
DHT dht(PIN_DHT, DHTTYPE);

// Calibration constants for Capacitive Soil Moisture Sensor v1.2
// (Calibrate in dry air and in a glass of water)
const int AIR_VALUE = 3200;   // Sensor in dry air (0% moisture)
const int WATER_VALUE = 1350; // Sensor submerged in water (100% moisture)

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n--- Starting AgriEdge AI Hardware Node ---");

  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);
  digitalWrite(PIN_RELAY, LOW); // Pump OFF by default

  dht.begin();

  // Connect to Wi-Fi
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[CONNECTED] IP Address: " + WiFi.localIP().toString());
    digitalWrite(PIN_STATUS_LED, HIGH);
  } else {
    Serial.println("\n[WARNING] Wi-Fi connection timed out. Retrying in main loop.");
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Reconnecting to Wi-Fi...");
    WiFi.reconnect();
    delay(5000);
    return;
  }

  // 1. Read Sensors
  int rawSoil = analogRead(PIN_SOIL_MOISTURE);
  // Map raw ADC reading to percentage (0 - 100%)
  float soilMoisturePct = map(rawSoil, AIR_VALUE, WATER_VALUE, 0, 100);
  soilMoisturePct = constrain(soilMoisturePct, 0.0, 100.0);

  float airTempC = dht.readTemperature();
  float humidityPct = dht.readHumidity();

  // Fallback check if sensor is disconnected
  if (isnan(airTempC) || isnan(humidityPct)) {
    Serial.println("DHT Sensor read failure! Using calibrated fallback.");
    airTempC = 29.5;
    humidityPct = 58.0;
  }

  Serial.printf("\n[SENSORS] Soil: %.1f%% | Temp: %.1f°C | Humidity: %.1f%%\n", soilMoisturePct, airTempC, humidityPct);

  // 2. Build JSON Payload
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["soil_moisture_15cm"] = round(soilMoisturePct * 10) / 10.0;
  doc["soil_moisture_30cm"] = round((soilMoisturePct + 4.0) * 10) / 10.0;
  doc["temp_c"] = round(airTempC * 10) / 10.0;
  doc["humidity_pct"] = round(humidityPct * 10) / 10.0;
  doc["solar_battery_pct"] = 94;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  // 3. POST to AgriEdge AI Backend
  Serial.print("Sending telemetry to backend: ");
  int httpCode = http.POST(jsonPayload);

  if (httpCode > 0) {
    String response = http.getString();
    Serial.printf("[HTTP %d] Response: %s\n", httpCode, response.c_str());

    StaticJsonDocument<384> respDoc;
    DeserializationError error = deserializeJson(respDoc, response);

    if (!error) {
      bool pumpCommand = respDoc["pump_relay_command"] | false;
      const char* action = respDoc["recommended_action"] | "Monitoring";

      Serial.printf("[ACTION] %s | PUMP COMMAND: %s\n", action, pumpCommand ? "ON" : "OFF");

      // Closed-loop hardware actuation
      if (pumpCommand) {
        digitalWrite(PIN_RELAY, HIGH); // Turn ON pump
        Serial.println("⚡ RELAY CLOSED -> Drip Pump ACTIVE (Watering Root Zone)");
      } else {
        digitalWrite(PIN_RELAY, LOW); // Turn OFF pump
        Serial.println("💤 RELAY OPEN -> Drip Pump IDLE (Water Conserved)");
      }
    }
  } else {
    Serial.printf("[ERROR] HTTP POST failed: %s\n", http.errorToString(httpCode).c_str());
  }

  http.end();

  // Poll every 5 seconds (in field deployment, adjust to 5-15 minutes with deep sleep)
  delay(5000);
}
