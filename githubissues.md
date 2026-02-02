# GitHub Issues for Hive Integrations

These integrations address the business process use cases identified in [#2853](https://github.com/adenhq/hive/issues/2853) - specifically enabling sales-focused agents like "Meeting Prepper", "Calendar Shark", "Job Board Sniper", and SDR automation workflows.

---

## Issue 1: News APIs

```markdown
# [Integration]: News APIs - Market Intelligence & Company News

## Overview

Add integration with News APIs to enable agents to monitor market intelligence, track company mentions, and gather competitive insights. News data is essential for sales workflows identified in #2853 - agents need access to recent news about prospects, competitors, and industry trends to automate meeting prep, lead scoring, and deal risk monitoring.

**Use Cases from #2853:**
- "Meeting Prepper" agent needs recent news about prospect companies before calls
- "Calendar Shark" agent needs trigger events (funding, expansion) for lead engagement
- "Job Board Sniper" agent needs market news for competitive intelligence

## Requirements

Implement the following 4 MCP tools:

1. **news_search** - Search news articles with filters
   - Parameters: `query`, `from_date`, `to_date`, `language`, `limit`
   - Optional: `sources`, `category`, `country`
   - Returns: List of articles with title, source, date, URL, snippet

2. **news_headlines** - Get top headlines by category/country
   - Parameters: `category` (business, tech, finance, etc.), `country`, `limit`
   - Returns: List of headline articles with source and publish date

3. **news_by_company** - Get news mentioning a specific company
   - Parameters: `company_name`, `days_back` (default 7)
   - Optional: `limit`, `language`
   - Returns: Articles mentioning the company with relevance context

4. **news_sentiment** - Get news with sentiment analysis (Finlight provider)
   - Parameters: `query`, `from_date`, `to_date`
   - Returns: Articles with sentiment scores (positive/negative/neutral)

## Authentication

- **Primary Credential:** `NEWSDATA_API_KEY` (NewsData.io)
- **Optional Credential:** `FINLIGHT_API_KEY` (for sentiment analysis)
- **Auth Method:** API key in query param (NewsData) or header (Finlight)

**Provider Strategy:**
- NewsData.io (primary): 200 credits/day free, commercial use allowed
- Finlight.me (optional): 5K requests/mo free, includes sentiment
- Auto-fallback between providers

**Costing:**
| Provider | Free Tier | Paid Starting |
|----------|-----------|---------------|
| NewsData.io | 200 credits/day (2K articles) | $199/mo |
| Finlight.me | 5K-10K req/mo | $29/mo |

## Implementation Details

### Credential Management
- Add credential specs to `tools/src/aden_tools/credentials/integrations.py`
- NewsData.io: `NEWSDATA_API_KEY`
- Finlight: `FINLIGHT_API_KEY` (optional)

### Tool Implementation
- Create `tools/src/aden_tools/tools/news_tool/` directory
- Implement multi-provider pattern (like `web_search_tool`)
- NewsData.io API: `https://newsdata.io/api/1/news`
- Finlight API: `https://api.finlight.me/v1/news`
- Register 4 tools using FastMCP decorators
- Handle provider-specific errors:
  - 401 - Invalid API key
  - 429 - Rate limit (30 credits/15 min for NewsData free tier)
  - 422 - Invalid parameters

### Tests
- Add unit tests to `tools/tests/tools/test_news_tool.py`
- Mock all API calls
- Test provider fallback logic
- Test date filtering, company entity matching

## Use Cases (from #2853)

| Agent from #2853 | How News API Helps |
|------------------|-------------------|
| Meeting Prepper | `news_by_company("Acme Corp", days=7)` → summarize for pre-call brief |
| Calendar Shark | `news_search("Series B funding")` → find trigger events for outreach |
| Job Board Sniper | `news_search("layoffs tech")` → identify companies with changes |
| Deal Risk Monitor | `news_sentiment("prospect company")` → flag negative sentiment |

## Notes

- **Free Tier:** NewsData.io offers 200 credits/day (2K articles) with commercial use
- **Rate Limits:** 30 credits per 15 minutes on free tier
- **12-Hour Delay:** Free tier articles delayed 12 hours (paid = real-time)
- **Sentiment:** Only available via Finlight provider (optional)
- **Different from web_search:** News APIs provide structured article metadata (date, source, category) vs unstructured snippets

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 2: Apollo.io

```markdown
# [Integration]: Apollo.io - Contact & Company Data Enrichment

## Overview

Add integration with Apollo.io API to enable agents to enrich contact and company data. Apollo provides access to 210M+ B2B contacts and is essential for sales workflows identified in #2853 - agents need to enrich leads, find decision makers, and research prospect companies. This replaces the need for Clearbit (which killed its free tier in April 2025).

**Use Cases from #2853:**
- "Meeting Prepper" agent needs prospect enrichment (title, company size, tech stack)
- "Calendar Shark" agent needs lead qualification data
- SDR agents need to find decision makers at target accounts
- All sales agents need identity & data resolution (Clearbit/Apollo mentioned in #2853)

## Requirements

Implement the following 4 MCP tools:

1. **apollo_enrich_person** - Enrich contact by email or LinkedIn URL
   - Parameters: `email` or `linkedin_url`
   - Optional: `first_name`, `last_name`, `domain` (improves match accuracy)
   - Returns: Full profile (name, title, phone, email, company info, LinkedIn)

2. **apollo_enrich_company** - Enrich company by domain
   - Parameters: `domain`
   - Returns: Firmographics (name, industry, size, funding, tech stack, HQ)

3. **apollo_search_people** - Search contacts with filters
   - Parameters: `titles` (array), `limit`
   - Optional: `seniorities`, `locations`, `company_sizes`, `industries`, `technologies`
   - Returns: List of matching contacts with email and company info

4. **apollo_search_companies** - Search companies with filters
   - Parameters: `limit`
   - Optional: `industries`, `employee_counts`, `locations`, `technologies`
   - Returns: List of matching companies with firmographic data

## Authentication

- **Credential:** `APOLLO_API_KEY`
- **Auth Method:** API key in request body (`api_key` parameter)
- **Get Key:** Settings → Integrations → API → Connect

**Costing:**
| Plan | Price | Export Credits/mo |
|------|-------|-------------------|
| Free | $0 | 10 |
| Basic | $49/user/mo | 1,000 |
| Professional | $79/user/mo | 2,000 |
| Overage | - | $0.20/credit |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- Support `APOLLO_API_KEY` environment variable
- Health check endpoint: `https://api.apollo.io/v1/auth/health`

### Tool Implementation
- Create `tools/src/aden_tools/tools/apollo_tool/` directory
- Implement `_ApolloClient` class wrapping API calls
- API Base URL: `https://api.apollo.io/v1`
- Register 4 tools using FastMCP decorators
- Handle Apollo-specific errors:
  - 401 - Invalid API key
  - 403 - Insufficient credits
  - 422 - Invalid parameters
  - 429 - Rate limit exceeded

### Tests
- Add unit tests to `tools/tests/tools/test_apollo_tool.py`
- Mock all Apollo API calls
- Test enrichment responses
- Test search filters (title, seniority, company size)
- Test "not found" handling (graceful empty response)

## Use Cases (from #2853)

| Agent from #2853 | How Apollo Helps |
|------------------|-----------------|
| Meeting Prepper | `apollo_enrich_person(email)` → get title, company, LinkedIn before call |
| Calendar Shark | `apollo_search_people(titles=["VP Sales"])` → find leads matching ICP |
| SDR Agent | `apollo_enrich_company(domain)` → research account before outreach |
| Data Hygiene | `apollo_enrich_person(email)` → validate/update stale CRM records |

**#2853 explicitly requests:** "Identity & Data Resolution" tools like Clearbit and Apollo for lead enrichment and company data.

## Notes

- **Replaces Clearbit:** Clearbit killed free tier April 2025; Apollo offers similar data
- **Credit-Based:** Each enrichment/search consumes 1 export credit
- **No Rollover:** Credits reset monthly (don't accumulate)
- **Rate Limits:** ~300 requests/minute (varies by plan)
- **Bulk Support:** `/v1/people/bulk_match` supports up to 10K records (future enhancement)

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 3: Greenhouse

```markdown
# [Integration]: Greenhouse - ATS & Recruiting Workflow Automation

## Overview

Add integration with Greenhouse Harvest API to enable agents to manage recruiting workflows. Greenhouse is a leading ATS used by thousands of companies - agents need access to job postings, candidates, and applications to automate sourcing, track hiring progress, and gather competitive intelligence on hiring trends.

**Use Cases from #2853:**
- "Job Board Sniper" agent needs job posting data for competitive intelligence
- Recruiting automation workflows need candidate submission
- #2853 explicitly lists Greenhouse as a required "Business Systems" integration

## Requirements

Implement the following 6 MCP tools:

1. **greenhouse_list_jobs** - List job postings with filters
   - Parameters: `limit` (default 50)
   - Optional: `status` (open/closed/draft), `department_id`, `office_id`
   - Returns: List of jobs with ID, title, status, department, location

2. **greenhouse_get_job** - Get detailed job information
   - Parameters: `job_id`
   - Returns: Complete job data (description, openings, hiring team, created/updated dates)

3. **greenhouse_list_candidates** - List candidates with filters
   - Parameters: `limit` (default 50)
   - Optional: `job_id`, `stage`, `created_after`, `updated_after`
   - Returns: List of candidates with name, email, current stage, application status

4. **greenhouse_get_candidate** - Get full candidate details
   - Parameters: `candidate_id`
   - Returns: Complete candidate profile (applications, resume, activity, interviews)

5. **greenhouse_add_candidate** - Submit new candidate to pipeline
   - Parameters: `first_name`, `last_name`, `email`, `job_id`
   - Optional: `phone`, `source`, `resume_url`, `notes`
   - Returns: Candidate ID and application status

6. **greenhouse_list_applications** - List applications for a job
   - Parameters: `job_id`, `limit`
   - Optional: `status` (active/rejected/hired)
   - Returns: List of applications with candidate, stage, status

## Authentication

- **Credential:** `GREENHOUSE_API_KEY` (Harvest API key)
- **Auth Method:** HTTP Basic Auth (API key as username, empty password)
- **Header:** `Authorization: Basic {base64(api_key:)}`
- **Requirement:** HTTPS mandatory (HTTP returns 403)

**Costing:**
| Aspect | Details |
|--------|---------|
| API Cost | Included with Greenhouse subscription |
| Per-Call Cost | $0 (no additional charges) |
| Platform Cost | $6,000-$25,000/year (quote-based) |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- Support `GREENHOUSE_API_KEY` environment variable
- Health check: `GET https://harvest.greenhouse.io/v1/jobs?per_page=1`

### Tool Implementation
- Create `tools/src/aden_tools/tools/greenhouse_tool/` directory
- Implement `_GreenhouseClient` class with Basic Auth
- API Base URL: `https://harvest.greenhouse.io/v1`
- Register 6 tools using FastMCP decorators
- Handle pagination (link-based, `per_page` max 500)
- Handle Greenhouse-specific errors:
  - 401 - Invalid API key
  - 403 - Insufficient permissions / HTTP used
  - 404 - Resource not found
  - 429 - Rate limit (50 requests/10 seconds)

### Tests
- Add unit tests to `tools/tests/tools/test_greenhouse_tool.py`
- Mock all Greenhouse API calls
- Test Basic Auth encoding
- Test pagination handling
- Test candidate creation flow

## Use Cases (from #2853)

| Agent from #2853 | How Greenhouse Helps |
|------------------|---------------------|
| Job Board Sniper | `greenhouse_list_jobs(status="open")` → monitor competitor hiring |
| Recruiting Agent | `greenhouse_add_candidate(...)` → submit sourced candidates |
| Meeting Prepper | `greenhouse_list_jobs(department="Engineering")` → understand team growth |
| RevOps | `greenhouse_list_applications(job_id)` → track hiring pipeline |

**#2853 explicitly requests:** Greenhouse as a "Business Systems" integration for ATS/recruiting workflows.

## Notes

- **No API Cost:** API access included with Greenhouse subscription
- **Rate Limits:** 50 requests per 10 seconds (check `X-RateLimit-Remaining` header)
- **Pagination:** Uses Link header (not offset) - implement cursor-based pagination
- **Basic Auth:** Must base64 encode `{api_key}:` (note trailing colon)
- **Enterprise Features:** Custom fields on applications require Enterprise tier
- **Two APIs:** Harvest (private, full access) vs Job Board (public, read-only) - this implements Harvest

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Summary

| Issue | Integration | Tools | Effort | #2853 Use Cases |
|-------|-------------|-------|--------|-----------------|
| 1 | News APIs | 4 | 1-2 days | Meeting Prepper, Calendar Shark, Deal Risk |
| 2 | Apollo.io | 4 | 2-3 days | Meeting Prepper, SDR, Lead Enrichment |
| 3 | Greenhouse | 6 | 2-3 days | Job Board Sniper, Recruiting Automation |

## Issue 4: Plaid

```markdown
# [Integration]: Plaid - Bank Account & Transaction Data

## Overview

Add integration with Plaid - Bank Account & Transaction Data to enable agents to access bank account data, verify identity via bank metadata, and analyze transaction history.

## Requirements

Implement the following 4 MCP tools:

1. **plaid_link_account** - Initiate bank account linking
2. **plaid_get_transactions** - Retrieve transaction history
3. **plaid_verify_identity** - Identity verification via bank data
4. **plaid_get_balance** - Real-time account balance

## Authentication

- **Credentials:** `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV`
- Production requires Plaid approval

**Costing:**
| Plan | Price |
|------|-------|
| Free (Sandbox) | $0 |
| Production | $0.30-$1.50/connection/month |

## Implementation Details

### Credential Management
- Add credential specs to `tools/src/aden_tools/credentials/integrations.py`
- Plaid: `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV`

### Tool Implementation
- Create `tools/src/aden_tools/tools/plaid_tool/` directory
- Implement `_PlaidClient` class wrapping API calls
- API Base URL: `https://api.plaid.com`
- Register 4 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_plaid_tool.py`
- Mock all Plaid API calls
- Test account linking, transaction retrieval, and identity verification

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 5: Onfido

```markdown
# [Integration]: Onfido - Identity Document Verification

## Overview

Add integration with Onfido - Identity Document Verification to provide automated identity document and facial biometric verification.

## Requirements

Implement the following 4 MCP tools:

1. **onfido_create_applicant** - Create verification applicant
2. **onfido_upload_document** - Upload ID document for verification
3. **onfido_create_check** - Run verification check
4. **onfido_get_check_result** - Retrieve verification result

## Authentication

- **Credential:** `ONFIDO_API_TOKEN`
- Sandbox available for testing

**Costing:**
| Check Type | Price |
|------------|-------|
| Document Check | $1-3/check |
| Biometric Check | $3-5/check |
| Full KYC | $5-10/check |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- Onfido: `ONFIDO_API_TOKEN`

### Tool Implementation
- Create `tools/src/aden_tools/tools/onfido_tool/` directory
- Implement `_OnfidoClient` class wrapping API calls
- API Base URL: `https://api.onfido.com/v3.4`
- Register 4 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_onfido_tool.py`
- Mock all Onfido API calls
- Test applicant creation and check result retrieval

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 6: Sanctions.io

```markdown
# [Integration]: Sanctions.io - PEP/Sanctions Screening

## Overview

Add integration with Sanctions.io - PEP/Sanctions Screening for global PEP (Politically Exposed Persons) and sanctions watchlists screening.

## Requirements

Implement the following 4 MCP tools:

1. **sanctions_search_individual** - Screen individual against watchlists
2. **sanctions_search_entity** - Screen organization against watchlists
3. **sanctions_get_lists** - Retrieve available sanction lists
4. **sanctions_monitor_entity** - Set up continuous monitoring

## Authentication

- **Credential:** `SANCTIONS_API_KEY`

**Costing:**
| Plan | Price |
|------|-------|
| Starter | $99/month (1,000 searches) |
| Growth | $299/month (5,000 searches) |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- Sanctions.io: `SANCTIONS_API_KEY`

### Tool Implementation
- Create `tools/src/aden_tools/tools/sanctions_tool/` directory
- Implement `_SanctionsClient` class wrapping API calls
- API Base URL: `https://api.sanctions.io/v1`
- Register 4 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_sanctions_tool.py`
- Mock all Sanctions.io API calls
- Test individual and entity screening

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 7: Google Maps Platform

```markdown
# [Integration]: Google Maps Platform - Routing & Geolocation

## Overview

Add integration with Google Maps Platform - Routing & Geolocation to enable agents to power logistics and delivery workflows.

## Requirements

Implement the following 6 MCP tools:

1. **maps_geocode** - Convert address to coordinates
2. **maps_reverse_geocode** - Convert coordinates to address
3. **maps_directions** - Get route between points
4. **maps_distance_matrix** - Calculate distances for multiple origins/destinations
5. **maps_traffic** - Get real-time traffic conditions
6. **maps_optimize_route** - Optimize multi-stop route (TSP solver)

## Authentication

- **Credential:** `GOOGLE_MAPS_API_KEY`
- Enable: Geocoding, Directions, Distance Matrix, Routes APIs

**Costing:**
| API | Price |
|-----|-------|
| Geocoding | $5/1,000 requests |
| Directions | $5-10/1,000 requests |
| Distance Matrix | $5-10/1,000 elements |
| Route Optimization | $10/1,000 requests |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- Google Maps: `GOOGLE_MAPS_API_KEY`

### Tool Implementation
- Create `tools/src/aden_tools/tools/google_maps_tool/` directory
- Implement `_GoogleMapsClient` class wrapping API calls
- API Base URL: `https://maps.googleapis.com`
- Register 6 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_google_maps_tool.py`
- Mock all Google Maps API calls
- Test geocoding, directions, and route optimization

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 8: Samsara

```markdown
# [Integration]: Samsara - Fleet Telematics

## Overview

Add integration with Samsara - Fleet Telematics to enable agents to track vehicle health and location in real-time.

## Requirements

Implement the following 6 MCP tools:

1. **samsara_list_vehicles** - Get all fleet vehicles
2. **samsara_get_vehicle_stats** - Get vehicle health metrics
3. **samsara_get_location** - Get real-time vehicle location
4. **samsara_get_driver_safety** - Get driver safety scores
5. **samsara_get_fuel_usage** - Get fuel consumption data
6. **samsara_get_alerts** - Get vehicle/driver alerts

## Authentication

- **Credential:** `SAMSARA_API_TOKEN`
- Webhook support for real-time events

**Costing:**
| Plan | Price |
|------|-------|
| Complete | Custom pricing per vehicle |
| API Access | Included with subscription |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- Samsara: `SAMSARA_API_TOKEN`

### Tool Implementation
- Create `tools/src/aden_tools/tools/samsara_tool/` directory
- Implement `_SamsaraClient` class wrapping API calls
- API Base URL: `https://api.samsara.com`
- Register 6 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_samsara_tool.py`
- Mock all Samsara API calls
- Test vehicle list, location, and alert retrieval

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 9: ShipStation

```markdown
# [Integration]: ShipStation - Shipping Labels

## Overview

Add integration with ShipStation - Shipping Labels to automate order fulfillment by connecting to ShipStation for label generation and tracking.

## Requirements

Implement the following 5 MCP tools:

1. **shipstation_create_order** - Create shipping order
2. **shipstation_get_rates** - Get carrier rates
3. **shipstation_create_label** - Generate shipping label
4. **shipstation_track_shipment** - Get tracking updates
5. **shipstation_void_label** - Cancel/void label

## Authentication

- **Credential:** `SHIPSTATION_API_KEY`, `SHIPSTATION_API_SECRET`

**Costing:**
| Plan | Price |
|------|-------|
| Starter | $9.99/month (50 shipments) |
| Bronze | $29.99/month (500 shipments) |
| Gold | $99.99/month (2,000 shipments) |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- ShipStation: `SHIPSTATION_API_KEY`, `SHIPSTATION_API_SECRET`

### Tool Implementation
- Create `tools/src/aden_tools/tools/shipstation_tool/` directory
- Implement `_ShipStationClient` class wrapping API calls
- API Base URL: `https://ssapi.shipstation.com`
- Register 5 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_shipstation_tool.py`
- Mock all ShipStation API calls
- Test order creation and label generation

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 10: FHIR R4

```markdown
# [Integration]: FHIR R4 - EHR Data Access

## Overview

Add integration with FHIR R4 - EHR Data Access to allow agents to interact directly with Electronic Health Records (EHR) safely and securely.

## Requirements

Implement the following 6 MCP tools:

1. **fhir_get_patient** - Retrieve patient demographics
2. **fhir_get_conditions** - Get patient diagnoses/conditions
3. **fhir_get_medications** - Get active medications
4. **fhir_get_appointments** - Get scheduled appointments
5. **fhir_create_appointment** - Schedule new appointment
6. **fhir_create_document** - Insert clinical document

## Authentication

- **Credentials:** `FHIR_BASE_URL`, `FHIR_CLIENT_ID`, `FHIR_CLIENT_SECRET`
- OAuth 2.0 / SMART on FHIR authentication
- Requires EHR vendor approval for production

**Costing:**
| Vendor | API Access |
|--------|------------|
| Epic | Via App Orchard (approval required) |
| Cerner | Via CODE program |
| Sandbox | Free for development |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- FHIR: `FHIR_BASE_URL`, `FHIR_CLIENT_ID`, `FHIR_CLIENT_SECRET`

### Tool Implementation
- Create `tools/src/aden_tools/tools/fhir_tool/` directory
- Implement `_FHIRClient` class wrapping API calls
- API Base URL: Dynamic based on `FHIR_BASE_URL`
- Register 6 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_fhir_tool.py`
- Mock all FHIR API calls
- Test patient retrieval and appointment creation

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 11: ClinicalTrials.gov

```markdown
# [Integration]: ClinicalTrials.gov - Clinical Trial Data

## Overview

Add integration with ClinicalTrials.gov - Clinical Trial Data to enable agents to match patients to eligible clinical trials.

## Requirements

Implement the following 4 MCP tools:

1. **ct_search_trials** - Search trials by condition, location, phase
2. **ct_get_trial** - Get detailed trial information
3. **ct_get_eligibility** - Get inclusion/exclusion criteria
4. **ct_get_locations** - Get trial site locations

## Authentication

- **Credential:** None required (public API)
- Rate limits apply

**Costing:**
| Plan | Price |
|------|-------|
| API Access | Free |

## Implementation Details

### Tool Implementation
- Create `tools/src/aden_tools/tools/clinical_trials_tool/` directory
- Implement `_ClinicalTrialsClient` class wrapping API calls
- API Base URL: `https://clinicaltrials.gov/api/v2`
- Register 4 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_clinical_trials_tool.py`
- Mock all ClinicalTrials.gov API calls
- Test trial search and eligibility criteria extraction

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 12: Deepgram

```markdown
# [Integration]: Deepgram/Whisper - Medical Transcription

## Overview

Add integration with Deepgram/Whisper - Medical Transcription to provide high-accuracy medical transcription for agents.

## Requirements

Implement the following 4 MCP tools:

1. **transcribe_audio** - Transcribe audio file
2. **transcribe_stream** - Real-time streaming transcription
3. **transcribe_with_diarization** - Transcribe with speaker labels
4. **get_medical_entities** - Extract clinical entities from transcript

## Authentication

- **Credential:** `DEEPGRAM_API_KEY` or `WHISPER_API_KEY`

**Costing:**
| Provider | Price |
|----------|-------|
| Deepgram | $0.0043/minute (medical model) |
| Whisper (OpenAI) | $0.006/minute |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`
- Deepgram: `DEEPGRAM_API_KEY`

### Tool Implementation
- Create `tools/src/aden_tools/tools/transcription_tool/` directory
- Implement `_TranscriptionClient` class wrapping API calls
- API Base URL: `https://api.deepgram.com/v1`
- Register 4 tools using FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_transcription_tool.py`
- Mock all Transcription API calls
- Test audio transcription and entity extraction

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

## Issue 13: Salesforce

```markdown
# [Integration]: Salesforce CRM - Leads, Contacts, Opportunities, and SOQL

## Overview

Add integration with Salesforce CRM to enable agents to manage the full sales lifecycle. Salesforce is the industry standard system-of-record for enterprise sales. This integration is critical for agents like "Zombie Deal Waker" and "Deal Intelligence Agent" identified in #2853.

## Requirements

Implement the following 6 MCP tools:

1. **salesforce_query** - Execute arbitrary SOQL queries
2. **salesforce_get_record** - Retrieve a specific record (Lead, Contact, Opportunity)
3. **salesforce_create_record** - Create a new record
4. **salesforce_update_record** - Update existing record fields
5. **salesforce_list_objects** - List available SObjects and metadata
6. **salesforce_search** - Use SOSL to search across multiple objects

## Authentication

- **Credentials:** `SALESFORCE_CLIENT_ID`, `SALESFORCE_CLIENT_SECRET`, `SALESFORCE_USERNAME`, `SALESFORCE_PASSWORD`, `SALESFORCE_SECURITY_TOKEN`
- OAuth 2.0 Web Server Flow or Username-Password Flow (for headless)

**Costing:**
- Included in Salesforce Professional/Enterprise/Unlimited editions with API access enabled.

## Implementation Details

### Credential Management
- Add credential specs to `tools/src/aden_tools/credentials/integrations.py`
- Support both Sandbox and Production instance URLs.

### Tool Implementation
- Create `tools/src/aden_tools/tools/salesforce_tool/`
- Use `simple-salesforce` library for easy REST API interaction.
- Register tools using FastMCP decorators.

### Tests
- Add unit tests to `tools/tests/tools/test_salesforce_tool.py`
- Mock Salesforce REST API responses.

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 14: Twilio

```markdown
# [Integration]: Twilio - SMS, Voice, and WhatsApp Engagement

## Overview

Add integration with Twilio to enable agents to communicate with humans via SMS, Voice, and WhatsApp. This powers the "Calendar Shark" and "KYC Guardian" agents for real-time notifications and lead engagement.

## Requirements

Implement the following 5 MCP tools:

1. **twilio_send_sms** - Send outbound SMS messages
2. **twilio_make_call** - Initiate outbound voice calls with TwiML instructions
3. **twilio_send_whatsapp** - Send WhatsApp messages via Twilio Sandbox/API
4. **twilio_list_messages** - Fetch recent message history
5. **twilio_validate_number** - Use Lookup API to verify phone number format and carrier

## Authentication

- **Credentials:** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

**Costing:**
- Usage-based pricing (per message/minute).

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`

### Tool Implementation
- Create `tools/src/aden_tools/tools/twilio_tool/`
- Use `twilio` Python library.

### Tests
- Add unit tests to `tools/tests/tools/test_twilio_tool.py`
- Mock Twilio API calls.

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 15: DocuSign

```markdown
# [Integration]: DocuSign - E-Signature and Document Workflow

## Overview

Add integration with DocuSign to enable agents to manage document signatures and contract workflows. Critical for "Contract Auditor" and "Onboarding Orchestrator" agents in Legal and HR verticals.

## Requirements

Implement the following 6 MCP tools:

1. **docusign_create_envelope** - Create a signature request from a template or file
2. **docusign_add_recipient** - Add signers to an existing envelope
3. **docusign_send_envelope** - Trigger the delivery of an envelope
4. **docusign_get_status** - Check terminal status of an envelope (Signed, Voided, etc.)
5. **docusign_download_document** - Retrieve the signed PDF agreement
6. **docusign_list_templates** - Search available document templates

## Authentication

- **Credentials:** `DOCUSIGN_INTEGRATION_KEY`, `DOCUSIGN_USER_ID`, `DOCUSIGN_ACCOUNT_ID`, `DOCUSIGN_PRIVATE_KEY` (JWT Auth)

## Implementation Details

### Tool Implementation
- Create `tools/src/aden_tools/tools/docusign_tool/`
- Use DocuSign Python SDK.

### Tests
- Mock DocuSign API Responses.

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 16: Okta

```markdown
# [Integration]: Okta - Workforce Identity and Access Management

## Overview

Add integration with Okta to enable agents to manage user provisioning, group assignments, and application access. Essential for the "Onboarding Orchestrator" agent in the HR vertical.

## Requirements

Implement the following 5 MCP tools:

1. **okta_create_user** - Provision a new user in Okta
2. **okta_assign_app** - Grant a user access to a specific application
3. **okta_add_to_group** - Add a user to a security/distribution group
4. **okta_deactivate_user** - Deprovision or suspend a user
5. **okta_list_users** - Search for users by email or attribute

## Authentication

- **Credentials:** `OKTA_ORG_URL`, `OKTA_API_TOKEN`

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 17: BambooHR

```markdown
# [Integration]: BambooHR - Employee Data and HR Management

## Overview

Add integration with BambooHR to enable agents to access and manage employee records. Core requirement for HR operations automation.

## Requirements

Implement the following 5 MCP tools:

1. **bamboohr_get_employee** - Fetch detailed profile for an employee
2. **bamboohr_add_employee** - Create a new employee record (for onboarding)
3. **bamboohr_update_employee** - Update existing records (promotions, address changes)
4. **bamboohr_list_directory** - Get company directory for networking agents
5. **bamboohr_get_time_off** - Check leave balances and status

## Authentication

- **Credentials:** `BAMBOOHR_SUBDOMAIN`, `BAMBOOHR_API_KEY`

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

---

## Issue 18: Apple Health

```markdown
# [Integration]: Apple Health - Personal Wellness & Wearable Data

## Overview

Add integration with Apple Health data to enable "Personal Wellness" and "Chronic Disease Management" agents. Since Apple HealthKit is restricted to on-device access, this integration implements a dual-path approach: 
1. **Direct Ingestion**: Tools to parse and analyze exported Apple Health `export.zip` (XML/CSV) files.
2. **Aggregator Support**: Integration with a wearable data aggregator (e.g., [Vital API](https://tryvital.io)) to pull real-time HealthKit, Oura, and Garmin data server-side.

## Requirements

Implement the following 4 MCP tools:

1. **health_analyze_export** - Parse a provided `export.zip` and return activity/vitals summaries.
2. **health_get_vitals** - (via Aggregator) Fetch recent heart rate, HRV, and sleep data.
3. **health_get_activity** - (via Aggregator) Fetch steps, calories, and workout history.
4. **health_check_anomalies** - Agent-specific logic to flag vitals outside of baseline.

## Authentication

- **Direct Ingestion**: None (File-based).
- **Aggregator**: `VITAL_API_KEY`, `VITAL_REGION` (US/EU).

## Implementation Details

### Tool Implementation
- Create `tools/src/aden_tools/tools/apple_health_tool/`
- Use `xml.etree.ElementTree` for high-performance parsing of large `export.xml` files.
- Implement a VITAL API client for real-time polling.

**Parent Issue:** #2805
**Use Cases Issue:** #2853
```

### Summary (Updated)

| Issue | Integration | Tools | Effort | #2853 Use Cases |
|-------|-------------|-------|--------|-----------------|
| 1 | News APIs | 4 | 1-2 days | Meeting Prepper, Calendar Shark, Deal Risk |
| 2 | Apollo.io | 4 | 2-3 days | Meeting Prepper, SDR, Lead Enrichment |
| 3 | Greenhouse | 6 | 2-3 days | Job Board Sniper, Recruiting Automation |
| 4 | Plaid | 4 | 2-3 days | KYC, Transaction Monitoring |
| 5 | Onfido | 4 | 2-3 days | KYC, ID Verification |
| 6 | Sanctions.io | 4 | 1-2 days | AML, Compliance |
| 7 | Google Maps | 6 | 2-3 days | Route Optimization, Geocoding |
| 8 | Samsara | 6 | 2-3 days | Fleet Management, Predictive Maintenance |
| 9 | ShipStation | 5 | 2-3 days | Warehouse, Fulfillment |
| 10 | FHIR R4 | 6 | 3-5 days | EHR Access, Medical Agents |
| 11 | ClinicalTrials.gov | 4 | 1-2 days | Clinical Trials, Patient Matching |
| 12 | Deepgram | 4 | 2-3 days | Ambient Scribe, Medical Transcription |
| 13 | Salesforce | 6 | 3-5 days | CRM, Pipeline Management, Deal Intel |
| 14 | Twilio | 5 | 2-3 days | SMS, Voice, Lead Engagement |
| 15 | DocuSign | 6 | 3-5 days | Legal, Contracts, Onboarding signatures |
| 16 | Okta | 5 | 2-3 days | IT Provisioning, Identity Management |
| 17 | BambooHR | 5 | 2-3 days | HR Ops, Employee Records |
| 18 | Apple Health | 4 | 2-3 days | Wellness, Personal Health, Chronic Management |

### Labels for All Issues
- `enhancement`
- `help wanted`
- `integrations`
- `tools`

### References
- Parent Issue: [#2805](https://github.com/adenhq/hive/issues/2805) - Integration Hub
- Use Cases Issue: [#2853](https://github.com/adenhq/hive/issues/2853) - Business Process Use Cases




Existing Integrations in Codebase:                                                                                   
  - hubspot_tool - CRM (already done)                                                                                  
  - apollo_tool - Data enrichment (your PR pending)                                                                    
  - email_tool - Email (Resend)                                                                                        
  - web_search_tool - Search (Brave/Google)                                                                            
  - web_scrape_tool - Web scraping                                                                                     
                                                                                                                       
  No traces found for any of these 16 tools:                                                                           
  ┌─────┬────────────────────┬───────────────────┬─────────────────────────────┬──────────────────────────────┐        
  │  #  │    Integration     │     Free Tier     │          Use Cases          │        Recommendation        │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 1   │ News APIs          │ Yes (200/day)     │ Meeting Prep, Lead Triggers │ ⭐ HIGH - Easy, free         │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 2   │ Greenhouse         │ No (enterprise)   │ Recruiting                  │ Medium                       │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 3   │ Plaid              │ Sandbox only      │ FinTech KYC                 │ Medium                       │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 4   │ Onfido             │ Sandbox           │ ID Verification             │ Low                          │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 5   │ Sanctions.io       │ No ($99/mo)       │ Compliance                  │ Low                          │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 6   │ Google Maps        │ $200 free credit  │ Logistics                   │ ⭐ HIGH - Widely useful      │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 7   │ Samsara            │ No (enterprise)   │ Fleet                       │ Low                          │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 8   │ ShipStation        │ No ($10/mo)       │ Shipping                    │ Low                          │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 9   │ FHIR R4            │ Sandbox           │ Healthcare                  │ Medium                       │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 10  │ ClinicalTrials.gov │ Yes (free API)    │ Clinical trials             │ ⭐ HIGH - 100% free          │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 11  │ Deepgram           │ Yes ($200 credit) │ Transcription               │ Medium                       │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 12  │ Salesforce         │ Dev org free      │ CRM                         │ ⭐ HIGH - Critical for sales │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 13  │ Twilio             │ Yes (trial)       │ SMS/Voice                   │ ⭐ HIGH - Widely useful      │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 14  │ DocuSign           │ Sandbox           │ E-signatures                │ Medium                       │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 15  │ Okta               │ Dev org free      │ Identity                    │ Medium                       │        
  ├─────┼────────────────────┼───────────────────┼─────────────────────────────┼──────────────────────────────┤        
  │ 16  │ BambooHR           │ No                │ HR                          │ Low                          │        
  └─────┴────────────────────┴───────────────────┴─────────────────────────────┴──────────────────────────────┘        
  Top Recommendations (No duplicates, high value)                                                                      
                                                                                                                       
  1. News APIs - Free, easy, directly supports Meeting Prepper agent                                                   
  2. ClinicalTrials.gov - 100% free public API, unique healthcare value                                                
  3. Twilio - SMS/Voice, widely needed for notifications                                                               
  4. Salesforce - Industry standard CRM, critical for sales agents                                                     
  5. Google Maps - $200 free credit, logistics/geocoding                                                               
                                                                                                                       
  Which one would you like to implement next?                                                                          
                                                                                                                       
✻ Cooked for 1m 32s                                                                                                    
                     