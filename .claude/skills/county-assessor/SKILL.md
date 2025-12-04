---
name: county-assessor
description: Extract authoritative property data from Maricopa County Assessor API including lot size, year built, garage spaces, pool, and valuations. Requires MARICOPA_ASSESSOR_TOKEN. Use for Phase 0 data collection, verifying listing claims, or obtaining kill-switch field values (lot, year, garage).
allowed-tools: Read, Bash(python:*), WebFetch
---

# Maricopa County Assessor API Skill

Extract authoritative property data from Maricopa County Assessor's office.

## Environment Setup

**Required:** `MARICOPA_ASSESSOR_TOKEN` environment variable

## CLI Usage

```bash
# Single property
python scripts/extract_county_data.py --address "123 Main St, Phoenix, AZ 85001"

# All properties
python scripts/extract_county_data.py --all

# Only update missing fields
python scripts/extract_county_data.py --all --update-only

# Preview without saving
python scripts/extract_county_data.py --all --dry-run
```

## Fields Retrieved

| Field | API Source | Notes |
|-------|-----------|-------|
| `lot_sqft` | LotSize | **Kill-switch** (7k-15k) |
| `year_built` | ConstructionYear | **Kill-switch** (<2024) |
| `garage_spaces` | NumberOfGarages | **Kill-switch** (2+) |
| `has_pool` | Pool sqft | Truthy = has pool |
| `livable_sqft` | LivableSpace | Interior sqft |
| `baths` | BathFixtures / 3 | Estimated |
| `roof_type` | RoofType | Tile, shingle, etc. |

## Fields NOT Available

| Field | Where to Get |
|-------|-------------|
| `sewer_type` | City GIS manual lookup |
| `beds` | Listing sites |
| `hoa_fee` | Listing sites |

## Error Handling

| Error | Action |
|-------|--------|
| Token missing | Skip, mark "skipped" |
| Parcel not found | Log warning, continue |
| API timeout | Retry once |
| Rate limit (429) | Wait 60s, retry |

## Reference Files

| File | Content |
|------|---------|
| `api-reference.md` | API structure, code examples, Phase 0 integration |

**Load detail:** `Read .claude/skills/county-assessor/api-reference.md`

## Best Practices

1. Run early (Phase 0) - authoritative data
2. Check token - fail gracefully if not set
3. Use `--update-only` to preserve manual data
4. Track source with `_county_data_source` field
5. Early kill-switch check before expensive phases
