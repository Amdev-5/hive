# [Integration]: SerpAPI - Enhanced Google SERP Scraping

## Overview

Add SerpAPI as an additional provider for the existing `web_search_tool` to enable agents to scrape Google and other search engines with advanced features like CAPTCHA solving, location targeting, and rich structured SERP data.

**Why SerpAPI over Google Custom Search API?**

| Feature | Google Custom Search | SerpAPI |
|---------|---------------------|---------|
| Real SERP Data | ❌ Synthetic index | ✅ Real Google results |
| Rich Snippets | ❌ Limited | ✅ Full (Maps, Shopping, Knowledge Graph) |
| CAPTCHA Solving | ❌ No | ✅ Automatic |
| Location Targeting | ⚠️ Basic | ✅ Advanced (city-level accuracy) |
| Rate Limits | 100 queries/day (free) | 100 searches/month (free) |

**Use Cases from #2853:**
- **Meeting Prepper Agent**: Real-time company/prospect intelligence from actual Google SERPs
- **Lead Enrichment Agent**: Structured company data from Knowledge Graph
- **Research Agent**: Access to Google Scholar, News, Shopping, Maps, and other specialized engines

## Requirements

Extend the existing `web_search_tool` to support SerpAPI as a third provider:

### Modified Tool: `web_search`
- Add `provider: Literal["auto", "google", "brave", "serpapi"] = "auto"` option
- When `provider="serpapi"`, use SerpAPI's `/search` endpoint
- Auto-detection priority: Brave → Google CSE → SerpAPI (or configurable)

### New Parameters (SerpAPI-specific):
| Parameter | Type | Description |
|-----------|------|-------------|
| `engine` | str | Search engine: `google`, `google_news`, `google_scholar`, `google_maps`, `bing`, `duckduckgo`, `yahoo` |
| `location` | str | City/region for localized results (e.g., "Austin, Texas") |
| `device` | str | `desktop` or `mobile` results |

### Response Enhancements:
When using SerpAPI, return additional structured data:
- `organic_results` - Standard web results
- `knowledge_graph` - Entity information (if present)
- `related_questions` - "People also ask" data
- `local_results` - Maps/local pack data (if present)

## Authentication

- **Credential:** `SERPAPI_API_KEY`
- **Auth Method:** API key in query parameter (`api_key`)
- **Get Key:** [https://serpapi.com/dashboard](https://serpapi.com/dashboard) → API Key section

**Costing:**
| Plan | Price | Searches/Month |
|------|-------|----------------|
| Free | $0 | 100 |
| Developer | $75/mo | 5,000 |
| Production | $150/mo | 15,000 |
| Big Data | $250/mo | 30,000 |

## Implementation Details

### Credential Management
- Add credential spec to `tools/src/aden_tools/credentials/integrations.py`:
  ```python
  "SERPAPI_API_KEY": CredentialSpec(
      name="SerpAPI API Key",
      env_var="SERPAPI_API_KEY",
      description="API key for SerpAPI Google SERP scraping",
  )
  ```

### Tool Implementation
- Modify existing `tools/src/aden_tools/tools/web_search_tool/web_search_tool.py`
- Add `_search_serpapi()` function following the same pattern as `_search_brave()` and `_search_google()`
- API Base URL: `https://serpapi.com/search`
- Handle SerpAPI-specific errors:
  - 401 - Invalid API key
  - 429 - Rate limit exceeded
  - 400 - Invalid parameters

### Example SerpAPI Request
```python
def _search_serpapi(
    query: str,
    num_results: int,
    location: str,
    engine: str,
    api_key: str,
) -> dict:
    response = httpx.get(
        "https://serpapi.com/search",
        params={
            "api_key": api_key,
            "engine": engine,
            "q": query,
            "num": num_results,
            "location": location,
        },
        timeout=30.0,
    )
    # Parse response...
```

### Tests
- Add unit tests to `tools/tests/tools/test_web_search_tool.py`
- Mock SerpAPI responses
- Test provider fallback logic with SerpAPI in chain
- Test engine parameter variations (google, google_news, google_scholar)

## Use Cases (from #2853)

| Agent from #2853 | How SerpAPI Helps |
|------------------|-------------------|
| Meeting Prepper | Real Google SERP for prospect company → get Knowledge Graph, news, reviews |
| Lead Enrichment | `engine="google"` + company name → structured business info from Knowledge Graph |
| Research Agent | `engine="google_scholar"` → academic papers and citations |
| Local Business | `engine="google_maps"` → business listings with ratings, hours, reviews |

## Advantages Over Current Implementation

1. **Real Google Results**: Unlike Google Custom Search API which uses a synthetic index, SerpAPI returns actual Google SERP data
2. **Rich Data Extraction**: Knowledge Graph, People Also Ask, Local Pack, Shopping results - all structured as JSON
3. **Multi-Engine Support**: Google Scholar, News, Maps, Bing, DuckDuckGo, Yahoo all through one integration
4. **CAPTCHA Handling**: SerpAPI handles all anti-bot measures automatically
5. **Accurate Geolocation**: City-level location targeting with proxy routing

## Notes

- **100 Free Searches/Month**: Sufficient for development/testing
- **Response Size**: SerpAPI returns much richer data than Google CSE (~10KB vs ~2KB per query)
- **Existing Pattern**: Follow the multi-provider pattern already established in `web_search_tool.py`
- **Backward Compatible**: Adding as a third provider option doesn't break existing Brave/Google integrations

## References

- **SerpAPI Documentation**: https://serpapi.com/search-api
- **SerpAPI Playground**: https://serpapi.com/playground
- **Python Library**: `pip install google-search-results` (official, but we'll use httpx for consistency)

---

**Parent Issue:** #2805 (Integration Hub)
**Use Cases Issue:** #2853 (Business Process Use Cases)
**Related Tool:** [web_search_tool](file:///Users/siketyson/Desktop/aden/tools/src/aden_tools/tools/web_search_tool/)

## Labels
- `enhancement`
- `help wanted`
- `integrations`
- `tools`
