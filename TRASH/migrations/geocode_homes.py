"""
Geocoding module for Phoenix home listings.

Converts addresses from phx_homes.csv to latitude/longitude coordinates
using geopy's Nominatim geocoder. Results are cached to avoid re-geocoding
on subsequent runs.
"""

import csv
import json
import time
from pathlib import Path

from geopy.geocoders import Nominatim


class HomeGeocoder:
    """Geocodes home addresses and manages caching."""

    def __init__(
        self,
        cache_file: str = "geocoded_homes.json",
        rate_limit_delay: float = 1.0,
    ):
        """
        Initialize the geocoder.

        Args:
            cache_file: Path to JSON file for caching geocoded results
            rate_limit_delay: Seconds to wait between geocoding requests
                              (Nominatim requires ~1 sec minimum)
        """
        self.cache_file = Path(cache_file)
        self.rate_limit_delay = rate_limit_delay
        self.geolocator = Nominatim(user_agent="phx_home_analyzer")
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cached geocoding results from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    cached_list = json.load(f)
                    # Convert list to dict keyed by address for faster lookup
                    return {item["full_address"]: item for item in cached_list}
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load cache file: {e}")
                return {}
        return {}

    def _save_cache(self) -> None:
        """Save cached geocoding results to file."""
        # Convert dict back to list for JSON serialization
        cache_list = list(self.cache.values())
        with open(self.cache_file, "w") as f:
            json.dump(cache_list, f, indent=2)
        print(f"Cached results saved to {self.cache_file}")

    def geocode_address(self, address: str) -> dict | None:
        """
        Geocode a single address.

        Args:
            address: Full address string

        Returns:
            Dictionary with full_address, lat, lng keys, or None if geocoding fails
        """
        # Check cache first
        if address in self.cache:
            return self.cache[address]

        try:
            # Rate limiting to avoid Nominatim throttling
            time.sleep(self.rate_limit_delay)

            location = self.geolocator.geocode(address)

            if location:
                result = {
                    "full_address": address,
                    "lat": round(location.latitude, 4),
                    "lng": round(location.longitude, 4),
                }
                self.cache[address] = result
                return result
            else:
                print(f"Warning: Could not geocode address: {address}")
                return None

        except Exception as e:
            print(f"Error geocoding {address}: {e}")
            return None

    def geocode_csv(self, csv_file: str) -> list:
        """
        Geocode all addresses from a CSV file.

        Args:
            csv_file: Path to CSV file with 'full_address' column

        Returns:
            List of geocoded results with successful coordinates
        """
        results = []
        failed_addresses = []

        with open(csv_file) as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                address = row.get("full_address")
                if not address:
                    print(f"Row {i}: Missing full_address column")
                    continue

                geocoded = self.geocode_address(address)
                if geocoded:
                    results.append(geocoded)
                    print(f"[{i}] Geocoded: {address} -> ({geocoded['lat']}, {geocoded['lng']})")
                else:
                    failed_addresses.append(address)
                    print(f"[{i}] FAILED: {address}")

        # Save cache after processing all addresses
        self._save_cache()

        # Print summary
        print("\n" + "=" * 80)
        print("GEOCODING SUMMARY")
        print("=" * 80)
        print(f"Successfully geocoded: {len(results)}/{len(results) + len(failed_addresses)}")

        if failed_addresses:
            print(f"\nFailed addresses ({len(failed_addresses)}):")
            for addr in failed_addresses:
                print(f"  - {addr}")
        else:
            print("All addresses geocoded successfully!")

        if results:
            print("\nSample coordinates (Phoenix area verification):")
            for item in results[:3]:
                print(f"  {item['full_address']}")
                print(f"    Lat: {item['lat']}, Lng: {item['lng']}")

        return results


def main():
    """Main entry point for geocoding script."""
    geocoder = HomeGeocoder(cache_file="geocoded_homes.json", rate_limit_delay=1.0)

    # Geocode all homes from CSV
    results = geocoder.geocode_csv("phx_homes.csv")

    # Save results to JSON file (already done via _save_cache, but be explicit)
    with open("geocoded_homes.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to geocoded_homes.json")


if __name__ == "__main__":
    main()
