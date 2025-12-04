# DIAGRAM 7: DATA STRUCTURE RELATIONSHIPS

```
                   DATA FLOW & RELATIONSHIPS

              ┌──────────────────────────────┐
              │ phx_homes.csv (read-only)    │
              │ - street, city, zip, price   │
              │ - beds, baths, sqft          │
              └────────────┬──────────────────┘
                           │
                           │ Load via property-data skill
                           │
                           ▼
              ┌──────────────────────────────┐
              │ enrichment_data.json (LIST)  │
              │ - PRIMARY DATA STORE         │
              │                              │
              │ Phase 0 fields:              │
              │  lot_sqft, year_built        │
              │  garage_spaces               │
              │                              │
              │ Phase 1 fields:              │
              │  price, hoa_fee              │
              │  school_rating, orientation │
              │  safety_score               │
              │                              │
              │ Phase 2 fields:              │
              │  interior_total             │
              │  exterior_total             │
              │                              │
              │ Phase 3 fields:              │
              │  total_score, tier          │
              │  kill_switch_passed         │
              └───┬──────────┬──────────┬────┘
                  │          │          │
         ┌────────┘          │          └────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │ work_items   │  │ address_     │  │ extraction_  │
   │ .json        │  │ folder_      │  │ state.json   │
   │              │  │ lookup.json  │  │              │
   │ Progress     │  │              │  │ Image meta   │
   │ tracking     │  │ Maps addr→   │  │ Image status │
   │ Phase status │  │ image folder │  │ Run history  │
   │              │  │              │  │              │
   └──────────────┘  └──────────────┘  └──────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
         ┌──────────────────────────────────┐
         │ phx_homes_ranked.csv (output)    │
         │ - All enrichment fields          │
         │ - Final scores and tier          │
         │ - Kill-switch verdict            │
         └──────────────────────────────────┘

CONSISTENCY RULES:
- enrichment_data.json is source of truth
- work_items.json tracks progress only
- address_folder_lookup.json is derived from Phase 1
- extraction_state.json is transient (can be regenerated)

═════════════════════════════════════════════════════════════
KEY: Use Read tool to load, property-data skill to manipulate
═════════════════════════════════════════════════════════════
```

---
