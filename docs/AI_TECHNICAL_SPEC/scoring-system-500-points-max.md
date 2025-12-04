# SCORING SYSTEM (500 POINTS MAX)

### Section A: Location & Environment (150 points max)

| Factor | Weight | Scoring Function |
|--------|--------|------------------|
| School District | 5 | `school_rating` directly (1-10 scale) |
| Quietness | 5 | `>2mi: 10, 1-2mi: 7, 0.5-1mi: 5, <0.5mi: 3` |
| Safety | 5 | Default 5.0 (manual assessment) |
| Supermarket | 4 | `<=1mi: 10, 1-2mi: 8, 2-3mi: 6, >3mi: 4` |
| Walkability | 3 | Default 5.0 (manual assessment) |
| Orientation | 3 | `N:10, S:9, NE/NW:8, E:7, SE:6, SW:5, W:3` |

**Formula**: `sum(weight * score)` where score is 0-10

### Section B: Lot & Systems (160 points max)

| Factor | Weight | Scoring Function |
|--------|--------|------------------|
| Roof | 5 | `<=5yr: 10, 5-10yr: 8, 10-15yr: 6, 15-20yr: 4, >20yr: 2` |
| Backyard | 4 | `estimated_backyard = lot_sqft - (sqft * 0.6)`, then `>5000: 10, 3000-5000: 7, 1500-3000: 5, <1500: 3` |
| Plumbing/Elec | 4 | `>=2000: 9, 1990-1999: 7, 1980-1989: 5, <1980: 4` |
| Pool | 3 | If no pool: 5. If pool: `equip <=3yr: 9, 3-7yr: 7, >7yr: 4` |

### Section C: Interior & Features (190 points max)

| Factor | Weight | Default |
|--------|--------|---------|
| Kitchen | 4 | 5.0 (visual inspection) |
| Master Suite | 4 | 5.0 (visual inspection) |
| Natural Light | 3 | 5.0 (visual inspection) |
| High Ceilings | 3 | 5.0 (visual inspection) |
| Fireplace | 2 | 5.0 (check photos) |
| Laundry | 2 | 5.0 (check photos) |
| Aesthetics | 1 | 5.0 (subjective) |

### Tier Classification

- **Unicorn**: `total_score > 400`
- **Contender**: `300 <= total_score <= 400`
- **Pass**: `total_score < 300`

---
