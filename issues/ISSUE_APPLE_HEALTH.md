# [Integration]: Apple Health - Personal Wellness & Wearable Data

## Overview

Add integration with Apple Health data to enable wellness, fitness, and chronic disease management agents. Since Apple HealthKit is restricted to on-device iOS access, this integration implements a **dual-path approach**:

1.  **Export Analysis** - Parse and analyze Apple Health `export.zip` files for deep historical insights.
2.  **Aggregator API** - Real-time data access via [Vital](https://tryvital.io) or [Terra](https://tryterra.co) APIs for continuous monitoring.

**Why This Matters:**
- 150M+ Apple Watch users generating high-fidelity health data daily.
- HealthKit stores 100+ metrics (heart rate, sleep, ECG, activity, etc.).
- Critical for chronic disease management and preventive healthcare.
- Personal health data enables truly personalized AI coaching.
- Overcomes the "siloed data" problem for AI agents.

## Requirements

Implement the following 8 MCP tools:

### Export Analysis (3 tools)

| Tool | Description |
| :--- | :--- |
| `health_parse_export` | Parse Apple Health `export.zip` and return structured JSON data |
| `health_analyze_trends` | Analyze historical trends in parsed data (sleep, activity, vitals) |
| `health_detect_anomalies` | Flag metrics that deviate from the user's personal baseline |

### Real-Time Aggregator (5 tools)

| Tool | Description |
| :--- | :--- |
| `health_get_vitals` | Get recent heart rate, HRV, blood oxygen, and respiratory rate |
| `health_get_activity` | Get daily steps, distance, active calories, and workout history |
| `health_get_sleep` | Get detailed sleep stages (REM, Deep, Light) and efficiency |
| `health_get_body` | Get weight, body fat %, and BMI trends |
| `health_get_nutrition` | Get nutrition/food log data and macronutrient breakdown |

## Authentication

### Export Analysis
- **Auth Method:** None (Local file processing)
- **Inputs:** Path to `export.zip` file

### Aggregator (Vital API)
- **Credentials:** `VITAL_API_KEY`, `VITAL_REGION`
- **Auth Method:** API Key in header (`x-vital-api-key`)
- **Scopes:** User must grant permission via Vital's Link flow

## Costing

| Service | Cost | Notes |
| :--- | :--- | :--- |
| **Export Analysis** | **Free** | Local processing, no external API costs |
| **Vital/Terra API** | **Free Tier** | Vital offers 50 connected users for free |

## Use Cases

### 🏋️ Personalized Fitness Coach
```
"How am I doing on my fitness goals?"
├── health_get_activity(last_7_days) → Steps, workouts, calories
├── health_get_vitals() → Resting heart rate trend
├── health_get_sleep() → Recovery quality
├── Analyze vs goals:
│   ├── Steps: 8,234/10,000 (Lagging)
│   ├── Active calories: 2,450 (On track)
│   ├── Resting HR: 58 bpm (Improving)
│   └── Sleep: 6.8 hours (Below target)
└── "Activity is great! Focus on bedtime for better recovery."
```

### 😴 Sleep optimization Agent
```
"Why is my sleep quality declining?"
├── health_get_sleep(last_30_days) → Full sleep data
├── health_analyze_trends("sleep") → Bedtime variance
├── Correlate:
│   ├── Bedtime consistency → Irregular (±90 min)
│   ├── Deep sleep % → Declining trend
│   └── Pre-sleep activity → High screen time
├── Insights:
│   ├── "Deep sleep down 20% on nights with late bedtime"
│   └── "Irregular schedule correlates with higher stress markers"
└── Personalized sleep hygiene plan
```

### ❤️ Heart Health Monitor
```
"Monitor my cardiovascular health for anomalies"
├── health_get_vitals(continuous) → Real-time heart data
├── health_detect_anomalies("heart_rate")
├── If anomaly detected:
│   ├── Alert: "Elevated resting HR detected (85 vs 62 baseline)"
│   ├── Context: "Started 2 days ago, correlates with low sleep"
│   └── Recommendation: "Monitor and rest; see doctor if persists"
└── Weekly heart health summary report
```

### 📊 Health Export Deep Dive
```
"Analyze my health data from the last year"
├── health_parse_export("export.zip")
├── health_analyze_trends(period="12months")
├── Generate Report:
│   ├── Activity: Yearly step count, workout frequency
│   ├── Sleep: Average duration & quality changes
│   ├── Vitals: Heart rate trend & variability
│   └── Body: Weight & BMI transitions
└── PDF report for medical consultation
```

## Implementation Details

### Credential Spec

```python
"apple_health": CredentialSpec(
    env_var="VITAL_API_KEY",
    tools=[
        "health_parse_export", "health_analyze_trends", "health_detect_anomalies",
        "health_get_vitals", "health_get_activity", "health_get_sleep",
        "health_get_body", "health_get_nutrition",
    ],
    required=False,
    startup_required=False,
    help_url="https://docs.tryvital.io/",
    description="Vital API Key for real-time Apple Health data access",
    api_key_instructions="""1. Sign up at https://tryvital.io
2. Get API key from Dashboard -> API Keys
3. Set VITAL_API_KEY and VITAL_REGION
(Export analysis works without an API key)""",
    credential_id="apple_health",
    credential_key="api_key",
),
```

### File Structure

```
tools/src/aden_tools/tools/apple_health_tool/
├── __init__.py
├── apple_health_tool.py
├── export_parser.py      # XML parser for export.zip
├── vital_client.py       # Vital API client
├── terra_client.py       # Terra API client (Optional)
├── anomaly_detection.py  # Trend analysis & baseline logic
└── README.md
```

### Key Endpoints (Vital)

| Resource | Endpoint |
| :--- | :--- |
| **Vitals** | `/v2/summary/vitals/{user_id}` |
| **Activity** | `/v2/summary/activity/{user_id}` |
| **Sleep** | `/v2/summary/sleep/{user_id}` |
| **Workouts** | `/v2/summary/workouts/{user_id}` |

## Privacy Considerations

⚠️ **Health data is extremely sensitive:**
1.  **In-Memory Only:** Process health data without persistent storage where possible.
2.  **Explicit Consent:** Always inform the user before fetching or parsing data.
3.  **Local Preference:** Default to local export parsing to keep data on-device.
4.  **Minimization:** Only request necessary scopes and fields.

## Why Agents Need This

| Without Health Tools | With Health Tools |
| :--- | :--- |
| "Am I healthy?" → Generic advice | "Your HRV is up 15%, recovery is optimal." |
| "Plan a workout" → Standard routines | "Reduced sleep detected; lighter intensity plan." |
| "Check my heart" → Impossible | "Anomaly detected: Resting HR is 20% above baseline." |

**The Vision:** AI that acts as a 24/7 health guardian, leveraging the data users already collect to provide proactive, lifesaving guidance.

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`, `health`, `wellness`
