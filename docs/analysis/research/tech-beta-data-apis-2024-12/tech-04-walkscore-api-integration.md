# TECH-04: WalkScore API Integration

### WalkScore API Overview

**Official Documentation:** https://www.walkscore.com/professional/api.php

| Feature | Details | Confidence |
|---------|---------|------------|
| Base URL | `https://api.walkscore.com` | High |
| Authentication | API Key (wsapikey) | High |
| Coverage | US, Canada, Australia, New Zealand | High |
| Response Format | JSON, XML | High |

### Available Scores

| Score Type | Range | Description |
|------------|-------|-------------|
| Walk Score | 0-100 | Walkability to errands |
| Transit Score | 0-100 | Public transit accessibility |
| Bike Score | 0-100 | Bike infrastructure quality |

### API Endpoints

#### 1. Score API (Main)
```
GET https://api.walkscore.com/score
    ?format=json
    &address=1234+Main+St+Phoenix+AZ+85001
    &lat=33.4484
    &lon=-112.0740
    &transit=1
    &bike=1
    &wsapikey=YOUR_API_KEY
```

**Response Fields:**
- `walkscore` (integer 0-100)
- `description` (e.g., "Walker's Paradise", "Car-Dependent")
- `transit.score` (integer 0-100)
- `bike.score` (integer 0-100)

#### 2. Public Transit API
```
Base URL: https://transit.walkscore.com
Coverage: 350+ transit agencies
```

Six available API calls for transit stop/route data. [High Confidence]

#### 3. Travel Time API
```
Endpoint: https://api.walkscore.com/traveltime/
Modes: drive, walk, bike, transit
Limit: 60 minutes maximum trip duration
```

#### 4. Travel Time Polygon API
```
Endpoint: https://api2.walkscore.com/api/v1/traveltime_polygon/json
Method: GET, POST
Purpose: Generate commute shed polygons
```

### Rate Limits & Quotas

| Tier | Widget Views/Day | API Calls/Day | Additional APIs |
|------|------------------|---------------|-----------------|
| Free | 1,000 | 5,000 | No |
| Professional | Higher | Higher | Yes (Score Details, Transit, Travel Time) |
| Enterprise | Custom | Custom | Yes + multi-domain |

**Quota Enforcement:** Exceeding quota returns 4xx status code. [High Confidence]

### Pricing

| Tier | Cost | Notes |
|------|------|-------|
| Free | $0 | 5,000 calls/day, basic scores only |
| Professional | Contact sales | Score Details, Transit API, Travel Time API |
| Enterprise | Contact sales | Multi-domain, high-volume |

**Contact:** professional@walkscore.com or (253) 256-1634

**Sources:**
- [WalkScore API Documentation](https://www.walkscore.com/professional/api.php)
- [WalkScore APIs Overview](https://www.walkscore.com/professional/walk-score-apis.php)
- [WalkScore Pricing](https://www.walkscore.com/professional/pricing.php)

### Terms of Service Key Points

**Prohibited:**
- Bulk downloads
- Caching/storing scores without written consent
- Modifying WalkScore content
- Reverse engineering

**Required:**
- Follow branding requirements
- Attribution/linking to WalkScore

**Termination:** WalkScore reserves right to terminate access at any time for any reason. [High Confidence]

**Sources:**
- [WalkScore Terms of Use](https://www.walkscore.com/professional/terms-of-use.php)

### Python Integration Example

```python
import requests

def get_walkscore(address: str, lat: float, lon: float, api_key: str) -> dict:
    """
    Get Walk Score, Transit Score, and Bike Score for an address.
    """
    base_url = "https://api.walkscore.com/score"
    params = {
        "format": "json",
        "address": address,
        "lat": lat,
        "lon": lon,
        "transit": 1,
        "bike": 1,
        "wsapikey": api_key
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()

    data = response.json()
    return {
        "walk_score": data.get("walkscore"),
        "walk_description": data.get("description"),
        "transit_score": data.get("transit", {}).get("score"),
        "bike_score": data.get("bike", {}).get("score")
    }

# Example usage for Phoenix property
result = get_walkscore(
    address="123 Main St Phoenix AZ 85001",
    lat=33.4484,
    lon=-112.0740,
    api_key="YOUR_API_KEY"
)
```

---
