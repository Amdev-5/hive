"""Node definitions for Timesheet Orchestration Agent.

6 nodes, 7 edges, 2 feedback loops, 3 HIL points.

Channel strategy:
- Slack: 2-way (send + read) — primary collection channel
- Telegram: 1-way push — reminders and escalations
- Email (Resend): 1-way push — executive report delivery
"""

from framework.graph import NodeSpec

# ─────────────────────────────────────────────────────────────
# Node 1: INTAKE (HIL #1 — admin setup)
# ─────────────────────────────────────────────────────────────
intake_node = NodeSpec(
    id="intake",
    name="Intake & Setup",
    description=(
        "One-time setup: collect employee spreadsheet, configure reminder "
        "schedule, set executive recipient, validate roster data"
    ),
    node_type="event_loop",
    client_facing=True,
    max_node_visits=1,
    input_keys=[],
    output_keys=["employee_roster", "config"],
    success_criteria=(
        "Employee roster parsed with name, role, department, slack_user_id for "
        "each person. Config includes schedule, deadline, executive email, "
        "sender email, and Slack channel."
    ),
    system_prompt="""\
You are a timesheet system setup assistant. Your ONLY job is to parse employee \
data and save configuration.

STEP 1: The user will provide employee data (CSV or pasted text). Parse it into JSON.
Required per employee: name, role, department, slack_user_id.
Optional: telegram_chat_id, manager_name.

STEP 2: Ask for configuration (or use defaults if user provided them):
- Reminder day/time (default: Monday 9am)
- Deadline day/time (default: Friday 5pm)
- Executive name + email for reports
- Sender email for Resend (from_email). If unknown, leave blank and rely on EMAIL_FROM.
- Optional executive Telegram chat ID for report pings
- Slack channel ID or name for collection (default: timesheets)

STEP 3: You MUST call these two tool calls to finish:
- set_output("employee_roster", <JSON array of employees>)
- set_output("config", {"reminder_day": "Monday", "reminder_time": "09:00", \
"deadline_day": "Friday", "deadline_time": "17:00", "executive_name": "...", \
"executive_email": "...", "sender_email": "", "executive_telegram_chat_id": "", \
"slack_channel": "..."})

If the user provides all data upfront, skip asking and go straight to STEP 3.
Do NOT proceed without calling set_output for both keys.
""",
    tools=["csv_read", "excel_read", "save_data"],
)

# ─────────────────────────────────────────────────────────────
# Node 2: DISPATCH REMINDERS (autonomous)
# ─────────────────────────────────────────────────────────────
dispatch_node = NodeSpec(
    id="dispatch-reminders",
    name="Dispatch Reminders",
    description=(
        "Send weekly timesheet reminders via Slack (@mention in #timesheets) "
        "and Telegram (DM push). Escalates on re-visits for missing employees."
    ),
    node_type="event_loop",
    client_facing=False,
    max_node_visits=3,
    input_keys=["employee_roster", "config", "missing_employees"],
    output_keys=["dispatch_log"],
    nullable_output_keys=["missing_employees"],
    success_criteria=(
        "All target employees have been sent reminders via Slack and Telegram. "
        "Dispatch log saved for idempotency."
    ),
    system_prompt="""\
You are a reminder dispatcher. Your ONLY job is to SEND messages. \
Do NOT read channel history. Do NOT look for files. Just SEND reminders.

STEP 0: Load existing dispatch history for idempotency.
- Try: load_data("dispatch_log.json")
- If prior log exists, avoid duplicate reminder sends for the same employee in the same run.

STEP 1: Check who to notify.
- If missing_employees is empty or null: notify ALL employees from employee_roster.
- If missing_employees has names: notify only those people (this is a follow-up).

STEP 2: For EACH target employee, do these tool calls:

a) Send Slack message to the channel from config:
   slack_send_message(channel=config.slack_channel, text="Hey <@SLACK_ID>! ...")

   Use channel ID if available (e.g. "C0AK2E7PFK5"), otherwise use channel name.

b) If the employee has a telegram_chat_id, send Telegram DM:
   telegram_send_message(chat_id=telegram_chat_id, text="Hi NAME, ...")

Message tone for first visit (friendly):
"Hey <@{slack_user_id}>! Time to submit your weekly timesheet. Reply here \
with: projects worked on, tasks completed, and hours per task. \
Deadline: {config.deadline_day} {config.deadline_time}."

STEP 3: After ALL messages are sent, you MUST call:
   save_data("dispatch_log.json", <log array>)
   set_output("dispatch_log", <log array>)

The log array format: [{"name": "...", "slack_status": "sent", \
"telegram_status": "sent|skipped|error", "visit": 1, "timestamp": "..."}]

CRITICAL RULES:
- Do NOT call load_data to look for channel messages. That is NOT your job.
- Do NOT try to collect or read timesheets. Another node handles that.
- Your ONLY tools are: slack_send_message, telegram_send_message, \
get_current_time, save_data, load_data (only for dispatch_log.json).
- You MUST call set_output("dispatch_log", ...) to finish this node.
""",
    tools=[
        "slack_send_message",
        "telegram_send_message",
        "get_current_time",
        "save_data",
        "load_data",
    ],
)

# ─────────────────────────────────────────────────────────────
# Node 3: COLLECT TIMESHEETS (HIL #2 — admin oversight)
# ─────────────────────────────────────────────────────────────
collect_node = NodeSpec(
    id="collect-timesheets",
    name="Collect Timesheets",
    description=(
        "Read Slack channel history to collect employee timesheet submissions. "
        "Extract structured data from unstructured text using LLM. Track missing."
    ),
    node_type="event_loop",
    client_facing=True,
    max_node_visits=3,
    input_keys=["employee_roster", "config", "clarification_requests"],
    output_keys=["raw_submissions", "structured_timesheets", "missing_employees"],
    nullable_output_keys=["clarification_requests"],
    success_criteria=(
        "Structured timesheet data extracted for each responding employee. "
        "Missing employees identified. Arithmetic validated."
    ),
    system_prompt="""\
You are a timesheet data collector. Your job is to READ Slack channel history \
and extract timesheet submissions.

STEP 1: Read the Slack channel to find timesheet replies.
Call: slack_get_channel_history(channel=config.slack_channel, limit=50)
Use channel ID if available (e.g. "C0AK2E7PFK5"), otherwise channel name.

STEP 2: Match messages to employees from employee_roster by their Slack user ID.
For each employee who replied, extract:
{
  "person": "name",
  "entries": [{"project": "...", "task": "...", "hours": N}],
  "total_hours": N,
  "raw_input": "original message"
}

STEP 3: Check arithmetic — do entry hours add up to total_hours?

STEP 4: Identify who is MISSING (in roster but did not reply).

STEP 5: Present summary to the admin (this is a client-facing node):
"Collected X/Y timesheets. Missing: [names]. Should I proceed or wait?"

STEP 6: After admin confirms, you MUST call all three:
  set_output("raw_submissions", <raw message data>)
  set_output("structured_timesheets", <structured JSON array>)
  set_output("missing_employees", <list of missing names or empty list>)

RULES:
- Never fabricate hours. Only extract from actual Slack messages.
- If no replies found, set structured_timesheets to empty array and list all as missing.
- You MUST call set_output for all three keys to finish this node.
""",
    tools=[
        "slack_get_channel_history",
        "slack_send_message",
        "telegram_send_message",
        "save_data",
        "load_data",
        "get_current_time",
    ],
)

# ─────────────────────────────────────────────────────────────
# Node 4: VALIDATE & CONSOLIDATE (autonomous)
# ─────────────────────────────────────────────────────────────
validate_node = NodeSpec(
    id="validate-consolidate",
    name="Validate & Consolidate",
    description=(
        "Validate timesheet data, consolidate into master dataset, generate "
        "insights including anomaly detection and capacity flags."
    ),
    node_type="event_loop",
    client_facing=False,
    max_node_visits=2,
    input_keys=["structured_timesheets", "employee_roster", "config"],
    output_keys=[
        "master_dataset",
        "insights",
        "clarification_requests",
        "missing_employees",
        "validation_passed",
    ],
    success_criteria=(
        "All timesheets validated. Master dataset consolidated with summary "
        "statistics. Insights generated with risk flags."
    ),
    system_prompt="""\
You are a timesheet validator. Validate data and generate insights.

PHASE A — VALIDATE each timesheet:
1. Do per-task hours sum correctly? Flag if >1hr off.
2. Is total_hours in range 1-80?
3. Are all fields present (project, task, hours)?
4. Any low-confidence entries?
Build clarification_requests: [{"person": "...", "issue": "...", "question": "..."}]

PHASE B — CONSOLIDATE into master_dataset:
{
  "week": "ISO week string",
  "submission_count": N,
  "total_employees": N,
  "submissions": [<all structured timesheets>],
  "summary": {
    "total_hours_all": N,
    "by_person": {"Name": hours},
    "by_project": {"Project": hours},
    "by_department": {"Dept": hours}
  }
}

PHASE C — GENERATE insights:
{
  "risk_flags": [{"type": "over_allocation", "person": "...", "hours": N}],
  "anomalies": ["..."],
  "capacity_flags": {"Dept": "at_capacity|under_utilized"},
  "recommendations": ["..."]
}

PHASE D — OUTPUT (you MUST call ALL of these):
  set_output("master_dataset", <dataset>)
  set_output("insights", <insights>)
  set_output("clarification_requests", <list or empty list>)
  set_output("missing_employees", <list or empty list>)
  set_output("validation_passed", "true" or "false")

Set validation_passed="false" if clarification_requests is non-empty.
Set validation_passed="true" if data quality is clean, even when some employees are missing.
Save master_dataset with save_data("master_dataset.json", ...) for persistence.
""",
    tools=["save_data", "load_data", "csv_write"],
)

# ─────────────────────────────────────────────────────────────
# Node 5: GENERATE REPORT (autonomous)
# ─────────────────────────────────────────────────────────────
report_node = NodeSpec(
    id="generate-report",
    name="Generate Report",
    description=(
        "Generate a professional executive HTML report with embedded Chart.js "
        "charts, structured summaries, insights, and risk flags. Also export CSV."
    ),
    node_type="event_loop",
    client_facing=False,
    max_node_visits=1,
    input_keys=["master_dataset", "insights", "config"],
    output_keys=["report_file", "report_csv", "report_uri"],
    success_criteria=(
        "HTML report generated with charts, summaries, risk flags. "
        "CSV export created. File URIs ready for delivery."
    ),
    system_prompt="""\
You are a report generator. Build a professional HTML timesheet report.

Build the report in chunks using save_data then append_data.

STEP 1: save_data("timesheet_report.html", <HTML head with CSS>)
Include:
- Clean CSS (sans-serif font, max-width 1000px, stat cards, risk flags, tables)
- Chart.js CDN: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

STEP 2: append_data("timesheet_report.html", <executive summary>)
Include stat cards: Total Hours, Submission Rate, Projects Active, Risk Flags.

STEP 3: append_data("timesheet_report.html", <charts section>)
Add Chart.js charts using data from master_dataset.summary:
- Bar chart: Hours by Project
- Horizontal bar: Hours by Person
- Doughnut: Department Allocation

STEP 4: append_data("timesheet_report.html", <detail table>)
Person | Project | Task | Hours table.

STEP 5: append_data("timesheet_report.html", <risk flags + recommendations>)
From insights.risk_flags and insights.recommendations.

STEP 6: append_data("timesheet_report.html", "</body></html>")

STEP 7: csv_write(path="timesheet_data.csv", columns=["person","project","task","hours","total_hours"], rows=<all entries as rows>)

STEP 8: serve_file_to_user("timesheet_report.html", open_in_browser=true)

STEP 9: You MUST call all three:
  set_output("report_file", "timesheet_report.html")
  set_output("report_csv", "timesheet_data.csv")
  set_output("report_uri", <URI from serve_file_to_user>)
""",
    tools=[
        "save_data",
        "append_data",
        "serve_file_to_user",
        "csv_write",
    ],
)

# ─────────────────────────────────────────────────────────────
# Node 6: DELIVER & FOLLOW-UP (HIL #3 — executive Q&A)
# ─────────────────────────────────────────────────────────────
deliver_node = NodeSpec(
    id="deliver-report",
    name="Deliver & Follow-Up",
    description=(
        "Send executive report via Email (Resend) and Telegram. Enter Q&A mode "
        "for executive follow-up questions about the timesheet data."
    ),
    node_type="event_loop",
    client_facing=True,
    max_node_visits=1,
    input_keys=[
        "report_file",
        "report_csv",
        "report_uri",
        "master_dataset",
        "insights",
        "employee_roster",
        "config",
    ],
    output_keys=["delivery_status"],
    success_criteria=(
        "Report delivered to executive via email. Executive can ask follow-up "
        "questions and receive data-driven answers."
    ),
    system_prompt="""\
You are delivering the weekly timesheet report. Send it via all channels.

STEP 1 — Email:
send_email(to=config.executive_email, subject="Weekly Timesheet Report", \
html="<HTML summary with key stats and report link>", provider="resend", \
from_email=config.sender_email)

If config.sender_email is empty, call send_email without from_email and rely on EMAIL_FROM.

STEP 2 — Telegram (optional executive ping):
If config.executive_telegram_chat_id exists, call:
telegram_send_message(chat_id=config.executive_telegram_chat_id, \
text="Weekly report summary: ...")

STEP 3 — Slack summary:
slack_send_message(channel=config.slack_channel, \
text="Weekly timesheet report generated. X/Y submissions. Z risk flags. \
Full report sent to executive.")

STEP 4 — Tell the admin: "Report delivered! Ask me anything about the data."
Answer follow-up questions using master_dataset and insights.

STEP 5 — When admin is done, you MUST call:
set_output("delivery_status", {"sent_to": "<email>", \
"channels": ["email","slack"] or ["email","telegram","slack"], "timestamp": "..."})
""",
    tools=[
        "send_email",
        "telegram_send_message",
        "telegram_send_document",
        "slack_send_message",
        "load_data",
        "serve_file_to_user",
        "get_current_time",
    ],
)

__all__ = [
    "intake_node",
    "dispatch_node",
    "collect_node",
    "validate_node",
    "report_node",
    "deliver_node",
]
