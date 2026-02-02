## Description

Add Apollo.io MCP tool integration for B2B contact and company data enrichment. Addresses #3061.

Implements 4 MCP tools:
- `apollo_enrich_person`: Enrich contact by email or LinkedIn URL
- `apollo_enrich_company`: Enrich company by domain
- `apollo_search_people`: Search contacts with filters
- `apollo_search_companies`: Search companies with filters

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [x] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Related Issues

Closes #3061

## Changes Made

- Added `tools/src/aden_tools/tools/apollo_tool/` with `_ApolloClient` class and 4 MCP tools
- Added Apollo credential spec to `tools/src/aden_tools/credentials/integrations.py`
- Registered Apollo tools in `tools/src/aden_tools/tools/__init__.py`
- Added comprehensive test suite (34 tests) in `tools/src/aden_tools/tools/apollo_tool/tests/`

## Testing

- [x] Unit tests pass (34/34 tests passing)
- [x] Lint passes (`ruff check` - all checks passed)
- [x] Manual testing performed (live API test with real credentials - company enrichment verified)

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] My changes generate no new warnings
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] New and existing unit tests pass locally with my changes
