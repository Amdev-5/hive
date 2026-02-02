# [Integration]: Google Health (Fitbit & Google Fit) - Fitness & Wellness Data

## Overview

Add integration with Google Fitness APIs (Fitbit Web API + Google Fit REST API) to enable wellness, fitness, and health management agents. Google's health ecosystem spans 30M+ Fitbit users and millions of Google Fit users - agents need access to this data for personalized fitness coaching, sleep optimization, and health monitoring.

**Why This Matters:**
- 30M+ active Fitbit users with deep health data
- Google Fit aggregates data from 100+ fitness apps
- Fitbit Premium features world-class sleep analysis
- Heart rate, SpO2, stress management, and more
- Cross-platform: works on Android, iOS, and web

## Requirements

Implement the following 10 MCP tools:

### Fitbit API (6 tools)

| Tool | Description |
|------|-------------|
| `fitbit_get_activity` | Get daily activity (steps, distance, calories, floors, active minutes) |
| `fitbit_get_sleep` | Get sleep logs with stages (light, deep, REM, awake) |
| `fitbit_get_heart` | Get heart rate data (resting, zones, intraday) |
| `fitbit_get_weight` | Get weight and body composition logs |
| `fitbit_get_workouts` | Get exercise/workout logs with details |
| `fitbit_get_devices` | Get connected devices and battery status |

### Google Fit API (4 tools)

| Tool | Description |
|------|-------------|
| `googlefit_get_activity` | Get activity data (steps, calories, distance) |
| `googlefit_get_sleep` | Get sleep sessions and segments |
| `googlefit_get_heart` | Get heart rate data points |
| `googlefit_list_sources` | List connected apps/devices |

## Authentication

### Fitbit
- **Credentials:** `FITBIT_CLIENT_ID`, `FITBIT_CLIENT_SECRET`, `FITBIT_REFRESH_TOKEN`
- **Auth Method:** OAuth 2.0 with refresh token
- **Scopes:** `activity`, `sleep`, `heartrate`, `weight`, `profile`

### Google Fit
- **Credentials:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
- **Auth Method:** OAuth 2.0 with refresh token
- **Scopes:** `fitness.activity.read`, `fitness.sleep.read`, `fitness.heart_rate.read`

## Costing

| Service | Cost | Notes |
|---------|------|-------|
| Fitbit Web API | **Free** | Rate limited to 150 req/hour |
| Google Fit API | **Free** | Standard Google API quotas |

**Note:** Both APIs are completely free. Fitbit requires app registration approval for production.

## Use Cases

### 🏋️ Personalized Fitness Coach
```
"Create my workout plan for this week"
├── fitbit_get_activity(last_7_days) → Recent activity levels
├── fitbit_get_sleep(last_7_days) → Recovery status
├── fitbit_get_heart() → Resting HR trend (fitness indicator)
├── fitbit_get_workouts(last_30_days) → Training history
├── Analyze:
│   ├── Current fitness level (VO2 max estimate)
│   ├── Recovery status (HRV, sleep quality)
│   ├── Training load (recent intensity)
│   └── Preferred workout types
├── Generate: Periodized weekly plan
│   ├── Monday: Upper body strength (recovered)
│   ├── Tuesday: Light cardio (active recovery)
│   ├── Wednesday: HIIT (peak recovery day)
│   └── ...
└── "Based on your recovery metrics, here's your optimized week..."
```

### 😴 Sleep Quality Agent
```
"Why is my sleep score declining?"
├── fitbit_get_sleep(last_30_days) → Full sleep data
├── Analyze trends:
│   ├── Time in bed vs actual sleep
│   ├── Sleep stage distribution
│   ├── Wake episodes frequency
│   ├── Bedtime consistency
│   └── Weekend vs weekday patterns
├── Correlate with:
│   ├── fitbit_get_activity() → Late evening activity
│   ├── fitbit_get_heart() → Evening HR elevation
│   └── External: caffeine, alcohol, stress
├── Insights:
│   ├── "Deep sleep down 25% when bedtime after 11pm"
│   ├── "Evening workouts correlate with +15min awake time"
│   └── "Weekend sleep debt averages 3.5 hours"
└── Personalized sleep improvement plan
```

### ❤️ Heart Health Tracking
```
"Monitor my cardiovascular health"
├── fitbit_get_heart(detail_level="1min", period="30d")
├── Calculate:
│   ├── Resting HR trend
│   ├── HR recovery after exercise
│   ├── Time in HR zones
│   └── Irregular rhythm notifications (if available)
├── fitbit_get_activity() → Correlate with exercise
├── Insights:
│   ├── "Resting HR improved from 68 to 62 over 3 months"
│   ├── "HR recovery is excellent (30 bpm drop in 1 min)"
│   └── "You spend 45min/day in cardio zone (good!)"
└── Flag: Any concerning patterns for doctor review
```

### 🎯 Goal Achievement Agent
```
Daily check-in:
├── fitbit_get_activity(today) → Current progress
├── Compare to goals:
│   ├── Steps: 7,234 / 10,000 (72%)
│   ├── Active minutes: 22 / 30 (73%)
│   ├── Floors: 8 / 10 (80%)
│   └── Calories: 1,890 / 2,200 (86%)
├── Time remaining: 4 hours
├── Recommendation:
│   └── "A 20-min evening walk will hit all your goals!"
├── If goals hit:
│   └── "🎉 All goals achieved! 5-day streak!"
└── Weekly summary with trends
```

### 🏃 Workout Optimization
```
After workout detected:
├── fitbit_get_workouts(latest) → Workout details
├── fitbit_get_heart(during_workout) → HR during exercise
├── Analyze:
│   ├── Time in zones (fat burn, cardio, peak)
│   ├── Calories burned vs estimated
│   ├── Workout efficiency score
│   └── Compare to similar past workouts
├── Feedback:
│   ├── "Great run! 25% more time in cardio zone than last week"
│   ├── "Consider longer warm-up - HR spiked early"
│   └── "Recovery HR improving - fitness is increasing!"
└── Log: Workout performance history
```

### 📊 Multi-Source Fitness Dashboard
```
"Unified view of all my fitness data"
├── fitbit_get_activity() → Fitbit daily stats
├── googlefit_get_activity() → Google Fit aggregated
├── googlefit_list_sources() → See all connected apps
├── Merge and deduplicate:
│   ├── Prefer Fitbit for sleep/HR (more accurate)
│   ├── Use Google Fit for app-specific workouts
│   └── Aggregate steps from all sources
├── Unified dashboard:
│   ├── Today's activity (all sources)
│   ├── Sleep (Fitbit primary)
│   ├── Workouts (by source app)
│   └── Trends (normalized data)
└── Single source of truth for health data
```

### 🔔 Smart Health Reminders
```
Contextual reminders based on data:
├── fitbit_get_activity(today) → Check step count
├── If 2pm and < 3000 steps:
│   └── "You've been sedentary today. Time for a walk?"
├── fitbit_get_sleep(last_night) → Check sleep quality
├── If poor sleep:
│   └── "Low sleep score last night. Consider lighter workout today."
├── fitbit_get_heart() → Check stress indicators
├── If elevated resting HR:
│   └── "Your body might be fighting something. Extra rest today?"
└── Proactive, personalized health nudges
```

## Implementation Details

### Credential Spec

```python
"fitbit": CredentialSpec(
    env_var="FITBIT_CREDENTIALS",  # JSON with client_id, client_secret, refresh_token
    tools=[
        "fitbit_get_activity", "fitbit_get_sleep", "fitbit_get_heart",
        "fitbit_get_weight", "fitbit_get_workouts", "fitbit_get_devices",
    ],
    required=True,
    startup_required=False,
    help_url="https://dev.fitbit.com/build/reference/web-api/",
    description="Fitbit OAuth2 credentials for fitness and health data",
    api_key_instructions="""To set up Fitbit integration:
1. Go to https://dev.fitbit.com and create an app
2. Set OAuth 2.0 Application Type: "Personal"
3. Set Callback URL: http://localhost:8080/callback
4. Note your Client ID and Client Secret
5. Run OAuth flow to obtain refresh token
6. Store as JSON: {"client_id": "...", "client_secret": "...", "refresh_token": "..."}""",
    credential_id="fitbit",
    credential_key="refresh_token",
),

"google_fit": CredentialSpec(
    env_var="GOOGLE_FIT_CREDENTIALS",  # JSON with client_id, client_secret, refresh_token
    tools=[
        "googlefit_get_activity", "googlefit_get_sleep",
        "googlefit_get_heart", "googlefit_list_sources",
    ],
    required=True,
    startup_required=False,
    help_url="https://developers.google.com/fit/rest/",
    description="Google Fit OAuth2 credentials for fitness data",
    api_key_instructions="""To set up Google Fit integration:
1. Go to Google Cloud Console
2. Enable Fitness API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download client configuration
5. Run OAuth flow with fitness scopes
6. Store as JSON: {"client_id": "...", "client_secret": "...", "refresh_token": "..."}""",
    credential_id="google_fit",
    credential_key="refresh_token",
),
```

### File Structure

```
tools/src/aden_tools/tools/google_health_tool/
├── __init__.py
├── google_health_tool.py
├── fitbit_client.py      # Fitbit Web API client
├── googlefit_client.py   # Google Fit REST API client
└── README.md
```

### API Base URLs

| Service | Base URL |
|---------|----------|
| Fitbit | `https://api.fitbit.com` |
| Google Fit | `https://www.googleapis.com/fitness/v1/users/me` |

### Key Endpoints

**Fitbit:**
| Resource | Endpoint |
|----------|----------|
| Activity | `/1/user/-/activities/date/{date}.json` |
| Sleep | `/1.2/user/-/sleep/date/{date}.json` |
| Heart | `/1/user/-/activities/heart/date/{date}/1d.json` |
| Weight | `/1/user/-/body/log/weight/date/{date}.json` |

**Google Fit:**
| Resource | Endpoint |
|----------|----------|
| Data Sources | `/dataSources` |
| Datasets | `/dataSources/{dataSourceId}/datasets/{datasetId}` |
| Sessions | `/sessions` |
| Aggregate | `/dataset:aggregate` |

## Privacy Considerations

⚠️ **Health data requires careful handling:**

1. **User consent** - Clear explanation of data access
2. **Minimal scopes** - Only request needed permissions
3. **Secure storage** - Encrypt refresh tokens
4. **No raw storage** - Process and discard raw data
5. **User control** - Easy revocation of access
6. **Transparency** - Clear data usage policies

## Why Agents Need This

| Without Health Tools | With Health Tools |
|---------------------|-------------------|
| "How active am I?" → Check your Fitbit | Instant activity insights |
| "Optimize my workout" → Generic advice | Data-driven personalization |
| "Sleep better" → Standard tips | Your specific sleep patterns analyzed |
| "Am I improving?" → Manual tracking | Automated trend analysis |

**The Quantified Self:** Users already collect this data. Agents make it actionable.

## References

- [Fitbit Web API Reference](https://dev.fitbit.com/build/reference/web-api/)
- [Google Fit REST API](https://developers.google.com/fit/rest/)
- [Fitbit OAuth Tutorial](https://dev.fitbit.com/build/reference/web-api/developer-guide/authorization/)
- [Google Fitness Data Types](https://developers.google.com/fit/datatypes)

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`, `health`, `fitness`, `wellness`
