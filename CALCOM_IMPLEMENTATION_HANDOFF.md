# Cal.com Integration Implementation - Handoff Document

## Current Status: IN PROGRESS

**Branch:** `feat/calcom-integration`
**Issue:** https://github.com/adenhq/hive/issues/3188
**API Key (for testing):** `cal_live_920fcab1b90b4a026b8b6c54e5804db7`

---

## What's Been Done

### 1. Branch Created
```bash
git checkout -b feat/calcom-integration
```
Branch is based on latest `origin/main`.

### 2. Tool Directory Created
```
tools/src/aden_tools/tools/calcom_tool/
├── __init__.py       ✅ Created
├── calcom_tool.py    ✅ Created (full implementation)
└── README.md         ❌ Not yet created
```

### 3. Files Created

#### `__init__.py`
```python
from .calcom_tool import register_tools
__all__ = ["register_tools"]
```

#### `calcom_tool.py`
Full implementation with:
- `_CalcomClient` class with all API methods
- 8 MCP tools registered:
  - `calcom_list_bookings`
  - `calcom_get_booking`
  - `calcom_create_booking`
  - `calcom_cancel_booking`
  - `calcom_get_availability`
  - `calcom_update_schedule`
  - `calcom_list_event_types`
  - `calcom_get_event_type`

---

## What Still Needs to Be Done

### 1. Add Credential Spec to `integrations.py`

**File:** `tools/src/aden_tools/credentials/integrations.py`

Add after the `hubspot` credential:

```python
"calcom": CredentialSpec(
    env_var="CALCOM_API_KEY",
    tools=[
        "calcom_list_bookings",
        "calcom_get_booking",
        "calcom_create_booking",
        "calcom_cancel_booking",
        "calcom_get_availability",
        "calcom_update_schedule",
        "calcom_list_event_types",
        "calcom_get_event_type",
    ],
    required=True,
    startup_required=False,
    help_url="https://cal.com/docs/api-reference/v1",
    description="Cal.com API key for scheduling and booking management",
    aden_supported=False,
    direct_api_key_supported=True,
    api_key_instructions="""To get a Cal.com API key:
1. Log in to Cal.com
2. Go to Settings → Developer → API Keys
3. Click "Create new API key"
4. Give it a name and set expiration
5. Copy the key (shown only once)""",
    health_check_endpoint="https://api.cal.com/v1/me",
    health_check_method="GET",
    credential_id="calcom",
    credential_key="api_key",
),
```

### 2. Register Tools in `tools/__init__.py`

**File:** `tools/src/aden_tools/tools/__init__.py`

Add import (around line 44):
```python
from .calcom_tool import register_tools as register_calcom
```

Add registration in `register_all_tools()` (around line 72, after hubspot):
```python
register_calcom(mcp, credentials=credentials)
```

Add tool names to return list (at the end of the list):
```python
"calcom_list_bookings",
"calcom_get_booking",
"calcom_create_booking",
"calcom_cancel_booking",
"calcom_get_availability",
"calcom_update_schedule",
"calcom_list_event_types",
"calcom_get_event_type",
```

### 3. Create README.md

**File:** `tools/src/aden_tools/tools/calcom_tool/README.md`

Create documentation with:
- Tool descriptions
- Usage examples
- Environment variables
- API reference links

### 4. Create Test File

**File:** `tools/tests/tools/test_calcom_tool.py`

Create tests following the pattern in `test_hubspot_tool.py` or `test_web_search_tool.py`:
- Test tool registration
- Test client methods with mocked responses
- Test error handling
- Test input validation

### 5. Run Tests and Linting

```bash
cd tools

# Run ruff linting
uv run ruff check src/aden_tools/tools/calcom_tool/
uv run ruff format src/aden_tools/tools/calcom_tool/

# Run tests
uv run pytest tests/tools/test_calcom_tool.py -v

# Run all tests to ensure no regressions
uv run pytest -v
```

### 6. Manual Testing with Real API Key

```bash
export CALCOM_API_KEY="cal_live_920fcab1b90b4a026b8b6c54e5804db7"

# Test the tools
uv run python -c "
from aden_tools.tools.calcom_tool import register_tools
from fastmcp import FastMCP

mcp = FastMCP('test')
register_tools(mcp)

# Test list event types
fn = mcp._tool_manager._tools['calcom_list_event_types'].fn
print(fn())
"
```

### 7. Commit and Push

```bash
git add .
git commit -m "$(cat <<'EOF'
feat(tools): Add Cal.com integration for scheduling automation

This integration adds 8 new MCP tools for accessing the Cal.com API,
enabling agents to manage bookings, availability, and event types.

Features:
- Implemented _CalcomClient with Bearer token auth
- Added credential management for CALCOM_API_KEY
- Registered 8 MCP tools: list_bookings, get_booking, create_booking,
  cancel_booking, get_availability, update_schedule, list_event_types,
  get_event_type
- Added comprehensive unit tests

Fixes #3188

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"

git push -u origin feat/calcom-integration
```

### 8. Create PR

```bash
gh pr create --title "feat(tools): Add Cal.com integration for scheduling automation" --body "$(cat <<'EOF'
## Summary
- Adds Cal.com API integration with 8 MCP tools
- Enables agents to manage scheduling, bookings, and availability
- Follows established tool patterns (HubSpot, web_search)

## Tools Added
| Tool | Description |
|------|-------------|
| `calcom_list_bookings` | List bookings with filters |
| `calcom_get_booking` | Get booking details |
| `calcom_create_booking` | Create new booking |
| `calcom_cancel_booking` | Cancel booking |
| `calcom_get_availability` | Get available slots |
| `calcom_update_schedule` | Update schedule |
| `calcom_list_event_types` | List event types |
| `calcom_get_event_type` | Get event type details |

## Test plan
- [ ] Unit tests pass
- [ ] Ruff linting passes
- [ ] Manual testing with real API key
- [ ] No regressions in existing tools

Fixes #3188

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Key Files Reference

| File | Status | Purpose |
|------|--------|---------|
| `tools/src/aden_tools/tools/calcom_tool/__init__.py` | ✅ Done | Package exports |
| `tools/src/aden_tools/tools/calcom_tool/calcom_tool.py` | ✅ Done | Main implementation |
| `tools/src/aden_tools/tools/calcom_tool/README.md` | ❌ TODO | Documentation |
| `tools/src/aden_tools/credentials/integrations.py` | ❌ TODO | Add credential spec |
| `tools/src/aden_tools/tools/__init__.py` | ❌ TODO | Register tools |
| `tools/tests/tools/test_calcom_tool.py` | ❌ TODO | Unit tests |

---

## API Reference

**Base URL:** `https://api.cal.com/v1`

**Authentication:** Bearer token in Authorization header

**Key Endpoints:**
- `GET /bookings` - List bookings
- `GET /bookings/{id}` - Get booking
- `POST /bookings` - Create booking
- `DELETE /bookings/{id}` - Cancel booking
- `GET /slots` - Get available slots
- `GET /schedules` - List schedules
- `PATCH /schedules/{id}` - Update schedule
- `GET /event-types` - List event types
- `GET /event-types/{id}` - Get event type

---

## Patterns to Follow

Look at these files for reference:
- `tools/src/aden_tools/tools/hubspot_tool/hubspot_tool.py` - Similar tool structure
- `tools/src/aden_tools/credentials/integrations.py` - Credential spec pattern
- `tools/tests/tools/test_web_search_tool.py` - Test patterns

---

## Environment Setup

```bash
cd /Users/siketyson/Desktop/aden/tools
export CALCOM_API_KEY="cal_live_920fcab1b90b4a026b8b6c54e5804db7"
```

---

## Quick Resume Commands

```bash
# Switch to the branch
cd /Users/siketyson/Desktop/aden
git checkout feat/calcom-integration

# Check status
git status

# See what's been done
ls -la tools/src/aden_tools/tools/calcom_tool/
```
