# [Integration]: Intercom - Customer Messaging & Engagement Platform

## Overview

Add integration with Intercom API to enable agents to manage customer conversations, user data, and proactive messaging. Intercom is the leading customer messaging platform used by 25,000+ businesses - agents need access to provide seamless customer engagement, support automation, and user lifecycle management.

**Why This Matters:**
- 25,000+ businesses use Intercom for customer messaging
- 500M+ conversations happen on Intercom monthly
- Unified inbox for chat, email, and social messaging
- Rich user data enables personalized automation
- Real-time engagement drives conversion and retention

## Requirements

Implement the following 10 MCP tools:

### Conversations (4 tools)

| Tool | Description |
|------|-------------|
| `intercom_search_conversations` | Search conversations by user, status, tags, or time range |
| `intercom_get_conversation` | Get full conversation with messages and participant details |
| `intercom_reply_conversation` | Send reply as admin, bot, or note |
| `intercom_update_conversation` | Update status (open/snoozed/closed), assignee, or tags |

### Contacts (3 tools)

| Tool | Description |
|------|-------------|
| `intercom_search_contacts` | Search users/leads by email, name, or custom attributes |
| `intercom_get_contact` | Get full contact profile with companies and tags |
| `intercom_update_contact` | Update contact attributes, tags, or custom data |

### Messages (2 tools)

| Tool | Description |
|------|-------------|
| `intercom_send_message` | Send proactive in-app or email message to user |
| `intercom_create_note` | Add internal note to a contact's profile |

### Data (1 tool)

| Tool | Description |
|------|-------------|
| `intercom_track_event` | Track custom event for a user (for segmentation) |

## Authentication

- **Credential:** `INTERCOM_ACCESS_TOKEN`
- **Auth Method:** Bearer token in Authorization header
- **Get Token:** Settings → Integrations → Developer Hub → New App → Access Token

## Costing

| Plan | Price | API Access |
|------|-------|------------|
| Essential | $39/seat/mo | ✅ Basic API |
| Advanced | $99/seat/mo | ✅ Full API |
| Expert | $139/seat/mo | ✅ Full API + Priority |

**Rate Limits:**
- 1,000 requests/minute (burstable)
- Scroll API for large data sets

## Use Cases

### 💬 Conversational Support Agent
```
When new conversation arrives:
├── intercom_get_conversation(id) → Full context
├── intercom_get_contact(user) → User profile & history
├── intercom_search_conversations("user:{id}") → Past conversations
├── Analyze: intent, sentiment, complexity
├── If simple query:
│   ├── Generate response with KB context
│   └── intercom_reply_conversation() → Send reply
├── If complex:
│   ├── intercom_update_conversation(assignee=human) → Route to agent
│   └── intercom_reply_conversation(note=true) → Add context note
└── Resolution time reduced by 50%
```

### 🎯 Proactive Engagement Agent
```
Identify users who need help:
├── intercom_search_contacts("last_seen<7days AND plan=trial")
├── For at-risk users:
│   ├── intercom_get_contact() → Check engagement
│   ├── intercom_track_event("at_risk_identified")
│   ├── Generate: Personalized re-engagement message
│   └── intercom_send_message() → Send in-app or email
└── Trial conversion improved by 25%
```

### 📊 Customer Health Monitor
```
"Which customers need attention?"
├── intercom_search_contacts("custom.health_score<50")
├── For each at-risk customer:
│   ├── intercom_search_conversations() → Recent interactions
│   ├── Analyze: complaint frequency, sentiment trend
│   ├── intercom_create_note() → Add health assessment
│   └── Alert: CSM notification with context
└── Churn prediction + proactive intervention
```

### 🔄 Conversation Summarizer Agent
```
When conversation closed:
├── intercom_get_conversation(id) → All messages
├── Generate:
│   ├── Issue summary
│   ├── Resolution steps taken
│   ├── Customer sentiment
│   └── Follow-up needed (Y/N)
├── intercom_update_contact() → Update custom attributes
├── intercom_track_event("support_resolved", {category, resolution_time})
└── Feed into: analytics, product feedback, training data
```

### 🚀 Onboarding Orchestrator
```
When new user signs up:
├── intercom_get_contact(new_user) → Profile data
├── Segment: company size, role, use case
├── intercom_send_message() → Personalized welcome
├── Schedule: Day 1, 3, 7 onboarding messages
├── intercom_track_event("onboarding_started")
├── Monitor: feature adoption milestones
└── intercom_send_message() if stuck → Offer help
```

### 🏷️ Auto-Tagging Agent
```
For every conversation:
├── intercom_get_conversation() → Analyze content
├── Classify:
│   ├── Category: billing, technical, feature-request, bug
│   ├── Product area: auth, payments, integrations
│   ├── Sentiment: positive, neutral, negative
│   └── Priority: urgent, normal, low
├── intercom_update_conversation(tags=[...])
└── Consistent tagging for reporting & routing
```

## Implementation Details

### Credential Spec

```python
"intercom": CredentialSpec(
    env_var="INTERCOM_ACCESS_TOKEN",
    tools=[
        "intercom_search_conversations", "intercom_get_conversation",
        "intercom_reply_conversation", "intercom_update_conversation",
        "intercom_search_contacts", "intercom_get_contact", "intercom_update_contact",
        "intercom_send_message", "intercom_create_note", "intercom_track_event",
    ],
    required=True,
    startup_required=False,
    help_url="https://developers.intercom.com/building-apps/docs/authentication",
    description="Intercom access token for conversations, contacts, and messaging",
    api_key_instructions="""To get Intercom API access token:
1. Go to Intercom Settings → Integrations → Developer Hub
2. Click "New app" or select existing app
3. Go to "Authentication" tab
4. Copy the Access Token
5. Ensure required scopes are enabled:
   - Read/Write conversations
   - Read/Write users
   - Read/Write companies
   - Send messages""",
    health_check_endpoint="https://api.intercom.io/me",
    health_check_method="GET",
    credential_id="intercom",
    credential_key="access_token",
),
```

### File Structure

```
tools/src/aden_tools/tools/intercom_tool/
├── __init__.py
├── intercom_tool.py
└── README.md
```

### API Base URL

```
https://api.intercom.io
```

### Key Endpoints

| Resource | Endpoint |
|----------|----------|
| Conversations | `/conversations`, `/conversations/{id}`, `/conversations/{id}/reply` |
| Contacts | `/contacts`, `/contacts/{id}`, `/contacts/search` |
| Messages | `/messages` |
| Events | `/events` |
| Notes | `/contacts/{id}/notes` |

## Why Agents Need This

| Without Intercom Tools | With Intercom Tools |
|-----------------------|---------------------|
| "Check conversations" → "Log into Intercom" | Real-time conversation access |
| "Reply to customer" → Copy-paste workflow | Direct conversation reply |
| "Find user history" → Manual search | Instant user + conversation lookup |
| "Send campaign" → Marketing team request | Automated personalized outreach |

**Support + Sales Fusion:** Intercom bridges support and sales. Agents with Intercom access can identify expansion opportunities during support conversations.

## API Response Examples

### Conversation Object
```json
{
  "id": "12345",
  "type": "conversation",
  "title": "How do I upgrade my plan?",
  "state": "open",
  "priority": "not_priority",
  "contacts": {
    "contacts": [{"id": "5678", "type": "contact"}]
  },
  "source": {
    "type": "conversation",
    "delivered_as": "customer_initiated"
  },
  "conversation_parts": {
    "conversation_parts": [...]
  }
}
```

### Contact Object
```json
{
  "id": "5678",
  "type": "contact",
  "email": "user@example.com",
  "name": "Jane Doe",
  "custom_attributes": {
    "plan": "pro",
    "company_size": "50-100"
  },
  "companies": {"companies": [...]},
  "tags": {"tags": [...]}
}
```

## References

- [Intercom API Reference](https://developers.intercom.com/intercom-api-reference/reference)
- [Conversations API](https://developers.intercom.com/intercom-api-reference/reference/conversation-model)
- [Contacts API](https://developers.intercom.com/intercom-api-reference/reference/contact-model)
- [Search API](https://developers.intercom.com/intercom-api-reference/reference/search-for-contacts)

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`, `customer-support`, `sales`
