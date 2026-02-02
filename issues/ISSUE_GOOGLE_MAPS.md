# [Integration]: Google Maps Platform - Geocoding, Routing & Location Intelligence

## Overview

Add integration with Google Maps Platform Web Services APIs to enable agents to power logistics, delivery, and location-based workflows. Google Maps provides industry-leading geocoding, routing, and distance calculation capabilities essential for fleet management, delivery optimization, and address validation.

**Use Cases from #2853:**
- Logistics agents need route optimization for multi-stop deliveries
- Address validation for order processing and CRM data hygiene
- Real-time distance/ETA calculations for customer communications
- Geocoding for location-based lead scoring and territory management

## Requirements

Implement the following 6 MCP tools:

### 1. `maps_geocode` - Convert address to coordinates
- **Parameters:** `address` (required)
- **Optional:** `components` (country, postal_code filter), `bounds`, `language`
- **Returns:** Lat/lng coordinates, formatted address, place_id, address components

### 2. `maps_reverse_geocode` - Convert coordinates to address
- **Parameters:** `lat`, `lng` (required)
- **Optional:** `result_type` (street_address, locality, etc.), `language`
- **Returns:** Formatted addresses, place_id, address components

### 3. `maps_directions` - Get route between two points
- **Parameters:** `origin`, `destination` (required)
- **Optional:** `mode` (driving/walking/bicycling/transit), `waypoints`, `alternatives`, `avoid` (tolls/highways/ferries), `departure_time`, `arrival_time`
- **Returns:** Routes with steps, distance, duration, polyline, traffic info

### 4. `maps_distance_matrix` - Calculate distances for multiple origins/destinations
- **Parameters:** `origins` (list), `destinations` (list)
- **Optional:** `mode`, `avoid`, `units` (metric/imperial), `departure_time`
- **Returns:** Matrix of distances and durations for all origin-destination pairs

### 5. `maps_place_details` - Get detailed place information
- **Parameters:** `place_id` (required)
- **Optional:** `fields` (name, formatted_address, geometry, opening_hours, etc.)
- **Returns:** Place details including name, address, phone, hours, reviews, photos

### 6. `maps_place_search` - Search for places by query or nearby
- **Parameters:** `query` or `location` + `radius`
- **Optional:** `type` (restaurant, gas_station, etc.), `min_price`, `max_price`, `open_now`
- **Returns:** List of places with basic info and place_ids

## Authentication

- **Credential:** `GOOGLE_MAPS_API_KEY`
- **Auth Method:** API key in query parameter (`key=...`)
- **Required APIs to Enable:**
  - Geocoding API
  - Directions API
  - Distance Matrix API
  - Places API

**Get API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable the Maps APIs (Geocoding, Directions, Distance Matrix, Places)
4. Go to APIs & Services > Credentials
5. Create API Key
6. (Recommended) Restrict key to specific APIs and IP addresses

## Costing

| API | Free Tier | Price After |
|-----|-----------|-------------|
| Geocoding | $200/mo credit (~40K requests) | $5.00 per 1,000 |
| Directions | $200/mo credit (~40K requests) | $5.00 per 1,000 |
| Distance Matrix | $200/mo credit (~40K elements) | $5.00 per 1,000 elements |
| Places - Search | $200/mo credit | $32.00 per 1,000 |
| Places - Details | $200/mo credit | $17.00 per 1,000 |

**Note:** Google provides $200 free monthly credit across all Maps APIs. This covers ~40,000 geocoding requests or equivalent usage.

## Implementation Details

### Credential Management

Add credential spec to `tools/src/aden_tools/credentials/integrations.py`:

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

### Tool Implementation

- Create `tools/src/aden_tools/tools/google_maps_tool/` directory
- Implement `_GoogleMapsClient` class wrapping API calls
- API Base URLs:
  - Geocoding: `https://maps.googleapis.com/maps/api/geocode/json`
  - Directions: `https://maps.googleapis.com/maps/api/directions/json`
  - Distance Matrix: `https://maps.googleapis.com/maps/api/distancematrix/json`
  - Places: `https://maps.googleapis.com/maps/api/place`
- Register 6 tools using FastMCP decorators
- Handle Google Maps-specific errors:
  - `OK` - Success
  - `ZERO_RESULTS` - No results found (not an error)
  - `OVER_QUERY_LIMIT` - Rate limit or billing issue
  - `REQUEST_DENIED` - Invalid API key or API not enabled
  - `INVALID_REQUEST` - Missing required parameter
  - `UNKNOWN_ERROR` - Server error (retry)

### File Structure

```
tools/src/aden_tools/tools/google_maps_tool/
├── __init__.py              # Export register_tools
├── google_maps_tool.py      # Tool implementation with _GoogleMapsClient
└── README.md                # Documentation
```

### Tests

- Add unit tests to `tools/tests/tools/test_google_maps_tool.py`
- Mock all Google Maps API calls
- Test cases:
  - Geocoding forward and reverse
  - Directions with waypoints and modes
  - Distance matrix with multiple origins/destinations
  - Place search and details
  - Error handling (invalid key, over limit, zero results)
  - Input validation (empty address, invalid coordinates)

## Use Cases (from #2853)

| Agent | How Google Maps Helps |
|-------|----------------------|
| Logistics Agent | `maps_distance_matrix` → calculate delivery ETAs for route planning |
| Delivery Optimizer | `maps_directions` with waypoints → optimize multi-stop routes |
| Address Validator | `maps_geocode` → standardize and validate customer addresses |
| Territory Manager | `maps_geocode` → geocode leads for territory assignment |
| Store Locator | `maps_place_search` → find nearest locations for customers |
| Fleet Tracker | `maps_directions` → calculate routes and ETAs for drivers |

## API Response Examples

### Geocode Response
```json
{
  "results": [{
    "formatted_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043",
    "geometry": {
      "location": {"lat": 37.4224764, "lng": -122.0842499}
    },
    "place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA",
    "address_components": [...]
  }],
  "status": "OK"
}
```

### Directions Response
```json
{
  "routes": [{
    "legs": [{
      "distance": {"text": "35.5 mi", "value": 57127},
      "duration": {"text": "45 mins", "value": 2700},
      "steps": [...]
    }],
    "overview_polyline": {"points": "...encoded..."}
  }],
  "status": "OK"
}
```

### Distance Matrix Response
```json
{
  "rows": [{
    "elements": [{
      "distance": {"text": "35.5 mi", "value": 57127},
      "duration": {"text": "45 mins", "value": 2700},
      "status": "OK"
    }]
  }],
  "status": "OK"
}
```

## Notes

- **$200 Free Credit:** All new Google Cloud accounts get $200/month in Maps API credits
- **API Key Restrictions:** Strongly recommend restricting keys by API and IP/referrer
- **Rate Limits:** 50 requests/second for most APIs (higher limits available)
- **Caching:** Google TOS allows caching for up to 30 days
- **Units:** Default is metric; set `units=imperial` for miles/feet
- **Real-time Traffic:** Available in Directions API with `departure_time=now`
- **Routes API:** Google's newer Routes API combines Directions + Distance Matrix with enhanced features (consider future migration)

## References

- [Geocoding API Documentation](https://developers.google.com/maps/documentation/geocoding)
- [Directions API Documentation](https://developers.google.com/maps/documentation/directions)
- [Distance Matrix API Documentation](https://developers.google.com/maps/documentation/distance-matrix)
- [Places API Documentation](https://developers.google.com/maps/documentation/places/web-service)
- [API Key Best Practices](https://developers.google.com/maps/api-security-best-practices)

---

**Parent Issue:** #2805
**Use Cases Issue:** #2853
**Labels:** `enhancement`, `help wanted`, `integrations`, `tools`
