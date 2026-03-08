# Timesheet Orchestration Agent

Autonomous weekly timesheet collection, validation, and executive reporting across multiple channels.

## Architecture

```
[intake] → [dispatch] → [collect] → [validate] → [report] → [deliver]
              ▲             ▲            │
              │             └── e4 ──────┘ (clarification needed)
              └──────── e5 ──────────────┘ (missing submissions)
```

**6 nodes** | **7 edges** | **2 feedback loops** | **3 HIL points**

## Channel Strategy

| Channel | Direction | Purpose |
|---------|-----------|---------|
| **Slack** | 2-way | Primary collection — send reminders + read replies |
| **Telegram** | 1-way push | High-visibility reminders and escalations |
| **Email (Resend)** | 1-way push | Executive report delivery with PDF |

## Nodes

| # | Node | Client-Facing | Description |
|---|------|:---:|-------------|
| 1 | `intake` | HIL #1 | Admin uploads employee roster, configures schedule |
| 2 | `dispatch-reminders` | — | Sends reminders via Slack + Telegram (escalates) |
| 3 | `collect-timesheets` | HIL #2 | Reads Slack, extracts structured hours via LLM |
| 4 | `validate-consolidate` | — | Validates arithmetic, consolidates, generates insights |
| 5 | `generate-report` | — | Creates HTML report with Chart.js charts + CSV |
| 6 | `deliver-report` | HIL #3 | Sends to executive, enters Q&A mode |

## Feedback Loops

- **e4**: Validation fails → re-collect with clarification requests
- **e5**: Missing submissions → re-dispatch with escalation

Both loops terminate via `max_node_visits` (3 for dispatch/collect, 2 for validate).

## Setup

```bash
# 1. Copy env file and fill in your API keys
cp .env.example .env

# 2. Export env vars from .env for child processes (MCP tools)
set -a; source .env; set +a

# 3. Run the agent
uv run python -m timesheet_orchestration run

# For browser UI, use hive open (TUI is deprecated)
hive open
```

## Credentials

| Variable | Provider | Free? | Where to Get |
|----------|----------|:-----:|-------------|
| `GLM_API_KEY` | Zhipu AI | ✅ | open.bigmodel.cn |
| `SLACK_BOT_TOKEN` | Slack | ✅ | api.slack.com → Create App → Bot Token |
| `TELEGRAM_BOT_TOKEN` | Telegram | ✅ | @BotFather → /newbot |
| `RESEND_API_KEY` | Resend | ✅ | resend.com → API Keys |
| `EMAIL_FROM` | Resend | ✅ | Verified sender/domain in Resend |

Required Slack bot scopes: `chat:write`, `channels:history`, `channels:read`

## Evaluation Criteria Coverage

| Dimension | Implementation |
|-----------|---------------|
| Systems Thinking | 6-node DAG, 2 feedback loops, 3 entry points, checkpoint recovery |
| Workflow Architecture | Conditional edges, priority routing, max_visits termination |
| Tool Orchestration | 14 MCP tools, channel-appropriate routing |
| Prompt Engineering | Per-node system prompts with structured extraction schemas |
| Data Modeling | Person → Project → Task → Hours with confidence scoring |
| Error Handling | Feedback loops, escalation, idempotent reminders, restart-safe |
| Executive Communication | HTML + Chart.js report with risk flags and recommendations |
| Engineering Discipline | Checkpointing, credential encryption, clean separation of concerns |
