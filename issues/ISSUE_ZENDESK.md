# [Integration]: Zendesk - Customer Support & Ticketing

## Overview

Add integration with Zendesk Support API to enable agents to manage customer support workflows. Zendesk powers support for 100,000+ companies worldwide - agents need access to automate ticket triage, response drafting, escalation workflows, and customer satisfaction analysis.

**Why This Matters:**
- 100,000+ companies use Zendesk for customer support
- Average support team handles 500+ tickets/week
- 60% of tickets are repetitive and automatable
- Response time directly impacts customer satisfaction (CSAT)
- Support data is gold for product improvement insights

## Requirements

Implement the following 8 MCP tools:

| Tool | Description |
|------|-------------|
| `zendesk_search_tickets` | Search tickets with Zendesk Query Language (status, priority, assignee, tags) |
| `zendesk_get_ticket` | Get full ticket details including comments, attachments, and custom fields |
| `zendesk_create_ticket` | Create new support ticket with requester, subject, and description |
| `zendesk_update_ticket` | Update ticket status, priority, assignee, or add internal notes |
| `zendesk_add_comment` | Add public reply or internal note to ticket |
| `zendesk_list_users` | Search for users (customers or agents) by email or name |
| `zendesk_get_user` | Get user profile, ticket history, and organization |
| `zendesk_get_satisfaction` | Get CSAT ratings and feedback for tickets |

## Authentication

- **Credentials:** `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN`
- **Auth Method:** Basic Auth with `{email}/token:{api_token}`
- **Alternative:** OAuth 2.0 for user-context actions

**Get API Token:**
1. Admin Center → Apps and integrations → APIs → Zendesk API
2. Enable Token Access
3. Add API Token
4. Copy token (shown only once)

## Costing

| Plan | Price | API Access |
|------|-------|------------|
| Suite Team | $55/agent/mo | ✅ Full API |
| Suite Growth | $89/agent/mo | ✅ Full API |
| Suite Professional | $115/agent/mo | ✅ Full API + Advanced |
| API-only | - | Included with any plan |

**Rate Limits:** 700 requests/minute (varies by plan)

## Use Cases

### 🎫 Intelligent Ticket Triage Agent
```
Every 5 minutes, process new tickets:
├── zendesk_search_tickets("status:new") → Get unassigned tickets
├── For each ticket:
│   ├── Analyze: intent, sentiment, urgency, product area
│   ├── zendesk_update_ticket() → Set priority, tags, custom fields
│   ├── Route: assign to appropriate team/agent
│   └── If urgent: escalate immediately
└── Report: "Triaged 23 tickets, 3 escalated to Tier 2"
```

### 💬 Auto-Response Drafter Agent
```
When agent opens a ticket:
├── zendesk_get_ticket(id) → Full ticket context
├── zendesk_get_user(requester) → Customer history
├── zendesk_search_tickets("similar:{issue}") → Past similar tickets
├── Generate: Contextual response draft
├── Include: Relevant KB articles, past solutions
└── Agent reviews and sends (human-in-loop)
```

### 📊 Support Analytics Agent
```
"How's our support performance this week?"
├── zendesk_search_tickets("created>7days") → This week's tickets
├── zendesk_get_satisfaction() → CSAT scores
├── Analyze:
│   ├── Volume by category, product, channel
│   ├── Resolution time trends
│   ├── Agent performance metrics
│   └── Common complaint themes
└── Generate: Weekly support insights report
```

### 🔥 Escalation Monitor Agent
```
Continuously monitor for escalation triggers:
├── zendesk_search_tickets("priority:urgent updated<2hours")
├── zendesk_search_tickets("satisfaction:bad")
├── zendesk_search_tickets("tags:churn_risk")
├── For escalation candidates:
│   ├── zendesk_add_comment() → Alert internal note
│   ├── Notify: Slack/Teams message to manager
│   └── zendesk_update_ticket() → Bump priority
└── Escalation dashboard updated in real-time
```

### 🤖 Self-Service Deflection Agent
```
When ticket created via email/form:
├── zendesk_get_ticket(new_ticket) → Analyze issue
├── Search: Knowledge base for solutions
├── If high-confidence match:
│   ├── zendesk_add_comment() → Send KB article
│   ├── zendesk_update_ticket(status="pending") → Wait for response
│   └── If resolved: auto-close after 24h
└── Deflection rate: 30-40% of L1 tickets
```

### 👤 Customer 360 Agent
```
"Tell me about customer acme@company.com"
├── zendesk_list_users("acme@company.com") → Find user
├── zendesk_get_user(user_id) → Profile & org
├── zendesk_search_tickets("requester:{user}") → Ticket history
├── zendesk_get_satisfaction() → Their CSAT scores
├── Compile:
│   ├── Total tickets, open tickets
│   ├── Common issues they face
│   ├── Satisfaction trend
│   └── Account health score
└── "Acme Corp: 47 tickets lifetime, 2 open, CSAT 4.2/5"
```

## Implementation Details

### Credential Spec

```python
"zendesk": CredentialSpec(
    env_var="ZENDESK_CREDENTIALS",  # JSON with subdomain, email, api_token
    tools=[
        "zendesk_search_tickets", "zendesk_get_ticket", "zendesk_create_ticket",
        "zendesk_update_ticket", "zendesk_add_comment", "zendesk_list_users",
        "zendesk_get_user", "zendesk_get_satisfaction",
    ],
    required=True,
    startup_required=False,
    help_url="https://developer.zendesk.com/api-reference/",
    description="Zendesk Support API credentials for ticket and user management",
    api_key_instructions="""To get Zendesk API credentials:
1. Log in to Zendesk Admin Center
2. Go to Apps and integrations → APIs → Zendesk API
3. Enable "Token Access" if not already enabled
4. Click "Add API token"
5. Give it a description and click "Create"
6. Copy the token (shown only once!)
7. Store as JSON: {"subdomain": "yourcompany", "email": "you@company.com", "api_token": "..."}""",
    health_check_endpoint="https://{subdomain}.zendesk.com/api/v2/users/me.json",
    health_check_method="GET",
    credential_id="zendesk",
    credential_key="api_token",
),
```

### File Structure

```
tools/src/aden_tools/tools/zendesk_tool/
├── __init__.py
├── zendesk_tool.py
└── README.md
```

### API Base URL

```
https://{subdomain}.zendesk.com/api/v2
```

### Key Endpoints

| Resource | Endpoint |
|----------|----------|
| Tickets | `/tickets`, `/tickets/{id}`, `/search.json?query=type:ticket ...` |
| Comments | `/tickets/{id}/comments` |
| Users | `/users`, `/users/{id}`, `/users/search.json` |
| Satisfaction | `/satisfaction_ratings` |

## Why Agents Need This

| Without Zendesk Tools | With Zendesk Tools |
|----------------------|-------------------|
| "Check support queue" → "Log into Zendesk" | Real-time ticket visibility |
| "Draft a response" → No context access | Full ticket + customer history |
| "Triage this ticket" → Manual classification | Automatic priority + routing |
| "Customer health check" → Dig through multiple systems | Instant 360° view |

**Support Reality:** The #1 cost in support is agent time. Automating triage, drafting, and routing can reduce handling time by 40-60%.

## API Response Examples

### Ticket Object
```json
{
  "id": 35436,
  "subject": "My printer is on fire!",
  "description": "The smoke is very colorful.",
  "status": "open",
  "priority": "urgent",
  "requester_id": 20978392,
  "assignee_id": 235323,
  "tags": ["hardware", "fire", "urgent"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:22:00Z"
}
```

## References

- [Zendesk API Reference](https://developer.zendesk.com/api-reference/)
- [Ticket API](https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/)
- [Search API](https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/)
- [Zendesk Query Language](https://support.zendesk.com/hc/en-us/articles/4408886879258)

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`, `customer-support`
