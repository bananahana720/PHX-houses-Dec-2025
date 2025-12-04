# Appendix B: Lineage Example

**Example lineage trace for property "4732 W Davis Rd":**

```json
{
  "a12177f5": {
    "lot_sqft": {
      "field_name": "lot_sqft",
      "source": "assessor_api",
      "confidence": 0.95,
      "updated_at": "2025-12-02T08:07:32.809015",
      "original_value": 8069,
      "notes": "Maricopa County Assessor parcel 123-45-678"
    },
    "sewer_type": {
      "field_name": "sewer_type",
      "source": "manual",
      "confidence": 0.85,
      "updated_at": "2025-11-15T14:32:10.123456",
      "original_value": "city",
      "notes": "Verified with Phoenix Water Services"
    },
    "school_rating": {
      "field_name": "school_rating",
      "source": "greatschools",
      "confidence": 0.85,
      "updated_at": "2025-10-01T09:15:22.456789",
      "original_value": 7.0,
      "notes": "GreatSchools API 2025-09-30"
    }
  }
}
```

**Lineage trace shows:**
- `lot_sqft`: Official county data (95% confidence)
- `sewer_type`: Manual verification (85% confidence)
- `school_rating`: GreatSchools API (85% confidence)

---
