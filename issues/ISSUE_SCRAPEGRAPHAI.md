# [Integration]: ScrapeGraphAI - AI-Powered Web Scraping with Natural Language

## Overview

Add integration with ScrapeGraphAI to enable agents to perform intelligent web scraping using natural language prompts. ScrapeGraphAI is an AI-native scraping platform that extracts structured data from any website using LLM-powered understanding, eliminating the need for complex CSS selectors or XPath queries.

**Why ScrapeGraphAI over Playwright-based `web_scrape_tool`?**

| Feature | Current `web_scrape_tool` | ScrapeGraphAI |
|---------|---------------------------|---------------|
| Extraction Method | CSS selectors / auto-detect | Natural language prompts |
| Output Format | Raw text | Structured JSON, CSV, Markdown |
| JavaScript Handling | Playwright (local) | Cloud-based with stealth mode |
| Anti-Bot Bypass | Playwright-stealth | Advanced proxy rotation + residential IPs |
| Multi-Page Crawling | ❌ No | ✅ SmartCrawler with depth control |
| Agentic Browsing | ❌ No | ✅ AgenticScraper for complex workflows |
| LLM Integration | ❌ Manual | ✅ Built-in AI inference |
| MCP Server | ❌ No | ✅ Official MCP server |

**Use Cases from #2853:**
- **Lead Enrichment Agent**: Extract company info, team pages, pricing from prospect websites using natural language
- **Research Agent**: Crawl entire documentation sites and convert to structured knowledge
- **Meeting Prepper Agent**: Get structured competitor data without writing selectors
- **Market Research**: Extract product data, reviews, pricing from e-commerce sites

## Duplicate Check

- ✅ **No ScrapeGraphAI references found** in codebase
- ✅ **No existing issues/PRs** for ScrapeGraphAI
- ⚠️ **Related but different**: Existing `web_scrape_tool` (Playwright-based, selector-driven)

## Requirements

### Option A: External MCP Server Integration (Recommended)

Add ScrapeGraphAI as an **external MCP server** in agent configurations, leveraging their official MCP server:

```json
{
  "mcpServers": {
    "scrapegraph": {
      "type": "sse",
      "url": "https://mcp.scrapegraphai.com/sse",
      "apiKey": "${SCRAPEGRAPH_API_KEY}"
    }
  }
}
```

This approach immediately exposes all 8 ScrapeGraphAI tools to Hive agents:

| Tool | Description | Parameters |
|------|-------------|------------|
| `smartscraper` | AI extraction from a single page | `user_prompt`, `website_url`, `number_of_scrolls`, `render_heavy_js` |
| `searchscraper` | Web-wide search + extraction | `user_prompt`, `num_results`, `number_of_scrolls` |
| `markdownify` | Convert webpage to clean Markdown | `website_url` |
| `scrape` | Basic HTML content extraction | `website_url`, `render_heavy_js` |
| `sitemap` | Extract website sitemap | `website_url` |
| `smartcrawler_initiate` | Start multi-page crawl | `url`, `prompt`, `extraction_mode`, `depth`, `max_pages` |
| `smartcrawler_fetch_results` | Retrieve crawl results | `request_id` |
| `agentic_scrapper` | Autonomous multi-step browsing | `url`, `user_prompt`, `output_schema`, `steps`, `ai_extraction` |

### Option B: Native Tool Implementation

Alternatively, implement native MCP tools wrapping the ScrapeGraphAI API:

1. **smart_scrape** - AI-powered single page extraction
2. **search_scrape** - Search and analyze across the web
3. **web_to_markdown** - Convert any page to clean Markdown
4. **smart_crawl** - Multi-page site crawling with AI extraction

## Authentication

- **Credential:** `SCRAPEGRAPH_API_KEY`
- **Auth Method:** API key in request header
- **Get Key:** [https://dashboard.scrapegraphai.com](https://dashboard.scrapegraphai.com)

**Costing:**
| Plan | Price | Credits | Rate Limit |
|------|-------|---------|------------|
| Free | $0 | 50 (one-time) | 10 req/min |
| Starter | $99/year | 60,000/year | 30 req/min |
| Growth | $349/year | 480,000/year | 60 req/min |
| Pro | $1,499/year | 3,000,000/year | 200 req/min |

**What's Included Per Credit:**
- ✅ HTTP requests + JavaScript rendering + stealth mode
- ✅ Proxy rotation + anti-bot bypass
- ✅ AI inference + NLP + data structuring
- ✅ Output formatting (JSON, CSV, Markdown)
- ✅ Optional output schema validation

## Implementation Details

### Option A: MCP Server Configuration (Minimal Effort)

**Step 1:** Add ScrapeGraphAI to `core/examples/mcp_servers.json`:
```json
{
  "scrapegraph": {
    "type": "sse",
    "url": "https://mcp.scrapegraphai.com/sse",
    "env": {
      "SCRAPEGRAPH_API_KEY": "SCRAPEGRAPH_API_KEY"
    },
    "description": "AI-powered web scraping with natural language prompts"
  }
}
```

**Step 2:** Document in `core/MCP_INTEGRATION_GUIDE.md`

**Step 3:** Add credential spec to `tools/src/aden_tools/credentials/integrations.py`

### Option B: Native Tool Implementation (Full Control)

**Step 1:** Create `tools/src/aden_tools/tools/scrapegraph_tool/`

**Step 2:** Implement API client:
```python
def _smart_scrape(
    url: str,
    prompt: str,
    api_key: str,
    output_schema: dict | None = None,
) -> dict:
    response = httpx.post(
        "https://api.scrapegraphai.com/v1/smartscraper",
        headers={"x-api-key": api_key},
        json={
            "website_url": url,
            "user_prompt": prompt,
            "output_schema": output_schema,
        },
        timeout=60.0,
    )
    return response.json()
```

**Step 3:** Register tools with FastMCP decorators

### Tests
- Add unit tests to `tools/tests/tools/test_scrapegraph_tool.py`
- Mock ScrapeGraphAI API responses
- Test AI extraction with various prompts
- Test sitemap and crawl functionality

## Use Cases (from #2853)

| Agent from #2853 | How ScrapeGraphAI Helps |
|------------------|------------------------|
| Meeting Prepper | `smartscraper("Extract company overview, team size, and funding", prospect_url)` → structured JSON |
| Lead Enrichment | `smartscraper("Get all team member names, titles, and LinkedIn URLs", "/about-us")` → contact list |
| Research Agent | `smartcrawler_initiate(docs_url, "Extract all API endpoints", depth=3)` → documentation knowledge |
| Competitor Intel | `searchscraper("Find pricing pages for CRM software")` → market comparison data |

## Impact Assessment

### Benefits
1. **Natural Language Extraction**: No CSS selectors or XPath needed - just describe what you want
2. **Structured Output**: Returns validated JSON matching your schema
3. **Official MCP Support**: ScrapeGraphAI already provides an MCP server
4. **Anti-Bot**: Handles CAPTCHAs, proxies, and fingerprint evasion
5. **Multi-Page Crawling**: SmartCrawler can traverse entire sites
6. **Agentic Workflows**: AgenticScraper handles complex multi-step interactions

### Considerations
- **Cost**: Credits consumed per request (free tier is limited)
- **Latency**: Cloud-based processing adds ~2-5 seconds vs local
- **Dependency**: Relies on external service availability

## Comparison with Existing Tools

| Capability | `web_scrape` | `web_search` | ScrapeGraphAI |
|------------|--------------|--------------|---------------|
| Single page text | ✅ | ❌ | ✅ |
| Search web | ❌ | ✅ | ✅ (searchscraper) |
| Multi-page crawl | ❌ | ❌ | ✅ (smartcrawler) |
| Natural language | ❌ | ❌ | ✅ |
| Structured JSON | ❌ | ✅ | ✅ (with schema) |
| Page → Markdown | Manual | ❌ | ✅ (markdownify) |
| Form interaction | ❌ | ❌ | ✅ (agentic_scrapper) |

## Notes

- **50 Free Credits**: Sufficient for prototyping and agent development
- **Official MCP Server**: https://docs.scrapegraphai.com/services/mcp-server
- **Open Source Library**: Also available as `pip install scrapegraphai` for self-hosted
- **Output Schema**: Can define Pydantic-like schemas for validated extraction

## References

- **Website**: https://scrapegraphai.com/
- **API Documentation**: https://docs.scrapegraphai.com/
- **MCP Server Docs**: https://docs.scrapegraphai.com/services/mcp-server
- **GitHub (Open Source)**: https://github.com/ScrapeGraphAI/Scrapegraph-ai
- **Python Package**: `pip install scrapegraphai`

---

**Parent Issue:** #2805 (Integration Hub)
**Use Cases Issue:** #2853 (Business Process Use Cases)
**Related Tool:** [web_scrape_tool](file:///Users/siketyson/Desktop/aden/tools/src/aden_tools/tools/web_scrape_tool/)

## Labels
- `enhancement`
- `help wanted`
- `integrations`
- `tools`

## Recommendation

**Start with Option A (MCP Server Integration)** - minimal effort, immediate access to all 8 tools, maintained by ScrapeGraphAI team. This can later be extended to Option B if custom logic is needed.
