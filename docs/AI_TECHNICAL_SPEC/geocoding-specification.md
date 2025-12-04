# GEOCODING SPECIFICATION

### Geocoder Implementation (`geocode_homes.py` → `geocoded_homes.json`)

**Library**: `geopy`

```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import json
import pandas as pd
import time

class HomeGeocoder:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="phx_home_analyzer")
        self.geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=1.0  # Respect rate limits
        )
        self.cache_file = 'geocoded_homes.json'
        self.cache = self._load_cache()

    def _load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                return {item['full_address']: item for item in data}
        except FileNotFoundError:
            return {}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(list(self.cache.values()), f, indent=2)

    def geocode_address(self, address):
        if address in self.cache:
            return self.cache[address]

        try:
            location = self.geocode(address)
            if location:
                result = {
                    'full_address': address,
                    'lat': location.latitude,
                    'lng': location.longitude
                }
                self.cache[address] = result
                self._save_cache()
                return result
        except Exception as e:
            print(f"Geocoding failed for {address}: {e}")

        return None

    def geocode_csv(self, csv_file):
        df = pd.read_csv(csv_file)
        results = []

        for address in df['full_address']:
            result = self.geocode_address(address)
            if result:
                results.append(result)
            time.sleep(0.1)  # Additional safety delay

        return results
```

**Expected Output** (`geocoded_homes.json`):
```json
[
  {
    "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
    "lat": 33.6314,
    "lng": -112.1998
  }
]
```

**Phoenix Metro Coordinate Bounds** (for validation):
- Latitude: 33.3 - 33.75
- Longitude: -112.3 - -111.8

---
