"""
AgriEdge AI - Edge Vision & Crop Diagnostic Engine
Designed for ultra-low latency, 100% on-device edge inference in English.
Simulates MobileNetV4 / YOLOv8-Nano quantized (INT8) vision pipeline
tailored for Indian crops, diseases, pests, and nutrient stress.
"""

import math
import random
import time
from typing import Dict, Any, List, Optional

# Pre-indexed knowledge base of crop conditions (100% English)
CROP_DIAGNOSTIC_DB = {
    "sample_tomato_late_blight": {
        "id": "sample_tomato_late_blight",
        "crop": "Tomato",
        "condition": "Late Blight",
        "pathogen": "Phytophthora infestans (Oomycete)",
        "category": "Fungal/Oomycete Disease",
        "severity": "Severe",
        "stage": "Active Sporulation / Lesion Spread",
        "affected_area_pct": 34.5,
        "confidence": 97.2,
        "latency_ms": 38.4,
        "model_used": "MobileNetV4-Agri-INT8 (4.2 MB on Edge TPU)",
        "symptoms": [
            "Water-soaked irregular dark brown to purplish lesions on foliage",
            "White velvety fungal growth on undersides of leaves during high humidity",
            "Rapid stem collapse and brown firm rot on developing fruit"
        ],
        "organic_treatment": [
            "Spray 5% Neem Seed Kernel Extract (NSKE) or Copper Oxychloride @ 2.5g/L water.",
            "Apply Trichoderma viride or Bacillus subtilis bio-fungicide to soil.",
            "Prune lower infected leaves immediately and dispose away from field; do not compost."
        ],
        "targeted_chemical_treatment": [
            "Targeted spot-spray of Metalaxyl-M + Mancozeb (Ridomil Gold) @ 2g/L.",
            "Alternate with Cymoxanil + Mancozeb (Curzate) @ 2g/L to prevent pathogen resistance.",
            "Limit spraying strictly to affected micro-plots (zone B3) to cut chemical costs by 70%."
        ],
        "prevention_advisory": "Avoid overhead sprinkler irrigation. Ensure wide spacing (60x45cm) for air circulation. Mulch soil to prevent rain-splash spore transmission.",
        "translations": {
            "en": "Late Blight detected on Tomato. Immediate spot-spraying with Copper Oxychloride (2.5g/L) or Metalaxyl recommended. Prune lower diseased foliage and halt overhead watering to stop spore germination."
        }
    },
    "sample_wheat_yellow_rust": {
        "id": "sample_wheat_yellow_rust",
        "crop": "Wheat",
        "condition": "Yellow / Stripe Rust",
        "pathogen": "Puccinia striiformis f. sp. tritici",
        "category": "Fungal Rust",
        "severity": "Critical Early Warning",
        "stage": "Early Pustule Emergence (Foliar Stripes)",
        "affected_area_pct": 18.2,
        "confidence": 96.5,
        "latency_ms": 36.1,
        "model_used": "MobileNetV4-Agri-INT8 (4.2 MB on Edge TPU)",
        "symptoms": [
            "Bright yellow powder-filled pustules arranged in linear stripes along leaf veins",
            "Yellowing and premature drying of photosynthetic leaf blades",
            "Chalky yellow dust adhering to fingers when touching foliage"
        ],
        "organic_treatment": [
            "Apply prophylactic bio-formulation of Pseudomonas fluorescens @ 5g/L.",
            "Spray fermented bio-stimulant foliar spray diluted 1:10 with water."
        ],
        "targeted_chemical_treatment": [
            "Spot spray Propiconazole 25% EC (Tilt) @ 1ml per liter of water immediately.",
            "Alternatively spray Tebuconazole 25.9% EC @ 1.25ml/L at first appearance of striping.",
            "Target application at windward edge of field to block airborne spore dispersal."
        ],
        "prevention_advisory": "Plant resistant cultivars (e.g., HD-3086, DBW-187, PBW-725). Avoid excessive nitrogenous fertilizers (Urea) which promote soft succulent tissue vulnerable to rust.",
        "translations": {
            "en": "Yellow Rust (Stripe Rust) detected on Wheat. Immediate spot application of Propiconazole (Tilt @ 1ml/L) recommended along field borders to prevent regional airborne epidemic."
        }
    },
    "sample_rice_blast": {
        "id": "sample_rice_blast",
        "crop": "Rice / Paddy",
        "condition": "Rice Leaf Blast",
        "pathogen": "Magnaporthe oryzae",
        "category": "Fungal Disease",
        "severity": "Moderate",
        "stage": "Spindle-shaped Diamond Lesions",
        "affected_area_pct": 22.8,
        "confidence": 95.8,
        "latency_ms": 41.2,
        "model_used": "YOLOv8n-Agri (3.8 MB Quantized)",
        "symptoms": [
            "Spindle-shaped or diamond-shaped lesions with gray-white centers and dark brown reddish margins",
            "Lesions coalescing into larger blighted areas killing the leaf blade",
            "Neck rot risk if disease ascends to panicle during booting stage"
        ],
        "organic_treatment": [
            "Foliar spray with Pseudomonas fluorescens @ 10g/L or Neem oil 3000 ppm @ 3ml/L.",
            "Ensure silicon supplementation (potassium silicate @ 2g/L) to strengthen leaf cuticle."
        ],
        "targeted_chemical_treatment": [
            "Spray Tricyclazole 75% WP (Baan) @ 0.6g/L or Isoprothiolane 40% EC @ 1.5ml/L.",
            "Conduct drone or knapsack spraying early morning before dew dries completely."
        ],
        "prevention_advisory": "Split nitrogen fertilizer doses; avoid dumping urea in single basal dose. Drain excess standing water for 48 hours to aerate the root zone.",
        "translations": {
            "en": "Rice Leaf Blast detected. Apply Tricyclazole (0.6g/L) or Neem formulation. Avoid excessive urea application and temporarily drain excess standing water to aerate root zone."
        }
    },
    "sample_fall_armyworm": {
        "id": "sample_fall_armyworm",
        "crop": "Maize / Corn",
        "condition": "Fall Armyworm Infestation",
        "pathogen": "Spodoptera frugiperda (Insect Pest)",
        "category": "Invasive Pest Infestation",
        "severity": "High Alert",
        "stage": "2nd & 3rd Instar Larval Feeding in Whorl",
        "affected_area_pct": 27.6,
        "confidence": 98.4,
        "latency_ms": 34.2,
        "model_used": "YOLOv8n-Pest-Detection (4.1 MB INT8)",
        "symptoms": [
            "Pinholes and extensive window-pane ragged skeletonized feeding on whorl leaves",
            "Heavy accumulation of moist sawdust-like fecal frass deep inside central whorl",
            "Four distinct dark spots in a square on the 8th abdominal segment of larvae"
        ],
        "organic_treatment": [
            "Install Pheromone Traps @ 5 traps/acre for adult moth monitoring and mass disruption.",
            "Apply Metarhizium rileyi or Bacillus thuringiensis (Bt kurstaki) @ 2g/L.",
            "Apply sand mixed with lime or wood ash (9:1 ratio) directly into central plant whorls."
        ],
        "targeted_chemical_treatment": [
            "Whorl application of Emamectin Benzoate 5% SG @ 0.4g/L or Chlorantraniliprole 18.5% SC @ 0.3ml/L.",
            "Apply specifically into the central funnel/whorl of affected plants using targeted nozzle."
        ],
        "prevention_advisory": "Intercrop with pulses (Cowpea or Pigeon pea). Encourage predatory wasps and birds by setting bird perches (10 per acre).",
        "translations": {
            "en": "Fall Armyworm detected in Maize whorls. Insert sand/ash or spray Emamectin Benzoate (0.4g/L) directly into whorls. Install pheromone traps immediately to break reproduction cycle."
        }
    },
    "sample_cotton_whitefly": {
        "id": "sample_cotton_whitefly",
        "crop": "Cotton",
        "condition": "Whitefly & Leaf Curl Risk",
        "pathogen": "Bemisia tabaci (Insect Vector)",
        "category": "Sap-sucking Pest Vector",
        "severity": "Moderate to High",
        "stage": "Nymphal Colony & Sooty Mold Initiation",
        "affected_area_pct": 19.4,
        "confidence": 94.6,
        "latency_ms": 35.8,
        "model_used": "MobileNetV4-Agri-INT8 (4.2 MB on Edge TPU)",
        "symptoms": [
            "Clusters of tiny white-winged insects fluttering when plant is shaken",
            "Sticky honeydew secretions on upper leaf surfaces leading to black sooty mold",
            "Upward curling of leaf margins and thickened dark green vein network"
        ],
        "organic_treatment": [
            "Install Yellow Sticky Traps @ 8 to 10 traps per acre placed at crop canopy height.",
            "Foliar spray with 5% Neem Oil (Azadirachtin 1500 ppm) @ 5ml/L targeting leaf undersides.",
            "Conserve natural predators: Ladybird beetles, Chrysoperla carnea (Green lacewing)."
        ],
        "targeted_chemical_treatment": [
            "If above Economic Threshold Level (6-8 adults/leaf): Spray Diafenthiuron 50% WP @ 1.2g/L or Pyriproxyfen 10% EC @ 2ml/L.",
            "Avoid synthetic pyrethroids as they cause whitefly pest resurgence."
        ],
        "prevention_advisory": "Eradicate alternate weed hosts around borders. Maintain balanced NPK nutrition; avoid excess urea.",
        "translations": {
            "en": "Whitefly infestation detected on Cotton. Install yellow sticky traps (10/acre) and spray Neem oil (5ml/L). Whitefly carries the deadly Cotton Leaf Curl Virus vector."
        }
    },
    "sample_nitrogen_deficiency": {
        "id": "sample_nitrogen_deficiency",
        "crop": "Wheat / Maize",
        "condition": "Nitrogen (N) Deficiency",
        "pathogen": "Nutrient Imbalance / Soil Exhaustion",
        "category": "Nutrient Deficiency",
        "severity": "Moderate",
        "stage": "Generalized Chlorosis of Older Leaves",
        "affected_area_pct": 42.0,
        "confidence": 96.1,
        "latency_ms": 32.5,
        "model_used": "Edge-Colorimetric-Analyzer (1.2 MB)",
        "symptoms": [
            "V-shaped pale yellowing (chlorosis) progressing from leaf tips along midribs",
            "Older bottom leaves turn pale yellow first while younger leaves stay light green",
            "Stunted vegetative stature with thin, spindly stems and reduced tillering"
        ],
        "organic_treatment": [
            "Top-dress with well-decomposed Vermicompost @ 500 kg/acre or Mustard/Neem cake @ 100 kg/acre.",
            "Apply Azotobacter / Azospirillum biofertilizer mixed with compost at root zone."
        ],
        "targeted_chemical_treatment": [
            "Foliar spray of 2% Urea solution (20g Urea in 1 liter water) for rapid nitrogen uptake within 48h.",
            "Apply top-dressing of Neem-coated Urea @ 25-30 kg/acre just before light irrigation."
        ],
        "prevention_advisory": "Implement soil testing every 2 seasons. Practice green manuring with Sesbania or Sunn hemp during fallow window.",
        "translations": {
            "en": "Nitrogen deficiency detected. Older leaves exhibit V-shaped chlorosis. Apply 2% foliar Urea spray for rapid green recovery, followed by root-zone top-dressing."
        }
    },
    "sample_healthy_crop": {
        "id": "sample_healthy_crop",
        "crop": "Wheat / Tomato",
        "condition": "Healthy Canopy",
        "pathogen": "None (No Pathogen Detected)",
        "category": "Healthy Control",
        "severity": "Optimal",
        "stage": "Active Photosynthesis / Vigorous Growth",
        "affected_area_pct": 0.0,
        "confidence": 99.1,
        "latency_ms": 31.8,
        "model_used": "MobileNetV4-Agri-INT8 (4.2 MB)",
        "symptoms": [
            "Uniform deep green chlorophyll coloration across foliage",
            "Intact epidermal layer with no necrotic lesions, fungal spores, or insect chew holes",
            "Turgid erect leaf angles indicating optimal hydraulic pressure"
        ],
        "organic_treatment": [
            "Maintain current bi-weekly prophylactic organic bio-stimulant sprays.",
            "Continue regular monitoring via edge camera sensors."
        ],
        "targeted_chemical_treatment": [
            "Zero pesticide or fungicide intervention required. Total chemical cost savings: 100%."
        ],
        "prevention_advisory": "Maintain soil moisture between 65-75% field capacity. Avoid prophylactic chemical sprays to preserve beneficial predatory insects.",
        "translations": {
            "en": "Crop is healthy with optimal chlorophyll index. No chemical or fungal treatments required. Continue standard irrigation and organic bio-stimulant schedule."
        }
    }
}


class EdgeAIEngine:
    """Simulates on-device Edge AI diagnostic inference in English."""

    def __init__(self):
        self.sample_keys = list(CROP_DIAGNOSTIC_DB.keys())

    def get_all_samples(self) -> List[Dict[str, Any]]:
        """Returns metadata for all pre-indexed field samples for UI testing."""
        return [
            {
                "id": v["id"],
                "crop": v["crop"],
                "condition": v["condition"],
                "category": v["category"],
                "severity": v["severity"],
                "confidence": v["confidence"]
            }
            for v in CROP_DIAGNOSTIC_DB.values()
        ]

    def diagnose(self, sample_id: Optional[str] = None, image_filename: Optional[str] = None, image_bytes_len: int = 0) -> Dict[str, Any]:
        start_t = time.perf_counter()

        if sample_id and sample_id in CROP_DIAGNOSTIC_DB:
            result = dict(CROP_DIAGNOSTIC_DB[sample_id])
            elapsed = (time.perf_counter() - start_t) * 1000 + random.uniform(32.0, 44.0)
            result["latency_ms"] = round(elapsed, 1)
            result["source"] = "field_sample_library"
            return result

        salt = (image_bytes_len ^ len(image_filename or "")) % 100
        if salt < 20:
            target_key = "sample_tomato_late_blight"
        elif salt < 40:
            target_key = "sample_wheat_yellow_rust"
        elif salt < 60:
            target_key = "sample_fall_armyworm"
        elif salt < 75:
            target_key = "sample_rice_blast"
        elif salt < 90:
            target_key = "sample_nitrogen_deficiency"
        else:
            target_key = "sample_healthy_crop"

        base = dict(CROP_DIAGNOSTIC_DB[target_key])
        base["confidence"] = round(random.uniform(93.5, 98.8), 1)
        elapsed = (time.perf_counter() - start_t) * 1000 + random.uniform(34.0, 48.0)
        base["latency_ms"] = round(elapsed, 1)
        base["source"] = f"edge_vision_inference (file: {image_filename or 'camera_feed.jpg'})"
        base["bounding_box"] = {
            "x": round(random.uniform(15, 30), 1),
            "y": round(random.uniform(20, 35), 1),
            "width": round(random.uniform(40, 60), 1),
            "height": round(random.uniform(40, 55), 1),
            "label": base["condition"]
        }
        return base


# Singleton instance
edge_vision_engine = EdgeAIEngine()
