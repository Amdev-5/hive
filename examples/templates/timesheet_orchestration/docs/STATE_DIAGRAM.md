# Timesheet Orchestration Agent — Workflow State Diagram

## Mermaid Diagram

Copy the code block below into [mermaid.live](https://mermaid.live) or any Mermaid renderer to generate the visual diagram.

```mermaid
stateDiagram-v2
    direction LR

    [*] --> Intake: start

    state "Node 1: Intake & Setup" as Intake {
        direction TB
        [*] --> ParseRoster: User provides employee data
        ParseRoster --> ValidateRoster: Parse CSV/text → JSON
        ValidateRoster --> ConfigSchedule: Confirm roster
        ConfigSchedule --> SaveConfig: Set schedule, channels, email
        SaveConfig --> [*]: set_output(employee_roster, config)
    }

    Intake --> Dispatch: e1 [on_success]

    state "Node 2: Dispatch Reminders" as Dispatch {
        direction TB
        [*] --> CheckLog: load_data(dispatch_log.json)
        CheckLog --> DetermineTargets: First visit → ALL employees\nRe-visit → missing only
        DetermineTargets --> SendSlack: slack_send_message(@mention)
        SendSlack --> SendTelegram: telegram_send_message(DM)
        SendTelegram --> SaveLog: save_data(dispatch_log.json)
        SaveLog --> [*]: set_output(dispatch_log)
    }

    Dispatch --> Collect: e2 [on_success]

    state "Node 3: Collect Timesheets" as Collect {
        direction TB
        [*] --> ReadChannel: slack_get_channel_history
        ReadChannel --> ExtractData: LLM parses messages → structured JSON
        ExtractData --> ValidateArith: Check hours arithmetic
        ValidateArith --> IdentifyMissing: Cross-ref roster vs submissions
        IdentifyMissing --> AdminReview: Present summary to admin (HIL)
        AdminReview --> [*]: set_output(structured_timesheets,\nmissing_employees)
    }

    Collect --> Validate: e3 [on_success]

    state "Node 4: Validate & Consolidate" as Validate {
        direction TB
        [*] --> RunValidation: Check totals, duplicates, ranges
        RunValidation --> BuildDataset: Consolidate master_dataset
        BuildDataset --> GenInsights: Anomaly detection, capacity flags
        GenInsights --> RouteDecision: Set validation_passed
        RouteDecision --> [*]: set_output(master_dataset, insights,\nvalidation_passed)
    }

    Validate --> Collect: e4 [validation_passed ≠ true] ⟲ Loop 1
    Validate --> Dispatch: e5 [passed + missing employees] ⟲ Loop 2
    Validate --> Report: e6 [validation_passed = true]

    state "Node 5: Generate Report" as Report {
        direction TB
        [*] --> BuildHTML: save_data(report.html) + append_data chunks
        BuildHTML --> AddCharts: Chart.js (bar, horizontal bar, doughnut)
        AddCharts --> AddTable: Detailed breakdown table
        AddTable --> AddFlags: Risk flags + recommendations
        AddFlags --> ExportCSV: csv_write(timesheet_data.csv)
        ExportCSV --> ServeFile: serve_file_to_user(open_in_browser)
        ServeFile --> [*]: set_output(report_file, report_csv, report_uri)
    }

    Report --> Deliver: e7 [on_success]

    state "Node 6: Deliver & Follow-Up" as Deliver {
        direction TB
        [*] --> SendEmail: send_email(executive, HTML summary)
        SendEmail --> PostSlack: slack_send_message(#timesheets summary)
        PostSlack --> PingTelegram: telegram_send_message(executive)
        PingTelegram --> QAMode: "Ask me anything about the data"
        QAMode --> [*]: set_output(delivery_status)
    }

    Deliver --> [*]: Complete
```

## Simplified Flow (ASCII)

```
                    ┌─────────────────────────────────────────┐
                    │            HAPPY PATH                    │
                    │                                         │
 START ──► INTAKE ──► DISPATCH ──► COLLECT ──► VALIDATE ──► REPORT ──► DELIVER ──► END
            (HIL)                   (HIL)        │  │  │               (HIL)
                                                 │  │  │
                        FEEDBACK LOOPS           │  │  │
                    ┌────────────────────────────┘  │  │
                    │  Loop 1: Clarification        │  │
                    │  (validation_passed ≠ true)   │  │
                    ▼                               │  │
                  COLLECT ◄─────────────────────────┘  │
                                                       │
                    ┌──────────────────────────────────┘
                    │  Loop 2: Missing Employees
                    │  (passed but missing_employees)
                    ▼
                  DISPATCH ◄───────────────────────────┘
```

## Edge Priority Resolution

When multiple conditional edges leave the VALIDATE node:

```
VALIDATE completes
    │
    ├── Priority 3: e5 → DISPATCH  (if passed AND missing employees)
    │       Evaluated FIRST. If true, takes this path.
    │
    ├── Priority 2: e4 → COLLECT   (if NOT passed)
    │       Evaluated SECOND. If true, takes this path.
    │
    └── Priority 1: e6 → REPORT    (if passed, no issues)
            Evaluated LAST. Default happy path.
```

## Channel Flow Diagram

```
                    AGENT
                   ┌─────┐
                   │     │
          ┌────────┤     ├────────┐
          │        │     │        │
          ▼        │     │        ▼
    ┌──────────┐   │     │  ┌──────────┐
    │  SLACK   │◄──┤     │  │ TELEGRAM │
    │          │───►│     │  │          │
    │ send +   │   │     │  │ send     │
    │ read     │   │     │  │ only     │
    └──────────┘   │     │  └──────────┘
                   │     │
                   │     │        ┌──────────┐
                   │     ├───────►│  EMAIL   │
                   │     │        │ (Resend) │
                   └─────┘        │ send     │
                                  │ only     │
                                  └──────────┘

    Slack:    Reminders (@mention) + Read submissions (channel history)
    Telegram: Push notifications (reminders, escalation, report ping)
    Email:    Executive report delivery (HTML body)
```

## Checkpoint Diagram

```
  INTAKE          DISPATCH        COLLECT         VALIDATE        REPORT          DELIVER
    │                │               │               │              │               │
    ●─── start ──────●─── start ─────●─── start ─────●─── start ───●─── start ─────●─── start
    │                │               │               │              │               │
    ●─── complete ───●─── complete ──●─── complete ──●─── complete ─●─── complete ──●─── complete
    │                │               │               │              │               │
    ▼                ▼               ▼               ▼              ▼               ▼
  [CP1]            [CP2]           [CP3]           [CP4]          [CP5]           [CP6]

    CP = Checkpoint (shared memory snapshot)
    On crash: resume from last clean CP
    On restart: dispatch checks dispatch_log.json for idempotency
```
