# Image Count Comparison

### Current (Wrong) Extraction

```
Extraction from Search Results Page:

Property A (4209 W Wahalla Ln - CORRECT):
  └─ Images: 3-5 (thumbnails from result card)

Property B (4210 W Wahalla Ln - WRONG):
  └─ Images: 5-8 (thumbnails from result card)

Property C (4208 W Wahalla Ln - WRONG):
  └─ Images: 5-8 (thumbnails from result card)

Featured/Similar Properties (WRONG):
  └─ Images: 5-15 (carousel images)

Total: 27-39 images ✗
  From 4 different properties
  Mixed architectural styles
  User sees "townhomes" and "different houses"
```

### Fixed (Correct) Extraction

```
Extraction from Property Detail Page:

Property A (4209 W Wahalla Ln - CORRECT):
  └─ Images: 8-15
    - Exterior views: 2-3
    - Interior/kitchen: 2-3
    - Bathrooms: 1-2
    - Bedrooms: 1-2
    - Yard/features: 2-3

Total: 8-15 images ✓
  From 1 property only
  Consistent architectural style
  User sees correct property
```

---
