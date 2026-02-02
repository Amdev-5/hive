# Code Review: Greenhouse Integration (PR for Issue #3062)

**Commit:** `312917b8b9c15d9810d189956dd6c529e4d722ee`
**Fork:** `Samir-atra/hive_fork`
**Issue:** https://github.com/adenhq/hive/issues/3062

Based on `BUILDING_TOOLS.md` guidelines and existing codebase patterns.

---

## 🔴 CRITICAL - Must Fix Before Merge

### 1. Incomplete CredentialSpec
**File:** `tools/src/aden_tools/credentials/greenhouse.py`
**Lines:** 1-11

The credential spec is missing required fields per `BUILDING_TOOLS.md` and the HubSpot pattern in `integrations.py:10-52`.

| Missing Field | Required Value |
|---------------|----------------|
| `tools` | List of all 6 tool names |
| `help_url` | Greenhouse API docs URL |
| `api_key_instructions` | Step-by-step guide |
| `health_check_endpoint` | API endpoint for validation |
| `credential_id` | `"greenhouse"` |
| `credential_key` | `"api_key"` |

---

### 2. Wrong Type Hint - Deprecated Class
**File:** `tools/src/aden_tools/tools/greenhouse_tool/__init__.py`
**Lines:** 9-11

```python
# ❌ Current (deprecated):
from aden_tools.credentials import CredentialManager

# ✅ Should be:
from aden_tools.credentials import CredentialStoreAdapter
```

The codebase uses `CredentialStoreAdapter`, not `CredentialManager`. See `web_search_tool.py:19-26`.

---

### 3. Typo in Error Message
**File:** `tools/src/aden_tools/tools/greenhouse_tool/greenhouse.py`
**Line:** 82

```python
# ❌ Current:
"Authenticaton failed: Invalid Greenhouse API key"
#  ^^^^^^^^^^^^ typo

# ✅ Should be:
"Authentication failed: Invalid Greenhouse API key"
```

---

## 🟡 MEDIUM - Should Fix

### 4. Raising Exceptions Instead of Returning Error Dicts
**File:** `tools/src/aden_tools/tools/greenhouse_tool/greenhouse.py`
**Lines:** 80-85

Per `BUILDING_TOOLS.md` > "Error Handling":
> *"Return error dicts instead of raising exceptions"*

```python
# ❌ Current (raises):
if response.status_code == 401:
    raise ValueError("Authentication failed...")
elif response.status_code == 403:
    raise PermissionError("Access denied...")

# ✅ Should be (returns dict):
if response.status_code == 401:
    return {"error": "Authentication failed: Invalid Greenhouse API key"}
elif response.status_code == 403:
    return {"error": "Access denied: Check API permissions or use HTTPS"}
```

---

### 5. Missing `os.getenv` Fallback
**File:** `tools/src/aden_tools/tools/greenhouse_tool/__init__.py`
**Lines:** 17-22

Per `BUILDING_TOOLS.md` > "Credential Management":
> *"Use CredentialManager if provided, fallback to direct env access"*

```python
# ❌ Current:
api_key = credentials.get("greenhouse_api_key") if credentials else None

# ✅ Should be:
if credentials is not None:
    api_key = credentials.get("greenhouse_api_key")
else:
    api_key = os.getenv("GREENHOUSE_API_KEY")
```

Also missing `import os` at top of file.

---

### 6. Tool Docstrings Missing "Returns" Section
**File:** `tools/src/aden_tools/tools/greenhouse_tool/__init__.py`
**Lines:** 28-44, 47-54, 57-76, 79-87, 90-119, 122-138

Per `BUILDING_TOOLS.md` > "Documentation":
> *"Include: What the tool does, When to use it, Args with types and constraints, What it returns"*

All 6 tool functions need a `Returns:` section. Example:

```python
# ❌ Current (greenhouse_list_jobs):
"""
List job postings with filters.

Args:
    limit: Maximum number of jobs to return (default: 50)
    ...
"""

# ✅ Should add:
"""
List job postings with filters.

Args:
    limit: Maximum number of jobs to return (default: 50)
    ...

Returns:
    List of job dicts containing id, title, status, departments, offices
"""
```

---

### 7. Indentation Error
**File:** `tools/src/aden_tools/tools/greenhouse_tool/greenhouse.py`
**Line:** 227

```python
# ❌ Current (13 spaces):
        if notes:
             data["notes"] = [{"body": notes, "visibility": "admin_only"}]

# ✅ Should be (12 spaces):
        if notes:
            data["notes"] = [{"body": notes, "visibility": "admin_only"}]
```

---

## 🟢 MINOR - Suggestions

### 8. Credential File Location
**File:** `tools/src/aden_tools/credentials/greenhouse.py`

Consider moving Greenhouse credentials into `integrations.py` alongside HubSpot rather than creating a separate file. This follows the existing pattern of grouping integration credentials.

---

### 9. Missing Tool Registration Tests
**File:** `tools/tests/tools/test_greenhouse_tool.py`

Per `BUILDING_TOOLS.md` > "Testing", add tests for MCP tool registration:

```python
def test_tool_registration(mcp):
    """Test that all greenhouse tools are registered."""
    register_tools(mcp)
    tools = mcp._tool_manager._tools

    expected_tools = [
        "greenhouse_list_jobs",
        "greenhouse_get_job",
        "greenhouse_list_candidates",
        "greenhouse_get_candidate",
        "greenhouse_add_candidate",
        "greenhouse_list_applications",
    ]
    for tool_name in expected_tools:
        assert tool_name in tools
```

---

### 10. Missing README.md
**File:** `tools/src/aden_tools/tools/greenhouse_tool/README.md` (missing)

Per `BUILDING_TOOLS.md` > "Tool Structure":
> *"Every tool folder needs a README.md"*

Should include:
- Description and use cases
- Usage examples
- Argument table for each tool
- Environment variables
- Error handling notes

---

## 📋 Registration Checklist

These files need updates to complete the integration:

| File | Action | Line |
|------|--------|------|
| `tools/__init__.py` | Add import | ~44 |
| `tools/__init__.py` | Add `register_greenhouse(mcp, credentials=credentials)` | ~72 |
| `tools/__init__.py` | Add 6 tool names to return list | ~105+ |
| `credentials/__init__.py` | Add import | ~49 |
| `credentials/__init__.py` | Add `**GREENHOUSE_CREDENTIALS` to CREDENTIAL_SPECS | ~62 |
| `credentials/__init__.py` | Add to `__all__` | ~94 |

---

## ✅ What's Good

- Clean client/tool separation (`greenhouse.py` vs `__init__.py`)
- Pagination handling implemented correctly
- Basic Auth format is correct (API key as username, empty password)
- Test coverage for client methods is comprehensive
- Error handling for timeouts and network errors
- Correct use of `httpx` with proper timeout

---

## Summary

| Severity | Count | Action Required |
|----------|-------|-----------------|
| 🔴 Critical | 3 | Must fix before merge |
| 🟡 Medium | 4 | Should fix |
| 🟢 Minor | 3 | Nice to have |

**Recommendation:** Address all critical and medium issues before merging. The implementation is solid but needs alignment with codebase conventions.
