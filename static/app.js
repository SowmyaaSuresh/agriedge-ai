/**
 * AgriEdge AI - KisanDrishti Frontend Client Application
 * Handles on-device edge simulation, Web Speech voice synthesis,
 * 24h sensor canvas graphing, and scenario toggling.
 */

// Global State
let currentLanguage = 'en';
let currentDiagnosisData = null;
let currentTelemetryData = null;
let isAudioPlaying = false;
let highContrastMode = false;

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  // Load default normal scenario
  loadScenario('normal');

  // Load initial tomato late blight sample
  diagnoseSample('sample_tomato_late_blight');

  // Draw initial canvas chart
  renderTelemetryChart();

  // Resize listener for responsive canvas
  window.addEventListener('resize', renderTelemetryChart);
});

// ==================== TAB SWITCHING ====================
function switchTab(tabKey) {
  const tabs = ['vision', 'irrigation', 'climate', 'voice', 'analytics', 'hardware'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const content = document.getElementById(`tab-${t}`);
    if (t === tabKey) {
      if (btn) btn.classList.add('active');
      if (content) content.classList.add('active');
    } else {
      if (btn) btn.classList.remove('active');
      if (content) content.classList.remove('active');
    }
  });

  if (tabKey === 'analytics') {
    setTimeout(renderTelemetryChart, 50);
  }
}

// ==================== SUNLIGHT CONTRAST MODE ====================
function toggleHighContrast() {
  highContrastMode = !highContrastMode;
  document.body.classList.toggle('sunlight-mode', highContrastMode);
  const btn = document.getElementById('contrast-toggle');
  if (btn) {
    btn.textContent = highContrastMode ? '🌙 Dark Mode' : '☀️ Sun Mode';
  }
  renderTelemetryChart();
}

// ==================== LANGUAGE SELECTOR ====================
function changeLanguage(langCode) {
  currentLanguage = langCode;
  const langDisplay = document.getElementById('current-lang-code');
  if (langDisplay) langDisplay.textContent = langCode.toUpperCase();

  // Update diagnostic vernacular text if available
  if (currentDiagnosisData && currentDiagnosisData.translations) {
    const text = currentDiagnosisData.translations[langCode] || currentDiagnosisData.translations['en'];
    const vernEl = document.getElementById('diag-vernacular-text');
    if (vernEl) vernEl.textContent = text;

    const scriptBox = document.getElementById('full-voice-script');
    if (scriptBox) scriptBox.textContent = text;
  }
}

// ==================== SCENARIO SIMULATION ====================
async function loadScenario(scenarioKey, autoSwitch = true) {
  // Update buttons
  const buttons = ['normal', 'heatwave', 'flood', 'drought', 'pest_spike'];
  buttons.forEach(k => {
    const btn = document.getElementById(`btn-scen-${k}`);
    if (btn) {
      if (k === scenarioKey) btn.classList.add('active');
      else btn.classList.remove('active');
    }
  });

  try {
    const res = await fetch(`/api/telemetry/live?scenario=${scenarioKey}`);
    const data = await res.json();
    if (data.status === 'success') {
      currentTelemetryData = data.telemetry;
      updateTelemetryUI(data.telemetry);

      // Auto-navigate to the most relevant tab so judges see the changes instantly!
      if (autoSwitch) {
        if (scenarioKey === 'heatwave') {
          switchTab('climate');
        } else if (scenarioKey === 'flood') {
          switchTab('climate');
        } else if (scenarioKey === 'drought') {
          switchTab('irrigation');
        } else if (scenarioKey === 'pest_spike') {
          switchTab('climate');
        }
      }
    }
  } catch (err) {
    console.error('Failed to load telemetry scenario:', err);
  }
}

function updateTelemetryUI(t) {
  // Status bar
  const solarEl = document.getElementById('solar-metric');
  if (solarEl) solarEl.textContent = `${t.solar_battery_pct}% (${t.solar_charge_w}W)`;

  // 1. Update Scenario Alert Banner
  const banner = document.getElementById('scenario-alert-banner');
  const bIcon = document.getElementById('banner-icon');
  const bTitle = document.getElementById('banner-title');
  const bDetail = document.getElementById('banner-detail');
  const bBtn = document.getElementById('banner-action-btn');

  // Tab badges
  const badgeIrrig = document.getElementById('badge-tab-irrig');
  const badgeClim = document.getElementById('badge-tab-clim');

  // Tab 1 Quick field bar
  const t1Temp = document.getElementById('tab1-ambient-temp');
  const t1Moist = document.getElementById('tab1-soil-moist');
  const t1Vpd = document.getElementById('tab1-vpd');
  const t1Action = document.getElementById('tab1-action-text');

  if (t1Temp) t1Temp.textContent = `${t.temp_c} °C`;
  if (t1Moist) t1Moist.textContent = `${t.soil_moisture_15cm} %`;
  if (t1Vpd && t.climate) {
    t1Vpd.textContent = `${t.climate.vpd_kpa} kPa (${t.climate.vpd_kpa > 2.5 ? 'High Demand' : 'Normal'})`;
  }

  if (banner && bTitle && bDetail) {
    banner.className = 'scenario-alert-banner';
    
    if (t.scenario === 'heatwave') {
      banner.classList.add('banner-heatwave');
      if (bIcon) bIcon.textContent = '🔥';
      bTitle.textContent = 'CRITICAL HEATWAVE ACTIVE (43.8°C) - High Thermal Crop Stress';
      bDetail.innerHTML = 'VPD: <strong>3.2 kPa</strong> | Transpiration Demand: Extreme | <strong>Action:</strong> Run micro-sprinklers for 20 mins for canopy cooling.';
      if (bBtn) {
        bBtn.textContent = 'View Heat Stress Matrix ➔';
        bBtn.onclick = () => switchTab('climate');
      }
      if (badgeClim) {
        badgeClim.textContent = 'CRITICAL (44°C)';
        badgeClim.className = 'tab-badge badge-danger';
      }
      if (badgeIrrig) {
        badgeIrrig.textContent = 'HIGH ET₀';
        badgeIrrig.className = 'tab-badge badge-warning';
      }
      if (t1Action) {
        t1Action.textContent = 'CRITICAL: Severe Heatwave (VPD > 3.0 kPa)';
        t1Action.className = 'text-red';
      }

    } else if (t.scenario === 'flood') {
      banner.classList.add('banner-flood');
      if (bIcon) bIcon.textContent = '🌊';
      bTitle.textContent = 'MONSOON FLOOD & CLOUDBURST WARNING (84.5mm Rain Detected)';
      bDetail.innerHTML = 'Soil Moisture: <strong>46.8% (Saturated)</strong> | Hypoxia Risk: High | <strong>Action:</strong> Open field drainage trenches and halt all irrigation.';
      if (bBtn) {
        bBtn.textContent = 'View Flood Advisory ➔';
        bBtn.onclick = () => switchTab('climate');
      }
      if (badgeClim) {
        badgeClim.textContent = 'FLOOD 85mm';
        badgeClim.className = 'tab-badge badge-danger';
      }
      if (badgeIrrig) {
        badgeIrrig.textContent = 'WATERLOGGED';
        badgeIrrig.className = 'tab-badge badge-warning';
      }
      if (t1Action) {
        t1Action.textContent = 'WARNING: Saturated Root Zone - Open Trenches';
        t1Action.className = 'text-red';
      }

    } else if (t.scenario === 'drought') {
      banner.classList.add('banner-drought');
      if (bIcon) bIcon.textContent = '🍂';
      bTitle.textContent = 'ACUTE DROUGHT & ROOT ZONE WATER DEFICIT (13.8% Moisture)';
      bDetail.innerHTML = 'Root Zone: <strong>Critical Wilting Point</strong> | Depletion: 85% | <strong>Action:</strong> Run life-saving pulse drip irrigation (158,400 L/ha).';
      if (bBtn) {
        bBtn.textContent = 'View Pump Schedule ➔';
        bBtn.onclick = () => switchTab('irrigation');
      }
      if (badgeIrrig) {
        badgeIrrig.textContent = 'IRRIGATE NOW';
        badgeIrrig.className = 'tab-badge badge-danger';
      }
      if (badgeClim) {
        badgeClim.textContent = 'DROUGHT';
        badgeClim.className = 'tab-badge badge-warning';
      }
      if (t1Action) {
        t1Action.textContent = 'URGENT: Root Zone Moisture Depleted (13.8%)';
        t1Action.className = 'text-red';
      }

    } else if (t.scenario === 'pest_spike') {
      banner.classList.add('banner-pest_spike');
      if (bIcon) bIcon.textContent = '🐛';
      bTitle.textContent = 'FUNGAL SPORE & PEST OUTBREAK VECTOR SURGE (89% Humidity)';
      bDetail.innerHTML = 'Conditions: <strong>Warm & Humid (29.5°C / 89% RH)</strong> | Threat: Rice Blast & Aphids | <strong>Action:</strong> Conduct prophylactic bio-spray.';
      if (bBtn) {
        bBtn.textContent = 'View Pest Vector ➔';
        bBtn.onclick = () => switchTab('climate');
      }
      if (badgeClim) {
        badgeClim.textContent = 'PEST VECTOR';
        badgeClim.className = 'tab-badge badge-warning';
      }
      if (badgeIrrig) {
        badgeIrrig.textContent = '';
        badgeIrrig.className = 'tab-badge';
      }
      if (t1Action) {
        t1Action.textContent = 'ALERT: Microclimate Favorable for Pest Outbreak';
        t1Action.className = 'text-amber';
      }

    } else {
      // Normal
      banner.classList.add('banner-normal');
      if (bIcon) bIcon.textContent = '🟢';
      bTitle.textContent = 'Normal Optimal Field Conditions';
      bDetail.innerHTML = 'Microclimate: <strong>31.2°C</strong> | Soil Moisture: <strong>29.5%</strong> | Status: <span class="text-green">All Systems Nominal</span>';
      if (bBtn) {
        bBtn.textContent = 'View Field Telemetry ➔';
        bBtn.onclick = () => switchTab('analytics');
      }
      if (badgeIrrig) {
        badgeIrrig.textContent = '';
        badgeIrrig.className = 'tab-badge';
      }
      if (badgeClim) {
        badgeClim.textContent = '';
        badgeClim.className = 'tab-badge';
      }
      if (t1Action) {
        t1Action.textContent = 'Optimal (No Active Hazards)';
        t1Action.className = 'text-green';
      }
    }
  }

  // Tab 2: Irrigation Gauges
  const m15 = document.getElementById('val-moist-15');
  const b15 = document.getElementById('bar-moist-15');
  if (m15) m15.textContent = `${t.soil_moisture_15cm}%`;
  if (b15) b15.style.width = `${Math.min(100, t.soil_moisture_15cm * 2)}%`;

  const m30 = document.getElementById('val-moist-30');
  const b30 = document.getElementById('bar-moist-30');
  if (m30) m30.textContent = `${t.soil_moisture_30cm}%`;
  if (b30) b30.style.width = `${Math.min(100, t.soil_moisture_30cm * 2)}%`;

  if (t.irrigation) {
    const ir = t.irrigation;
    const decBox = document.getElementById('irrig-decision-box');
    const decTitle = document.getElementById('irrig-decision-title');
    const decReason = document.getElementById('irrig-decision-reason');
    const decIcon = document.getElementById('irrig-decision-icon');

    if (decTitle) decTitle.textContent = ir.action_title;
    if (decReason) decReason.textContent = ir.reason;

    if (decBox) {
      decBox.className = 'decision-box';
      if (ir.urgency === 'danger') {
        decBox.classList.add('danger');
        if (decIcon) decIcon.textContent = '🚨';
      } else if (ir.urgency === 'warning' || ir.urgency === 'caution') {
        decBox.classList.add('warning');
        if (decIcon) decIcon.textContent = '⚠️';
      } else {
        if (decIcon) decIcon.textContent = '✅';
      }
    }

    const et0El = document.getElementById('et0-value');
    if (et0El) et0El.textContent = `${ir.et0_mm_day} mm/day`;

    const etcEl = document.getElementById('etc-value');
    if (etcEl) etcEl.textContent = `${ir.crop_water_demand_mm} mm/day`;

    const litEl = document.getElementById('irrig-liters-needed');
    if (litEl) litEl.textContent = `${ir.water_required_liters_per_ha.toLocaleString()} L / ha`;

    const pumpEl = document.getElementById('irrig-pump-hours');
    if (pumpEl) pumpEl.textContent = `${ir.recommended_pump_hours} Hours`;

    const winEl = document.getElementById('irrig-optimal-window');
    if (winEl) winEl.textContent = ir.optimal_window;

    const saveEl = document.getElementById('water-saved-display');
    if (saveEl) saveEl.textContent = `${ir.estimated_water_saved_liters.toLocaleString()} Liters`;
  }

  // Tab 3: Climate Risks
  if (t.climate) {
    const cl = t.climate;
    const resScore = document.getElementById('resilience-score-val');
    if (resScore) resScore.textContent = cl.resilience_score;

    const vpdEl = document.getElementById('val-vpd');
    if (vpdEl) vpdEl.textContent = `${cl.vpd_kpa} kPa`;

    const atmoEl = document.getElementById('val-atmo-demand');
    if (atmoEl) {
      atmoEl.textContent = cl.vpd_kpa > 2.5 ? 'Very High (Crop Dehydration)' : 'Normal';
    }

    // Update 4 hazard cards
    const risks = ['heatwave', 'flood', 'drought', 'pest_vector'];
    risks.forEach(rk => {
      const riskObj = cl.risks[rk];
      if (!riskObj) return;

      const card = document.getElementById(`card-${rk}`);
      const badge = document.getElementById(`badge-${rk}`);
      const fill = document.getElementById(`fill-${rk}`);
      const score = document.getElementById(`score-${rk}`);
      const desc = document.getElementById(`desc-${rk}`);
      const act = document.getElementById(`act-${rk}`);

      if (score) score.textContent = `${riskObj.score}/100`;
      if (desc) desc.textContent = riskObj.advisory;
      if (fill) {
        fill.style.width = `${riskObj.score}%`;
        fill.className = 'hazard-meter-fill';
        if (riskObj.score >= 70) fill.classList.add('fill-crit');
        else if (riskObj.score >= 40) fill.classList.add('fill-mod');
        else fill.classList.add('fill-low');
      }

      if (badge) {
        badge.textContent = `${riskObj.level} RISK`;
        badge.className = 'hazard-badge';
        if (riskObj.level === 'CRITICAL' || riskObj.level === 'HIGH') {
          badge.classList.add('badge-crit');
          if (card) card.classList.add('threat-critical');
        } else if (riskObj.level === 'MODERATE') {
          badge.classList.add('badge-mod');
          if (card) card.classList.remove('threat-critical');
        } else {
          badge.classList.add('badge-low');
          if (card) card.classList.remove('threat-critical');
        }
      }
    });
  }

  // Tab 5: Sensor Stat Numbers
  const sTemp = document.getElementById('stat-temp');
  if (sTemp) sTemp.textContent = `${t.temp_c} °C`;

  const sHum = document.getElementById('stat-humidity');
  if (sHum) sHum.textContent = `${t.humidity_pct} %`;

  const sSoilT = document.getElementById('stat-soil-temp');
  if (sSoilT) sSoilT.textContent = `${t.soil_temp_c} °C`;

  const sSolar = document.getElementById('stat-solar');
  if (sSolar) sSolar.textContent = `${t.solar_radiation_wm2} W/m²`;

  const sRain = document.getElementById('stat-rain');
  if (sRain) sRain.textContent = `${t.rainfall_24h_mm} mm`;

  const sWind = document.getElementById('stat-wind');
  if (sWind) sWind.textContent = `${t.wind_kmh} km/h`;

  // Re-draw chart with current telemetry as baseline
  renderTelemetryChart();
}

// ==================== EDGE AI VISION DIAGNOSTICS ====================
async function diagnoseSample(sampleId) {
  try {
    const formData = new FormData();
    formData.append('sample_id', sampleId);

    const res = await fetch('/api/diagnose/image', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'success') {
      currentDiagnosisData = data.diagnosis;
      renderDiagnosisUI(data.diagnosis);
    }
  } catch (err) {
    console.error('Diagnostic inference failed:', err);
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Show preview in drop-zone
  const reader = new FileReader();
  reader.onload = (e) => {
    const previewContainer = document.getElementById('preview-container');
    if (previewContainer) {
      previewContainer.innerHTML = `
        <img src="${e.target.result}" style="max-height: 180px; max-width: 100%; border-radius: 8px; object-fit: contain; box-shadow: 0 2px 10px rgba(0,0,0,0.3);" />
        <p style="font-size: 0.8rem; margin-top: 8px;"><strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)</p>
        <span class="upload-hint">Running edge quantization inference...</span>
      `;
    }
  };
  reader.readAsDataURL(file);

  try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/api/diagnose/image', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'success') {
      currentDiagnosisData = data.diagnosis;
      renderDiagnosisUI(data.diagnosis);
    }
  } catch (err) {
    console.error('File diagnostic failed:', err);
  }
}

function renderDiagnosisUI(d) {
  // Crop name, condition, pathogen, severity
  const cropEl = document.getElementById('diag-crop-name');
  if (cropEl) cropEl.textContent = d.crop;

  const condEl = document.getElementById('diag-condition-title');
  if (condEl) condEl.textContent = d.condition;

  const pathEl = document.getElementById('diag-pathogen-name');
  if (pathEl) pathEl.textContent = d.pathogen;

  const sevEl = document.getElementById('diag-severity');
  if (sevEl) sevEl.textContent = d.severity;

  const catEl = document.getElementById('diag-category');
  if (catEl) catEl.textContent = d.category;

  // Confidence and latency
  const confEl = document.getElementById('diag-conf-score');
  if (confEl) confEl.textContent = `${d.confidence}%`;

  const confBar = document.getElementById('diag-conf-progress');
  if (confBar) confBar.style.width = `${d.confidence}%`;

  const areaEl = document.getElementById('diag-area-pct');
  if (areaEl) areaEl.textContent = `${d.affected_area_pct}%`;

  const latEl = document.getElementById('diag-latency-val');
  if (latEl) latEl.textContent = `${d.latency_ms} ms`;

  const topLatEl = document.getElementById('npu-latency');
  if (topLatEl) topLatEl.textContent = `${Math.round(d.latency_ms)}ms INT8`;

  // Vernacular advisory text
  const vernText = (d.translations && d.translations[currentLanguage]) || d.translations['en'] || d.prevention_advisory;
  const vernEl = document.getElementById('diag-vernacular-text');
  if (vernEl) vernEl.textContent = vernText;

  const scriptBox = document.getElementById('full-voice-script');
  if (scriptBox) scriptBox.textContent = vernText;

  // Update SMS phone preview
  const smsEl = document.getElementById('phone-sms-text');
  if (smsEl) {
    smsEl.innerHTML = `
      <strong>[AgriEdge Alert]</strong><br>
      🌾 <strong>Crop:</strong> ${d.crop}<br>
      ⚠️ <strong>Condition:</strong> ${d.condition}<br>
      🌿 <strong>Action:</strong> ${(d.organic_treatment && d.organic_treatment[0]) || 'Apply preventive bio-spray.'}<br>
      🎯 <strong>Spot Treatment:</strong> ${(d.targeted_chemical_treatment && d.targeted_chemical_treatment[0]) || 'Nil'}
    `;
  }

  // Symptoms list
  const sympList = document.getElementById('diag-symptoms-list');
  if (sympList) {
    sympList.innerHTML = (d.symptoms || []).map(s => `<li>${s}</li>`).join('');
  }

  // Organic list
  const orgList = document.getElementById('diag-organic-list');
  if (orgList) {
    orgList.innerHTML = (d.organic_treatment || []).map(o => `<li>${o}</li>`).join('');
  }

  // Chemical list
  const chemList = document.getElementById('diag-chemical-list');
  if (chemList) {
    chemList.innerHTML = (d.targeted_chemical_treatment || []).map(c => `<li>${c}</li>`).join('');
  }

  // Prevention
  const prevEl = document.getElementById('diag-prevention-text');
  if (prevEl) prevEl.textContent = d.prevention_advisory || 'Ensure balanced fertilization and proper field drainage.';
}

// ==================== WEB SPEECH API (ENGLISH AUDIO) ====================
function playCurrentAdvisoryAudio() {
  if (!('speechSynthesis' in window)) {
    alert('Web Speech Synthesis is not supported in this browser. You can still read the text advisory!');
    return;
  }

  window.speechSynthesis.cancel();

  const scriptBox = document.getElementById('full-voice-script');
  const textToSpeak = scriptBox ? scriptBox.textContent.trim() : 'AgriEdge AI is active.';

  const utterance = new SpeechSynthesisUtterance(textToSpeak);
  utterance.lang = 'en-US';
  utterance.rate = 0.95; // Slightly slower for clarity
  utterance.pitch = 1.0;

  // Visualizer animation
  const visualizer = document.querySelector('.audio-visualizer');
  const playBtn = document.getElementById('btn-play-voice');

  utterance.onstart = () => {
    isAudioPlaying = true;
    if (visualizer) visualizer.classList.add('playing');
    if (playBtn) playBtn.textContent = '🔊 Playing Audio...';
  };

  utterance.onend = () => {
    isAudioPlaying = false;
    if (visualizer) visualizer.classList.remove('playing');
    if (playBtn) playBtn.textContent = '▶️ Play Voice Advisory (Listen in Audio)';
  };

  utterance.onerror = (e) => {
    console.warn('SpeechSynthesis error:', e);
    isAudioPlaying = false;
    if (visualizer) visualizer.classList.remove('playing');
    if (playBtn) playBtn.textContent = '▶️ Play Voice Advisory (Listen in Audio)';
  };

  window.speechSynthesis.speak(utterance);
}

function stopAudio() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  isAudioPlaying = false;
  const visualizer = document.querySelector('.audio-visualizer');
  if (visualizer) visualizer.classList.remove('playing');
  const playBtn = document.getElementById('btn-play-voice');
  if (playBtn) playBtn.textContent = '▶️ Play Voice Advisory (Listen in Audio)';
}

// ==================== IRRIGATION RECALCULATION & RELAY ====================
async function triggerRecalculateIrrigation() {
  const soilType = document.getElementById('irrig-soil-type').value;
  const rainForecast = parseFloat(document.getElementById('irrig-rain-forecast').value) || 0.0;

  if (!currentTelemetryData) return;

  try {
    const res = await fetch('/api/irrigation/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        soil_moisture_15cm: currentTelemetryData.soil_moisture_15cm,
        soil_moisture_30cm: currentTelemetryData.soil_moisture_30cm,
        temp_c: currentTelemetryData.temp_c,
        humidity_pct: currentTelemetryData.humidity_pct,
        rainfall_forecast_mm: rainForecast,
        soil_type: soilType,
        crop_type: 'Tomato / Wheat'
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      currentTelemetryData.irrigation = data.data;
      updateTelemetryUI(currentTelemetryData);
    }
  } catch (err) {
    console.error('Irrigation recalculation failed:', err);
  }
}

function togglePumpRelay(isChecked) {
  const note = document.getElementById('pump-status-note');
  if (isChecked) {
    note.textContent = 'Status: PUMP RUNNING (Relay Active • Solenoid Open • Drawing 3.8A)';
    note.style.color = '#22c55e';
  } else {
    note.textContent = 'Status: PUMP OFF (Standby • Power 0W)';
    note.style.color = 'var(--text-secondary)';
  }
}

// ==================== COPY & SHARING HELPERS ====================
function copyAdvisoryText() {
  const vernEl = document.getElementById('diag-vernacular-text');
  if (vernEl) {
    navigator.clipboard.writeText(vernEl.textContent.trim());
    alert('Advisory copied to clipboard!');
  }
}

function copySmsText() {
  const smsEl = document.getElementById('phone-sms-text');
  if (smsEl) {
    navigator.clipboard.writeText(smsEl.innerText.trim());
    alert('SMS alert text copied to clipboard!');
  }
}

function simulateWhatsAppShare() {
  const smsEl = document.getElementById('phone-sms-text');
  if (smsEl) {
    const text = encodeURIComponent(smsEl.innerText.trim());
    window.open(`https://api.whatsapp.com/send?text=${text}`, '_blank');
  }
}

// ==================== CLOUD SYNC SIMULATION ====================
async function triggerManualSync() {
  try {
    const res = await fetch('/api/sync/queue', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      const cnt = document.getElementById('sync-cached-count');
      if (cnt) cnt.textContent = '0';
      const msg = document.getElementById('sync-result-msg');
      if (msg) msg.textContent = `✅ ${data.message}`;
    }
  } catch (err) {
    console.error('Sync failed:', err);
  }
}

// ==================== HTML5 CANVAS 24H CHART ====================
function renderTelemetryChart() {
  const canvas = document.getElementById('telemetry-chart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  // Set internal resolution for high DPI displays
  canvas.width = rect.width * dpr;
  canvas.height = 300 * dpr;
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = 300;
  const pad = { top: 30, right: 30, bottom: 40, left: 50 };

  // Clear background
  ctx.clearRect(0, 0, w, h);

  // Time labels (24 hours in 3h steps)
  const hours = ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'];
  const numPts = hours.length;

  // Base data curves simulating realistic diurnal cycles
  const baseM15 = (currentTelemetryData && currentTelemetryData.soil_moisture_15cm) || 29.5;
  const baseM30 = (currentTelemetryData && currentTelemetryData.soil_moisture_30cm) || 33.0;
  const baseTemp = (currentTelemetryData && currentTelemetryData.temp_c) || 31.0;

  // Hourly curves
  const dataMoist15 = [baseM15 + 2.5, baseM15 + 2.0, baseM15 + 1.2, baseM15 - 0.5, baseM15 - 2.8, baseM15 - 3.2, baseM15 - 1.5, baseM15];
  const dataMoist30 = [baseM30 + 0.8, baseM30 + 0.7, baseM30 + 0.5, baseM30 + 0.2, baseM30 - 0.4, baseM30 - 0.8, baseM30 - 0.5, baseM30];
  const dataTemp = [baseTemp - 6.0, baseTemp - 8.0, baseTemp - 5.0, baseTemp + 1.0, baseTemp + 6.0, baseTemp + 7.5, baseTemp + 2.0, baseTemp - 2.0];
  const dataET0 = [0.2, 0.1, 0.4, 2.2, 5.8, 6.2, 2.8, 0.6];

  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;

  // Draw grid lines & Y-axis labels (0 to 60)
  ctx.strokeStyle = highContrastMode ? '#cbd5e1' : 'rgba(255, 255, 255, 0.08)';
  ctx.lineWidth = 1;
  ctx.fillStyle = highContrastMode ? '#64748b' : '#9ca3af';
  ctx.font = '11px sans-serif';

  const yTicks = [0, 15, 30, 45, 60];
  yTicks.forEach(val => {
    const y = pad.top + plotH - (val / 60) * plotH;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(w - pad.right, y);
    ctx.stroke();
    ctx.fillText(`${val}`, pad.left - 25, y + 4);
  });

  // X-axis time ticks
  hours.forEach((hr, i) => {
    const x = pad.left + (i / (numPts - 1)) * plotW;
    ctx.fillText(hr, x - 14, h - pad.bottom + 20);
  });

  // Helper to draw smoothed curve
  function drawSeries(data, color, maxVal = 60, isDashed = false) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    if (isDashed) ctx.setLineDash([4, 4]);
    else ctx.setLineDash([]);

    ctx.beginPath();
    data.forEach((val, i) => {
      const x = pad.left + (i / (numPts - 1)) * plotW;
      const y = pad.top + plotH - (Math.max(0, Math.min(maxVal, val)) / maxVal) * plotH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Draw dots
    ctx.fillStyle = color;
    data.forEach((val, i) => {
      const x = pad.left + (i / (numPts - 1)) * plotW;
      const y = pad.top + plotH - (Math.max(0, Math.min(maxVal, val)) / maxVal) * plotH;
      ctx.beginPath();
      ctx.arc(x, y, 3.5, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // Draw each series
  drawSeries(dataMoist15, '#22c55e'); // Green
  drawSeries(dataMoist30, '#3b82f6'); // Blue
  drawSeries(dataTemp, '#ef4444');    // Red
  drawSeries(dataET0, '#f59e0b', 12, true); // Amber dashed (scaled to 12)
}
