# Timesheet Orchestration Agent — System Design

## 0. Channel Strategy (Why Each Channel Exists)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CHANNEL CAPABILITY MATRIX                         │
├────────────┬──────────┬──────────┬───────────┬──────────────────────┤
│  Channel   │  Send    │  Read    │  Cost     │  Role in System      │
├────────────┼──────────┼──────────┼───────────┼──────────────────────┤
│  Slack     │  ✅      │  ✅      │  Free     │  PRIMARY: 2-way      │
│            │          │          │           │  collection channel  │
│            │          │          │           │  (send + read)       │
├────────────┼──────────┼──────────┼───────────┼──────────────────────┤
│  Telegram  │  ✅      │  ❌      │  Free     │  PUSH: reminders,    │
│            │          │          │           │  escalations, report │
│            │          │          │           │  delivery (1-way)    │
├────────────┼──────────┼──────────┼───────────┼──────────────────────┤
│  Email     │  ✅      │  ❌*     │  Free     │  FORMAL: executive   │
│  (Resend)  │          │          │           │  report + PDF attach │
│            │          │          │           │  (1-way)             │
├────────────┼──────────┼──────────┼───────────┼──────────────────────┤
│  * Gmail   │  ✅      │  ✅      │  Free     │  OPTIONAL: 2-way     │
│  (OAuth)   │          │          │  (complex)│  email collection    │
└────────────┴──────────┴──────────┴───────────┴──────────────────────┘

Design principle: Each channel used for what it's BEST at.
Not "send everything everywhere" — that's a chatbot, not a system.
```

**The flow:**
1. Slack `#timesheets` channel = where employees submit hours (agent reads replies)
2. Telegram = push notifications for reminders + escalations (high visibility, instant)
3. Email = executive report delivery with PDF attachment (formal, archivable)

This is MORE impressive than single-channel because it demonstrates
**channel-appropriate orchestration** — a key evaluation criterion.

## 1. High-Level Architecture

```
                          ┌──────────────────────────────────────────────┐
                          │           EXTERNAL TRIGGERS                  │
                          │  Cron (weekly) ──► HTTP API trigger          │
                          └──────────────┬───────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ADEN GRAPH EXECUTOR                                     │
│                                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────────────┐  │
│  │  INTAKE   │───►│   DISPATCH   │───►│   COLLECT    │───►│    VALIDATE &     │  │
│  │ (setup)   │    │  REMINDERS   │    │  TIMESHEETS  │    │   CONSOLIDATE     │  │
│  │ HIL #1    │    │ Telegram +   │    │ Slack read   │    │                   │  │
│  └──────────┘    │ Slack ping   │    │  HIL #2      │    │                   │  │
│                  └──────┬───────┘    └──────▲───────┘    └────┬──────┬───────┘  │
│                         │                   │                 │      │           │
│                         │         ┌─────────┘                 │      │           │
│                         │         │ FEEDBACK LOOP 1           │      │           │
│                         │         │ (clarification needed)    │      │           │
│                         │                                     │      │           │
│                         │    FEEDBACK LOOP 2                  │      │           │
│                         ◄─────(missing submissions)───────────┘      │           │
│                                                                      │           │
│                                                               ┌──────▼────────┐  │
│                                                               │   GENERATE    │  │
│                                                               │    REPORT     │  │
│                                                               └──────┬────────┘  │
│                                                                      │           │
│                                                               ┌──────▼────────┐  │
│                                                               │   DELIVER &   │  │
│                                                               │   FOLLOW-UP   │  │
│                                                               │   HIL #3      │  │
│                                                               │ Email + Tg    │  │
│                                                               └───────────────┘  │
│                                                                                  │
│  ─── Checkpoints at every node boundary (restart-safe) ───                       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Node Specifications

### Node 1: `intake` (One-time setup)

| Property | Value |
|----------|-------|
| **Type** | `event_loop` |
| **Client-Facing** | Yes (HIL #1) |
| **Input Keys** | `[]` |
| **Output Keys** | `employee_roster`, `config` |
| **Max Visits** | 1 |
| **Tools** | `csv_read`, `excel_read`, `google_sheets_read`, `save_data` |

**What it does:**
- Greets the admin, asks them to provide the employee spreadsheet (10 people with names, roles, departments, channels)
- Parses the spreadsheet into structured JSON
- Asks admin to confirm: reminder schedule (which day/time), preferred channels, executive recipient
- Saves config to memory

**System prompt logic:**
```
1. Ask user to upload/paste employee data
2. Parse into structured format: [{name, role, department, channel, contact_id}]
3. Confirm schedule preferences (e.g., "Monday 9am reminders, Friday 5pm deadline")
4. set_output("employee_roster", <structured JSON>)
5. set_output("config", {schedule, deadline, executive_email, channels})
```

---

### Node 2: `dispatch_reminders`

| Property | Value |
|----------|-------|
| **Type** | `event_loop` |
| **Client-Facing** | No |
| **Input Keys** | `employee_roster`, `config`, `missing_employees` |
| **Output Keys** | `dispatch_log` |
| **Nullable Inputs** | `missing_employees` |
| **Max Visits** | 3 (allows re-dispatch for stragglers) |
| **Tools** | `telegram_send_message`, `slack_send_message`, `time_now` |

**What it does:**
- **Dual-channel dispatch:** Posts to Slack `#timesheets` (where they reply) AND sends Telegram DM (high-visibility nudge)
- On first visit: reminds ALL employees
- On subsequent visits (feedback loop): only `missing_employees` with escalating urgency
- Slack message includes instructions: "Reply in this thread with your hours"

**Escalation logic (via visit count):**
```
Visit 1 — Friendly:
  Slack: "@alice Please share your hours for this week in this thread 🙏"
  Telegram: "Hey Alice! Time to submit your weekly timesheet on Slack #timesheets"

Visit 2 — Firm:
  Slack: "@alice ⏰ Your timesheet is still pending. Deadline in 24h."
  Telegram: "Reminder: Alice, your timesheet is overdue. Please submit on Slack."

Visit 3 — Escalation:
  Slack: "@alice @manager-bob 🚨 Final notice: Alice's timesheet is overdue."
  Telegram: "Final notice: Escalating to your manager."
```

**Data flow out:**
```json
{
  "dispatch_log": [
    {"name": "Alice", "slack_status": "sent", "telegram_status": "sent", "visit": 1},
    {"name": "Bob", "slack_status": "sent", "telegram_status": "sent", "visit": 1}
  ]
}
```

---

### Node 3: `collect_timesheets` (Read from Slack + Extract)

| Property | Value |
|----------|-------|
| **Type** | `event_loop` |
| **Client-Facing** | Yes (HIL #2) |
| **Input Keys** | `employee_roster`, `config`, `clarification_requests` |
| **Output Keys** | `raw_submissions`, `structured_timesheets`, `missing_employees` |
| **Nullable Inputs** | `clarification_requests` |
| **Max Visits** | 3 |
| **Tools** | `slack_get_channel_history`, `slack_send_message`, `telegram_send_message`, `save_data`, `load_data`, `time_now` |

**What it does — the most important node:**

**Step 1: Read Slack replies**
- Calls `slack_get_channel_history` on `#timesheets` channel
- Filters messages from the current week
- Matches messages to employee roster by Slack user ID

**Step 2: LLM extraction (the intelligence layer)**
- Takes unstructured text and extracts structured timesheet data:
  ```
  Raw: "I worked on Project Alpha Mon-Wed, about 5 hours each day on the API.
        Thursday was meetings for Project Beta, maybe 6 hours. Friday I was off."

  → Extracted:
  {
    "person": "Alice",
    "entries": [
      {"project": "Project Alpha", "task": "API development", "hours": 15, "confidence": "medium"},
      {"project": "Project Beta", "task": "Meetings", "hours": 6, "confidence": "high"}
    ],
    "total_hours": 21,
    "blockers": [],
    "raw_input": "<original text preserved for audit>"
  }
  ```
- **Confidence scoring**: "about 5 hours each day" → `medium` (imprecise language)
- **Arithmetic check**: Do entry hours sum to total? If not → flag.

**Step 3: Handle clarifications**
- If `clarification_requests` from validate node (re-visit), ask specific employees via Slack reply:
  "Alice, your hours add up to 21 but you mentioned working 5 days. Can you clarify Friday?"

**Step 4: Identify missing**
- Cross-reference roster vs. submissions → output `missing_employees`

**Why this is client-facing (HIL #2):**
- Admin can intervene: "Skip Carol, she's on vacation"
- Admin can manually enter hours for someone who didn't respond
- Agent asks admin to resolve ambiguities it can't handle autonomously

**Extraction schema enforced by prompt:**
```json
{
  "person": "string",
  "week": "2026-W10",
  "entries": [
    {
      "project": "string",
      "task": "string",
      "hours": "number",
      "confidence": "high|medium|low"
    }
  ],
  "total_hours": "number",
  "blockers": ["string"],
  "raw_input": "original text preserved for audit trail"
}
```

---

### Node 4: `validate_consolidate`

| Property | Value |
|----------|-------|
| **Type** | `event_loop` |
| **Client-Facing** | No |
| **Input Keys** | `structured_timesheets`, `employee_roster`, `config` |
| **Output Keys** | `master_dataset`, `insights`, `clarification_requests`, `missing_employees`, `validation_passed` |
| **Max Visits** | 2 |
| **Tools** | `save_data`, `load_data`, `csv_write` |

**What it does — three phases:**

#### Phase A: Validation
- Hours per task sum correctly to total?
- Total hours within reasonable range (0-80)?
- All required fields present?
- No duplicate entries?
- Confidence scoring on extracted data

#### Phase B: Consolidation
```json
// Master dataset structure
{
  "week": "2026-W10",
  "submissions": [...],
  "summary": {
    "total_hours_all": 340,
    "by_person": {"Alice": 40, "Bob": 38, ...},
    "by_project": {"Project Alpha": 120, "Project Beta": 85, ...},
    "by_department": {"Engineering": 200, "Design": 80, ...},
    "allocation_pct": {"Project Alpha": "35.3%", ...}
  }
}
```

#### Phase C: Insight Generation
- Over-allocation flags (>45 hrs/week)
- Under-allocation flags (<30 hrs/week)
- Project imbalance detection
- Workload anomaly vs. previous weeks (if data exists)
- Capacity flags per department
- Risk identification

**Routing decision (output determines next edge):**
```
IF clarification_requests is non-empty → feedback to collect_timesheets
IF missing_employees is non-empty → feedback to dispatch_reminders
IF validation_passed == true → forward to generate_report
```

---

### Node 5: `generate_report`

| Property | Value |
|----------|-------|
| **Type** | `event_loop` |
| **Client-Facing** | No |
| **Input Keys** | `master_dataset`, `insights`, `config` |
| **Output Keys** | `report_file`, `report_csv`, `report_uri` |
| **Max Visits** | 1 |
| **Tools** | `save_data`, `append_data`, `serve_file_to_user`, `csv_write`, `execute_command` |

**What it does:**
Generates a professional executive report in HTML (convertible to PDF).

**Report structure:**
```
┌─────────────────────────────────────────────┐
│  WEEKLY TIMESHEET REPORT — Week 10, 2026    │
├─────────────────────────────────────────────┤
│  EXECUTIVE SUMMARY                          │
│  • 10/10 employees submitted (100%)         │
│  • Total: 385 hours across 5 projects       │
│  • 2 risk flags identified                  │
├─────────────────────────────────────────────┤
│  CHARTS (embedded Chart.js / SVG)           │
│  • Hours by Project (bar chart)             │
│  • Hours by Person (horizontal bar)         │
│  • Department Allocation (pie chart)        │
│  • Week-over-Week Trend (line chart)        │
├─────────────────────────────────────────────┤
│  DETAILED BREAKDOWN                         │
│  Person → Project → Task → Hours table      │
├─────────────────────────────────────────────┤
│  RISK FLAGS & OBSERVATIONS                  │
│  • Alice: 52 hrs (over-allocated)           │
│  • Project Gamma: 0 hrs (abandoned?)        │
├─────────────────────────────────────────────┤
│  RECOMMENDATIONS                            │
│  • Rebalance Alice's workload               │
│  • Review Project Gamma staffing            │
└─────────────────────────────────────────────┘
```

**Charts approach:**
- Embed Chart.js via CDN in the HTML `<script>` tag
- LLM generates the data arrays and chart configs inline
- Result: self-contained HTML with interactive charts
- Optional: `execute_command` to run `wkhtmltopdf` for PDF conversion

**Also generates:** CSV export of the master dataset for further analysis.

---

### Node 6: `deliver_report` (Executive delivery + Q&A)

| Property | Value |
|----------|-------|
| **Type** | `event_loop` |
| **Client-Facing** | Yes (HIL #3) |
| **Input Keys** | `report_file`, `report_csv`, `report_uri`, `master_dataset`, `insights` |
| **Output Keys** | `delivery_status` |
| **Max Visits** | 1 |
| **Tools** | `email_send`, `telegram_send_message`, `slack_post`, `serve_file_to_user`, `load_data` |

**What it does:**
- Sends the report to the designated executive via their preferred channel
- Attaches/links the PDF and CSV
- Enters Q&A mode — executive can ask follow-up questions:
  - "How many hours did the design team spend on Project Alpha?"
  - "Who had the lowest utilization this week?"
  - "Compare this week to last week"
- Agent answers from `master_dataset` and `insights` in memory

---

## 3. Edge Map (Complete)

```
ID                           Source              Target              Condition        Expression                                    Priority
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
e1-setup                     intake              dispatch_reminders  on_success       —                                             1
e2-dispatch-to-collect       dispatch_reminders  collect_timesheets  on_success       —                                             1
e3-collect-to-validate       collect_timesheets  validate_consolidate on_success      —                                             1

── FEEDBACK LOOP 1: Clarification ──
e4-validate-to-collect       validate_consolidate collect_timesheets  conditional     str(validation_passed).lower() != 'true'      2
                                                                                      AND clarification_requests is non-empty

── FEEDBACK LOOP 2: Missing submissions ──
e5-validate-to-dispatch      validate_consolidate dispatch_reminders  conditional     len(missing_employees) > 0                    2
                                                                                      AND validation_passed != 'true'

── HAPPY PATH: All validated ──
e6-validate-to-report        validate_consolidate generate_report     conditional     str(validation_passed).lower() == 'true'      1
e7-report-to-deliver         generate_report     deliver_report       on_success      —                                             1
```

### Visual Edge Flow

```
              ┌─────────────────────────── e5 (missing) ────────────────────┐
              │                                                              │
              ▼                                                              │
  [intake] ──e1──► [dispatch] ──e2──► [collect] ──e3──► [validate] ──e6──► [report] ──e7──► [deliver]
                                         ▲                   │
                                         │                   │
                                         └──── e4 (clarify) ─┘
```

**Feedback loop termination:** `max_node_visits` prevents infinite loops:
- `dispatch_reminders`: max 3 visits (initial + 2 follow-ups)
- `collect_timesheets`: max 3 visits (initial + 2 clarification rounds)
- `validate_consolidate`: max 2 visits

If max visits exceeded, executor moves to next priority edge (the happy path).

---

## 4. Memory (Shared State) Flow

Memory is the shared key-value store that flows between nodes. Here's what exists at each stage:

```
After INTAKE:
  ├── employee_roster: [{name, role, dept, channel, contact_id}, ...]
  └── config: {schedule, deadline, executive, channels}

After DISPATCH:
  └── dispatch_log: [{name, channel, status, timestamp}, ...]

After COLLECT:
  ├── raw_submissions: [{person, raw_text}, ...]
  ├── structured_timesheets: [{person, entries: [{project, task, hours}], total}, ...]
  └── missing_employees: ["Carol", "Dave"]

After VALIDATE:
  ├── master_dataset: {week, submissions, summary: {by_person, by_project, by_dept}}
  ├── insights: {risk_flags, anomalies, recommendations}
  ├── clarification_requests: [{person, issue, question}, ...]
  ├── missing_employees: [...]
  └── validation_passed: "true" | "false"

After REPORT:
  ├── report_file: "timesheet_report_W10.html"
  ├── report_csv: "timesheet_data_W10.csv"
  └── report_uri: "file:///path/to/report.html"

After DELIVER:
  └── delivery_status: {sent_to, channel, timestamp, followup_questions: [...]}
```

---

## 5. Checkpoint & Restart Safety

Aden creates checkpoints at every node boundary automatically:

```
Checkpoint 1: [node_start]  intake
Checkpoint 2: [node_complete] intake → memory has employee_roster, config
Checkpoint 3: [node_start]  dispatch_reminders
Checkpoint 4: [node_complete] dispatch_reminders → memory has dispatch_log
...
```

**Crash scenario:** Agent crashes after sending reminders but before collecting timesheets.
- On restart: executor loads latest clean checkpoint (after dispatch_reminders)
- Resumes at `collect_timesheets` — no duplicate reminders sent
- Memory intact with all previous outputs

**Idempotency:** Each node can check `dispatch_log` to avoid re-sending to people already notified.

---

## 6. Multi-Channel Architecture (Purpose-Driven)

```
┌──────────────────────────────────────────────────────────────────┐
│                    CHANNEL USAGE BY NODE                          │
├──────────────────┬───────────┬───────────┬───────────────────────┤
│  Node            │ Slack     │ Telegram  │ Email (Resend)        │
├──────────────────┼───────────┼───────────┼───────────────────────┤
│  dispatch        │ WRITE     │ WRITE     │  —                    │
│  (reminders)     │ @mention  │ DM nudge  │                       │
├──────────────────┼───────────┼───────────┼───────────────────────┤
│  collect         │ READ ✅   │  —        │  —                    │
│  (timesheets)    │ history   │           │                       │
├──────────────────┼───────────┼───────────┼───────────────────────┤
│  validate        │ WRITE     │ WRITE     │  —                    │
│  (clarify)       │ ask back  │ escalate  │                       │
├──────────────────┼───────────┼───────────┼───────────────────────┤
│  deliver         │ WRITE     │ WRITE     │ WRITE                 │
│  (report)        │ summary   │ PDF file  │ formal report + CSV   │
└──────────────────┴───────────┴───────────┴───────────────────────┘

Key insight: Slack is the ONLY 2-way channel (read + write).
Telegram and Email are 1-way push channels.
This is intentional — it's channel-appropriate design.
```

---

## 7. HIL (Human-in-Loop) Strategy

The assignment requires max 3 HIL interventions. Here's the strategic justification:

| HIL | Node | Justification |
|-----|------|--------------|
| **HIL #1** | `intake` | Admin must configure the system — employee data, schedule, channels. Cannot be automated. |
| **HIL #2** | `collect_timesheets` | Employees submit their hours conversationally. This IS the core interaction. |
| **HIL #3** | `deliver_report` | Executive receives report and can ask follow-up questions. High-value interaction. |

Everything else (dispatch, validate, consolidate, report generation) runs **fully autonomously**.

---

## 8. Entry Points (External Triggers)

```python
entry_points = {
    "start": "intake",              # First-time setup (run once)
    "weekly": "dispatch_reminders",  # Cron triggers this every Monday
    "collect": "collect_timesheets", # Webhook when employee responds
}
```

**Cron setup (external):**
```bash
# Every Monday at 9am
0 9 * * 1 curl -X POST http://localhost:8080/api/sessions/{id}/trigger \
  -d '{"entry_point_id": "weekly", "input_data": {"week": "2026-W10"}}'
```

---

## 9. Tools Required

| Tool | Used By | Purpose |
|------|---------|---------|
| `telegram_send_message` | dispatch, collect, deliver | Send/receive via Telegram |
| `email_send` | dispatch, collect, deliver | Send via Email |
| `slack_post` | dispatch, deliver | Post to Slack |
| `csv_read` | intake | Parse employee spreadsheet |
| `excel_read` | intake | Parse .xlsx spreadsheet |
| `csv_write` | validate, report | Export data as CSV |
| `save_data` | collect, validate, report | Persist structured data |
| `load_data` | collect, validate, deliver | Read back persisted data |
| `append_data` | report | Build HTML report incrementally |
| `serve_file_to_user` | report, deliver | Generate clickable file URIs |
| `execute_command` | report | Run wkhtmltopdf for PDF |
| `time_now` | dispatch, collect | Timezone-aware timestamps |
| `google_sheets_read` | intake | Alternative spreadsheet source |

---

## 10. Credentials Required

```
# LLM (you have this)
ZAI_API_KEY                  — Zhipu GLM for all nodes (FREE)

# Communication — ALL FREE
SLACK_BOT_TOKEN              — Slack: 2-way collection channel
                               Setup: api.slack.com → Create App → Bot Token
                               Scopes: chat:write, channels:history, channels:read

TELEGRAM_BOT_TOKEN           — Telegram: push notifications
                               Setup: @BotFather on Telegram → /newbot → get token

RESEND_API_KEY               — Email: executive report delivery
                               Setup: resend.com → signup → API Keys → Create

Total cost: $0
Total setup time: ~15 minutes
```

---

## 11. Goal Definition

```python
Goal(
    id="timesheet-orchestration",
    name="Timesheet Orchestration Agent",
    description="Autonomously collect weekly timesheets from 10 team members "
                "across multiple channels, validate and consolidate data, "
                "generate executive insights, and deliver a professional report.",
    success_criteria=[
        SuccessCriterion(
            id="collection-rate",
            description="Collect timesheets from >=90% of employees",
            metric="submission_rate", target=">=0.9", weight=0.25,
        ),
        SuccessCriterion(
            id="data-accuracy",
            description="All submitted hours pass arithmetic validation",
            metric="validation_pass_rate", target=">=0.95", weight=0.25,
        ),
        SuccessCriterion(
            id="report-quality",
            description="Executive report contains charts, insights, and risk flags",
            metric="report_completeness", target=">=0.9", weight=0.3,
        ),
        SuccessCriterion(
            id="delivery-success",
            description="Report delivered to executive within 24h of deadline",
            metric="delivery_latency_hours", target="<=24", weight=0.2,
        ),
    ],
    constraints=[
        Constraint(id="max-3-hil", description="Maximum 3 human-in-loop points",
                   constraint_type="hard", category="workflow"),
        Constraint(id="no-hallucinated-hours", description="Never fabricate timesheet data",
                   constraint_type="hard", category="accuracy"),
        Constraint(id="privacy", description="Timesheet data not shared between employees",
                   constraint_type="hard", category="security"),
        Constraint(id="idempotent-reminders", description="No duplicate reminders on restart",
                   constraint_type="hard", category="reliability"),
    ],
)
```

---

## 12. Evaluation Dimensions Mapping

How this design scores against the assignment's 8 evaluation criteria:

| Dimension | How We Address It |
|-----------|-------------------|
| **Systems Thinking** | 6-node DAG with 2 feedback loops, 3 entry points, checkpoint recovery. Not a linear chatbot — a real orchestration system. |
| **Workflow Architecture** | Explicit edge conditions, priority-based routing, max_node_visits for loop termination, parallel-ready fan-out potential. |
| **Tool Orchestration** | 14 MCP tools orchestrated by LLM per-node. Channel routing decided dynamically. No hardcoded tool sequences. |
| **Prompt Engineering** | Each node has a focused system prompt with step-by-step instructions, structured output schemas, and extraction confidence scoring. |
| **Data Modeling** | Strict schema: Person → Project → Task → Hours. Summary aggregations at multiple levels. Master dataset in memory + CSV export. |
| **Error Handling** | Feedback loops for validation failures, escalating reminders for non-response, checkpoint restart, max_visits termination. |
| **Executive Communication** | HTML report with Chart.js charts, structured summaries, risk flags, recommendations. Not a data dump — an executive briefing. |
| **Engineering Discipline** | Aden framework handles checkpointing, tool registration, credential encryption, memory management. Clean separation of concerns. |

---

## 13. Bonus Capabilities Plan

| Bonus | Approach |
|-------|----------|
| **Voice input** | Add `vision_tool` or Whisper API tool. Transcribe voice notes before extraction. |
| **Adaptive surveys** | Load previous week's data in `dispatch_reminders`. Pre-fill known projects: "Last week you worked on Alpha (20h) and Beta (15h). Same this week?" |
| **Confidence scoring** | LLM assigns `high/medium/low` confidence per extracted entry. Flag `low` for clarification. |
| **Anomaly detection** | Compare current week vs. rolling 4-week average. Flag >20% deviation. |
| **Real-time dashboard** | Generate a live HTML page with auto-refresh, served via `serve_file_to_user`. |
| **Reasoning logs** | Every node's LLM conversation is persisted in session transcripts. Full transparency. |
| **Health monitoring** | Aden has built-in session state tracking, checkpoint metrics, and execution path logging. |
| **Scalability (1000+)** | Fan-out pattern: batch employees into groups of 50, process in parallel branches. |

---

## 14. Implementation Sequence

```
Session 1 (3h): /hive-create → build goal, 6 nodes, 7 edges, export agent.json
Session 2 (2h): Set up Telegram bot, configure credentials, test dispatch + collect
Session 3 (2h): Test full flow with mock data, tune report generation
Session 4 (1h): Record demo video, write reflection note, push to repo
```
