# [Integration]: Microsoft 365 - Outlook, Calendar, OneDrive & Teams

## Overview

Add integration with Microsoft Graph API to enable agents to manage email, calendar, files, and team collaboration. Microsoft 365 dominates enterprise productivity with 400M+ paid seats - agents need native access to automate the workflows where enterprise knowledge workers spend 60%+ of their time.

**Why This Matters:**
- 400M+ paid Microsoft 365 users (enterprise standard)
- Outlook is the #1 enterprise email client
- Teams has 320M+ monthly active users
- SharePoint/OneDrive stores 85% of enterprise documents
- Microsoft Graph provides unified API access to all services

## Requirements

Implement the following 16 MCP tools across 4 services:

### Outlook Mail (4 tools)

| Tool | Description |
|------|-------------|
| `outlook_search_mail` | Search emails with OData filters (from, subject, hasAttachments, etc.) |
| `outlook_get_message` | Get full email content, attachments, and conversation thread |
| `outlook_send_mail` | Send emails with HTML body, attachments, CC/BCC |
| `outlook_reply_mail` | Reply/Reply All to existing message thread |

### Outlook Calendar (4 tools)

| Tool | Description |
|------|-------------|
| `outlook_list_events` | List calendar events within date range |
| `outlook_get_event` | Get event details including attendees and Teams link |
| `outlook_create_event` | Create events with attendees, Teams meeting, and recurrence |
| `outlook_update_event` | Update event time, attendees, or details |

### OneDrive/SharePoint (4 tools)

| Tool | Description |
|------|-------------|
| `onedrive_search` | Search files across OneDrive and SharePoint |
| `onedrive_get_file` | Download file content or get metadata |
| `onedrive_upload` | Upload files to OneDrive or SharePoint |
| `sharepoint_list_items` | Query SharePoint list data |

### Microsoft Teams (4 tools)

| Tool | Description |
|------|-------------|
| `teams_list_channels` | List channels in a team |
| `teams_send_message` | Post message to a channel |
| `teams_get_messages` | Get recent messages from a channel |
| `teams_create_meeting` | Schedule Teams meeting with participants |

## Authentication

- **Credentials:** `MS365_CLIENT_ID`, `MS365_CLIENT_SECRET`, `MS365_TENANT_ID`, `MS365_REFRESH_TOKEN`
- **Auth Method:** OAuth 2.0 with Microsoft Identity Platform
- **Permissions Required:**
  ```
  Mail.ReadWrite
  Mail.Send
  Calendars.ReadWrite
  Files.ReadWrite.All
  Sites.ReadWrite.All
  ChannelMessage.Send
  OnlineMeetings.ReadWrite
  ```

**Setup Flow:**
1. Register app in Azure Portal (App Registrations)
2. Configure API permissions (delegated or application)
3. Create client secret
4. Run OAuth flow or use client credentials
5. Store tokens securely

## Costing

| Aspect | Details |
|--------|---------|
| API Cost | **Free** - included with Microsoft 365 subscription |
| Rate Limits | 10,000 requests/10 minutes per app |
| Throttling | 429 responses with Retry-After header |

**Note:** Microsoft Graph API is free. You only pay for the Microsoft 365 subscription.

## Use Cases

### 🏢 Enterprise Assistant Agent
```
"What's on my plate today?"
├── outlook_list_events(today) → Get meetings
├── outlook_search_mail("is:unread importance:high") → Priority emails
├── teams_get_messages(urgent_channel) → Team updates
├── onedrive_search("modified:today") → Recent documents
└── Generate: Prioritized daily briefing with action items
```

### 📧 Enterprise Email Processor
```
"Handle my inbox intelligently"
├── outlook_search_mail("isRead eq false") → Unread emails
├── For each email:
│   ├── Analyze: sentiment, urgency, required action
│   ├── outlook_reply_mail() → Draft contextual responses
│   ├── outlook_create_event() → Schedule follow-ups
│   └── teams_send_message() → Notify team if urgent
└── Summary: "43 emails processed, 5 flagged for review"
```

### 🤝 Meeting Coordinator Agent
```
"Set up a project kickoff with the team"
├── outlook_list_events(next_week) → Find availability
├── teams_create_meeting() → Create Teams meeting
├── outlook_create_event() → Send calendar invites
├── onedrive_upload(agenda.docx) → Share meeting docs
├── teams_send_message() → Announce in project channel
└── outlook_send_mail() → Send prep materials to externals
```

### 📁 Document Workflow Agent
```
"Find and share the Q4 budget with finance team"
├── onedrive_search("Q4 budget 2024") → Locate document
├── onedrive_get_file() → Verify it's the right version
├── sharepoint_list_items("Finance Team") → Get team members
├── outlook_send_mail() → Email with secure link
└── teams_send_message(#finance) → Post in channel
```

### 🔔 Proactive Notification Agent
```
When important events occur:
├── Monitor: outlook_search_mail(from:CEO) → Executive emails
├── Monitor: teams_get_messages(announcements) → Company news
├── Detect: contract mentions, deadline changes, escalations
├── teams_send_message() → Alert relevant team members
└── outlook_create_event() → Schedule response meetings
```

### 📊 Weekly Standup Automator
```
Every Monday at 9 AM:
├── outlook_list_events(last_week) → Meetings attended
├── outlook_search_mail(sent, last_week) → Emails sent
├── onedrive_search(modified:last_week) → Files worked on
├── Generate: Weekly accomplishments summary
├── teams_send_message(#standup) → Post to team channel
└── outlook_send_mail(manager) → Send manager update
```

## Implementation Details

### Credential Spec

```python
"microsoft_365": CredentialSpec(
    env_var="MS365_CREDENTIALS",  # JSON with client_id, client_secret, tenant_id, refresh_token
    tools=[
        "outlook_search_mail", "outlook_get_message", "outlook_send_mail", "outlook_reply_mail",
        "outlook_list_events", "outlook_get_event", "outlook_create_event", "outlook_update_event",
        "onedrive_search", "onedrive_get_file", "onedrive_upload", "sharepoint_list_items",
        "teams_list_channels", "teams_send_message", "teams_get_messages", "teams_create_meeting",
    ],
    required=True,
    startup_required=False,
    help_url="https://docs.microsoft.com/en-us/graph/auth-register-app-v2",
    description="Microsoft 365 OAuth2 credentials for Outlook, Calendar, OneDrive, and Teams",
    api_key_instructions="""To set up Microsoft 365 integration:
1. Go to Azure Portal > App Registrations
2. Click "New registration"
3. Name your app and select account type
4. Add redirect URI: http://localhost:8080/callback
5. Go to "API permissions" and add:
   - Mail.ReadWrite, Mail.Send
   - Calendars.ReadWrite
   - Files.ReadWrite.All
   - ChannelMessage.Send
6. Go to "Certificates & secrets" > New client secret
7. Run OAuth flow to obtain refresh token
8. Store as JSON: {"client_id": "...", "client_secret": "...", "tenant_id": "...", "refresh_token": "..."}""",
    credential_id="microsoft_365",
    credential_key="refresh_token",
),
```

### File Structure

```
tools/src/aden_tools/tools/microsoft365_tool/
├── __init__.py
├── microsoft365_tool.py
├── outlook_mail.py      # Mail client methods
├── outlook_calendar.py  # Calendar client methods
├── onedrive.py          # OneDrive/SharePoint methods
├── teams.py             # Teams client methods
└── README.md
```

### API Base URL

All Microsoft 365 APIs use Microsoft Graph:
```
https://graph.microsoft.com/v1.0
```

### Key Endpoints

| Service | Endpoint |
|---------|----------|
| Mail | `/me/messages`, `/me/sendMail` |
| Calendar | `/me/events`, `/me/calendar/events` |
| OneDrive | `/me/drive/root/search`, `/me/drive/items` |
| SharePoint | `/sites/{site-id}/lists/{list-id}/items` |
| Teams | `/teams/{team-id}/channels`, `/chats/{chat-id}/messages` |

## Why Agents Need This

| Without Microsoft 365 Tools | With Microsoft 365 Tools |
|----------------------------|--------------------------|
| "Check my Outlook" → "I can't access Microsoft services" | Full inbox and calendar access |
| "Post in Teams" → "Please open Teams and post manually" | Direct channel messaging |
| "Find that SharePoint doc" → "Search SharePoint yourself" | Cross-service file search |
| "Schedule with my team" → "Check everyone's calendars" | Automatic availability + booking |

**Enterprise Reality:** 80% of Fortune 500 companies use Microsoft 365. Without this integration, agents can't operate in enterprise environments.

## References

- [Microsoft Graph API Overview](https://docs.microsoft.com/en-us/graph/overview)
- [Graph Explorer (Test API)](https://developer.microsoft.com/en-us/graph/graph-explorer)
- [Authentication Guide](https://docs.microsoft.com/en-us/graph/auth/)
- [Mail API Reference](https://docs.microsoft.com/en-us/graph/api/resources/mail-api-overview)
- [Calendar API Reference](https://docs.microsoft.com/en-us/graph/api/resources/calendar)
- [OneDrive API Reference](https://docs.microsoft.com/en-us/graph/api/resources/onedrive)
- [Teams API Reference](https://docs.microsoft.com/en-us/graph/api/resources/teams-api-overview)

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`, `enterprise`, `high-priority`
