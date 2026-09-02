"""
AgriEdge AI - Smart Irrigation & Climate Disaster Risk Engine
Agronomic modeling tailored for smallholder farming resilience.
Calculates Evapotranspiration (ET0), Soil Water Depletion, and Early Warnings for
Heatwaves, Flash Floods, Droughts, and Pest Outbreaks (100% English).
"""

import math
from typing import Dict, Any, List


class IrrigationRiskEngine:
    """Computes agronomic water balance and multi-hazard climate risk indices."""

    def __init__(self):
        # Soil reference characteristics (Alluvial / Black Cotton / Sandy Loam)
        self.soil_specs = {
            "alluvial": {"name": "Alluvial Loam", "fc": 32.0, "pwp": 14.0, "saturation": 48.0},
            "black_cotton": {"name": "Black Cotton Soil", "fc": 38.0, "pwp": 18.0, "saturation": 54.0},
            "sandy_loam": {"name": "Sandy Loam", "fc": 24.0, "pwp": 9.0, "saturation": 38.0}
        }

    def calculate_et0(self, temp_c: float, humidity_pct: float, solar_radiation_wm2: float = 650.0, wind_kmh: float = 8.5) -> float:
        es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
        ea = es * (humidity_pct / 100.0)
        vpd = max(0.05, es - ea)
        r_net = max(1.0, solar_radiation_wm2 * 0.0035)
        wind_term = 1.0 + (0.34 * (wind_kmh / 3.6))
        et0 = (0.408 * 0.4 * r_net) + (0.24 * wind_term * vpd)
        return round(max(1.5, min(12.0, et0)), 2)

    def analyze_irrigation(
        self,
        soil_moisture_15cm: float,
        soil_moisture_30cm: float,
        temp_c: float,
        humidity_pct: float,
        rainfall_forecast_mm: float = 0.0,
        soil_type: str = "alluvial",
        crop_type: str = "Tomato / Wheat",
        kc_factor: float = 1.05
    ) -> Dict[str, Any]:
        spec = self.soil_specs.get(soil_type, self.soil_specs["alluvial"])
        fc = spec["fc"]
        pwp = spec["pwp"]
        saturation = spec["saturation"]

        root_moisture = (0.4 * soil_moisture_15cm) + (0.6 * soil_moisture_30cm)
        awc_total = max(1.0, fc - pwp)
        current_awc_pct = max(0.0, min(100.0, ((root_moisture - pwp) / awc_total) * 100.0))

        et0 = self.calculate_et0(temp_c, humidity_pct)
        etc = round(et0 * kc_factor, 2)

        if root_moisture >= (saturation - 2.0):
            action = "HALT_IRRIGATE_WATERLOGGED"
            action_title = "Waterlogging Danger - DO NOT IRRIGATE"
            urgency = "warning"
            reason = f"Soil moisture ({round(root_moisture, 1)}%) exceeds saturation limit. Root zone is hypoxic, risking fungal root rot (Pythium/Phytophthora)."
            liters_needed = 0
            pump_hours = 0.0
            window = "No irrigation for next 48-72 hours. Check and clear drainage channels."
            water_saved_l = round(etc * 10000, 0)

        elif rainfall_forecast_mm >= 15.0:
            action = "DELAY_RAIN_COMING"
            action_title = "Delay Irrigation - Rain Expected"
            urgency = "info"
            reason = f"{rainfall_forecast_mm} mm rainfall forecasted in the next 24 hours. Natural rain will replenish soil without electrical pump cost."
            liters_needed = 0
            pump_hours = 0.0
            window = "Hold irrigation until after rainfall event; re-check sensor telemetry tomorrow."
            water_saved_l = round(etc * 10000, 0)

        elif current_awc_pct < 40.0 or root_moisture <= (pwp + 3.0):
            action = "IRRIGATE_NOW_CRITICAL"
            action_title = "Irrigate Now - Critical Root Zone Stress"
            urgency = "danger"
            reason = f"Soil moisture at root depth is down to {round(root_moisture, 1)}% ({round(current_awc_pct, 1)}% of available water). Plant is approaching permanent wilting point."
            mm_deficit = max(5.0, (fc * 0.85 - root_moisture) * 1.8)
            liters_needed = int(mm_deficit * 10000)
            pump_hours = round(liters_needed / 25000.0, 1)
            window = "Best window: 5:00 AM - 7:30 AM (or after 6:00 PM) to minimize evaporative loss."
            water_saved_l = round(liters_needed * 0.35, 0)

        elif current_awc_pct < 60.0:
            action = "PLAN_LIGHT_IRRIGATION"
            action_title = "Optimal Timing - Schedule Light Drip Irrigation"
            urgency = "caution"
            reason = f"Soil moisture is at {round(root_moisture, 1)}% ({round(current_awc_pct, 1)}% AWC). Drip cycle recommended within 18 hours to maintain active fruit/grain filling."
            mm_deficit = 8.0
            liters_needed = int(mm_deficit * 10000)
            pump_hours = round(liters_needed / 25000.0, 1)
            window = "Tomorrow early morning (6:00 AM - 7:30 AM)."
            water_saved_l = round(liters_needed * 0.4, 0)

        else:
            action = "SOIL_OPTIMAL"
            action_title = "Adequate Moisture - No Irrigation Needed"
            urgency = "success"
            reason = f"Soil moisture is at optimal {round(root_moisture, 1)}% ({round(current_awc_pct, 1)}% AWC). Crops have sufficient hydraulic buffer for the next 24-36 hours."
            liters_needed = 0
            pump_hours = 0.0
            window = "System in autonomous monitoring mode. Next evaluation in 4 hours."
            water_saved_l = round(etc * 10000, 0)

        return {
            "action": action,
            "action_title": action_title,
            "urgency": urgency,
            "reason": reason,
            "root_moisture_pct": round(root_moisture, 1),
            "current_awc_pct": round(current_awc_pct, 1),
            "et0_mm_day": et0,
            "crop_water_demand_mm": etc,
            "water_required_liters_per_ha": liters_needed,
            "recommended_pump_hours": pump_hours,
            "optimal_window": window,
            "estimated_water_saved_liters": int(water_saved_l),
            "soil_type_used": spec["name"]
        }

    def evaluate_climate_risks(
        self,
        temp_c: float,
        humidity_pct: float,
        soil_moisture_15cm: float,
        rainfall_24h_mm: float,
        wind_kmh: float = 12.0
    ) -> Dict[str, Any]:
        es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
        ea = es * (humidity_pct / 100.0)
        vpd = max(0.05, es - ea)

        # 1. Heatwave Index
        if temp_c >= 42.0 or (temp_c >= 39.0 and vpd > 3.0):
            heat_level = "CRITICAL"
            heat_score = 92
            heat_advisory = "SEVERE HEATWAVE ALERT: Atmospheric demand exceeds plant vascular transport. Flower dropping and pollens drying up. Run micro-sprinklers for 20 mins at 1:00 PM for canopy cooling."
        elif temp_c >= 37.0:
            heat_level = "MODERATE"
            heat_score = 65
            heat_advisory = "MILD HEAT STRESS: Transpiration rate is elevated. Ensure soil moisture does not fall below 45% to prevent leaf scorching."
        else:
            heat_level = "LOW"
            heat_score = 20
            heat_advisory = "Thermal conditions are within normal physiological bounds for crop photosynthesis."

        # 2. Flash Flood / Waterlogging Risk
        if rainfall_24h_mm >= 65.0 or (soil_moisture_15cm >= 44.0 and rainfall_24h_mm >= 30.0):
            flood_level = "HIGH"
            flood_score = 88
            flood_advisory = "EXCESS RAIN / FLOOD ALERT: High risk of prolonged root submergence. Open tertiary drainage trenches, postpone all fertilizer/urea applications to prevent leaching."
        elif rainfall_24h_mm >= 35.0:
            flood_level = "MODERATE"
            flood_score = 52
            flood_advisory = "ELEVATED WATER ACCUMULATION: Monitor low-lying field parcels. Halt all mechanical tillage to prevent soil compaction."
        else:
            flood_level = "LOW"
            flood_score = 15
            flood_advisory = "Field drainage index is stable. No waterlogging detected."

        # 3. Drought & Dry Spell Index
        if soil_moisture_15cm <= 15.0 and rainfall_24h_mm < 1.0:
            drought_level = "CRITICAL"
            drought_score = 85
            drought_advisory = "ACUTE DROUGHT STRESS: Root moisture in deficit zone. Apply straw/dry grass mulch (5-7 cm) to curb soil evaporation. Schedule life-saving pulse drip irrigation."
        elif soil_moisture_15cm <= 22.0:
            drought_level = "MODERATE"
            drought_score = 55
            drought_advisory = "DRYING TREND: Soil water reserves depleting. Minimize intercultural operations to retain moisture."
        else:
            drought_level = "LOW"
            drought_score = 18
            drought_advisory = "Adequate soil water storage available."

        # 4. Fungal / Pest Outbreak Vector
        if (23.0 <= temp_c <= 32.0) and humidity_pct >= 82.0:
            pest_vector_level = "HIGH"
            pest_score = 84
            pest_advisory = "SPORE GERMINATION & PEST VECTOR SURGE: Micro-climate highly favorable for Rice Blast, Late Blight, and Aphid colonies. Conduct immediate prophylactic bio-fungicide spray."
        elif humidity_pct >= 75.0 and (22.0 <= temp_c <= 34.0):
            pest_vector_level = "MODERATE"
            pest_score = 58
            pest_advisory = "FAVORABLE INFESTATION CONDITIONS: Inspect leaf undersides daily for fungal spots and sap-sucking nymphs."
        else:
            pest_vector_level = "LOW"
            pest_score = 22
            pest_advisory = "Weather vector unfavorable for rapid fungal sporulation."

        max_threat = max(heat_score, flood_score, drought_score, pest_score)
        resilience_score = max(10, 100 - max_threat)

        return {
            "resilience_score": resilience_score,
            "vpd_kpa": round(vpd, 2),
            "risks": {
                "heatwave": {
                    "level": heat_level,
                    "score": heat_score,
                    "title": "Heatwave & Thermal Stress",
                    "advisory": heat_advisory
                },
                "flood": {
                    "level": flood_level,
                    "score": flood_score,
                    "title": "Flood & Waterlogging",
                    "advisory": flood_advisory
                },
                "drought": {
                    "level": drought_level,
                    "score": drought_score,
                    "title": "Drought & Moisture Deficit",
                    "advisory": drought_advisory
                },
                "pest_vector": {
                    "level": pest_vector_level,
                    "score": pest_score,
                    "title": "Pest & Disease Outbreak Index",
                    "advisory": pest_advisory
                }
            }
        }


# Singleton instance
irrigation_engine = IrrigationRiskEngine()
