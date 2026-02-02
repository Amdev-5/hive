# [Feature]: Vertical-Specific Agent Use Cases - Master Issue

## Overview

This is a **parent issue** for vertical-specific sample agent implementations that extend [#2853](https://github.com/adenhq/hive/issues/2853). While #2853 focuses on B2B SaaS/SDR workflows (targeting SDEs building internal tooling), this initiative opens Hive to a broader developer audience by demonstrating real-world agent use cases across multiple industries.

> **🎯 Goal:** Enable developers to identify which tools need to be built and understand how agents can be structured for real business workflows across different verticals.

---

## Related Issues

| Issue | Vertical | Target Persona | Primary Agents | Status |
|-------|----------|----------------|----------------|--------|
| [FINTECH](#fintech) | Financial Services | Compliance Lead / FinOps Engineer | KYC Verification, Transaction Monitor, RegTech Compliance | 📝 Draft |
| [HEALTHTECH](#healthtech) | Healthcare | Health IT Director / Digital Health PM | Smart Scheduler, Clinical Trial Matcher, Ambient Scribe | 📝 Draft |
| [LOGISTICS](#logistics) | Supply Chain | Operations Manager / Supply Chain Engineer | Route Optimizer, Predictive Maintenance, Warehouse Orchestrator | 📝 Draft |
| [LEGALTECH/HRTECH](#legaltech-hrtech) | Legal & HR | General Counsel / HR Director | Contract Review, Talent Screener, Onboarding Orchestrator | 📝 Draft |

---

## Why These Verticals?

### Market Opportunity Analysis

| Vertical | Market Size (2026) | AI Adoption Rate | Key Pain Points |
|----------|-------------------|------------------|-----------------|
| **Fintech** | $270B+ compliance spend | 75% by 2026 (Gartner) | KYC bottlenecks, fraud false positives |
| **HealthTech** | $500B admin waste | 60% pilot→production | No-shows, documentation burden |
| **Logistics** | $1.5T inefficiencies | 45% (logistics leaders) | Route inefficiency, breakdowns |
| **LegalTech/HR** | $7.4B legal AI by 2035 | 87% expect AI in contracts | Contract review time, hiring delays |

### Common Patterns Across Verticals

All verticals share core agent patterns that Hive excels at:

1. **Document Processing** → Already have PDF/CSV tools
2. **Data Enrichment** → Similar to Apollo.io pattern
3. **Workflow Orchestration** → DAG execution engine
4. **Human-in-the-Loop** → Built-in intervention nodes
5. **System Integration** → MCP tool pattern

---

## New Tool Integrations Required

### Priority 1 (Enables 3+ Agents)
| Tool | Verticals | Effort |
|------|-----------|--------|
| **Twilio** | HealthTech, Logistics, HR | 2-3 days |
| **DocuSign** | HealthTech, LegalTech, HR | 2-3 days |
| **Google Maps Platform** | Logistics | 1-2 days |

### Priority 2 (Enables Specific Vertical)
| Tool | Vertical | Effort |
|------|----------|--------|
| **Plaid** | Fintech | 2-3 days |
| **Onfido** | Fintech | 2-3 days |
| **FHIR R4** | HealthTech | 3-4 days |
| **Samsara** | Logistics | 2-3 days |
| **Lever/Workable** | HR | 2-3 days |
| **BambooHR** | HR | 2-3 days |
| **Okta** | HR | 2-3 days |

### Priority 3 (Nice to Have)
| Tool | Vertical | Effort |
|------|----------|--------|
| **Sanctions.io** | Fintech | 1-2 days |
| **ClinicalTrials.gov** | HealthTech | 1 day |
| **OpenWeather** | Logistics | 1 day |
| **ShipStation** | Logistics | 1-2 days |

---

## Motion Graphics Videos

Each vertical includes a **45-second motion graphics video concept** designed to:
- Explain the business problem (5-10s)
- Show the agent solution (15-20s)
- Demonstrate results (10-15s)
- Call to action (5s)

### Video Production Plan

| Vertical | Video Title | Key Visual |
|----------|-------------|------------|
| Fintech | "The KYC Agent in Action" | Document → Verification → Risk Score |
| HealthTech | "Never Miss an Appointment Again" | Calendar optimization animation |
| Logistics | "The Invisible Dispatcher" | Map with dynamic route calculation |
| LegalTech/HR | "From Inbox Zero to Hired" | Paper → Digital transformation |

**Recommended Tools:**
- **Rive** - For interactive web animations (embed in README)
- **Lottie** - For lightweight vector animations
- **Remotion** - For programmatic video generation
- **Canva/Figma** - For storyboard design

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create directory structure for vertical agents
- [ ] Implement Twilio tool (highest cross-vertical value)
- [ ] Implement DocuSign tool
- [ ] Create first sample agent (Smart Scheduler - most universally applicable)

### Phase 2: Fintech Vertical (Week 3-4)
- [ ] Implement Plaid tool
- [ ] Implement Onfido tool
- [ ] Build KYC Verification Agent
- [ ] Create Fintech motion graphics video

### Phase 3: HealthTech Vertical (Week 5-6)
- [ ] Implement FHIR R4 tool (sandbox first)
- [ ] Build Clinical Trial Matcher Agent
- [ ] Build Ambient Scribe Agent
- [ ] Create HealthTech motion graphics video

### Phase 4: Logistics Vertical (Week 7-8)
- [ ] Implement Google Maps Platform tool
- [ ] Implement Samsara tool
- [ ] Build Route Optimizer Agent
- [ ] Build Predictive Maintenance Agent
- [ ] Create Logistics motion graphics video

### Phase 5: LegalTech/HRTech Vertical (Week 9-10)
- [ ] Implement Lever tool (extend Greenhouse work)
- [ ] Implement BambooHR tool
- [ ] Build Contract Review Agent
- [ ] Build Onboarding Orchestrator Agent
- [ ] Create LegalTech/HR motion graphics video

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Sample Agents Delivered | 12 (3 per vertical) |
| New Tool Integrations | 15+ |
| Motion Graphics Videos | 4 |
| README Documentation | 4 vertical READMEs |
| Test Coverage | 80%+ per agent |
| Community Contributions | Enable 10+ external PRs |

---

## How to Contribute

### Pick a Tool Integration
1. Comment on this issue to claim a tool integration
2. Follow the pattern in [tools/BUILDING_TOOLS.md](BUILDING_TOOLS.md)
3. Include tests with mock API responses
4. Submit PR referencing this issue

### Build a Sample Agent
1. Review the agent design in the vertical-specific issue
2. Use `/building-agents-construction` skill to generate the agent
3. Add to `exports/` directory with `README.md`
4. Submit PR with tests and documentation

### Create Motion Graphics
1. Review the storyboard in the vertical-specific issue
2. Create animation using Rive, Lottie, or Remotion
3. Export as WebM/MP4 for README embedding
4. Export as Lottie JSON for web playback
5. Submit PR with video files

---

## Linked Resources

- **Parent Issue:** [#2853 - Missing sample use cases for business processes](https://github.com/adenhq/hive/issues/2853)
- **Integration Hub:** [#2805](https://github.com/adenhq/hive/issues/2805)
- **Existing Integrations:** [githubissues.md](githubissues.md) (News APIs, Apollo.io, Greenhouse)
- **Building Tools Guide:** [tools/BUILDING_TOOLS.md](tools/BUILDING_TOOLS.md)
- **Building Agents Skill:** [.claude/skills/building-agents-construction/SKILL.md](.claude/skills/building-agents-construction/SKILL.md)

---

## Child Issues

<details>
<summary><h3 id="fintech">📊 Fintech Vertical</h3></summary>

**File:** `issues/ISSUE_FINTECH_VERTICAL.md`

**Agents:**
1. KYC Verification Agent - Identity verification, document validation, sanctions screening
2. Transaction Monitor Agent - Real-time fraud detection with behavioral analytics
3. RegTech Compliance Agent - Regulatory monitoring and compliance reporting

**Tools Needed:** Plaid, Onfido, Sanctions.io

**Video:** "The KYC Agent in Action" (45s)
</details>

<details>
<summary><h3 id="healthtech">🏥 HealthTech Vertical</h3></summary>

**File:** `issues/ISSUE_HEALTHTECH_VERTICAL.md`

**Agents:**
1. Smart Scheduler Agent - AI-powered scheduling with no-show prediction
2. Clinical Trial Matcher Agent - Patient-to-trial matching and recruitment
3. Ambient Scribe Agent - Real-time encounter documentation

**Tools Needed:** FHIR R4, Twilio, ClinicalTrials.gov, Deepgram

**Video:** "Never Miss an Appointment Again" (45s)
</details>

<details>
<summary><h3 id="logistics">🚚 Logistics Vertical</h3></summary>

**File:** `issues/ISSUE_LOGISTICS_VERTICAL.md`

**Agents:**
1. Route Optimizer Agent - Dynamic routing with traffic/weather integration
2. Predictive Maintenance Agent - Fleet health monitoring and failure prediction
3. Warehouse Orchestrator Agent - Real-time picking/packing optimization

**Tools Needed:** Google Maps Platform, Samsara, ShipStation, OpenWeather

**Video:** "The Invisible Dispatcher" (45s)
</details>

<details>
<summary><h3 id="legaltech-hrtech">⚖️ LegalTech/HRTech Vertical</h3></summary>

**File:** `issues/ISSUE_LEGALTECH_HRTECH_VERTICAL.md`

**Agents:**
1. Contract Review Agent - AI-assisted redlining against company playbook
2. Talent Screener Agent - Resume screening with bias reduction
3. Onboarding Orchestrator Agent - End-to-end new hire automation

**Tools Needed:** DocuSign, Lever, BambooHR, Okta

**Video:** "From Inbox Zero to Hired" (45s)
</details>

---

**Labels:** `enhancement`, `help wanted`, `sample-agents`, `documentation`
**Milestone:** v0.5 - Sample Agents & Verticals
