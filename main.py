"""
AgriEdge AI - Smart Farming Assistant Backend Application
FastAPI server providing edge diagnostic vision APIs, smart irrigation engine,
climate risk analysis, multilingual farmer advisory, and field telemetry.
"""

import os
import time
import random
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from edge_ai_engine import edge_vision_engine, CROP_DIAGNOSTIC_DB
from irrigation_risk_engine import irrigation_engine

app = FastAPI(
    title="AgriEdge AI - Field Deployable Smart Farming Assistant",
    description="Edge AI & IoT assistant for crop disease detection, smart irrigation, and climate resilience in India",
    version="1.0.0"
)

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# In-memory edge telemetry sync queue simulating offline store-and-forward
edge_sync_store = {
    "cached_records_count": 142,
    "last_sync_timestamp": "2026-09-02 18:30 IST",
    "connectivity_mode": "EDGE_LOCAL_OFFLINE",
    "mesh_nodes_active": 4
}


class IrrigationRequest(BaseModel):
    soil_moisture_15cm: float = 24.5
    soil_moisture_30cm: float = 28.0
    temp_c: float = 34.2
    humidity_pct: float = 48.0
    rainfall_forecast_mm: float = 0.0
    soil_type: str = "alluvial"
    crop_type: str = "Tomato / Wheat"


class ClimateRequest(BaseModel):
    temp_c: float = 34.2
    humidity_pct: float = 48.0
    soil_moisture_15cm: float = 24.5
    rainfall_24h_mm: float = 0.0
    wind_kmh: float = 11.5


class HardwareTelemetryInput(BaseModel):
    device_id: str = "ESP32_AGRI_NODE_01"
    soil_moisture_15cm: float
    soil_moisture_30cm: Optional[float] = None
    temp_c: float
    humidity_pct: float
    soil_temp_c: Optional[float] = None
    solar_battery_pct: Optional[int] = 94
    solar_charge_w: Optional[float] = 18.0
    rainfall_24h_mm: Optional[float] = 0.0
    wind_kmh: Optional[float] = 8.5


latest_hardware_telemetry: Optional[Dict[str, Any]] = None
hardware_relay_state: bool = False


@app.get("/")
async def serve_dashboard():
    """Renders the main Field Assistant Dashboard."""
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"), media_type="text/html")


@app.get("/api/diagnose/samples")
async def get_diagnostic_samples():
    """Returns the pre-indexed field crop samples."""
    return {"status": "success", "samples": edge_vision_engine.get_all_samples()}


@app.post("/api/diagnose/image")
async def diagnose_crop_image(
    sample_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Simulates on-device Edge Vision AI inference on uploaded leaf image or sample preset.
    Zero cloud connection needed; returns quantized latency and localized advisory.
    """
    file_bytes_len = 0
    filename = None
    if file:
        content = await file.read()
        file_bytes_len = len(content)
        filename = file.filename

    diagnosis = edge_vision_engine.diagnose(
        sample_id=sample_id,
        image_filename=filename,
        image_bytes_len=file_bytes_len
    )
    return {"status": "success", "diagnosis": diagnosis}


@app.post("/api/irrigation/analyze")
async def analyze_irrigation(req: IrrigationRequest):
    """Evaluates soil water depletion and provides binary irrigation recommendations."""
    result = irrigation_engine.analyze_irrigation(
        soil_moisture_15cm=req.soil_moisture_15cm,
        soil_moisture_30cm=req.soil_moisture_30cm,
        temp_c=req.temp_c,
        humidity_pct=req.humidity_pct,
        rainfall_forecast_mm=req.rainfall_forecast_mm,
        soil_type=req.soil_type,
        crop_type=req.crop_type
    )
    return {"status": "success", "data": result}


@app.post("/api/climate/risks")
async def check_climate_risks(req: ClimateRequest):
    """Assesses early warning threats for heatwaves, floods, droughts, and pest swarms."""
    result = irrigation_engine.evaluate_climate_risks(
        temp_c=req.temp_c,
        humidity_pct=req.humidity_pct,
        soil_moisture_15cm=req.soil_moisture_15cm,
        rainfall_24h_mm=req.rainfall_24h_mm,
        wind_kmh=req.wind_kmh
    )
    return {"status": "success", "data": result}


@app.post("/api/hardware/telemetry")
async def ingest_hardware_telemetry(data: HardwareTelemetryInput):
    """
    Accepts real-time physical sensor readings from hardware:
    ESP32, Raspberry Pi, Arduino, or Serial Bridge.
    Computes agronomic decisions and returns real-time closed-loop pump command.
    """
    global latest_hardware_telemetry
    m30 = data.soil_moisture_30cm if data.soil_moisture_30cm is not None else round(data.soil_moisture_15cm + 3.5, 1)
    stemp = data.soil_temp_c if data.soil_temp_c is not None else round(data.temp_c - 4.5, 1)

    telemetry = {
        "scenario": "hardware",
        "device_id": data.device_id,
        "solar_battery_pct": data.solar_battery_pct or 94,
        "solar_charge_w": data.solar_charge_w or 18.0,
        "lora_rssi_dbm": -64,
        "edge_npu_temp_c": 39.5,
        "gateway_status": f"ONLINE (Physical Hardware Node: {data.device_id})",
        "cached_logs": 0,
        "temp_c": data.temp_c,
        "soil_temp_c": stemp,
        "humidity_pct": data.humidity_pct,
        "soil_moisture_15cm": data.soil_moisture_15cm,
        "soil_moisture_30cm": m30,
        "solar_radiation_wm2": 650.0,
        "rainfall_24h_mm": data.rainfall_24h_mm or 0.0,
        "rainfall_forecast_mm": 0.0,
        "wind_kmh": data.wind_kmh or 8.5,
        "description": f"LIVE Physical Sensor Feed ({data.device_id})"
    }

    irrig_eval = irrigation_engine.analyze_irrigation(
        soil_moisture_15cm=telemetry["soil_moisture_15cm"],
        soil_moisture_30cm=telemetry["soil_moisture_30cm"],
        temp_c=telemetry["temp_c"],
        humidity_pct=telemetry["humidity_pct"],
        rainfall_forecast_mm=0.0
    )
    climate_eval = irrigation_engine.evaluate_climate_risks(
        temp_c=telemetry["temp_c"],
        humidity_pct=telemetry["humidity_pct"],
        soil_moisture_15cm=telemetry["soil_moisture_15cm"],
        rainfall_24h_mm=telemetry["rainfall_24h_mm"],
        wind_kmh=telemetry["wind_kmh"]
    )

    telemetry["irrigation"] = irrig_eval
    telemetry["climate"] = climate_eval
    latest_hardware_telemetry = telemetry

    # Automated closed-loop pump control if needed
    auto_pump = (irrig_eval["action"] == "IRRIGATE_NOW_CRITICAL")

    return {
        "status": "success",
        "device_id": data.device_id,
        "recommended_action": irrig_eval["action_title"],
        "pump_relay_command": auto_pump or hardware_relay_state,
        "resilience_score": climate_eval["resilience_score"]
    }


@app.get("/api/hardware/relay_state")
async def get_hardware_relay_state():
    """Polled by microcontrollers (ESP32/Arduino) to set physical GPIO relay pin state."""
    return {
        "status": "success",
        "pump_relay": hardware_relay_state,
        "timestamp": time.time()
    }


@app.post("/api/hardware/relay")
async def set_hardware_relay(command: Dict[str, bool]):
    """Allows UI or automated logic to turn physical water pump relay ON or OFF."""
    global hardware_relay_state
    hardware_relay_state = command.get("pump_on", False)
    return {"status": "success", "pump_relay": hardware_relay_state}


@app.get("/api/telemetry/live")
async def get_live_telemetry(scenario: str = "normal"):
    """
    Provides real-time IoT sensor telemetry stream with instant preset scenario toggles:
    - hardware: Streams real physical sensor readings if hardware is connected!
    - normal: Balanced conditions
    - heatwave: 43.5°C thermal stress
    - flood: 85mm heavy monsoon downpour
    - drought: 14% critical moisture deficit
    - pest_spike: 29°C + 90% humidity fungal explosion
    """
    if scenario in ("hardware", "live_hardware") or (scenario == "normal" and latest_hardware_telemetry is not None):
        if latest_hardware_telemetry is not None:
            return {"status": "success", "telemetry": latest_hardware_telemetry}

    base = {
        "scenario": scenario,
        "solar_battery_pct": 94,
        "solar_charge_w": 18.4,
        "lora_rssi_dbm": -68,
        "edge_npu_temp_c": 41.2,
        "gateway_status": "ONLINE (OFFLINE-FIRST EDGE BUS)",
        "cached_logs": edge_sync_store["cached_records_count"]
    }

    if scenario == "heatwave":
        base.update({
            "temp_c": 43.8,
            "soil_temp_c": 36.4,
            "humidity_pct": 21.0,
            "soil_moisture_15cm": 22.0,
            "soil_moisture_30cm": 26.5,
            "solar_radiation_wm2": 960.0,
            "rainfall_24h_mm": 0.0,
            "rainfall_forecast_mm": 0.0,
            "wind_kmh": 18.5,
            "description": "Simulated Severe North-Western Heatwave"
        })
    elif scenario == "flood":
        base.update({
            "temp_c": 26.4,
            "soil_temp_c": 24.2,
            "humidity_pct": 96.0,
            "soil_moisture_15cm": 46.8,
            "soil_moisture_30cm": 47.5,
            "solar_radiation_wm2": 210.0,
            "rainfall_24h_mm": 84.5,
            "rainfall_forecast_mm": 45.0,
            "wind_kmh": 26.0,
            "description": "Simulated Monsoon Cloudburst & Waterlogging"
        })
    elif scenario == "drought":
        base.update({
            "temp_c": 38.5,
            "soil_temp_c": 34.0,
            "humidity_pct": 28.0,
            "soil_moisture_15cm": 13.8,
            "soil_moisture_30cm": 17.2,
            "solar_radiation_wm2": 880.0,
            "rainfall_24h_mm": 0.0,
            "rainfall_forecast_mm": 0.0,
            "wind_kmh": 12.0,
            "description": "Simulated Extended Dry Spell & Critical Drought"
        })
    elif scenario == "pest_spike":
        base.update({
            "temp_c": 29.5,
            "soil_temp_c": 27.0,
            "humidity_pct": 89.0,
            "soil_moisture_15cm": 31.0,
            "soil_moisture_30cm": 32.5,
            "solar_radiation_wm2": 520.0,
            "rainfall_24h_mm": 12.0,
            "rainfall_forecast_mm": 8.0,
            "wind_kmh": 6.5,
            "description": "Simulated High Spore Germination & Pest Outbreak Vector"
        })
    else:  # normal
        base.update({
            "temp_c": 31.2 + round(random.uniform(-0.5, 0.5), 1),
            "soil_temp_c": 26.8,
            "humidity_pct": 58.0 + round(random.uniform(-2.0, 2.0), 1),
            "soil_moisture_15cm": 29.5 + round(random.uniform(-0.8, 0.8), 1),
            "soil_moisture_30cm": 33.0,
            "solar_radiation_wm2": 670.0,
            "rainfall_24h_mm": 0.0,
            "rainfall_forecast_mm": 2.0,
            "wind_kmh": 9.5,
            "description": "Normal Optimal Field Conditions"
        })

    # Recalculate automatic irrigation and climate evaluations for this telemetry frame
    irrig_eval = irrigation_engine.analyze_irrigation(
        soil_moisture_15cm=base["soil_moisture_15cm"],
        soil_moisture_30cm=base["soil_moisture_30cm"],
        temp_c=base["temp_c"],
        humidity_pct=base["humidity_pct"],
        rainfall_forecast_mm=base["rainfall_forecast_mm"]
    )
    climate_eval = irrigation_engine.evaluate_climate_risks(
        temp_c=base["temp_c"],
        humidity_pct=base["humidity_pct"],
        soil_moisture_15cm=base["soil_moisture_15cm"],
        rainfall_24h_mm=base["rainfall_24h_mm"],
        wind_kmh=base["wind_kmh"]
    )

    base["irrigation"] = irrig_eval
    base["climate"] = climate_eval

    return {"status": "success", "telemetry": base}


@app.get("/api/hardware/specs")
async def get_hardware_specs():
    """Returns field edge gateway specs and low-cost Bill of Materials (BOM) under ₹4,500."""
    return {
        "status": "success",
        "gateway_title": "KisanDrishti Solar-Powered Edge IoT Gateway",
        "total_estimated_bom_inr": 4250,
        "currency": "INR (₹)",
        "operating_mode": "100% Offline with intermittent GSM/LoRa mesh sync",
        "power_autonomy": "Continuous solar harvest + 120-hour backup on cloudy days",
        "components": [
            {
                "name": "Edge Compute Core (ESP32-S3 Dual-Core AI SoC or Raspberry Pi Zero 2W)",
                "spec": "240 MHz Xtensa LX7, 8MB PSRAM, Vector AI Instructions / Quad-core 64-bit ARM",
                "cost_inr": 1150,
                "role": "Local model inference, sensor polling, flash storage & LoRa coordination"
            },
            {
                "name": "Edge Vision Camera Module (OV2640 / OV5640 5MP)",
                "spec": "1600x1200 resolution with 120° wide-angle lens, night IR illumination",
                "cost_inr": 450,
                "role": "Canopy and leaf macro-photography for on-device disease & pest vision"
            },
            {
                "name": "Soil Dual-Depth Capacitive Moisture Sensors (15cm & 30cm)",
                "spec": "Corrosion-resistant capacitive frequency measurement (analog output)",
                "cost_inr": 380,
                "role": "Root zone water depletion & hydraulic gradient tracking"
            },
            {
                "name": "Weather Station Sensors (SHT31 + DS18B20 + Rain Guage)",
                "spec": "Industrial temperature (±0.2°C), relative humidity (±2%), soil temp probe",
                "cost_inr": 420,
                "role": "Microclimate parameters for Evapotranspiration (ET0) and disease vectors"
            },
            {
                "name": "Long-Range Mesh Radio (SX1262 LoRa 868 MHz Transceiver)",
                "spec": "+22 dBm power, -148 dBm sensitivity, up to 12 km rural range line-of-sight",
                "cost_inr": 550,
                "role": "Zero-cost farm-to-house communication without cellular SIM card"
            },
            {
                "name": "Solar Harvesting & Battery Subsystem",
                "spec": "15W Monocrystalline PV Panel + MPPT BMS + 12V 6000mAh LiFePO4 battery pack",
                "cost_inr": 1300,
                "role": "Perpetual energy self-sufficiency in remote fields without grid electricity"
            }
        ],
        "edge_advantages": [
            "No monthly 4G/5G SIM card charges needed for basic operation",
            "Operates during cellular tower outages or monsoonal power cuts",
            "Millisecond response time for pump relay triggers",
            "Zero privacy issues regarding farm location and yield telemetry"
        ]
    }


@app.post("/api/sync/queue")
async def trigger_edge_sync():
    """Simulates edge store-and-forward synchronizing cached offline logs when back online."""
    synced = edge_sync_store["cached_records_count"]
    edge_sync_store["cached_records_count"] = 0
    edge_sync_store["last_sync_timestamp"] = "Just now (Synced to Central Agri Portal)"
    return {
        "status": "success",
        "synced_records": synced,
        "message": f"Successfully synced {synced} historical telemetry packets to cloud registry."
    }
