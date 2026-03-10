## Title

[Feature]: Add example/template agent: Timesheet Orchestration Agent

## Labels

`enhancement`, `size: large`

---

## Problem Statement

The current template agents (`job_hunter`, `professional_rewriter`, etc.) are relatively simple — linear pipelines with few nodes and no feedback loops. There is no template that demonstrates:

1. **Feedback loops** with conditional edges and re-entry into earlier nodes
2. **Multi-channel communication** (Slack 2-way + Telegram 1-way push + Email delivery)
3. **Autonomous data collection** from live Slack channel history
4. **Executive-grade report generation** with embedded charts (Chart.js)
5. **Idempotent dispatch** with checkpoint-safe restart behavior
6. **Complex edge routing** with priority-based conditional expressions

New contributors and users need a reference implementation that exercises the full power of the graph executor.

## Proposed Solution

### Architecture: 6 Nodes, 7 Edges, 2 Feedback Loops

```
[intake] ──► [dispatch] ──► [collect] ──► [validate] ──► [report] ──► [deliver]
                ▲               ▲              │
                │               └── e4 ────────┘ (clarification needed)
                └────────── e5 ────────────────┘ (missing submissions)
```

### Nodes

| # | Node | Type | Client-Facing | Purpose |
|---|------|------|:---:|---------|
| 1 | `intake` | event_loop | Yes (HIL #1) | Parse employee roster, configure schedule/channels/executive |
| 2 | `dispatch-reminders` | event_loop | No | Send reminders via Slack @mentions + Telegram DMs. Escalation tiers on re-visit |
| 3 | `collect-timesheets` | event_loop | Yes (HIL #2) | Read Slack channel history, extract structured timesheet data via LLM, identify missing |
| 4 | `validate-consolidate` | event_loop | No | Validate arithmetic, detect anomalies, generate insights, route via conditional edges |
| 5 | `generate-report` | event_loop | No | Build HTML report with Chart.js charts (bar, horizontal bar, doughnut), export CSV |
| 6 | `deliver-report` | event_loop | Yes (HIL #3) | Deliver via Email (Resend) + Slack summary, enter executive Q&A mode |

### Edges

| Edge | Source → Target | Condition | Priority | Purpose |
|------|----------------|-----------|:---:|---------|
| e1 | intake → dispatch | on_success | 1 | Happy path |
| e2 | dispatch → collect | on_success | 1 | Happy path |
| e3 | collect → validate | on_success | 1 | Happy path |
| e4 | validate → collect | conditional: `validation_passed != 'true'` | 2 | **Feedback loop 1**: clarification needed |
| e5 | validate → dispatch | conditional: `validation_passed == 'true' and missing_employees` | 3 | **Feedback loop 2**: re-remind missing employees |
| e6 | validate → report | conditional: `validation_passed == 'true'` | 1 | Happy path continues |
| e7 | report → deliver | on_success | 1 | Happy path |

### Channel Strategy

| Channel | Direction | Use Case | Tools |
|---------|-----------|----------|-------|
| Slack | 2-way (send + read) | Primary collection: @mention reminders, read timesheet replies from channel history | `slack_send_message`, `slack_get_channel_history` |
| Telegram | 1-way push | High-visibility DM nudges for reminders and escalation | `telegram_send_message`, `telegram_send_document` |
| Email (Resend) | 1-way push | Executive report delivery with HTML body | `send_email` |

### Tools Used (13 total)

`slack_send_message`, `slack_get_channel_history`, `telegram_send_message`, `telegram_send_document`, `send_email`, `csv_read`, `csv_write`, `excel_read`, `save_data`, `load_data`, `append_data`, `serve_file_to_user`, `get_current_time`

### Key Features

- **Idempotent dispatch**: Checks `dispatch_log.json` before sending to prevent duplicate reminders on restart
- **Escalation tiers**: Visit 1 (friendly) → Visit 2 (firm) → Visit 3 (manager escalation)
- **LLM-based extraction**: Parses unstructured Slack messages into structured timesheet JSON with confidence scoring
- **Anomaly detection**: Over/under-allocation flags, capacity analysis, actionable recommendations
- **Incremental report building**: Uses `save_data` + `append_data` to build HTML in chunks (token-safe)
- **Chart.js integration**: Bar chart (hours by project), horizontal bar (hours by person), doughnut (department allocation)
- **3 entry points**: `start` (full pipeline), `weekly` (cron trigger for reminders), `collect` (webhook trigger)
- **Checkpoint-safe**: Automatic checkpointing at node boundaries for crash recovery

### File Structure

```
examples/templates/timesheet_orchestration/
├── __init__.py
├── __main__.py          # CLI: run, tui, info, validate commands
├── agent.py             # Graph construction, edges, goal, agent class
├── config.py            # RuntimeConfig integration
├── mcp_servers.json     # MCP tool server config
├── .env.example         # Required environment variables
├── README.md            # Setup guide and architecture docs
└── nodes/
    └── __init__.py      # All 6 NodeSpec definitions with system prompts
```

## Credentials Required

| Service | Env Var | Purpose | Free Tier |
|---------|---------|---------|:---------:|
| Any LiteLLM-compatible LLM | Per provider (e.g. `ANTHROPIC_API_KEY`) | LLM inference | Varies by provider |
| Slack Bot | `SLACK_BOT_TOKEN` | Send messages + read channel history | Yes |
| Telegram Bot | `TELEGRAM_BOT_TOKEN` | Push notifications | Yes |
| Resend | `RESEND_API_KEY` | Email delivery | Yes (100/day) |

LLM provider is configurable via `~/.hive/configuration.json` (any LiteLLM-supported provider works). All communication channels are free-tier compatible.

## Slack Bot Scopes Required

`chat:write`, `chat:write.public`, `channels:read`, `channels:history`, `users:read`

## Acceptance Criteria

- [ ] Agent runs end-to-end: intake → dispatch → collect → validate → report → deliver
- [ ] Slack reminders sent with @mentions, channel history read for submissions
- [ ] Telegram DMs sent to employees with `telegram_chat_id`
- [ ] Executive HTML report generated with Chart.js charts and served to user
- [ ] Email delivered via Resend with report summary
- [ ] Feedback loop 1 fires when validation finds issues (validate → collect)
- [ ] Feedback loop 2 fires when employees are missing (validate → dispatch)
- [ ] Idempotent: no duplicate reminders on restart
- [ ] `python -m examples.templates.timesheet_orchestration validate` passes
- [ ] `python -m examples.templates.timesheet_orchestration info` shows correct topology
- [ ] All code passes `ruff check` and `ruff format`
- [ ] `.env.example` documents all required variables
- [ ] README.md includes setup guide, architecture diagram, and demo instructions

## Additional Context

This agent exercises framework capabilities not covered by any existing template:
- `EdgeCondition.CONDITIONAL` with `condition_expr` and priority-based routing
- `max_node_visits > 1` for feedback loop termination
- `nullable_output_keys` for optional inter-node data flow
- Multi-tool orchestration across 3 external APIs in a single pipeline
- `conversation_mode: continuous` with `identity_prompt`
- Multiple `EntryPointSpec` definitions (manual, cron, webhook)

Designed to serve as the go-to reference for building production-grade multi-channel agents on the framework.

**Reference Implementation**: `job_hunter` in `examples/templates/` — follows the same structure and patterns but with simpler linear flow.

**Validation Test**:
```bash
uv run python -m examples.templates.timesheet_orchestration validate
# Output: Agent structure is valid.

uv run python -m examples.templates.timesheet_orchestration info
# Output: Nodes: intake, dispatch-reminders, collect-timesheets, validate-consolidate, generate-report, deliver-report
#         HIL Points: intake, collect-timesheets, deliver-report
#         Feedback Loops: 2
```
