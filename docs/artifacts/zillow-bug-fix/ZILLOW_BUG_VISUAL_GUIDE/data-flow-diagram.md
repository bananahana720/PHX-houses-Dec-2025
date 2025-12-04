# Data Flow Diagram

### Current (Broken) Data Path

```
enrichment_data.json
  "4209 W Wahalla Ln"
    property_images: [
      "photo_of_correct_house.jpg",      ✓
      "photo_of_neighbor_townhome.jpg",  ✗
      "photo_of_other_property.jpg",     ✗
      "featured_property_photo.jpg",     ✗
      ... 23 more wrong images ...
    ]
            ↓ (Phase 2)
    image-assessor agent
      Scores images:
      - Kitchen: "Has white cabinets, modern style"  ✓
      - But also scores: "Townhome layout, condo"    ✗
      - Composite score: WRONG (mixed properties)
            ↓
    enrichment_data.json
      phase_2_interior_score: 280  ✗ (too high, scored townhome)
      phase_2_exterior_score: 250  ✗ (too high, scored different property)
            ↓ (Phase 3 - synthesis)
    Final Analysis
      Total Score: 520  ✗ (UNICORN tier - WRONG!)
      Recommendation: "BUY" ✗
      Actual: Images don't match property, score is inflated
```

### Fixed Data Path

```
enrichment_data.json
  "4209 W Wahalla Ln"
    property_images: [
      "exterior_front.jpg",    ✓
      "exterior_back.jpg",     ✓
      "kitchen.jpg",           ✓
      "master_bedroom.jpg",    ✓
      "bathroom.jpg",          ✓
      ... 8-10 images all same property ...
    ]
            ↓ (Phase 2)
    image-assessor agent
      Scores images:
      - Kitchen: "Has white cabinets, modern style" ✓
      - Exterior: "Two-story ranch, good condition" ✓
      - Score: Consistent, reliable
            ↓
    enrichment_data.json
      phase_2_interior_score: 165  ✓ (accurate for this property)
      phase_2_exterior_score: 180  ✓ (accurate for this property)
            ↓ (Phase 3 - synthesis)
    Final Analysis
      Total Score: 425  ✓ (CONTENDER tier - CORRECT!)
      Recommendation: "Consider" ✓
      Actual: Images match, score is accurate
```

---
