# Data Architecture

### Data Flow Diagram

```
                    +------------------+
                    | phx_homes.csv    |
                    | (source listings)|
                    +--------+---------+
                             |
                             v
            +----------------+----------------+
            |                                 |
            v                                 v
+-------------------+            +--------------------+
| County Assessor   |            | Listing Browser    |
| API (Phase 0)     |            | Agent (Phase 1)    |
+--------+----------+            +---------+----------+
         |                                 |
         |    +-------------------+        |
         |    | Map Analyzer      |        |
         |    | Agent (Phase 1)   |        |
         |    +--------+----------+        |
         |             |                   |
         +------+------+------+------------+
                |             |
                v             v
         +------+-------------+------+
         |   enrichment_data.json    |
         |   (LIST of property dicts)|
         +-------------+-------------+
                       |
                       v
         +-------------+-------------+
         |   Image Assessor Agent    |
         |   (Phase 2 - Sonnet)      |
         +-------------+-------------+
                       |
                       v
         +-------------+-------------+
         |   Kill-Switch Filter      |
         |   (7 HARD criteria)       |
         +-------------+-------------+
                       |
              +--------+--------+
              |                 |
              v                 v
         +----+----+      +-----+-----+
         | PASS    |      | FAIL      |
         +---------+      +-----------+
              |
              v
         +----+----+
         | Scorer  |
         | (605pt) |
         +---------+
              |
              v
         +----+----+
         | Tier    |
         | Classify|
         +---------+
              |
              v
    +---------+---------+
    |                   |
    v                   v
+---+---+          +----+----+
| Deal  |          | Report  |
| Sheet |          | (CSV/   |
| (HTML)|          |  HTML)  |
+-------+          +---------+
```

### JSON Schemas

#### enrichment_data.json (LIST format)

**CRITICAL:** This is a LIST of objects, NOT a dict keyed by address.

```json
[
  {
    "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
    "normalized_address": "4732 w davis rd glendale az 85306",

    "county_data": {
      "lot_sqft": 10500,
      "year_built": 2006,
      "garage_spaces": 2,
      "has_pool": true,
      "sewer_type": "city",
      "data_source": "maricopa_assessor",
      "fetched_at": "2025-12-03T10:00:00Z",
      "confidence": 0.95
    },

    "listing_data": {
      "price": 475000,
      "beds": 4,
      "baths": 2.5,
      "sqft": 2100,
      "hoa_fee": 0,
      "listing_url": "https://zillow.com/...",
      "data_source": "zillow",
      "fetched_at": "2025-12-03T10:15:00Z",
      "confidence": 0.85
    },

    "location_data": {
      "school_rating": 8.5,
      "crime_index": 75,
      "orientation": "north",
      "flood_zone": "X",
      "walk_score": 45,
      "transit_score": 30,
      "bike_score": 35,
      "data_source": "map_analyzer",
      "fetched_at": "2025-12-03T10:30:00Z",
      "confidence": 0.85
    },

    "image_assessment": {
      "kitchen_score": 8.5,
      "master_score": 7.5,
      "natural_light_score": 8.0,
      "ceiling_score": 7.0,
      "fireplace_present": true,
      "laundry_score": 6.5,
      "aesthetics_score": 7.5,
      "image_count": 42,
      "data_source": "image_assessor",
      "assessed_at": "2025-12-03T11:00:00Z",
      "confidence": 0.80
    },

    "kill_switch": {
      "verdict": "PASS",
      "criteria_results": {
        "hoa": {"passed": true, "value": 0},
        "beds": {"passed": true, "value": 4},
        "baths": {"passed": true, "value": 2.5},
        "sqft": {"passed": true, "value": 2100},
        "lot": {"passed": true, "value": 10500},
        "garage": {"passed": true, "value": 2},
        "sewer": {"passed": true, "value": "city"}
      },
      "evaluated_at": "2025-12-03T11:15:00Z"
    },

    "scoring": {
      "section_a": 195,
      "section_b": 145,
      "section_c": 155,
      "total": 495,
      "tier": "UNICORN",
      "scored_at": "2025-12-03T11:20:00Z"
    },

    "metadata": {
      "created_at": "2025-12-03T10:00:00Z",
      "last_updated": "2025-12-03T11:20:00Z",
      "pipeline_version": "2.0",
      "schema_version": "2025-12-03"
    }
  }
]
```

#### work_items.json (Pipeline State)

```json
{
  "session": {
    "session_id": "abc123-def456-ghi789",
    "started_at": "2025-12-03T10:00:00Z",
    "mode": "all",
    "properties_count": 50
  },

  "current_phase": "phase2_images",

  "work_items": [
    {
      "address": "4732 W Davis Rd, Glendale, AZ 85306",
      "phases": {
        "phase0_county": {
          "status": "completed",
          "started_at": "2025-12-03T10:00:00Z",
          "completed_at": "2025-12-03T10:01:00Z"
        },
        "phase1_listing": {
          "status": "completed",
          "started_at": "2025-12-03T10:02:00Z",
          "completed_at": "2025-12-03T10:15:00Z"
        },
        "phase1_map": {
          "status": "completed",
          "started_at": "2025-12-03T10:02:00Z",
          "completed_at": "2025-12-03T10:20:00Z"
        },
        "phase2_images": {
          "status": "in_progress",
          "started_at": "2025-12-03T10:25:00Z",
          "images_processed": 28,
          "images_total": 42
        },
        "phase3_synthesis": {
          "status": "pending"
        }
      },
      "last_updated": "2025-12-03T10:30:00Z"
    }
  ],

  "summary": {
    "total": 50,
    "phase0_completed": 50,
    "phase1_completed": 45,
    "phase2_completed": 30,
    "phase2_in_progress": 5,
    "phase3_completed": 25,
    "failed": 2,
    "skipped": 3
  },

  "last_checkpoint": "2025-12-03T10:30:00Z"
}
```

### Data Access Patterns

```python
# CORRECT: enrichment_data.json is a LIST
data = json.load(open('data/enrichment_data.json'))  # List[Dict]
prop = next((p for p in data if p["full_address"] == address), None)

# WRONG: Will raise TypeError
prop = data[address]  # TypeError: list indices must be integers

# CORRECT: work_items.json is a dict
work = json.load(open('data/work_items.json'))  # Dict
item = next((w for w in work["work_items"] if w["address"] == address), None)
```

---
