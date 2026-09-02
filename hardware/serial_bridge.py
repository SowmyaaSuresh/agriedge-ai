"""
AgriEdge AI - USB Serial Hardware Bridge
Reads real sensor data from Arduino/ESP32 plugged via USB cable (COM port)
and forwards it directly to the local AgriEdge AI dashboard in real-time.

Zero Wi-Fi setup needed! Ideal for hackathon demo tables.
"""

import sys
import time
import json
import urllib.request
import urllib.error

# Config
BACKEND_URL = "http://127.0.0.1:8000/api/hardware/telemetry"
BAUD_RATE = 115200

def post_telemetry(payload: dict):
    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            BACKEND_URL,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            print(f"[LIVE BACKEND RESPONSE] Action: {resp_data.get('recommended_action')} | Pump Relay: {resp_data.get('pump_relay_command')}")
    except Exception as e:
        print(f"[SYNC ERROR] Could not reach backend: {e}")

def run_simulation_stream():
    """Fallback generator if no physical COM port is plugged in."""
    print("\n--- Running Serial Bridge in Demo Mode (Simulating Hardware Serial Packets) ---")
    print("If you have an ESP32 or Arduino, plug it in via USB and specify the COM port.")
    print("Example: python serial_bridge.py COM3\n")

    soil = 28.5
    temp = 32.0
    hum = 55.0

    while True:
        payload = {
            "device_id": "ESP32_USB_SERIAL_NODE",
            "soil_moisture_15cm": round(soil, 1),
            "soil_moisture_30cm": round(soil + 3.2, 1),
            "temp_c": round(temp, 1),
            "humidity_pct": round(hum, 1),
            "solar_battery_pct": 95
        }
        print(f"[SERIAL TX] Soil: {soil:.1f}% | Temp: {temp:.1f}°C | Hum: {hum:.1f}%")
        post_telemetry(payload)
        time.sleep(4)

def run_serial_listener(port_name: str):
    try:
        import serial  # pyserial
    except ImportError:
        print("Please install pyserial: pip install pyserial")
        return

    print(f"Connecting to hardware on {port_name} @ {BAUD_RATE} baud...")
    ser = serial.Serial(port_name, BAUD_RATE, timeout=1.0)
    time.sleep(2.0)
    print(f"Connected to {port_name}! Listening for real sensor frames...")

    while True:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line:
            continue

        # Check if line is JSON
        if line.startswith("{") and line.endswith("}"):
            try:
                data = json.loads(line)
                post_telemetry(data)
            except json.JSONDecodeError:
                pass
        # Or key-value format: SOIL:24.5,TEMP:31.2,HUM:54.0
        elif "SOIL:" in line or "TEMP:" in line:
            try:
                parts = dict(item.split(":") for item in line.split(",") if ":" in item)
                payload = {
                    "device_id": "USB_HARDWARE_NODE",
                    "soil_moisture_15cm": float(parts.get("SOIL", 25.0)),
                    "temp_c": float(parts.get("TEMP", 30.0)),
                    "humidity_pct": float(parts.get("HUM", 50.0))
                }
                post_telemetry(payload)
            except Exception as e:
                print(f"Failed to parse line '{line}': {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_serial_listener(sys.argv[1])
    else:
        run_simulation_stream()
