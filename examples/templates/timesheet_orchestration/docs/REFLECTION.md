# Reflection Note — Timesheet Orchestration Agent

## 1. Tool & Framework Choice Rationale

### Why Aden Framework (over LangGraph, CrewAI, AutoGen)

I chose to build this on the **Aden graph execution framework** for several reasons:

- **Native graph executor with conditional edges**: Unlike LangGraph which requires manual state machine wiring, Aden's `EdgeCondition.CONDITIONAL` with `condition_expr` provides declarative routing. I can express `"validation_passed != 'true'"` as a string and the framework evaluates it against shared memory using safe AST-based evaluation. No custom router functions needed.

- **Built-in checkpoint/recovery**: Automatic checkpointing at node boundaries with session persistence. On crash, the executor resumes from the last clean checkpoint. This is critical for a production workflow that runs over hours (waiting for employee responses).

- **Model Context Protocol (MCP) for tools**: All 98+ tools are exposed via a single MCP server. The agent doesn't import tool code — it discovers tools at runtime via the protocol. This means adding a new channel (e.g., Microsoft Teams) is just adding a tool to the MCP server, zero changes to the agent graph.

- **Human-in-loop via `client_facing` nodes**: The framework natively supports HIL interaction through the TUI. Marking a node as `client_facing=True` enables bidirectional conversation with the admin during that node's execution. No webhook/callback plumbing required.

- **LiteLLM multi-provider support**: The agent works with any LLM provider — Anthropic, OpenAI-compatible endpoints, Zhipu GLM, etc. Configured once in `~/.hive/configuration.json`, used everywhere.

### Why Slack + Telegram + Email (over WhatsApp)

- **Slack**: The only channel with a free, programmable **read** API (`conversations.history`). WhatsApp Business API costs $0.005-0.08 per conversation and requires business verification. Slack is free for small workspaces and provides bidirectional capability — the agent can both send reminders and read replies from the same channel.

- **Telegram**: Free Bot API with instant delivery. Serves as a high-visibility push channel — employees who miss the Slack notification get a Telegram DM. The Bot API is send-only (no inbox reading without webhooks), which is fine for reminders.

- **Email (Resend)**: Free tier (100 emails/day). Used exclusively for executive report delivery. The HTML email contains a formatted summary with key stats — the executive doesn't need to open a separate dashboard.

### Why Chart.js (over Matplotlib, Plotly)

Chart.js renders in the browser via a CDN script tag. The agent builds HTML incrementally using `save_data` + `append_data`, embedding Chart.js canvas elements with inline data. No server-side rendering, no image generation, no Python dependency. The executive opens the HTML file and sees interactive charts immediately.

## 2. Architecture Tradeoffs

### Tradeoff 1: Slack Channel Collection vs. Structured Forms

**Chosen**: Collect timesheet data from unstructured Slack messages.
**Alternative**: Build a web form or Slack modal for structured input.

The unstructured approach is harder (requires LLM extraction with confidence scoring) but demonstrates the agent's intelligence layer. In production, I'd add a Slack Block Kit form as a secondary input method and fall back to channel history parsing for employees who ignore the form.

### Tradeoff 2: Three HIL Points vs. Fully Autonomous

**Chosen**: 3 HIL points (intake, collect, deliver).
**Why**: The assignment constrains to max 3 HIL. I placed them at high-value decision points:
1. **Intake**: Admin must confirm the parsed roster is correct (garbage in → garbage out)
2. **Collect**: Admin decides whether to proceed with partial submissions or wait
3. **Deliver**: Executive can ask follow-up questions about the data

Everything between HIL points runs autonomously — dispatch, validation, report generation.

### Tradeoff 3: Single-Channel Collection vs. Multi-Channel Aggregation

**Chosen**: Collect only from Slack. Telegram and Email are push-only.
**Why**: Telegram Bot API doesn't support reading user messages without webhook infrastructure. Building a webhook receiver would add deployment complexity (public URL, SSL, ngrok). For a demo, single-channel collection with multi-channel push is the right tradeoff.

### Tradeoff 4: HTML Report vs. PDF

**Chosen**: HTML with embedded Chart.js.
**Alternative**: PDF generation via WeasyPrint or ReportLab.

HTML is more portable (opens in any browser), supports interactive charts, and doesn't require heavy Python dependencies. The agent builds it incrementally in chunks to stay within LLM token limits. For production, I'd add a PDF export option using a headless browser (Playwright) to render the HTML to PDF.

## 3. Defects Encountered & Resolutions

### Defect 1: Slack Credential Resolution Crash
**Symptom**: `KeyError: "Unknown credential 'slack_user'"` when any Slack tool was called.
**Root Cause**: The `_get_user_token()` function in `slack_tool.py` called `credentials.get("slack_user")`, but `"slack_user"` was not registered in `CREDENTIAL_SPECS`. The `CredentialStoreAdapter.get()` raises `KeyError` for unknown credential names.
**Fix**: Wrapped `credentials.get("slack_user")` in a try/except with fallback to `os.getenv("SLACK_USER_TOKEN")`.
**Lesson**: Credential resolution should never crash on optional credentials. Defensive coding at system boundaries.

### Defect 2: Environment Variables Not Reaching MCP Subprocess
**Symptom**: Tools reported "Slack credentials not configured" despite `.env` having correct values.
**Root Cause**: The `.env` loader checked CWD first, found the repo-root `.env` (which had no Slack token), and stopped. The agent-specific `.env` was never loaded.
**Fix**: Changed `.env` loading order to check the agent's package directory first, then CWD. Also loads all found `.env` files instead of stopping at the first match.
**Lesson**: Relative path resolution is a common source of bugs in monorepos. Always check the most specific path first.

### Defect 3: LLM (GLM) Stalling on Dispatch Node
**Symptom**: The dispatch node tried to read channel history (collect node's job) instead of sending reminders. Stalled after 3 similar responses.
**Root Cause**: The system prompts were too long and ambiguous for the GLM model. GLM confused dispatch (sending) with collection (reading). It never called `set_output` to complete the node.
**Fix**: Rewrote all 6 system prompts to be shorter, more directive, with explicit tool call patterns and negative instructions ("Do NOT read channel history. Your ONLY job is to SEND messages."). Added "You MUST call set_output(...) to finish this node" to every prompt.
**Lesson**: Prompt engineering must account for model capability. Prompts that work for Claude may fail for smaller models. Be explicit, not suggestive.

### Defect 4: Resend Email Requires `from_email`
**Symptom**: `send_email` returned `{"error": "Sender email is required"}`.
**Root Cause**: Resend provider requires `from_email` parameter. The `EMAIL_FROM` env var was not set.
**Fix**: Added `EMAIL_FROM=onboarding@resend.dev` to `.env` (Resend's free-tier default sender).
**Lesson**: Read tool source code to understand required vs. optional parameters. Don't rely on LLM's assumptions about defaults.

## 4. Scalability Plan

### Current State: 2-10 Employees
- Single Slack channel, synchronous tool calls
- JSON file storage (`save_data`/`load_data`)
- Single LLM instance, ~100 iterations max

### Phase 2: 50-100 Employees
- **Batch dispatch**: Group Slack messages to avoid rate limits (1 msg/sec)
- **Paginated collection**: `slack_get_channel_history` with cursor pagination
- **Threaded replies**: Use Slack threads per employee to isolate submissions
- **Database storage**: Replace JSON files with SQLite or PostgreSQL for master dataset
- **Parallel validation**: Validate timesheets concurrently

### Phase 3: 500-1000 Employees
- **Structured input**: Replace free-text Slack replies with Slack Block Kit forms or a web portal
- **Queue-based dispatch**: Redis/Celery for rate-limited, parallel message sending
- **Multi-bot tokens**: Distribute across Slack app instances to avoid rate limits
- **Streaming reports**: Generate reports in sections, stream to executive dashboard
- **Multi-tenant**: Workspace isolation, per-org configuration
- **Cron automation**: Remove the manual "start" trigger, run fully on schedule via the `weekly` entry point

### Phase 4: Enterprise (1000+ Employees)
- **Department-level agents**: Shard by department, each with its own collection loop
- **Manager delegation**: Managers collect from their reports, agent aggregates upward
- **Real-time dashboard**: Replace HTML report with live web dashboard (WebSocket updates)
- **Audit trail**: Full logging of every message sent, response received, validation decision
- **SSO integration**: Connect to corporate identity provider for employee roster sync
- **Voice input**: Integrate Whisper API for voice note transcription (bonus capability from assignment)

## 5. What I Would Do Differently

1. **Start with structured input**: Free-text collection is impressive but brittle. A Slack Block Kit form with dropdowns for projects and number inputs for hours would eliminate 80% of validation issues.

2. **Add confidence scoring earlier**: The current system extracts data and validates after. I'd add confidence scores during extraction (high/medium/low) and only request clarification for low-confidence entries.

3. **Use webhooks for Telegram**: With a proper deployment (public URL), Telegram webhooks would enable bidirectional collection — employees could reply to the Telegram DM with their hours.

4. **Test with a larger dataset**: The 2-person demo works well but doesn't stress-test pagination, rate limits, or the insight layer's anomaly detection. I'd generate synthetic data for 50+ employees.

5. **Add monitoring**: The framework has LLM logging (`~/.hive/llm_logs/`), but I'd add structured telemetry — tool call latency, success rates, token usage per node — for production observability.
