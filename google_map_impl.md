# Google Maps Platform Integration - Implementation Plan

## Overview

This document outlines the implementation plan for integrating Google Maps Platform Web Services APIs into the Hive agent framework.

**Issue:** #2805 (Parent), See `issues/ISSUE_GOOGLE_MAPS.md` for full requirements
**Estimated Effort:** 2-3 days
**Priority:** HIGH (widely useful, $200 free credit)

---

## Phase 1: Setup & Credential Management

### 1.1 Add Credential Spec

**File:** `tools/src/aden_tools/credentials/integrations.py`

Add after the `hubspot` credential spec:

```python
"google_maps": CredentialSpec(
    env_var="GOOGLE_MAPS_API_KEY",
    tools=[
        "maps_geocode",
        "maps_reverse_geocode",
        "maps_directions",
        "maps_distance_matrix",
        "maps_place_details",
        "maps_place_search",
    ],
    required=True,
    startup_required=False,
    help_url="https://developers.google.com/maps/documentation/geocoding/get-api-key",
    description="Google Maps Platform API key for geocoding, routing, and places",
    aden_supported=False,
    direct_api_key_supported=True,
    api_key_instructions="""To get a Google Maps API key:
1. Go to Google Cloud Console (https://console.cloud.google.com)
2. Create or select a project
3. Navigate to APIs & Services > Library
4. Enable these APIs:
   - Geocoding API
   - Directions API
   - Distance Matrix API
   - Places API
5. Go to APIs & Services > Credentials
6. Click "Create Credentials" > "API Key"
7. Copy the API key
8. (Recommended) Click "Edit API key" to add restrictions""",
    health_check_endpoint="https://maps.googleapis.com/maps/api/geocode/json?address=test&key={api_key}",
    health_check_method="GET",
    credential_id="google_maps",
    credential_key="api_key",
),
```

---

## Phase 2: Client Implementation

### 2.1 Create Directory Structure

```bash
mkdir -p tools/src/aden_tools/tools/google_maps_tool
touch tools/src/aden_tools/tools/google_maps_tool/__init__.py
touch tools/src/aden_tools/tools/google_maps_tool/google_maps_tool.py
touch tools/src/aden_tools/tools/google_maps_tool/README.md
```

### 2.2 Implement `__init__.py`

**File:** `tools/src/aden_tools/tools/google_maps_tool/__init__.py`

```python
"""
Google Maps Platform Tool - Geocoding, routing, and location services.

Supports Geocoding, Directions, Distance Matrix, and Places APIs.
"""

from .google_maps_tool import register_tools

__all__ = ["register_tools"]
```

### 2.3 Implement `_GoogleMapsClient` Class

**File:** `tools/src/aden_tools/tools/google_maps_tool/google_maps_tool.py`

```python
"""
Google Maps Platform Tool - Geocoding, routing, and location services.

Supports:
- Geocoding API (address ↔ coordinates)
- Directions API (routing between points)
- Distance Matrix API (multi-origin/destination distances)
- Places API (search and details)

API Reference: https://developers.google.com/maps/documentation
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import httpx
from fastmcp import FastMCP

if TYPE_CHECKING:
    from aden_tools.credentials import CredentialStoreAdapter

# API Base URLs
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
PLACES_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

DEFAULT_TIMEOUT = 30.0


class _GoogleMapsClient:
    """Internal client wrapping Google Maps Platform API calls."""

    def __init__(self, api_key: str):
        self._api_key = api_key

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle Google Maps API response status codes."""
        if response.status_code != 200:
            return {"error": f"HTTP error: {response.status_code}"}

        data = response.json()
        status = data.get("status", "UNKNOWN_ERROR")

        if status == "OK":
            return data
        elif status == "ZERO_RESULTS":
            return {"results": [], "status": "ZERO_RESULTS", "message": "No results found"}
        elif status == "OVER_QUERY_LIMIT":
            return {"error": "API quota exceeded. Check billing or wait and retry."}
        elif status == "REQUEST_DENIED":
            error_msg = data.get("error_message", "API key invalid or API not enabled")
            return {"error": f"Request denied: {error_msg}"}
        elif status == "INVALID_REQUEST":
            error_msg = data.get("error_message", "Missing required parameter")
            return {"error": f"Invalid request: {error_msg}"}
        else:
            return {"error": f"Google Maps API error: {status}"}

    def geocode(
        self,
        address: str,
        components: dict[str, str] | None = None,
        bounds: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Convert address to coordinates."""
        params: dict[str, Any] = {
            "address": address,
            "key": self._api_key,
        }
        if components:
            params["components"] = "|".join(f"{k}:{v}" for k, v in components.items())
        if bounds:
            params["bounds"] = bounds
        if language:
            params["language"] = language

        response = httpx.get(GEOCODING_URL, params=params, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def reverse_geocode(
        self,
        lat: float,
        lng: float,
        result_type: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Convert coordinates to address."""
        params: dict[str, Any] = {
            "latlng": f"{lat},{lng}",
            "key": self._api_key,
        }
        if result_type:
            params["result_type"] = result_type
        if language:
            params["language"] = language

        response = httpx.get(GEOCODING_URL, params=params, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        waypoints: list[str] | None = None,
        alternatives: bool = False,
        avoid: str | None = None,
        departure_time: str | None = None,
        units: str = "metric",
    ) -> dict[str, Any]:
        """Get directions between two points."""
        params: dict[str, Any] = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "alternatives": str(alternatives).lower(),
            "units": units,
            "key": self._api_key,
        }
        if waypoints:
            params["waypoints"] = "|".join(waypoints)
        if avoid:
            params["avoid"] = avoid
        if departure_time:
            params["departure_time"] = departure_time

        response = httpx.get(DIRECTIONS_URL, params=params, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def distance_matrix(
        self,
        origins: list[str],
        destinations: list[str],
        mode: str = "driving",
        avoid: str | None = None,
        units: str = "metric",
        departure_time: str | None = None,
    ) -> dict[str, Any]:
        """Calculate distances between multiple origins and destinations."""
        params: dict[str, Any] = {
            "origins": "|".join(origins),
            "destinations": "|".join(destinations),
            "mode": mode,
            "units": units,
            "key": self._api_key,
        }
        if avoid:
            params["avoid"] = avoid
        if departure_time:
            params["departure_time"] = departure_time

        response = httpx.get(DISTANCE_MATRIX_URL, params=params, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def place_search(
        self,
        query: str | None = None,
        location: str | None = None,
        radius: int | None = None,
        type: str | None = None,
        open_now: bool | None = None,
    ) -> dict[str, Any]:
        """Search for places."""
        if query:
            url = PLACES_SEARCH_URL
            params: dict[str, Any] = {"query": query, "key": self._api_key}
        elif location and radius:
            url = PLACES_NEARBY_URL
            params = {"location": location, "radius": radius, "key": self._api_key}
        else:
            return {"error": "Either 'query' or 'location' + 'radius' required"}

        if type:
            params["type"] = type
        if open_now is not None:
            params["opennow"] = str(open_now).lower()

        response = httpx.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def place_details(
        self,
        place_id: str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get detailed place information."""
        params: dict[str, Any] = {
            "place_id": place_id,
            "key": self._api_key,
        }
        if fields:
            params["fields"] = ",".join(fields)

        response = httpx.get(PLACES_DETAILS_URL, params=params, timeout=DEFAULT_TIMEOUT)
        data = self._handle_response(response)

        # Places Details returns 'result' not 'results'
        if "result" in data:
            return {"result": data["result"], "status": "OK"}
        return data
```

### 2.4 Implement Tool Registration

**Continue in same file:**

```python
def register_tools(
    mcp: FastMCP,
    credentials: CredentialStoreAdapter | None = None,
) -> None:
    """Register Google Maps Platform tools with the MCP server."""

    def _get_api_key() -> str | None:
        """Get Google Maps API key from credential manager or environment."""
        if credentials is not None:
            return credentials.get("google_maps")
        return os.getenv("GOOGLE_MAPS_API_KEY")

    def _get_client() -> _GoogleMapsClient | dict[str, str]:
        """Get a Google Maps client, or return an error dict if no credentials."""
        api_key = _get_api_key()
        if not api_key:
            return {
                "error": "Google Maps API key not configured",
                "help": "Set GOOGLE_MAPS_API_KEY environment variable or configure via credential store",
            }
        return _GoogleMapsClient(api_key)

    # --- Geocoding Tools ---

    @mcp.tool()
    def maps_geocode(
        address: str,
        country: str | None = None,
        language: str = "en",
    ) -> dict:
        """
        Convert an address to geographic coordinates (latitude/longitude).

        Use this when you need to:
        - Get coordinates for an address
        - Validate and standardize addresses
        - Prepare addresses for mapping or distance calculations

        Args:
            address: The address to geocode (e.g., "1600 Amphitheatre Parkway, Mountain View, CA")
            country: Optional country code to bias results (e.g., "US", "GB")
            language: Language for results (default: "en")

        Returns:
            Dict with coordinates, formatted address, place_id, and address components
        """
        if not address or len(address.strip()) == 0:
            return {"error": "Address is required"}

        client = _get_client()
        if isinstance(client, dict):
            return client

        try:
            components = {"country": country} if country else None
            return client.geocode(address, components=components, language=language)
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def maps_reverse_geocode(
        lat: float,
        lng: float,
        result_type: str | None = None,
        language: str = "en",
    ) -> dict:
        """
        Convert geographic coordinates to a human-readable address.

        Use this when you need to:
        - Get an address from GPS coordinates
        - Identify location names from lat/lng
        - Validate coordinates are in expected areas

        Args:
            lat: Latitude (-90 to 90)
            lng: Longitude (-180 to 180)
            result_type: Filter results (e.g., "street_address", "locality", "country")
            language: Language for results (default: "en")

        Returns:
            Dict with formatted addresses and address components
        """
        if not (-90 <= lat <= 90):
            return {"error": "Latitude must be between -90 and 90"}
        if not (-180 <= lng <= 180):
            return {"error": "Longitude must be between -180 and 180"}

        client = _get_client()
        if isinstance(client, dict):
            return client

        try:
            return client.reverse_geocode(lat, lng, result_type=result_type, language=language)
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def maps_directions(
        origin: str,
        destination: str,
        mode: str = "driving",
        waypoints: list[str] | None = None,
        alternatives: bool = False,
        avoid: str | None = None,
        units: str = "metric",
    ) -> dict:
        """
        Get directions and route between two locations.

        Use this when you need to:
        - Calculate a route between two points
        - Get turn-by-turn directions
        - Estimate travel time and distance
        - Plan multi-stop routes with waypoints

        Args:
            origin: Starting point (address or "lat,lng")
            destination: Ending point (address or "lat,lng")
            mode: Travel mode - "driving", "walking", "bicycling", or "transit"
            waypoints: Optional intermediate stops (list of addresses)
            alternatives: Return alternative routes (default: False)
            avoid: Features to avoid - "tolls", "highways", "ferries" (comma-separated)
            units: Distance units - "metric" (km) or "imperial" (miles)

        Returns:
            Dict with routes containing steps, distance, duration, and polyline
        """
        if not origin or not destination:
            return {"error": "Origin and destination are required"}

        valid_modes = ["driving", "walking", "bicycling", "transit"]
        if mode not in valid_modes:
            return {"error": f"Invalid mode. Must be one of: {valid_modes}"}

        client = _get_client()
        if isinstance(client, dict):
            return client

        try:
            return client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                waypoints=waypoints,
                alternatives=alternatives,
                avoid=avoid,
                units=units,
            )
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def maps_distance_matrix(
        origins: list[str],
        destinations: list[str],
        mode: str = "driving",
        avoid: str | None = None,
        units: str = "metric",
    ) -> dict:
        """
        Calculate travel distance and time for multiple origin-destination pairs.

        Use this when you need to:
        - Compare distances from multiple starting points
        - Find the nearest location from a set
        - Build a distance/time matrix for route optimization
        - Calculate ETAs for multiple deliveries

        Args:
            origins: List of starting points (addresses or "lat,lng")
            destinations: List of ending points (addresses or "lat,lng")
            mode: Travel mode - "driving", "walking", "bicycling", or "transit"
            avoid: Features to avoid - "tolls", "highways", "ferries" (comma-separated)
            units: Distance units - "metric" (km) or "imperial" (miles)

        Returns:
            Dict with matrix of distances and durations for all origin-destination pairs
        """
        if not origins or not destinations:
            return {"error": "Origins and destinations are required"}

        # Google limits: 25 origins OR 25 destinations, max 100 elements
        if len(origins) > 25:
            return {"error": "Maximum 25 origins allowed"}
        if len(destinations) > 25:
            return {"error": "Maximum 25 destinations allowed"}
        if len(origins) * len(destinations) > 100:
            return {"error": "Maximum 100 elements (origins × destinations) allowed"}

        client = _get_client()
        if isinstance(client, dict):
            return client

        try:
            return client.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode=mode,
                avoid=avoid,
                units=units,
            )
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def maps_place_search(
        query: str | None = None,
        location: str | None = None,
        radius: int = 5000,
        place_type: str | None = None,
        open_now: bool | None = None,
    ) -> dict:
        """
        Search for places by text query or nearby location.

        Use this when you need to:
        - Find businesses or points of interest
        - Search for places near a location
        - Find specific types of places (restaurants, gas stations, etc.)

        Args:
            query: Text search query (e.g., "coffee shops in Seattle")
            location: Center point for nearby search ("lat,lng")
            radius: Search radius in meters (max 50000, default 5000)
            place_type: Filter by type (e.g., "restaurant", "gas_station", "hospital")
            open_now: Only return places open now (True/False)

        Returns:
            Dict with list of places including name, address, rating, and place_id
        """
        if not query and not location:
            return {"error": "Either 'query' or 'location' is required"}

        client = _get_client()
        if isinstance(client, dict):
            return client

        try:
            return client.place_search(
                query=query,
                location=location,
                radius=radius,
                type=place_type,
                open_now=open_now,
            )
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

    @mcp.tool()
    def maps_place_details(
        place_id: str,
        fields: list[str] | None = None,
    ) -> dict:
        """
        Get detailed information about a specific place.

        Use this when you need to:
        - Get full details for a place from search results
        - Get opening hours, phone number, website
        - Get reviews and ratings
        - Get photos for a location

        Args:
            place_id: Google Place ID (from geocode or search results)
            fields: Specific fields to return (reduces cost). Options include:
                    "name", "formatted_address", "geometry", "opening_hours",
                    "formatted_phone_number", "website", "rating", "reviews", "photos"

        Returns:
            Dict with detailed place information
        """
        if not place_id:
            return {"error": "place_id is required"}

        client = _get_client()
        if isinstance(client, dict):
            return client

        try:
            return client.place_details(place_id=place_id, fields=fields)
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}
```

---

## Phase 3: Registration

### 3.1 Update `tools/__init__.py`

**File:** `tools/src/aden_tools/tools/__init__.py`

Add import (around line 44):
```python
from .google_maps_tool import register_tools as register_google_maps
```

Add registration in `register_all_tools()` (around line 72):
```python
register_google_maps(mcp, credentials=credentials)
```

Add tool names to return list (around line 105):
```python
"maps_geocode",
"maps_reverse_geocode",
"maps_directions",
"maps_distance_matrix",
"maps_place_search",
"maps_place_details",
```

---

## Phase 4: Documentation

### 4.1 Create README

**File:** `tools/src/aden_tools/tools/google_maps_tool/README.md`

```markdown
# Google Maps Platform Tool

Provides geocoding, routing, distance calculation, and place search via Google Maps Platform APIs.

## Tools

| Tool | Description |
|------|-------------|
| `maps_geocode` | Convert address to coordinates |
| `maps_reverse_geocode` | Convert coordinates to address |
| `maps_directions` | Get route between two points |
| `maps_distance_matrix` | Calculate distances for multiple origins/destinations |
| `maps_place_search` | Search for places by query or location |
| `maps_place_details` | Get detailed place information |

## Environment Variables

- `GOOGLE_MAPS_API_KEY` - Your Google Maps Platform API key

## Required APIs

Enable these in Google Cloud Console:
- Geocoding API
- Directions API
- Distance Matrix API
- Places API

## Usage Examples

### Geocode an address
```python
result = maps_geocode(address="1600 Amphitheatre Parkway, Mountain View, CA")
# Returns: {lat: 37.422, lng: -122.084, formatted_address: "...", place_id: "..."}
```

### Get directions
```python
result = maps_directions(
    origin="San Francisco, CA",
    destination="Los Angeles, CA",
    mode="driving",
    avoid="tolls"
)
# Returns: {routes: [{distance: "382 mi", duration: "5 hours 45 mins", steps: [...]}]}
```

### Distance matrix
```python
result = maps_distance_matrix(
    origins=["Seattle, WA", "Portland, OR"],
    destinations=["San Francisco, CA", "Los Angeles, CA"]
)
# Returns: 2x2 matrix of distances and durations
```

## Pricing

Google provides $200/month free credit. After that:
- Geocoding: $5 per 1,000 requests
- Directions: $5 per 1,000 requests
- Distance Matrix: $5 per 1,000 elements
- Places: $17-32 per 1,000 requests

## Error Handling

All tools return error dicts on failure:
```python
{"error": "Request denied: API key invalid or API not enabled"}
{"error": "API quota exceeded. Check billing or wait and retry."}
```
```

---

## Phase 5: Testing

### 5.1 Create Test File

**File:** `tools/tests/tools/test_google_maps_tool.py`

```python
"""Tests for Google Maps Platform tool."""

import pytest
from unittest.mock import MagicMock, patch

from fastmcp import FastMCP
from aden_tools.tools.google_maps_tool.google_maps_tool import (
    register_tools,
    _GoogleMapsClient,
)


@pytest.fixture
def mcp():
    """Create a FastMCP instance."""
    return FastMCP("test")


@pytest.fixture
def client():
    """Create a client with dummy key."""
    return _GoogleMapsClient(api_key="test_key")


class TestGoogleMapsClient:
    """Test suite for _GoogleMapsClient."""

    @patch("aden_tools.tools.google_maps_tool.google_maps_tool.httpx.get")
    def test_geocode_success(self, mock_get, client):
        """Test successful geocoding."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "results": [{"formatted_address": "Test Address", "geometry": {"location": {"lat": 1.0, "lng": 2.0}}}]
        }
        mock_get.return_value = mock_response

        result = client.geocode("123 Main St")

        assert result["status"] == "OK"
        assert len(result["results"]) == 1
        mock_get.assert_called_once()
        assert "key=test_key" in str(mock_get.call_args)

    @patch("aden_tools.tools.google_maps_tool.google_maps_tool.httpx.get")
    def test_geocode_zero_results(self, mock_get, client):
        """Test geocoding with no results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ZERO_RESULTS"}
        mock_get.return_value = mock_response

        result = client.geocode("nonexistent address xyz123")

        assert result["status"] == "ZERO_RESULTS"
        assert result["results"] == []

    @patch("aden_tools.tools.google_maps_tool.google_maps_tool.httpx.get")
    def test_request_denied(self, mock_get, client):
        """Test handling of denied requests."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "REQUEST_DENIED",
            "error_message": "API key invalid"
        }
        mock_get.return_value = mock_response

        result = client.geocode("123 Main St")

        assert "error" in result
        assert "Request denied" in result["error"]

    @patch("aden_tools.tools.google_maps_tool.google_maps_tool.httpx.get")
    def test_directions_with_waypoints(self, mock_get, client):
        """Test directions with waypoints."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "routes": [{"legs": [{"distance": {"text": "100 mi"}}]}]
        }
        mock_get.return_value = mock_response

        result = client.directions(
            origin="A",
            destination="D",
            waypoints=["B", "C"]
        )

        assert result["status"] == "OK"
        call_args = mock_get.call_args
        assert "waypoints" in str(call_args)

    @patch("aden_tools.tools.google_maps_tool.google_maps_tool.httpx.get")
    def test_distance_matrix(self, mock_get, client):
        """Test distance matrix calculation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "OK",
            "rows": [{"elements": [{"distance": {"value": 1000}, "duration": {"value": 600}}]}]
        }
        mock_get.return_value = mock_response

        result = client.distance_matrix(
            origins=["Origin1"],
            destinations=["Dest1"]
        )

        assert result["status"] == "OK"
        assert "rows" in result


class TestToolRegistration:
    """Test MCP tool registration."""

    def test_all_tools_registered(self, mcp):
        """Test that all Google Maps tools are registered."""
        register_tools(mcp)
        tools = mcp._tool_manager._tools

        expected_tools = [
            "maps_geocode",
            "maps_reverse_geocode",
            "maps_directions",
            "maps_distance_matrix",
            "maps_place_search",
            "maps_place_details",
        ]
        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool {tool_name} not registered"


class TestToolValidation:
    """Test input validation."""

    def test_geocode_empty_address(self, mcp):
        """Test geocode with empty address."""
        register_tools(mcp)
        tool_fn = mcp._tool_manager._tools["maps_geocode"].fn

        result = tool_fn(address="")
        assert "error" in result

    def test_reverse_geocode_invalid_lat(self, mcp):
        """Test reverse geocode with invalid latitude."""
        register_tools(mcp)
        tool_fn = mcp._tool_manager._tools["maps_reverse_geocode"].fn

        result = tool_fn(lat=100, lng=0)  # lat > 90
        assert "error" in result
        assert "Latitude" in result["error"]

    def test_directions_invalid_mode(self, mcp):
        """Test directions with invalid travel mode."""
        register_tools(mcp)
        tool_fn = mcp._tool_manager._tools["maps_directions"].fn

        result = tool_fn(origin="A", destination="B", mode="flying")
        assert "error" in result
        assert "Invalid mode" in result["error"]

    def test_distance_matrix_too_many_origins(self, mcp):
        """Test distance matrix with too many origins."""
        register_tools(mcp)
        tool_fn = mcp._tool_manager._tools["maps_distance_matrix"].fn

        result = tool_fn(origins=["A"] * 30, destinations=["B"])
        assert "error" in result
        assert "Maximum 25" in result["error"]
```

---

## Phase 6: Verification Checklist

- [ ] Credential spec added to `integrations.py`
- [ ] Tool directory created with all files
- [ ] `_GoogleMapsClient` class implemented
- [ ] All 6 tools registered with proper docstrings
- [ ] Tools registered in `tools/__init__.py`
- [ ] README documentation created
- [ ] Unit tests written and passing
- [ ] Manual testing with real API key
- [ ] Error handling covers all Google Maps status codes

---

## Testing Commands

```bash
# Run tests
cd tools
uv run pytest tests/tools/test_google_maps_tool.py -v

# Run with coverage
uv run pytest tests/tools/test_google_maps_tool.py -v --cov=aden_tools.tools.google_maps_tool

# Manual test (requires API key)
export GOOGLE_MAPS_API_KEY="your_key_here"
uv run python -c "
from aden_tools.tools.google_maps_tool import register_tools
from fastmcp import FastMCP
mcp = FastMCP('test')
register_tools(mcp)
fn = mcp._tool_manager._tools['maps_geocode'].fn
print(fn(address='1600 Amphitheatre Parkway, Mountain View, CA'))
"
```

---

## Notes

- Use the HubSpot tool implementation as the primary reference pattern
- Ensure all tools return error dicts (not exceptions) for API failures
- Include `os.getenv` fallback for credential retrieval
- Add `Returns:` section to all docstrings
- Follow the existing code style (type hints, docstrings, error handling)
