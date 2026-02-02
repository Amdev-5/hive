# [Integration]: Decagon - AI-Native Customer Support Platform

## Overview

Add integration with Decagon API to enable agents to leverage AI-powered customer support capabilities. Decagon is the emerging leader in AI-native support automation, used by fast-growing companies like Notion, Rippling, and Webflow - agents need access to orchestrate AI-human hybrid support workflows and leverage Decagon's specialized support AI.

**Why This Matters:**
- Decagon handles 50%+ of support volume automatically for customers
- Purpose-built for AI-first support (not retrofitted like legacy tools)
- Native integration with knowledge bases and product data
- Seamless AI-to-human handoff workflows
- Real-time learning from every interaction

## Requirements

Implement the following 8 MCP tools:

### Conversations (4 tools)

| Tool | Description |
|------|-------------|
| `decagon_list_conversations` | List conversations with filters (status, assignee, channel, time range) |
| `decagon_get_conversation` | Get full conversation transcript with AI analysis and metadata |
| `decagon_send_message` | Send message in conversation (as AI or human agent) |
| `decagon_handoff` | Trigger AI-to-human or human-to-AI handoff with context |

### AI Analysis (2 tools)

| Tool | Description |
|------|-------------|
| `decagon_analyze_intent` | Analyze message/conversation for intent, sentiment, and entities |
| `decagon_suggest_response` | Get AI-generated response suggestions with confidence scores |

### Knowledge (2 tools)

| Tool | Description |
|------|-------------|
| `decagon_search_knowledge` | Search knowledge base for relevant articles/answers |
| `decagon_get_article` | Get full knowledge base article content |

## Authentication

- **Credential:** `DECAGON_API_KEY`
- **Auth Method:** API key in `X-API-Key` header
- **Get Key:** Decagon Dashboard → Settings → API → Generate Key

## Costing

| Plan | Price | Details |
|------|-------|---------|
| Growth | Custom | Up to 10K conversations/mo |
| Scale | Custom | Up to 100K conversations/mo |
| Enterprise | Custom | Unlimited + dedicated support |

**Note:** Decagon pricing is conversation-based. API access included with all plans.

## Use Cases

### 🤖 Hybrid Support Orchestrator
```
When customer reaches out:
├── decagon_analyze_intent() → Classify query
├── decagon_search_knowledge() → Find relevant articles
├── If simple + high-confidence answer:
│   ├── decagon_suggest_response() → Get AI response
│   └── decagon_send_message() → Auto-reply
├── If complex or sensitive:
│   ├── decagon_handoff(to="human") → Route to agent
│   └── Include: AI analysis, suggested response, KB articles
└── Resolution: 60% automated, 40% human-assisted
```

### 🧠 AI Quality Monitor
```
Review AI performance:
├── decagon_list_conversations(ai_handled=true, period="7d")
├── For each conversation:
│   ├── decagon_get_conversation() → Full transcript
│   ├── Analyze: Was AI response accurate? Was handoff appropriate?
│   ├── Flag: Incorrect answers, missed handoffs, poor sentiment
│   └── Feed back: Training data for improvement
└── Weekly AI quality report with specific examples
```

### 📚 Knowledge Gap Detector
```
Identify missing documentation:
├── decagon_list_conversations(escalated=true)
├── For escalated conversations:
│   ├── decagon_get_conversation() → Why was it escalated?
│   ├── decagon_search_knowledge() → What articles exist?
│   ├── Identify: Topics with no/poor KB coverage
│   └── Generate: Draft article suggestions
└── "Top 5 knowledge gaps this week: [topics]"
```

### 🔄 Smart Escalation Agent
```
Monitor for escalation triggers:
├── decagon_list_conversations(status="open")
├── For each active conversation:
│   ├── decagon_analyze_intent() → Detect frustration, urgency
│   ├── If escalation needed:
│   │   ├── decagon_handoff() → Immediate human routing
│   │   └── Include: Priority flag, customer context
│   └── If AI struggling:
│       └── decagon_suggest_response() → Get fresh suggestions
└── Reduce: Customer effort score by 30%
```

### 🎯 Proactive Support Agent
```
Predict issues before they happen:
├── Monitor: Product events, error logs, usage patterns
├── When issue detected:
│   ├── decagon_search_knowledge() → Find solution
│   ├── decagon_send_message() → Proactive outreach
│   └── "Hi! We noticed X. Here's how to fix it: [article]"
└── Support tickets prevented: 25% reduction
```

### 📊 Support Intelligence Dashboard
```
"How is support performing?"
├── decagon_list_conversations() → Get all conversations
├── Aggregate:
│   ├── AI resolution rate
│   ├── Handoff rate by category
│   ├── Average handle time
│   ├── Customer satisfaction by channel
│   └── Top intents this week
├── Compare: vs last week, last month
└── Insights: "Billing questions up 40%, suggest KB update"
```

## Implementation Details

### Credential Spec

```python
"decagon": CredentialSpec(
    env_var="DECAGON_API_KEY",
    tools=[
        "decagon_list_conversations", "decagon_get_conversation",
        "decagon_send_message", "decagon_handoff",
        "decagon_analyze_intent", "decagon_suggest_response",
        "decagon_search_knowledge", "decagon_get_article",
    ],
    required=True,
    startup_required=False,
    help_url="https://docs.decagon.ai/api",
    description="Decagon API key for AI-powered customer support",
    api_key_instructions="""To get Decagon API key:
1. Log in to Decagon Dashboard
2. Go to Settings → API
3. Click "Generate API Key"
4. Copy the key (shown only once)
5. Store securely""",
    credential_id="decagon",
    credential_key="api_key",
),
```

### File Structure

```
tools/src/aden_tools/tools/decagon_tool/
├── __init__.py
├── decagon_tool.py
└── README.md
```

### API Base URL

```
https://api.decagon.ai/v1
```

### Key Endpoints

| Resource | Endpoint |
|----------|----------|
| Conversations | `/conversations`, `/conversations/{id}` |
| Messages | `/conversations/{id}/messages` |
| Handoff | `/conversations/{id}/handoff` |
| Analysis | `/analyze/intent`, `/analyze/suggest` |
| Knowledge | `/knowledge/search`, `/knowledge/articles/{id}` |

## Why Agents Need This

| Without Decagon Tools | With Decagon Tools |
|----------------------|-------------------|
| AI silos from human support | Unified AI+human orchestration |
| No visibility into AI decisions | Full AI analysis access |
| Manual handoff workflows | Automated smart handoffs |
| Static knowledge search | AI-powered knowledge retrieval |

**AI-Native Advantage:** Decagon is built for AI from day one. Integration enables agents to leverage specialized support AI while maintaining human oversight.

## Competitive Differentiation

| Feature | Zendesk/Intercom | Decagon |
|---------|------------------|---------|
| AI Native | Retrofitted | Built-in |
| Handoff Intelligence | Basic routing | Context-aware |
| Response Suggestions | Generic | Customer-specific |
| Learning | Manual retraining | Continuous |

## References

- [Decagon API Documentation](https://docs.decagon.ai)
- [Decagon Platform](https://decagon.ai)

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`, `customer-support`, `ai-native`
