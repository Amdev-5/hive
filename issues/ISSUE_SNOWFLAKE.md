# [Integration]: Snowflake Data Cloud - SQL Queries, Cortex AI & MCP Server

## Overview

Add integration with Snowflake Data Cloud to enable agents to query enterprise data warehouses, execute SQL, and leverage Snowflake's Cortex AI services. Snowflake provides an **official MCP server** that exposes SQL execution, Cortex Analyst (text-to-SQL), Cortex Search (RAG), and Cortex Agents - making it a powerful data backbone for AI agents.

**Why Snowflake?**
- **#1 Enterprise Data Cloud** - Used by 10,000+ customers storing billions of rows
- **Official MCP Server** - Snowflake-managed, no infrastructure deployment needed
- **Cortex AI Suite** - Built-in text-to-SQL, semantic search, and AI agents
- **Zero data movement** - Agents query data in place with enterprise-grade security

**Use Cases from #2853:**
- **RevOps Agent**: Query sales pipelines, revenue metrics, customer cohorts directly
- **FinTech Agents**: Access financial models, transaction data, compliance reports
- **Analytics Agent**: Natural language queries to structured data ("What was Q4 revenue?")
- **Data Enrichment**: Write enriched lead/company data back to warehouse tables

## Duplicate Check

- ✅ **No Snowflake references found** in codebase
- ✅ **No data warehouse integrations exist** (gap in current tools)
- ✅ **No existing issues/PRs** for Snowflake or similar

## Requirements

### Option A: Snowflake-Managed MCP Server (Recommended)

Snowflake provides an **official managed MCP server** that can be configured directly in Snowflake and accessed by Hive agents:

```sql
-- Create MCP server in Snowflake
CREATE MCP SERVER my_agent_server
  TYPE = CORTEX_ANALYST
  SEMANTIC_MODEL = '@my_db.my_schema.semantic_model_stage/model.yaml';
```

This exposes tools to MCP clients including:

| Tool | Description | Cortex Service |
|------|-------------|----------------|
| `cortex_analyst` | Natural language → SQL → Results | Cortex Analyst |
| `cortex_search` | Semantic search over unstructured data | Cortex Search |
| `cortex_agent` | Multi-service orchestration | Cortex Agents |
| `execute_sql` | Direct SQL execution | SQL API |
| `describe_schema` | Database/table metadata | SQL API |

### Option B: Native Tool Implementation via SQL API

Implement direct MCP tools using Snowflake's REST SQL API:

1. **snowflake_query** - Execute SQL and return results
   - Parameters: `query`, `database`, `schema`, `warehouse`, `timeout`
   - Returns: JSON array of result rows

2. **snowflake_describe** - Get table/database schema
   - Parameters: `object_type` (database, schema, table), `object_name`
   - Returns: Schema metadata, columns, types

3. **snowflake_insert** - Insert/update data
   - Parameters: `table`, `data` (JSON array of rows)
   - Returns: Insert confirmation, row count

4. **snowflake_stored_procedure** - Call stored procedures
   - Parameters: `procedure_name`, `arguments`
   - Returns: Procedure output

5. **snowflake_cortex_analyst** - Text-to-SQL via Cortex
   - Parameters: `question`, `semantic_model_path`
   - Returns: Generated SQL, execution results

## Authentication

### For Snowflake-Managed MCP Server
- **Connection**: SSE endpoint from Snowflake account
- **Auth**: Snowflake OAuth or JWT tokens
- **No API key needed** - uses Snowflake's built-in auth

### For SQL API (Native Tools)
- **Credentials:**
  - `SNOWFLAKE_ACCOUNT` - Account identifier (e.g., `xy12345.us-east-1`)
  - `SNOWFLAKE_USER` - Username
  - `SNOWFLAKE_PASSWORD` or `SNOWFLAKE_PRIVATE_KEY` - Auth method
  - `SNOWFLAKE_WAREHOUSE` - Default compute warehouse
  - `SNOWFLAKE_DATABASE` - Default database
  - `SNOWFLAKE_SCHEMA` - Default schema

- **Auth Methods:**
  - OAuth 2.0 (recommended for production)
  - Key Pair authentication (JWT)
  - Username/Password (development only)

**Costing:**
| Component | Pricing |
|-----------|---------|
| Storage | $23-40/TB/month |
| Compute | $2-4/credit (1 credit ≈ 1 hour X-Small warehouse) |
| Cortex AI | Pay-per-token (varies by model) |
| SQL API | No additional cost |
| MCP Server | Included |

## Implementation Details

### Option A: MCP Server Configuration

**Step 1:** Document Snowflake MCP server setup in `core/MCP_INTEGRATION_GUIDE.md`:
```json
{
  "mcpServers": {
    "snowflake": {
      "type": "sse",
      "url": "https://<account>.snowflakecomputing.com/api/v2/mcp",
      "env": {
        "SNOWFLAKE_ACCOUNT": "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER": "SNOWFLAKE_USER",
        "SNOWFLAKE_PRIVATE_KEY": "SNOWFLAKE_PRIVATE_KEY"
      },
      "description": "Enterprise data warehouse with Cortex AI"
    }
  }
}
```

**Step 2:** Add example agent config using Snowflake MCP

### Option B: Native Tool Implementation

**Step 1:** Create `tools/src/aden_tools/tools/snowflake_tool/`

**Step 2:** Implement SQL API client:
```python
import httpx
import jwt

class SnowflakeClient:
    BASE_URL = "https://{account}.snowflakecomputing.com/api/v2"
    
    def __init__(self, account: str, user: str, private_key: str):
        self.account = account
        self.token = self._generate_jwt(user, private_key)
    
    def execute_query(self, sql: str, database: str, schema: str) -> dict:
        response = httpx.post(
            f"{self.BASE_URL.format(account=self.account)}/statements",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "statement": sql,
                "database": database,
                "schema": schema,
                "timeout": 60,
            },
        )
        return response.json()
```

**Step 3:** Register tools with FastMCP decorators

**Step 4:** Add credential specs to `tools/src/aden_tools/credentials/integrations.py`

### Tests
- Add unit tests to `tools/tests/tools/test_snowflake_tool.py`
- Mock SQL API responses
- Test query execution, schema discovery
- Test error handling (timeout, auth failure, invalid SQL)

## Use Cases (from #2853)

| Agent from #2853 | How Snowflake Helps |
|------------------|---------------------|
| RevOps Agent | `snowflake_query("SELECT SUM(revenue) FROM deals WHERE close_date >= '2025-01-01'")` |
| Meeting Prepper | Query CRM data synced to Snowflake for account history |
| FinTech Compliance | `cortex_analyst("Show me all transactions over $10K this month")` |
| Data Enrichment | `snowflake_insert("leads", enriched_lead_data)` → write back to warehouse |
| Analytics Agent | `cortex_analyst("What was our customer churn rate in Q4?")` → text-to-SQL |

## Impact Assessment

### Benefits
1. **Enterprise Data Access**: Query billions of rows of business data
2. **Official MCP Support**: Snowflake-managed server, no infrastructure
3. **Cortex AI Integration**: Text-to-SQL, semantic search, AI agents built-in
4. **Secure by Design**: Role-based access, data masking, audit logs
5. **Zero ETL**: Agents query data in place without data movement
6. **Multi-Cloud**: Works across AWS, Azure, GCP

### Considerations
- **Enterprise Focus**: Primarily used by mid-large companies
- **Cost Model**: Compute charges based on warehouse usage
- **Learning Curve**: Requires understanding of Snowflake concepts (warehouses, databases, schemas)
- **Cold Start**: Warehouses may have startup latency if suspended

## Comparison with Alternatives

| Feature | Snowflake | BigQuery | PostgreSQL |
|---------|-----------|----------|------------|
| Scale | Petabytes | Petabytes | Terabytes |
| MCP Server | ✅ Official | ❌ Community | ❌ No |
| Text-to-SQL | ✅ Cortex Analyst | ❌ Manual | ❌ Manual |
| Semantic Search | ✅ Cortex Search | ❌ No | ✅ pgvector |
| Serverless | ✅ | ✅ | ❌ |
| Cost Model | Credit-based | Query-based | Instance-based |

## Notes

- **Snowflake MCP Revision**: 2025-06-18 (latest)
- **Cortex Analyst**: Requires semantic model YAML definition
- **Python Connector**: `pip install snowflake-connector-python` (alternative to REST API)
- **Stored Procedures**: Can expose business logic as MCP tools

## References

- **SQL API Docs**: https://docs.snowflake.com/en/developer-guide/sql-api/
- **Cortex AI**: https://www.snowflake.com/en/data-cloud/cortex/
- **MCP Server Docs**: https://docs.snowflake.com/en/user-guide/snowflake-cortex/mcp (check latest)
- **Python Connector**: https://docs.snowflake.com/en/developer-guide/python-connector/
- **Authentication**: https://docs.snowflake.com/en/developer-guide/sql-api/authenticating

---

**Parent Issue:** #2805 (Integration Hub)
**Use Cases Issue:** #2853 (Business Process Use Cases)

## Labels
- `enhancement`
- `help wanted`
- `integrations`
- `tools`
- `enterprise`

## Recommendation

**Start with Option A (MCP Server Configuration)** - Document how to connect Hive agents to Snowflake's managed MCP server. This enables immediate access to Cortex AI services with enterprise security. Option B (native tools) can be added later for users who need direct SQL API access without Cortex.

## Future Extensions

- **BigQuery Tool**: Add Google BigQuery as alternative provider
- **PostgreSQL Tool**: Add direct PostgreSQL/Supabase support for smaller deployments
- **Multi-Warehouse Pattern**: Like `web_search_tool`, support multiple providers with auto-detection
