# [Integration]: Google Workspace - Gmail, Calendar, Drive & Docs

## Overview

Add integration with Google Workspace APIs to enable agents to manage email, calendar, documents, and cloud storage. Google Workspace is the productivity backbone for millions of businesses - agents need seamless access to automate communication workflows, schedule management, document generation, and file organization.

**Why This Matters:**
- 3+ billion users rely on Google Workspace daily
- Email and calendar are the #1 bottleneck for knowledge workers
- Document automation saves 5-10 hours/week per employee
- Unified workspace access enables true end-to-end workflow automation

## Requirements

Implement the following 14 MCP tools across 4 services:

### Gmail (4 tools)

| Tool | Description |
|------|-------------|
| `gmail_search` | Search emails with Gmail query syntax (from, to, subject, has:attachment, etc.) |
| `gmail_get_message` | Get full email content, attachments, and metadata by message ID |
| `gmail_send` | Send emails with HTML/plain text body, CC/BCC, and attachments |
| `gmail_reply` | Reply to an existing thread maintaining conversation context |

### Google Calendar (4 tools)

| Tool | Description |
|------|-------------|
| `gcal_list_events` | List events within a date range with filtering |
| `gcal_get_event` | Get detailed event information including attendees and conferencing |
| `gcal_create_event` | Create events with attendees, video conferencing, and reminders |
| `gcal_update_event` | Modify existing events (reschedule, add attendees, update description) |

### Google Drive (3 tools)

| Tool | Description |
|------|-------------|
| `gdrive_search` | Search files by name, type, owner, or content |
| `gdrive_get_file` | Download file content or get metadata |
| `gdrive_upload` | Upload files to Drive with folder organization |

### Google Docs/Sheets (3 tools)

| Tool | Description |
|------|-------------|
| `gdocs_create` | Create new Google Doc with initial content |
| `gsheets_read` | Read data from spreadsheet ranges |
| `gsheets_write` | Write data to spreadsheet cells/ranges |

## Authentication

- **Credentials:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
- **Auth Method:** OAuth 2.0 with refresh token
- **Scopes Required:**
  ```
  https://www.googleapis.com/auth/gmail.modify
  https://www.googleapis.com/auth/calendar
  https://www.googleapis.com/auth/drive
  https://www.googleapis.com/auth/documents
  https://www.googleapis.com/auth/spreadsheets
  ```

**Setup Flow:**
1. Create project in Google Cloud Console
2. Enable Gmail, Calendar, Drive, Docs, Sheets APIs
3. Create OAuth 2.0 credentials (Desktop app type)
4. Run OAuth flow to obtain refresh token
5. Store refresh token securely

## Costing

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Gmail API | 1 billion quota units/day | ~250M read operations |
| Calendar API | 1 million queries/day | Generous for most use cases |
| Drive API | 1 billion quota units/day | Varies by operation type |
| Docs/Sheets API | 300 requests/min/user | Per-user rate limiting |

**Note:** All APIs are free within quota limits. No per-request charges.

## Use Cases

### 🎯 Executive Assistant Agent
```
"Prepare my day"
├── gcal_list_events(today) → Get today's meetings
├── gmail_search("is:unread is:important") → Find urgent emails
├── For each meeting:
│   ├── gmail_search(from:{attendee}) → Recent context
│   └── gdrive_search({company_name}) → Related documents
└── Generate: Daily briefing with meeting prep notes
```

### 📧 Inbox Zero Agent
```
"Process my inbox"
├── gmail_search("is:unread") → Get all unread
├── For each email:
│   ├── Classify: urgent/delegate/archive/respond
│   ├── gmail_reply() → Auto-draft responses
│   └── gcal_create_event() → Schedule follow-ups
└── Report: "Processed 47 emails, 12 need your review"
```

### 📅 Meeting Scheduler Agent
```
"Schedule a meeting with John next week"
├── gcal_list_events(next_week) → Find free slots
├── gmail_search("from:john@company.com") → Get John's email
├── gcal_create_event() → Create with Google Meet
└── gmail_send() → Send personalized invite with context
```

### 📊 Report Generator Agent
```
"Create weekly sales report"
├── gsheets_read("Sales Data!A:F") → Pull raw data
├── Process and analyze data
├── gdocs_create() → Generate formatted report
├── gdrive_upload() → Save charts/attachments
└── gmail_send() → Distribute to stakeholders
```

### 🔍 Document Research Agent
```
"Find all contracts mentioning vendor X"
├── gdrive_search("type:document vendor_x") → Find docs
├── For each document:
│   └── gdocs_read() → Extract relevant sections
├── gsheets_write() → Create summary spreadsheet
└── gmail_send() → Share findings with legal team
```

### 📞 Meeting Follow-up Agent
```
After every meeting ends:
├── gcal_get_event(meeting_id) → Get attendees
├── Generate meeting summary from notes
├── gdocs_create() → Create shared meeting notes
├── gmail_send() → Send follow-up to all attendees
└── gcal_create_event() → Schedule follow-up if needed
```

## Implementation Details

### Credential Spec

```python
"google_workspace": CredentialSpec(
    env_var="GOOGLE_WORKSPACE_CREDENTIALS",  # JSON with client_id, client_secret, refresh_token
    tools=[
        "gmail_search", "gmail_get_message", "gmail_send", "gmail_reply",
        "gcal_list_events", "gcal_get_event", "gcal_create_event", "gcal_update_event",
        "gdrive_search", "gdrive_get_file", "gdrive_upload",
        "gdocs_create", "gsheets_read", "gsheets_write",
    ],
    required=True,
    startup_required=False,
    help_url="https://developers.google.com/workspace/guides/create-credentials",
    description="Google Workspace OAuth2 credentials for Gmail, Calendar, Drive, and Docs",
    api_key_instructions="""To set up Google Workspace integration:
1. Go to Google Cloud Console (https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable APIs: Gmail, Calendar, Drive, Docs, Sheets
4. Go to APIs & Services > Credentials
5. Create OAuth 2.0 Client ID (Desktop application)
6. Download the client configuration JSON
7. Run the OAuth flow to obtain a refresh token
8. Store as JSON: {"client_id": "...", "client_secret": "...", "refresh_token": "..."}""",
    credential_id="google_workspace",
    credential_key="refresh_token",
),
```

### File Structure

```
tools/src/aden_tools/tools/google_workspace_tool/
├── __init__.py
├── google_workspace_tool.py
├── gmail.py          # Gmail-specific client methods
├── calendar.py       # Calendar-specific client methods
├── drive.py          # Drive-specific client methods
├── docs.py           # Docs/Sheets-specific client methods
└── README.md
```

### API Endpoints

| Service | Base URL |
|---------|----------|
| Gmail | `https://gmail.googleapis.com/gmail/v1` |
| Calendar | `https://www.googleapis.com/calendar/v3` |
| Drive | `https://www.googleapis.com/drive/v3` |
| Docs | `https://docs.googleapis.com/v1` |
| Sheets | `https://sheets.googleapis.com/v4` |

## Why Agents Need This

| Without Google Workspace Tools | With Google Workspace Tools |
|-------------------------------|----------------------------|
| "Check my email" → "I can't access your inbox" | Full inbox search and management |
| "Schedule a meeting" → "Please use your calendar app" | Direct calendar manipulation |
| "Find that document" → "I don't have access to your files" | Instant Drive search |
| "Send the report" → Manual copy-paste workflow | Automated document + email |

**The Bottom Line:** Google Workspace integration transforms agents from "assistants that give advice" to "assistants that take action."

## References

- [Gmail API](https://developers.google.com/gmail/api)
- [Calendar API](https://developers.google.com/calendar/api)
- [Drive API](https://developers.google.com/drive/api)
- [Docs API](https://developers.google.com/docs/api)
- [Sheets API](https://developers.google.com/sheets/api)

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`, `high-priority`
