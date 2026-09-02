"""
AgriEdge AI - Smoke Test Suite
Uses Python standard library (asyncio) to test all route handlers and core engines
with zero external test dependencies.
"""

import sys
import asyncio

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from main import (
    app,
    diagnose_crop_image,
    analyze_irrigation,
    check_climate_risks,
    get_live_telemetry,
    get_hardware_specs,
    trigger_edge_sync,
    get_diagnostic_samples,
    IrrigationRequest,
    ClimateRequest,
    ingest_hardware_telemetry,
    HardwareTelemetryInput
)
from edge_ai_engine import edge_vision_engine
from irrigation_risk_engine import irrigation_engine

async def run_all_tests():
    print("--- Running AgriEdge AI Smoke Tests (Asyncio Native) ---")

    # 1. Test Edge Vision Engine
    samples = edge_vision_engine.get_all_samples()
    assert len(samples) >= 7, "Should have at least 7 sample cases"
    print(f"[PASS] Edge Vision Engine: {len(samples)} pre-indexed diagnostic cases loaded")

    # 2. Test Diagnosis Endpoint (Pre-indexed case)
    diag_res = await diagnose_crop_image(sample_id="sample_tomato_late_blight", file=None)
    assert diag_res["status"] == "success"
    diag = diag_res["diagnosis"]
    assert "Late Blight" in diag["condition"]
    assert diag["confidence"] > 90.0
    assert "en" in diag["translations"]
    assert diag["latency_ms"] < 100.0
    print(f"[PASS] Diagnostic route (Late Blight): {diag['condition']} (Conf: {diag['confidence']}%, Latency: {diag['latency_ms']}ms)")

    # 3. Test Diagnosis Endpoint (Uploaded image simulation)
    upload_res = await diagnose_crop_image(sample_id=None, file=None)
    assert upload_res["status"] == "success"
    print(f"[PASS] Dynamic image heuristic inference: {upload_res['diagnosis']['condition']}")

    # 4. Test Smart Irrigation Engine
    irrig_req = IrrigationRequest(
        soil_moisture_15cm=16.0,
        soil_moisture_30cm=20.0,
        temp_c=38.0,
        humidity_pct=30.0,
        rainfall_forecast_mm=0.0,
        soil_type="alluvial"
    )
    irrig_res = await analyze_irrigation(irrig_req)
    assert irrig_res["status"] == "success"
    ir_data = irrig_res["data"]
    assert ir_data["urgency"] == "danger" # Critical depletion
    assert ir_data["water_required_liters_per_ha"] > 0
    print(f"[PASS] Smart Irrigation decision: {ir_data['action_title']} ({ir_data['water_required_liters_per_ha']} L needed)")

    # 5. Test Climate Disaster Risks (Extreme Heatwave)
    clim_req = ClimateRequest(
        temp_c=44.0,
        humidity_pct=20.0,
        soil_moisture_15cm=14.0,
        rainfall_24h_mm=0.0,
        wind_kmh=20.0
    )
    clim_res = await check_climate_risks(clim_req)
    assert clim_res["status"] == "success"
    cl_data = clim_res["data"]
    assert cl_data["risks"]["heatwave"]["level"] == "CRITICAL"
    print(f"[PASS] Climate Risk engine: Heatwave level = {cl_data['risks']['heatwave']['level']}, Resilience = {cl_data['resilience_score']}/100")

    # 6. Test All Judging Scenarios
    scenarios = ["normal", "heatwave", "flood", "drought", "pest_spike"]
    for s in scenarios:
        res = await get_live_telemetry(scenario=s)
        assert res["status"] == "success"
        t = res["telemetry"]
        assert t["scenario"] == s
        assert "irrigation" in t
        assert "climate" in t
    print(f"[PASS] All {len(scenarios)} hackathon judging scenarios simulated successfully")

    # 7. Test Edge Hardware BOM Specs
    bom_res = await get_hardware_specs()
    assert bom_res["status"] == "success"
    assert bom_res["total_estimated_bom_inr"] <= 4500
    assert len(bom_res["components"]) == 6
    print(f"[PASS] Edge Hardware BOM verified: Rs. {bom_res['total_estimated_bom_inr']} (Budget < Rs. 4,500)")

    # 8. Test Offline Sync Queue
    sync_res = await trigger_edge_sync()
    assert sync_res["status"] == "success"
    print(f"[PASS] Edge Store-and-Forward sync simulated: {sync_res['message']}")

    # 9. Test Live Hardware Node Telemetry Ingestion
    hw_payload = HardwareTelemetryInput(
        device_id="ESP32_FIELD_PROBE_A",
        soil_moisture_15cm=15.2,
        soil_moisture_30cm=19.4,
        temp_c=36.5,
        humidity_pct=42.0,
        solar_battery_pct=91
    )
    hw_res = await ingest_hardware_telemetry(hw_payload)
    assert hw_res["status"] == "success"
    assert "recommended_action" in hw_res
    print(f"[PASS] Physical Hardware Ingestion: Received node {hw_res['device_id']} -> Relay Command: {hw_res['pump_relay_command']}")

    print("\n=======================================================")
    print("  ALL 8 AGRIEDGE AI SUBSYSTEMS VERIFIED & OPERATIONAL  ")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
