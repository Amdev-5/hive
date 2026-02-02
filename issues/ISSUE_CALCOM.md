# [Integration]: Cal.com - Open Source Scheduling Infrastructure

## Overview

Add integration with Cal.com API to enable agents to manage scheduling, availability, and calendar bookings. Cal.com is the open-source Calendly alternative with 15M+ monthly bookings - agents need access to automate meeting scheduling, manage availability, and orchestrate complex booking workflows.

**Why This Matters:**
- 15M+ bookings/month on Cal.com platform
- Open source = full customization and self-hosting option
- Native integrations with Google Calendar, Outlook, Zoom, and more
- Round-robin, collective, and sequential booking types
- Scheduling is the #1 friction point in sales and support

## Requirements

Implement the following 8 MCP tools:

### Bookings (4 tools)

| Tool | Description |
|------|-------------|
| `calcom_list_bookings` | List bookings with filters (status, event type, date range) |
| `calcom_get_booking` | Get full booking details including attendees and meeting links |
| `calcom_create_booking` | Create a new booking for a user/event type |
| `calcom_cancel_booking` | Cancel or reschedule an existing booking |

### Availability (2 tools)

| Tool | Description |
|------|-------------|
| `calcom_get_availability` | Get available time slots for a user/event type |
| `calcom_update_schedule` | Update user's availability schedule |

### Event Types (2 tools)

| Tool | Description |
|------|-------------|
| `calcom_list_event_types` | List all configured event types (15 min call, demo, etc.) |
| `calcom_get_event_type` | Get event type details including duration, location, and questions |

## Authentication

- **Credential:** `CALCOM_API_KEY`
- **Auth Method:** API key in `Authorization: Bearer {key}` header
- **Get Key:** Cal.com → Settings → Developer → API Keys → Create

## Costing

| Plan | Price | API Access |
|------|-------|------------|
| Free | $0 | ✅ Basic API |
| Team | $15/user/mo | ✅ Full API |
| Organization | $37/user/mo | ✅ Full API + Priority |
| Self-hosted | $0 | ✅ Full control |

**Rate Limits:** 100 requests/minute (standard), higher on paid plans

## Use Cases

### 📅 Intelligent Scheduling Agent
```
"Schedule a demo with john@company.com"
├── calcom_list_event_types() → Find "Product Demo" type
├── calcom_get_availability("demo", next_2_weeks) → Get slots
├── Analyze: John's timezone, preferences (if known)
├── calcom_create_booking() → Book optimal slot
├── Confirmation: "Demo scheduled for Tuesday 2pm PT"
└── Calendar invite sent automatically
```

### 🤖 Inbound Lead Scheduler
```
When lead fills out "Book a Demo" form:
├── calcom_get_availability("sales_team") → Round-robin slots
├── Lead selects preferred time
├── calcom_create_booking() → Create meeting
├── Enrich: Pull lead data from CRM
├── Notify: Sales rep with context
└── Pre-meeting: Send prep email to lead
```

### 🔄 Reschedule Manager
```
When meeting needs rescheduling:
├── calcom_get_booking(id) → Current details
├── calcom_get_availability() → New available slots
├── Present: Options to attendees
├── calcom_cancel_booking(id, reschedule=true)
├── calcom_create_booking() → New slot
└── All parties notified automatically
```

### 📊 Meeting Analytics Agent
```
"How's our demo scheduling performing?"
├── calcom_list_bookings(type="demo", period="30d")
├── Analyze:
│   ├── Bookings by day/week
│   ├── Most popular time slots
│   ├── No-show rate
│   ├── Reschedule rate
│   ├── Time-to-book (lead → meeting)
│   └── Rep utilization (round-robin fairness)
└── "Demo bookings up 23%, Tuesdays 2pm most popular"
```

### ⚡ Calendar Concierge
```
"Find time for a team lunch next week"
├── calcom_get_availability(team_members, next_week) → Collective availability
├── Filter: 11am-1pm slots only
├── Rank: By number of attendees available
├── calcom_create_booking() → Book best slot
└── "Team lunch booked: Thursday 12pm, 8/10 can attend"
```

### 🎯 Sales Follow-up Automator
```
After sales call ends:
├── Detect: Meeting outcome (interested, needs follow-up, closed)
├── If follow-up needed:
│   ├── calcom_get_availability(rep, next_week)
│   ├── Generate: Follow-up email with booking link
│   └── Send: Personalized scheduling link
├── If demo requested:
│   ├── calcom_create_booking() → Schedule immediately
│   └── Add: Calendar prep reminders
└── Pipeline velocity increased by 35%
```

### 🌍 Timezone-Aware Scheduler
```
"Book call with Tokyo team"
├── calcom_get_availability(team) → SF team's slots
├── Convert: To JST (Tokyo timezone)
├── Filter: Reasonable hours for both (8am-8pm overlap)
├── Present: "These slots work for both timezones"
├── calcom_create_booking() → Include timezone context
└── Meeting links auto-configured for both regions
```

## Implementation Details

### Credential Spec

```python
"calcom": CredentialSpec(
    env_var="CALCOM_API_KEY",
    tools=[
        "calcom_list_bookings", "calcom_get_booking",
        "calcom_create_booking", "calcom_cancel_booking",
        "calcom_get_availability", "calcom_update_schedule",
        "calcom_list_event_types", "calcom_get_event_type",
    ],
    required=True,
    startup_required=False,
    help_url="https://cal.com/docs/api",
    description="Cal.com API key for scheduling and booking management",
    api_key_instructions="""To get Cal.com API key:
1. Log in to Cal.com
2. Go to Settings → Developer → API Keys
3. Click "Create new API key"
4. Give it a name and set expiration
5. Copy the key (shown only once)
6. Store securely""",
    health_check_endpoint="https://api.cal.com/v1/me",
    health_check_method="GET",
    credential_id="calcom",
    credential_key="api_key",
),
```

### File Structure

```
tools/src/aden_tools/tools/calcom_tool/
├── __init__.py
├── calcom_tool.py
└── README.md
```

### API Base URL

```
https://api.cal.com/v1
```

### Key Endpoints

| Resource | Endpoint |
|----------|----------|
| Bookings | `/bookings`, `/bookings/{id}` |
| Availability | `/availability`, `/schedules` |
| Event Types | `/event-types`, `/event-types/{id}` |
| Users | `/me`, `/users` |
| Slots | `/slots` |

## Why Agents Need This

| Without Cal.com Tools | With Cal.com Tools |
|----------------------|-------------------|
| "Schedule a meeting" → Send scheduling link | Direct booking creation |
| "When are you free?" → Back-and-forth emails | Instant availability lookup |
| "Reschedule" → Manual coordination | One-click rescheduling |
| "Team availability" → Check multiple calendars | Unified collective availability |

**Scheduling Reality:** The average meeting takes 8+ emails to schedule. Agents with Cal.com access reduce this to zero.

## API Response Examples

### Booking Object
```json
{
  "id": 12345,
  "uid": "abc123",
  "title": "Product Demo",
  "description": "30 min product walkthrough",
  "startTime": "2024-01-20T14:00:00Z",
  "endTime": "2024-01-20T14:30:00Z",
  "attendees": [
    {"email": "lead@company.com", "name": "Jane Doe", "timeZone": "America/New_York"}
  ],
  "location": "https://meet.google.com/xxx-xxx-xxx",
  "status": "ACCEPTED"
}
```

### Availability Response
```json
{
  "busy": [
    {"start": "2024-01-20T09:00:00Z", "end": "2024-01-20T10:00:00Z"},
    {"start": "2024-01-20T14:00:00Z", "end": "2024-01-20T15:00:00Z"}
  ],
  "slots": [
    {"time": "2024-01-20T10:00:00Z"},
    {"time": "2024-01-20T11:00:00Z"},
    {"time": "2024-01-20T15:00:00Z"}
  ]
}
```

## Open Source Advantage

Cal.com is **open source** (AGPLv3), meaning:
- Self-host for full data control
- Customize booking flows
- No vendor lock-in
- Community-driven development
- Enterprise can run behind firewall

## References

- [Cal.com API Documentation](https://cal.com/docs/api-reference/v1)
- [Cal.com GitHub](https://github.com/calcom/cal.com)
- [Developer Guides](https://cal.com/docs)

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`, `scheduling`, `open-source`
