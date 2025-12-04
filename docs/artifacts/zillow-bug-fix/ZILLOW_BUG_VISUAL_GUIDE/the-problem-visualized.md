# The Problem Visualized

### Current (BROKEN) Flow

```
Input Property:
  Address: 4209 W Wahalla Ln, Glendale, AZ 85308

         ↓

_build_search_url() creates:
  URL: https://www.zillow.com/homes/4209-W-Wahalla-Ln-Glendale-AZ-85308_rb/
       (Note: "_rb" = Results Browse)

         ↓

Browser navigates to URL
  ✗ WRONG: Lands on SEARCH RESULTS PAGE
  Shows multiple properties:
    - 4209 W Wahalla Ln (yours, correct)
    - 4210 W Wahalla Ln (neighbor's, wrong)
    - 4208 W Wahalla Ln (other neighbor's, wrong)
    - Featured properties carousel (wrong)
    - Similar homes suggestions (wrong)

         ↓

_extract_urls_from_page() runs on SEARCH RESULTS page
  Queries all <img> elements on page
  Gets:
    - Thumbnail from property A (correct) ✓
    - Thumbnail from property B (wrong) ✗
    - Thumbnail from property C (wrong) ✗
    - Thumbnails from "Similar homes" (wrong) ✗

         ↓

_is_high_quality_url() filter
  ✓ Domain: photos.zillowstatic.com (PASSES - used by search results too!)
  ✓ Extension: .jpg (PASSES)
  ✗ No "thumb" in URL (PASSES - Zillow doesn't use "thumb" in URLs)

         ↓

Result: 27-39 images from MULTIPLE PROPERTIES
  ✗ Image 1: Correct house (by chance it's first in results)
  ✗ Images 2-10: Neighbor's townhome (different style!)
  ✗ Images 11-20: Another property's condo
  ✗ Images 21-39: Featured/similar properties
```

### What Happens During Extraction

```
SEARCH RESULTS PAGE (what you're landing on):

┌─────────────────────────────────────────────────────┐
│ Zillow Home Search Results                          │
├─────────────────────────────────────────────────────┤
│                                                      │
│ Result 1: 4209 W Wahalla Ln (YOURS - CORRECT)      │
│ ┌──────────────────┐                               │
│ │  [Photo: House]  │  3 bed | 2 bath | $450k      │
│ └──────────────────┘                               │
│                                                      │
│ Result 2: 4210 W Wahalla Ln (NEIGHBOR - WRONG)     │
│ ┌──────────────────┐                               │
│ │[Photo: Townhome] │  2 bed | 1.5 bath | $320k    │
│ └──────────────────┘                               │
│                                                      │
│ Result 3: 4208 W Wahalla Ln (OTHER - WRONG)        │
│ ┌──────────────────┐                               │
│ │  [Photo: Condo]  │  4 bed | 2 bath | $550k      │
│ └──────────────────┘                               │
│                                                      │
│ ═══ Suggested Properties ═══                        │
│ │[Photo A] [Photo B] [Photo C] ...                 │
│ └─────────────────────────────────────────────────┘
│                                                      │
└─────────────────────────────────────────────────────┘

Image Extraction happens on THIS PAGE, getting images from:
  ✓ 4209 W Wahalla Ln (3-5 images - correct)
  ✗ 4210 W Wahalla Ln (8-10 images - WRONG)
  ✗ 4208 W Wahalla Ln (8-10 images - WRONG)
  ✗ Suggested/Featured (5-10 images - WRONG)

Total: ~27-39 images from MULTIPLE PROPERTIES
```

---
