# URL Comparison

### Current (Wrong) URL Format

```
https://www.zillow.com/homes/4209-W-Wahalla-Ln-Glendale-AZ-85308_rb/
                       ^^^^^^                                     ^^^
                       /homes/  = search results path
                                                              _rb = Results Browse

Landing Page:
  Zillow Search Results
  - Multiple property listings
  - Address only approximately matches (could show many properties)
  - Shows related properties and suggestions
  - Image extraction gets thumbnails from multiple properties
```

### Fixed URL Format

```
https://www.zillow.com/homedetails/12345678_zpid/
                       ^^^^^^^^^^^             ^^^^
                       /homedetails/ = single property detail page
                                       zpid = unique Zillow property ID

OR (via interactive search, lands on):

https://www.zillow.com/property/12345678/
                       ^^^^^^^^
                       /property/ = also single property detail

Landing Page:
  Specific Property Detail Page
  - ONE property only
  - Complete property information (zestimate, history, etc.)
  - Property gallery/carousel
  - Image extraction gets all images from THIS property only
```

---
