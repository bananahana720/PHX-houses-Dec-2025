# 4. Fields to Investigate Before Cleanup

### 4.1 Data Sources (Generic)
```
data_source             (what data comes from what source?)
distance_to_park_miles_source
orientation_source
parks_data_source       (web_research_85306)
safety_data_source      (web_research_85306)
```

**Action:** Grep codebase for references. If unused, flag for removal.

### 4.2 Assessment Confidence Proliferation
```
assessment_confidence
image_assessment_confidence
interior_assessment_confidence
interior_confidence
section_c_confidence
```

Multiple fields suggest poor abstraction. Should consolidate into single confidence tracking system.

### 4.3 Scoring Timestamp
```
scored_at           (datetime when scoring occurred?)
```

**Action:** Verify if needed for audit trail. If yes, move to LineageTracker or Phase 4 output file.

---
