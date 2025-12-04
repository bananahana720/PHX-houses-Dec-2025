# Phase 3: Optimization (1 hour) - Use Property IDs

### Goal
If we can extract Zillow's zpid (property ID), use direct URL instead of search.

### Implementation

**Store zpid during Phase 1 listing extraction:**

In `scripts/extract_images.py` or listing-browser agent, capture:

```python
# When scraping Zillow listing, extract zpid from URL
# URL format: https://www.zillow.com/homedetails/{zpid}_{extra}

# Store in enrichment_data.json
enrichment_data[address]["sources"]["zillow"] = {
    "zpid": "12345678",  # Extract and store
    "url": "https://www.zillow.com/homedetails/12345678_zpid/",
    "extracted_at": "2025-12-02T10:30:00Z"
}
```

**Use zpid in image extraction:**

```python
def _build_search_url(self, property: Property) -> str:
    """Build Zillow URL from property.

    Priority:
    1. Use zpid if available (direct property URL)
    2. Fall back to interactive search
    """
    # Check if enrichment has zpid
    if hasattr(property, 'zillow_zpid') and property.zillow_zpid:
        url = f"https://www.zillow.com/homedetails/{property.zillow_zpid}/"
        logger.info(
            "%s using direct property URL with zpid: %s",
            self.name,
            url,
        )
        return url

    # Fallback to interactive search (Phase 2)
    # Build search URL for navigation
    full_address = f"{property.street}, {property.city}, {property.state} {property.zip_code}"
    # Signal to _navigate_with_stealth() that we need interactive search
    # by using a special marker
    return f"https://www.zillow.com/search?address={quote_plus(full_address)}"
```

---
