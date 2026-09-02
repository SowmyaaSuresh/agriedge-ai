# AgriEdge AI - Physical Hardware Wiring & Setup Guide

This guide details how to connect real physical sensors, microcontrollers (ESP32 / Arduino / Raspberry Pi), and relays directly to your **AgriEdge AI** dashboard.

---

## 🔌 1. Recommended Hardware Setup (< ₹1,500 for prototype)

| Component | Recommended Model | Approx Cost (India) |
|---|---|---|
| **Microcontroller** | ESP32-WROOM-32 / ESP32-S3 | ₹450 |
| **Soil Moisture Sensor** | Capacitive Soil Moisture Sensor v1.2 (Corrosion-resistant) | ₹90 |
| **Temperature & Humidity** | DHT22 (AM2302) or SHT31 | ₹180 |
| **Water Pump Actuator** | 5V 1-Channel Relay Module | ₹65 |
| **Drip Irrigation Mockup** | 5V / 12V Mini Submersible Pump + 8mm Tube | ₹140 |
| **Optional Edge Camera** | ESP32-CAM or USB Webcam | ₹450 |

---

## ⚡ 2. Exact Pin Connections (ESP32 Pinout)

### A. Capacitive Soil Moisture Sensor v1.2
- **VCC** $\rightarrow$ ESP32 **3.3V** (or 5V depending on board)
- **GND** $\rightarrow$ ESP32 **GND**
- **AOUT (Signal)** $\rightarrow$ ESP32 **GPIO 34** (ADC1 Channel 6)

### B. DHT22 Temperature & Humidity Sensor
- **Pin 1 (VCC)** $\rightarrow$ ESP32 **3.3V**
- **Pin 2 (DATA)** $\rightarrow$ ESP32 **GPIO 4** *(add a 10kΩ pull-up resistor to 3.3V if not using breakout module)*
- **Pin 4 (GND)** $\rightarrow$ ESP32 **GND**

### C. 5V Relay Module (Controls Water Pump / Solenoid Valve)
- **VCC** $\rightarrow$ ESP32 **5V (VIN)**
- **GND** $\rightarrow$ ESP32 **GND**
- **IN (Signal)** $\rightarrow$ ESP32 **GPIO 18**
- **Relay COM & NO** $\rightarrow$ Wired in series with your pump's power supply.

---

## 🚀 3. Two Ways to Connect to the Dashboard

### Method 1: Direct USB Cable (Fastest & Best for Hackathon Demo Tables)
No Wi-Fi password needed! Zero router issues:
1. Flash your Arduino or ESP32 to print sensor values over Serial:
   `SOIL:24.5,TEMP:32.1,HUM:55.0`
2. Plug the board into your laptop via USB cable (e.g., `COM3`).
3. Run our pre-built bridge script:
   ```bash
   python hardware/serial_bridge.py COM3
   ```
4. The script continuously reads the USB port and pushes real-time telemetry straight into the AgriEdge AI dashboard on `http://127.0.0.1:8000`!

---

### Method 2: Wi-Fi HTTP Client (Wireless Field Station)
1. Open [hardware/firmware_esp32.ino](file:///C:/Users/HP/.gemini/antigravity/scratch/agri_edge_assistant/hardware/firmware_esp32.ino) in the Arduino IDE.
2. In the code, set your Wi-Fi details and laptop IP:
   ```cpp
   const char* WIFI_SSID = "MyPhoneHotspot";
   const char* WIFI_PASSWORD = "password123";
   const char* SERVER_URL = "http://192.168.1.50:8000/api/hardware/telemetry";
   ```
3. Upload to the ESP32.
4. The ESP32 will read sensors every 5 seconds, post JSON to your laptop, and automatically trigger the relay to turn the water pump ON when critical drought/wilting stress is detected!

---

## 📷 4. Edge Camera for Crop Disease Diagnosis
If you connect an **ESP32-CAM** or a standard **USB Webcam**:
- An ESP32-CAM captures a leaf image and sends a standard `POST` request to `http://127.0.0.1:8000/api/diagnose/image`.
- The dashboard receives the image, runs the INT8 model in 38ms, and sends back the disease diagnosis, confidence score, and targeted treatment plan.
