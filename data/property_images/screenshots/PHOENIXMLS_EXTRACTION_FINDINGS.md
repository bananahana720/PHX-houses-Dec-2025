# Phoenix MLS Search - Autocomplete & Listing Page Analysis

**Test Date:** 2025-12-06
**Test Address:** 5219 W El Caminito Dr, Glendale, AZ 85302
**Test Property MLS#:** 6937912

---

## 1. AUTOCOMPLETE DROPDOWN STRUCTURE

### Entry Point
- **URL:** https://phoenixmlssearch.com/simple-search/
- **Input Field:**
  - Placeholder: "Enter an Address, City, Zip or MLS#"
  - Accessibility role: `textbox`
  - Combobox: `[expanded]` when active

### Dropdown DOM Structure
```
combobox [expanded]
  ├── list (contains selected items)
  │   └── listitem
  │       └── textbox (input field)
  └── tree (autocomplete results dropdown)
      ├── treeitem "5219 W EL CAMINITO Drive, Glendale, AZ 85302 / 6937912 (MLS #)"
      ├── treeitem "5219 W El Caminito Drive, Glendale, AZ 85302 / 4719507 (MLS #)"
      └── treeitem "5219 w el caminito dr glendale (Street Address)"
```

### Key Findings
- **Dropdown role:** `tree`
- **Item role:** `treeitem`
- **Cursor interaction:** `[cursor=pointer]`
- **Text format:** `"{ADDRESS} / {MLS_NUMBER} (MLS #)"`
- **Multiple results:** Yes - can have multiple MLS listings for same address
- **Result types:**
  - Full address with MLS# (primary results)
  - Street address only (tertiary result)

### Autocomplete Behavior
1. Input becomes active with message "Please enter 3 or more characters"
2. After typing full address, results appear in tree structure
3. Results include MLS# in parentheses format: `6937912 (MLS #)`
4. Clicking a treeitem adds it to a selected list above dropdown
5. **Important:** Clicking dropdown item does NOT navigate automatically
   - Must click the Search button to proceed
6. Selected item shows with "×" remove button in selected list

### MLS Number Extraction
```
Text: "5219 W EL CAMINITO Drive, Glendale, AZ 85302 / 6937912 (MLS #)"
Regex: /\/\s*(\d{7})\s*\(MLS #\)/
Extract: 6937912
```

---

## 2. SEARCH RESULTS PAGE

### Navigation Flow
1. **Start:** Simple search page with autocomplete
2. **Action:** Select address from dropdown + click Search button
3. **Result:** Search results page with query parameters

### Search Results URL Pattern
```
https://phoenixmlssearch.com/mls/search/
  ?OrderBy=-ListPrice
  &StandardStatus%5B%5D=Active
  &SavedSearch=20171227170325032090000000
  &Limit=10
  &ListingId={MLS_NUMBER}
```

**Example (MLS# 6937912):**
```
https://phoenixmlssearch.com/mls/search/?OrderBy=-ListPrice&StandardStatus%5B%5D=Active&SavedSearch=20171227170325032090000000&Limit=10&ListingId=6937912
```

### Key Parameters
| Parameter | Value | Notes |
|-----------|-------|-------|
| `OrderBy` | `-ListPrice` | Sort by price descending |
| `StandardStatus[]` | `Active` | Only active listings |
| `SavedSearch` | `20171227170325032090000000` | System-assigned search ID |
| `Limit` | `10` | Results per page |
| `ListingId` | `{MLS_NUMBER}` | Filter to specific MLS# |

### Search Results Page Content
- **Page Title:** "Search - Phoenix MLS Search.com"
- **Match Count:** "1 matches found"
- **Display Options:** List View, Map View
- **Sorting:** Available by price, beds, baths, year, sqft, recently updated
- **Per Page:** Dropdown to select 5, 10, 15, 20, 25

### Listing Card Structure
```
generic [ref=e58]:
  ├── price: "$520,000"
  ├── address_link: "5219 W EL CAMINITO Drive Glendale, AZ 85302"
  ├── mls_number: "6937912"
  ├── beds: "5"
  ├── baths: "2"
  ├── features:
  │   ├── property_type
  │   ├── beds/baths
  │   ├── year_built
  │   ├── subdivision
  │   └── description
  └── image_link: (SparkPlatform CDN)
```

---

## 3. LISTING DETAIL PAGE

### URL Pattern
```
https://phoenixmlssearch.com/mls/{NORMALIZED_ADDRESS}-mls_{MLS_NUMBER}/?{QUERY_PARAMS}
```

**Example (MLS# 6937912):**
```
https://phoenixmlssearch.com/mls/5219-W-EL-CAMINITO-Drive-Glendale-AZ-85302-mls_6937912/?SavedSearch=20171227170325032090000000&ListingId=6937912&StandardStatus=Active&pg=1&OrderBy=-ListPrice&p=n&m=20070913202326493241000000&n=n
```

### Address Normalization (URL Component)
- Input: `5219 W El Caminito Drive, Glendale, AZ 85302`
- URL: `5219-W-EL-CAMINITO-Drive-Glendale-AZ-85302`
- Pattern: `{STREET}-{CITY}-{STATE}-{ZIP}`
- Rules:
  - Spaces → hyphens
  - Uppercase
  - Full street direction (W, E, N, S)
  - Full street type (Drive, Street, etc.)

### Page Content
- **Title:** Full address with MLS#
- **Price:** $520,000
- **Beds:** 5
- **Baths:** 2
- **Photos:** 43 total
- **Details Sections:**
  - Contract Information (price, status, list date)
  - Location Tax Legal (address components, county, assessor#)
  - General Property Description (dwelling type, sqft, lot size, pool, fireplace)
  - Features (construction, heating/cooling, utilities, pool type, etc.)
  - Property Remarks (location, coordinates)
  - Legal Info (township, range, section, lot)
  - Parking Spaces (garage: 2, carport: 2)
  - Property Features (detailed list of features)

### Critical Data Fields Extracted
| Field | Value | Source |
|-------|-------|--------|
| Address | 5219 W EL CAMINITO Drive, Glendale, AZ 85302 | Page heading |
| MLS# | 6937912 | Page heading |
| Price | $520,000 | Contract Information |
| Beds | 5 | General Property Description |
| Baths | 2 (Full) | General Property Description |
| Year Built | 1977 | General Property Description |
| Sqft | 2239 | General Property Description |
| Lot Sqft | 8851 | General Property Description |
| Pool | Yes (Private, Diving Pool) | General Property Description |
| Fireplace | Yes (1) | General Property Description |
| Garage Spaces | 2 | Parking Spaces |
| Sewer | Public Sewer | Property Features |
| Water | City Water | Property Features |
| HOA Fee | No Fees | Property Features |
| Cooling | Central Air + Evaporative | Property Features |
| Heating | Electric | Property Features |
| Roofing | Composition | Property Features |
| Construction | Block | Construction |

---

## 4. IMAGE EXTRACTION

### SparkPlatform CDN URLs

#### Image URL Patterns
```
Full size:  https://cdn.photos.sparkplatform.com/az/{IDENTIFIER}-o.jpg
Thumbnail: https://cdn.photos.sparkplatform.com/az/{IDENTIFIER}-t.jpg
Resized:   https://cdn.resize.sparkplatform.com/az/{SIZE}/{BOOLEAN}/{IDENTIFIER}-o.jpg
```

#### Real Example URLs
```
Thumbnail 1: https://cdn.photos.sparkplatform.com/az/20251023213131892099000000-t.jpg
Full Size 1: https://cdn.photos.sparkplatform.com/az/20251023213131892099000000-o.jpg
Resized 1:   https://cdn.resize.sparkplatform.com/az/640x480/true/20251023213131892099000000-o.jpg

Thumbnail 2: https://cdn.photos.sparkplatform.com/az/20251023213124324538000000-t.jpg
Full Size 2: https://cdn.photos.sparkplatform.com/az/20251023213124324538000000-o.jpg

Thumbnail 3: https://cdn.photos.sparkplatform.com/az/20251023213417773188000000-t.jpg
Full Size 3: https://cdn.photos.sparkplatform.com/az/20251023213417773188000000-o.jpg

Thumbnail 4: https://cdn.photos.sparkplatform.com/az/20251023213302914516000000-t.jpg
Full Size 4: https://cdn.photos.sparkplatform.com/az/20251023213302914516000000-o.jpg
```

### Identifier Format
- **Pattern:** `{TIMESTAMP}{SEQUENCE}`
- **Example:** `20251023213131892099000000`
- **Components:**
  - `20251023` - Date (YYYYMMDD)
  - `213131` - Time (HHMMSS)
  - `892099000000` - Sequence/Property ID
- **Total images:** 43 (from "View Photos (43)" button)

### Image Variants
- `-o.jpg`: Original full-size image
- `-t.jpg`: Thumbnail version
- Can be resized via `/resize/{WIDTH}x{HEIGHT}/{QUALITY}` path
- Example: `/resize.sparkplatform.com/az/640x480/true/...`

---

## 5. IMPLEMENTATION RECOMMENDATIONS

### For Stealth Extraction Script

#### 1. Autocomplete Search
```python
# Steps:
1. Navigate to https://phoenixmlssearch.com/simple-search/
2. Find input: role=textbox, placeholder contains "Address"
3. Type address slowly (human-like delays)
4. Wait 2-3 seconds for tree dropdown
5. Parse tree items: role=treeitem
6. Extract MLS# using regex: /\d{7}\s*\(MLS #\)/
7. Click first treeitem with matching MLS#
8. Wait for selection (item appears in list with × button)
9. Click Search button
```

#### 2. Search Results Navigation
```python
# The ListingId parameter in search results is the MLS#
# Example: ListingId=6937912
# Can construct URL directly if MLS# is known
```

#### 3. Listing Detail Page Navigation
```python
# From search results, click the address link
# URL pattern: /mls/{NORMALIZED_ADDRESS}-mls_{MLS}/?{PARAMS}
# Alternative: construct directly from MLS# if address known
```

#### 4. Image Extraction
```python
# Method 1: Query all img[src*="sparkplatform"] tags
# Method 2: Extract from detail page DOM
# Images are SparkPlatform CDN hosted
# Use full-size (-o.jpg) suffix for best quality
# Total images shown in "View Photos (N)" button
```

### CSS Selectors for Key Elements
| Element | Selector | Notes |
|---------|----------|-------|
| Input | `input[placeholder*="Address"]` | Autocomplete input |
| Dropdown | `div[role="tree"]` | Results container |
| Results | `div[role="treeitem"]` | Each result item |
| Search Btn | `button:contains("Search")` | Submit form |
| Address Link | `a[href*="/mls/"]` | Detail page link |
| Images | `img[src*="sparkplatform"]` | Photo elements |

### Regex Patterns
```python
# Extract MLS# from dropdown text
r'/\s*(\d{7})\s*\(MLS #\)'

# Extract address from URL
r'/mls/([\w\-]+)-mls_(\d{7})'
# Group 1: normalized address
# Group 2: MLS number

# SparkPlatform CDN identifier
r'sparkplatform\.com/az/(\d{14,}[-o|t]\.jpg)'
```

---

## 6. ERROR HANDLING & EDGE CASES

### Autocomplete Issues
1. **No results:** Address not in MLS database
2. **Multiple results:** Same address, different MLS# (duplicate listings)
3. **Address variations:** Partial spelling matches in 3rd result (Street Address only)

### Navigation Issues
1. **404 Not Found:** Listing delisted after autocomplete
2. **Timeout:** Search form submission hangs
   - **Recovery:** Browser back, retry

### Image Issues
1. **Missing images:** Some properties have 0 photos
   - Show "View Photos (0)" button
2. **Mixed sources:** SparkPlatform is primary, fallback unknown
3. **Broken CDN links:** Rare, but check HTTP 200 before processing

### Blocking / Rate Limiting
- **Status:** No PerimeterX observed (unlike Zillow/Redfin)
- **Anti-bot level:** Light/minimal
- **Recommendation:** Standard playwright works, but add human-like delays for robustness

---

## 7. SUMMARY TABLE

| Aspect | Finding | Status |
|--------|---------|--------|
| **Autocomplete dropdown** | `role=tree` with `treeitem` results | CONFIRMED |
| **MLS# format** | 7 digits, visible in dropdown text | CONFIRMED |
| **Search results URL** | `/mls/search/?ListingId={MLS}` | CONFIRMED |
| **Listing detail URL** | `/mls/{ADDRESS}-mls_{MLS}/` | CONFIRMED |
| **Image CDN** | SparkPlatform (`cdn.photos.sparkplatform.com`) | CONFIRMED |
| **Image count** | 43 total for test property | CONFIRMED |
| **Data completeness** | All key fields available on detail page | CONFIRMED |
| **Navigation flow** | Autocomplete → Search Results → Detail | CONFIRMED |
| **Anti-bot protection** | Minimal/light (not PerimeterX) | CONFIRMED |

---

## 8. FILES CAPTURED

Screenshots saved to: `data/property_images/screenshots/`

1. **01-initial-page.png** - Simple search form initial state
2. **02-autocomplete-dropdown.png** - Autocomplete results showing MLS#s
3. **03-after-selection.png** - Selected item in list before search
4. **04-listing-detail-page.png** - Detail page with property image

All screenshots demonstrate the complete workflow from search through listing detail.

---

## Test Result: SUCCESS ✓

The Phoenix MLS Search site provides:
- Clear autocomplete with MLS# extraction
- Accessible URL patterns with normalized addresses
- Complete property data on detail pages
- Direct SparkPlatform image CDN access
- No PerimeterX or advanced anti-bot protection

**Recommendation:** Can build robust extractor using standard Playwright + regex parsing for MLS# and URLs.
