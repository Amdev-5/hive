# Timesheet Orchestration Agent — System Architecture

## 1. System Overview

A fully autonomous agent that manages weekly timesheet collection across an organization. It dispatches reminders via Slack and Telegram, collects submissions from Slack channel history, validates and consolidates data, generates executive-grade HTML reports with interactive charts, and delivers them via Email with Slack/Telegram notifications.

Built on the Aden graph execution framework — a directed graph of LLM-powered nodes connected by conditional edges, with automatic checkpointing, feedback loops, and human-in-loop interaction points.

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GRAPH EXECUTOR                               │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐  │
│  │  INTAKE   │───►│ DISPATCH │───►│ COLLECT  │───►│  VALIDATE    │  │
│  │  (HIL)    │    │          │    │  (HIL)   │    │              │  │
│  └──────────┘    └────▲─────┘    └────▲─────┘    └──┬───┬───┬───┘  │
│                       │               │             │   │   │      │
│                       │               └─── e4 ──────┘   │   │      │
│                       └──────────── e5 ─────────────────┘   │      │
│                                                             │      │
│                  ┌──────────┐    ┌──────────┐               │      │
│                  │ DELIVER  │◄───│  REPORT  │◄── e6 ────────┘      │
│                  │  (HIL)   │    │          │                       │
│                  └──────────┘    └──────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐
│  MCP TOOL   │    │  LLM PROVIDER│    │  CHECKPOINT      │
│  SERVER     │    │  (LiteLLM)   │    │  STORE           │
│             │    │              │    │                  │
│ • Slack API │    │ Any provider │    │ Node boundaries  │
│ • Telegram  │    │ via LiteLLM  │    │ Crash recovery   │
│ • Resend    │    │              │    │ Session state    │
│ • Data I/O  │    │              │    │                  │
└─────────────┘    └──────────────┘    └──────────────────┘
```

## 3. Node Architecture

### Node 1: Intake & Setup (HIL #1)
- **Type**: `event_loop` | **Client-facing**: Yes
- **Purpose**: Parse employee roster (CSV/text), configure schedule, channels, executive recipient
- **Inputs**: Raw user text
- **Outputs**: `employee_roster` (JSON array), `config` (schedule, channels, email)
- **Tools**: `csv_read`, `excel_read`, `save_data`
- **HIL Justification**: One-time setup requires admin confirmation of parsed data

### Node 2: Dispatch Reminders (Autonomous)
- **Type**: `event_loop` | **Client-facing**: No | **Max visits**: 3
- **Purpose**: Send timesheet reminders via Slack @mentions and Telegram DMs
- **Inputs**: `employee_roster`, `config`, `missing_employees` (nullable, for re-visits)
- **Outputs**: `dispatch_log`
- **Tools**: `slack_send_message`, `telegram_send_message`, `get_current_time`, `save_data`, `load_data`
- **Idempotency**: Checks `dispatch_log.json` before sending to prevent duplicate reminders on restart
- **Escalation tiers**: Visit 1 (friendly) → Visit 2 (firm) → Visit 3 (manager CC)

### Node 3: Collect Timesheets (HIL #2)
- **Type**: `event_loop` | **Client-facing**: Yes | **Max visits**: 3
- **Purpose**: Read Slack channel history, extract structured timesheet data via LLM
- **Inputs**: `employee_roster`, `config`, `clarification_requests` (nullable, from validate feedback)
- **Outputs**: `raw_submissions`, `structured_timesheets`, `missing_employees`
- **Tools**: `slack_get_channel_history`, `slack_send_message`, `telegram_send_message`, `save_data`, `load_data`, `get_current_time`
- **HIL Justification**: Admin reviews collected data and decides whether to proceed or wait for more submissions

### Node 4: Validate & Consolidate (Autonomous)
- **Type**: `event_loop` | **Client-facing**: No | **Max visits**: 2
- **Purpose**: Validate arithmetic, detect anomalies, consolidate master dataset, generate insights
- **Inputs**: `structured_timesheets`, `employee_roster`, `config`
- **Outputs**: `master_dataset`, `insights`, `clarification_requests`, `missing_employees`, `validation_passed`
- **Tools**: `save_data`, `load_data`, `csv_write`
- **Routing Decision**: Sets `validation_passed` to route via conditional edges

### Node 5: Generate Report (Autonomous)
- **Type**: `event_loop` | **Client-facing**: No
- **Purpose**: Build professional HTML report with Chart.js charts, export CSV
- **Inputs**: `master_dataset`, `insights`, `config`
- **Outputs**: `report_file`, `report_csv`, `report_uri`
- **Tools**: `save_data`, `append_data`, `serve_file_to_user`, `csv_write`
- **Report Contents**: Executive summary stat cards, bar chart (hours by project), horizontal bar (hours by person), doughnut (department allocation), detailed breakdown table, risk flags, recommendations

### Node 6: Deliver & Follow-Up (HIL #3)
- **Type**: `event_loop` | **Client-facing**: Yes
- **Purpose**: Deliver report via Email + Slack + Telegram, enter executive Q&A mode
- **Inputs**: `report_file`, `report_csv`, `report_uri`, `master_dataset`, `insights`, `employee_roster`, `config`
- **Outputs**: `delivery_status`
- **Tools**: `send_email`, `telegram_send_message`, `telegram_send_document`, `slack_send_message`, `load_data`, `serve_file_to_user`, `get_current_time`
- **HIL Justification**: Executive can ask follow-up questions about the data

## 4. Edge System & Routing

| Edge | Route | Condition | Priority | Description |
|------|-------|-----------|:---:|-------------|
| e1 | intake → dispatch | `on_success` | 1 | Happy path start |
| e2 | dispatch → collect | `on_success` | 1 | After reminders sent |
| e3 | collect → validate | `on_success` | 1 | After data collected |
| e4 | validate → collect | `validation_passed != 'true'` | 2 | **Loop 1**: Clarification needed |
| e5 | validate → dispatch | `validation_passed == 'true' and missing_employees` | 3 | **Loop 2**: Re-remind missing |
| e6 | validate → report | `validation_passed == 'true'` | 1 | All clean, generate report |
| e7 | report → deliver | `on_success` | 1 | Deliver final output |

**Priority resolution**: Higher priority edges are evaluated first. If e5 (priority 3) matches, it takes precedence over e6 (priority 1). This ensures missing employees get re-reminded before the report is generated.

**Loop termination**: `max_node_visits` caps re-entry. Dispatch allows 3 visits (3 escalation tiers), collect allows 3, validate allows 2. After max visits, the node fails and the `on_failure` path is taken.

## 5. Channel Strategy

| Channel | Direction | Capability | Use Case |
|---------|-----------|------------|----------|
| **Slack** | Bidirectional | Send messages (`chat:write`) + Read history (`channels:history`) | Primary collection channel. @mention reminders, read timesheet replies |
| **Telegram** | Unidirectional (push) | Send messages + documents | High-visibility DM nudges. Reaches employees outside Slack |
| **Email (Resend)** | Unidirectional (push) | Send HTML emails | Executive report delivery with formatted summary |

**Why this split**: Slack is the only channel with read capability (via `conversations.history` API). Telegram Bot API is send-only (no inbox reading without webhook setup). Email is inherently push-only. This drives the architecture: collect from Slack, push via all three.

## 6. Data Flow

```
User Input (roster + config)
        │
        ▼
employee_roster: [
  {"name": "Alice", "role": "Engineer", "department": "Eng",
   "slack_user_id": "U01...", "telegram_chat_id": "123456"}
]
config: {"reminder_day": "Monday", "deadline_day": "Friday",
         "executive_email": "exec@company.com", "slack_channel": "C0..."}
        │
        ▼ (dispatch)
dispatch_log: [
  {"name": "Alice", "slack_status": "sent", "telegram_status": "sent",
   "visit": 1, "timestamp": "2026-03-09T09:00:00"}
]
        │
        ▼ (collect from Slack channel history)
structured_timesheets: [
  {"person": "Alice", "entries": [{"project": "Alpha", "task": "API work", "hours": 20}],
   "total_hours": 40, "raw_input": "I worked on Alpha..."}
]
missing_employees: ["Bob"]
        │
        ▼ (validate)
master_dataset: {
  "week": "2026-W10", "submission_count": 9, "total_employees": 10,
  "summary": {"by_person": {...}, "by_project": {...}, "by_department": {...}}
}
insights: {
  "risk_flags": [{"type": "over_allocation", "person": "Alice", "hours": 52}],
  "capacity_flags": {"Engineering": "at_capacity"},
  "recommendations": ["Rebalance Alice's workload"]
}
        │
        ▼ (report)
timesheet_report.html  (Chart.js charts, stat cards, tables, risk flags)
timesheet_data.csv     (flat export)
        │
        ▼ (deliver)
Email → executive    Slack → #timesheets summary    Telegram → executive ping
```

## 7. Checkpoint & Recovery Strategy

- **Checkpoint on node start**: Captures shared memory before node execution begins
- **Checkpoint on node complete**: Captures outputs after successful node completion
- **Crash recovery**: On restart, the executor resumes from the last clean checkpoint
- **Idempotent dispatch**: Even without checkpoints, `dispatch_log.json` prevents duplicate sends
- **Session persistence**: All sessions stored at `~/.hive/agents/timesheet_orchestration/`

## 8. Error Handling

| Scenario | Handling |
|----------|---------|
| Slack API failure | Tool returns error dict, LLM retries or reports to admin |
| Telegram send failure | Logged as `"telegram_status": "error"`, Slack still sent |
| Resend email failure | Error surfaced in deliver node, admin can retry |
| No timesheet replies | `missing_employees` list populated, feedback loop triggers re-dispatch |
| Arithmetic mismatch | `validation_passed = "false"`, feedback loop sends clarification request |
| Node stall (repeated responses) | Framework stall detection kills node after threshold |
| LLM timeout | LiteLLM handles retries with exponential backoff |

## 9. Technology Stack

| Component | Technology |
|-----------|-----------|
| Framework | Aden Graph Executor (Python 3.11+) |
| LLM | Any LiteLLM-compatible provider |
| Tool Protocol | Model Context Protocol (MCP) via FastMCP |
| Slack | Slack Web API (Bot Token, `xoxb-`) |
| Telegram | Telegram Bot API |
| Email | Resend API |
| Charts | Chart.js (CDN, embedded in HTML) |
| Package Manager | uv |
| Linting | ruff |

## 10. Scalability Considerations

**Current design (10 employees)**: Single event loop per node, synchronous tool calls.

**Scaling to 100+**:
- Batch Slack messages (Slack rate limit: 1 msg/sec per token)
- Paginate `conversations.history` (currently limited to 50 messages)
- Shard dispatch across multiple Slack bot tokens

**Scaling to 1000+**:
- Replace Slack channel collection with structured form (Slack workflow or web form)
- Database backend for master dataset (replace JSON file storage)
- Queue-based dispatch with rate limiting
- Horizontal scaling via multiple agent instances with shared state
- Dashboard UI replacing TUI for executive interaction
