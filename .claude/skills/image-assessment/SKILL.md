---
name: image-assessment
description: Visually analyze property photos to score interior quality (kitchen, master, light, ceilings, fireplace, laundry, aesthetics). Use for Phase 2 image assessment, Section C scoring (190 pts), or condition evaluation.
allowed-tools: Read, Bash(python:*)
---

# Image Assessment Skill

Expert at visual analysis of property photos for interior quality scoring and condition assessment.

## Section C Scoring (190 pts max)

| Category | Max | Multiplier | Visual Indicators |
|----------|-----|------------|-------------------|
| Kitchen | 40 | 4x | Layout, counters, appliances, cabinets |
| Master Suite | 40 | 4x | Size, closet, en-suite, windows |
| Natural Light | 30 | 3x | Window count, skylights, brightness |
| High Ceilings | 30 | 3x | Height, vaulted, coffered |
| Fireplace | 20 | 2x | Presence, type, condition |
| Laundry | 20 | 2x | Dedicated room, hookups, storage |
| Aesthetics | 10 | 1x | Overall appeal, updates, style |

## Structured Vision Analysis Protocol

For EACH image analyzed, follow this 5-step chain-of-thought process:

### Step 1: Observation (Facts Only)
List concrete visual facts without interpretation:
- Objects present (appliances, fixtures, furniture)
- Materials visible (granite, laminate, tile, carpet)
- Colors and finishes
- Apparent dimensions (relative to known objects)
- Light quality (natural vs artificial, brightness)

**Example:**
```
Observation: Kitchen photo shows white shaker cabinets, dark countertops (appears granite), stainless steel appliances including French door refrigerator, gas range, and dishwasher. Island with seating for 3. Single pendant light over island. Windows above sink, natural light visible.
```

### Step 2: Era Contextualization
Compare against era-appropriate expectations based on year_built:

| Era | Baseline Expectation |
|-----|---------------------|
| Pre-1980 | Small kitchens, oak cabinets, tile counters, 8ft ceilings |
| 1980-1999 | Larger kitchens, raised panels, Corian/laminate, some vaulted |
| 2000-2010 | Open floor plans, granite standard, 9ft ceilings common |
| 2010+ | Full open concept, quartz/waterfall islands, 10ft+ ceilings |

**Example:**
```
Era Context: Built 1995. Kitchen exceeds era expectations - clearly renovated with modern finishes (granite, stainless) vs expected laminate/white appliances. This suggests intentional upgrade.
```

### Step 3: Condition Assessment
Note specific wear, damage, updates:
- Signs of wear (scratches, stains, fading)
- Damage indicators (water stains, cracks, warping)
- Update evidence (mismatched fixtures, partial renovations)
- Maintenance level (cleanliness, repair state)

**Example:**
```
Condition: Cabinet doors show minor wear at handles. Countertops in good condition, no chips visible. Appliances appear 3-5 years old based on style. Floor grout shows some discoloration. Overall: Well-maintained, normal wear for age.
```

### Step 4: Preliminary Score with Reasoning
Assign initial score with explicit reasoning:
```
Preliminary Score: 8/10
Reasoning:
- Layout: Open with island (+2 above baseline)
- Counters: Granite upgrade for era (+1)
- Appliances: Modern stainless, good brands (+1)
- Storage: Ample cabinets (+0, meets expectations)
- Deductions: Some wear (-1 from potential 9)
```

### Step 5: Final Score with Confidence
Finalize score and assess confidence:
```
Final Score: 8/10
Confidence: HIGH
Confidence Reasoning: Clear photos from 3 angles, all major features visible, good lighting
```

### Applying the Protocol

**Before starting:**
1. Load year_built from enrichment data for era context
2. Check how many photos available for each room
3. Note any missing room types

**During analysis:**
- Complete all 5 steps for each major room
- Reference specific photos by filename
- Cross-reference observations across multiple photos of same room

**Output integration:**
```json
{
  "category": "kitchen_layout",
  "raw_score": 8,
  "observations": ["white shaker cabinets", "granite counters", "island with seating"],
  "era_context": "Exceeds 1995 expectations, clearly renovated",
  "condition_notes": "Minor handle wear, grout discoloration",
  "confidence": "high",
  "photos_used": ["photo_003.png", "photo_004.png", "photo_005.png"]
}
```

## Image Reading

Use the Read tool to view property images:

```
Read: data/property_images/processed/{hash}/photo_001.png
```

The Read tool displays images for visual analysis.

## Finding Images

### Address Folder Lookup (CRITICAL)

```python
import json

# ALWAYS use this to find correct image folder
lookup = json.load(open("data/property_images/metadata/address_folder_lookup.json"))
mapping = lookup.get("mappings", {}).get(target_address)

if mapping:
    folder = mapping["path"]  # e.g., "data/property_images/processed/3e28ac5f/"
    count = mapping["image_count"]
else:
    # Fallback: calculate hash (may differ from actual!)
    import hashlib
    hash = hashlib.md5(target_address.lower().encode()).hexdigest()[:8]
    folder = f"data/property_images/processed/{hash}/"
```

### List Available Images

```bash
ls data/property_images/processed/{hash}/
# photo_001.png, photo_002.png, ..., satellite_view.png
```

## Scoring Rubrics

### Kitchen Layout (1-10)

| Score | Indicators |
|-------|------------|
| 9-10 | Open concept, quartz/granite counters, stainless appliances, ample storage, island |
| 7-8 | Modern layout, good counters, updated appliances, decent storage |
| 5-6 | Functional but dated, laminate counters, older appliances |
| 3-4 | Galley layout, very dated, limited storage |
| 1-2 | Major renovation needed, non-functional |

**Look For:**
- Layout type: galley, L-shape, U-shape, open concept
- Counter material: laminate, tile, granite, quartz
- Appliances: age, finish (stainless vs white), brand
- Cabinets: condition, storage capacity, soft-close
- Island or breakfast bar presence

### Master Suite (1-10)

| Score | Indicators |
|-------|------------|
| 9-10 | Large room, walk-in closet, luxury en-suite with dual vanity |
| 7-8 | Good size, adequate closet, updated bathroom |
| 5-6 | Average size, basic closet, standard bath |
| 3-4 | Small room, minimal closet |
| 1-2 | Cramped, no en-suite or walk-in |

**Look For:**
- Room proportions relative to furniture
- Closet type: walk-in, reach-in, size
- En-suite bathroom quality
- Natural light from windows
- Flooring condition

### Natural Light (1-10)

| Score | Indicators |
|-------|------------|
| 9-10 | Many large windows, skylights, glass doors, bright throughout |
| 7-8 | Good window count, bright main rooms |
| 5-6 | Average lighting, some dark areas |
| 3-4 | Limited windows, darker rooms |
| 1-2 | Very poor natural light, basement-like |

**Look For:**
- Number and size of windows
- Skylights or solar tubes
- Sliding glass doors
- Light flow between rooms

### High Ceilings (1-10)

| Score | Indicators |
|-------|------------|
| 9-10 | 10ft+ or vaulted/cathedral ceilings |
| 7-8 | 9ft ceilings throughout |
| 5-6 | Standard 8ft ceilings |
| 3-4 | Low ceilings, some cramped areas |
| 1-2 | Very low ceilings (<8ft) |

**Visual Cues:**
- Door height relative to room
- Ceiling fans (indicate higher ceilings)
- Crown molding height
- Vaulted in great room

### Fireplace (1-10)

| Score | Indicators |
|-------|------------|
| 9-10 | Gas fireplace, modern styling, focal point |
| 7-8 | Wood-burning, well-maintained surround |
| 5-6 | Decorative or older gas unit |
| 3-4 | Non-functional or very dated |
| 0 | No fireplace present |

### Laundry Area (1-10)

| Score | Indicators |
|-------|------------|
| 9-10 | Dedicated laundry room with storage, sink |
| 7-8 | Good-sized laundry area, shelving |
| 5-6 | Hallway laundry, adequate space |
| 3-4 | Garage laundry or cramped |
| 1-2 | No dedicated space, poor setup |

### Aesthetics (1-10)

| Score | Indicators |
|-------|------------|
| 9-10 | Modern, move-in ready, designer touches |
| 7-8 | Clean, neutral, recently updated |
| 5-6 | Average, some dated elements |
| 3-4 | Dated 80s/90s style throughout |
| 1-2 | Major cosmetic work needed |

**Consider:**
- Overall style cohesion
- Paint colors (neutral vs bold)
- Flooring consistency
- Update recency

## Era-Based Visual Calibration Anchors

Use these visual anchors to calibrate scores by construction era:

### Pre-1980 Properties

**Kitchen Baseline (5-6/10):**
- Small galley or L-shape layout
- Oak or painted wood cabinets
- Tile or laminate counters
- White or almond appliances
- Limited counter space

**Pre-1980 Scoring Adjustments:**
| If you see... | Adjustment |
|--------------|------------|
| Original cabinets, functional | +0 (expected) |
| Updated counters only | +1 |
| Full renovation (modern finishes) | +2-3 |
| Severe wear/damage | -1-2 |

**Master Suite Baseline (4-5/10):**
- Smaller room (11x12 typical)
- Reach-in closet
- Basic en-suite or shared bath
- Single window

### 1980-1999 Properties

**Kitchen Baseline (5-6/10):**
- L-shape or U-shape common
- Raised panel oak or white cabinets
- Corian, laminate, or tile counters
- Mix of white/black appliances
- Breakfast bar possible

**1980-1999 Scoring Adjustments:**
| If you see... | Adjustment |
|--------------|------------|
| Oak cabinets, Corian counters | +0 (expected) |
| Granite upgrade | +1 |
| Full stainless appliance suite | +1 |
| Modern renovation | +2-3 |
| Dated brass fixtures | -0.5 |

**Master Suite Baseline (5-6/10):**
- Moderate size (12x14 typical)
- Walk-in closet emerging
- En-suite bath standard
- Some vaulted ceilings

### 2000+ Properties

**Kitchen Baseline (6-7/10):**
- Open floor plan to living
- 42" cabinets standard
- Granite/solid surface counters
- Stainless appliances expected
- Island common

**2000+ Scoring Adjustments:**
| If you see... | Adjustment |
|--------------|------------|
| Granite, stainless, island | +0 (expected) |
| Quartz, waterfall edge | +1 |
| Smart appliances, pot filler | +1-2 |
| Builder-grade finishes | -1 |
| Outdated by 2000s standards | -2 |

**Master Suite Baseline (6-7/10):**
- Large room (14x16+)
- Walk-in closet required
- Dual vanity en-suite
- 9ft ceilings standard

### Visual Reference Examples

**Kitchen Score 3/10 (Any Era):**
- Cramped layout
- Damaged or missing cabinets
- Worn/stained counters
- Non-functional appliances
- Major renovation needed

**Kitchen Score 5/10 (Era-Appropriate):**
- Functional layout
- Cabinets in fair condition
- Counters match era expectation
- Working appliances
- Usable as-is

**Kitchen Score 7/10 (Above Era):**
- Good layout with some upgrades
- Cabinets updated or refinished
- Counters upgraded from era baseline
- Modern appliances
- Move-in ready

**Kitchen Score 9/10 (Exceptional):**
- Open concept, large island
- Custom or high-end cabinets
- Premium counters (quartz, quartzite)
- Professional-grade appliances
- Designer details

## Few-Shot Scoring Examples

### Aesthetics Category (1-10)

**Example 1: Score 3/10**
```
Photo Observations:
- Floral wallpaper throughout (1980s pattern)
- Brass light fixtures, door hardware
- Pink tile bathroom with brass accents
- Oak parquet flooring, worn finish
- Popcorn ceilings visible

Era Context: Built 1987, original finishes
Condition: Maintained but severely dated
Score Reasoning: All finishes original to era, no updates. Cohesive but dated. Would require $30k+ in cosmetic updates.
Confidence: High (multiple rooms clearly photographed)
```

**Example 2: Score 5/10**
```
Photo Observations:
- Neutral beige paint throughout
- Mix of updated (kitchen) and dated (baths) areas
- Tile flooring in common areas, carpet in bedrooms
- Standard builder fixtures
- Flat ceilings, white trim

Era Context: Built 2003, partial updates
Condition: Clean, normal wear, inconsistent updates
Score Reasoning: Neutral canvas, nothing offensive but nothing impressive. Partial updates create some inconsistency. Move-in ready for non-picky buyer.
Confidence: Medium (some rooms not photographed)
```

**Example 3: Score 8/10**
```
Photo Observations:
- Gray-on-gray modern palette
- Consistent LVP flooring throughout
- Updated lighting (recessed + modern pendants)
- Fresh paint, clean lines
- Coordinated fixtures (matte black or brushed nickel)

Era Context: Built 1998, recently renovated
Condition: Excellent, recently completed renovation
Score Reasoning: Cohesive modern update. On-trend finishes that appeal to broad buyer base. Move-in ready with no immediate cosmetic needs.
Confidence: High (professional photos, all rooms shown)
```

### Master Suite Category (1-10)

**Example 1: Score 4/10**
```
Photo Observations:
- Room fits queen bed with nightstands, tight clearance
- Single window, north-facing (good for AZ)
- Reach-in closet, basic bifold doors
- No en-suite visible (shared bath)
- Carpet shows wear patterns

Era Context: Built 1978, pre-master suite era
Condition: Original, functional but dated
Score Reasoning: Below modern expectations for master. No en-suite is significant drawback. Closet space inadequate. Acceptable for era but limits appeal.
Confidence: High (room fully visible in photos)
```

**Example 2: Score 6/10**
```
Photo Observations:
- Queen bed with desk fits comfortably
- Walk-in closet visible (moderate size)
- En-suite with single vanity, tub/shower combo
- Two windows, good natural light
- Carpet in good condition

Era Context: Built 1995, standard for era
Condition: Good, minor updates (paint, carpet)
Score Reasoning: Meets basic expectations. Walk-in and en-suite are minimum requirements. Nothing exceptional but functional. Average suburban master.
Confidence: Medium (closet interior not shown)
```

**Example 3: Score 9/10**
```
Photo Observations:
- King bed centered with ample clearance all sides
- Vaulted ceiling with ceiling fan
- Large walk-in closet with built-in organizers
- En-suite with dual vanity, separate tub/shower, water closet
- Wall of windows, abundant natural light
- Sitting area near windows

Era Context: Built 2008, expected quality for price point
Condition: Excellent, move-in ready
Score Reasoning: Exceeds expectations even for era. True retreat space with sitting area. Spa-like bathroom. Storage exceeds typical needs. Aspirational space.
Confidence: High (multiple photos, all features visible)
```

## Condition Issues to Flag

### High Priority (Deduct Points)

- Water damage (stains, warping, bubbling)
- Cracked walls or ceilings
- Outdated electrical (visible knob-and-tube)
- Foundation cracks visible
- Mold or mildew
- Significant wear patterns

### Medium Priority (Note)

- Dated finishes (popcorn ceilings, brass fixtures)
- Worn carpet
- Peeling paint
- Deferred maintenance signs

### Positive Features (Add Points)

- Recent renovation evident
- High-end appliances
- Custom built-ins
- Premium flooring (hardwood, large tile)
- Smart home features

## Roof/Exterior Age Estimation

### From Aerial/Exterior Photos

| Indicator | Age Estimate |
|-----------|--------------|
| Uniform tile color, crisp edges | 0-5 years |
| Slight fading, minimal wear | 5-15 years |
| Noticeable fading, some discoloration | 15-25 years |
| Significant wear, missing pieces, moss | 25+ years |

### If No Roof Images

Create research task:

```python
task = {
    "property_address": address,
    "field": "roof_age",
    "reason": "no_roof_images",
    "fallback_command": f'python scripts/estimate_ages.py --property "{address}"'
}
# Add to data/research_tasks.json
```

## Context-Aware Scoring

### Use County Data

```python
# Calibrate expectations based on year_built
year_built = enrichment.get("year_built")

if year_built and year_built < 1980:
    # Pre-1980s: lower aesthetics baseline
    # 5-6 is "normal" for era
    era_note = "Pre-1980s construction - dated finishes expected"
elif year_built and year_built < 2000:
    era_note = "1980s-1990s era - common dated elements"
else:
    era_note = "2000s+ modern construction"
```

### Pool Assessment

```python
if enrichment.get("has_pool"):
    # Look for pool equipment in photos
    # Estimate equipment age from condition
    # Score 1-10 based on equipment/decking condition
```

## Output Format

```json
{
  "address": "123 Main St, Phoenix, AZ 85001",
  "status": "success|partial|failed",
  "scores": {
    "kitchen_layout": 7,
    "master_suite": 8,
    "natural_light": 6,
    "high_ceilings": 5,
    "fireplace": 8,
    "laundry_area": 6,
    "aesthetics": 7
  },
  "total_interior_score": 128,
  "max_possible": 190,
  "confidence": "high|medium|low",
  "condition_issues": [
    {"severity": "high", "issue": "Water stain on ceiling", "location": "bedroom_2"},
    {"severity": "medium", "issue": "Carpet wear", "location": "hallway"}
  ],
  "positive_features": [
    "Updated kitchen with granite counters",
    "Vaulted ceilings in living room"
  ],
  "photos_analyzed": 12,
  "photos_missing": ["garage_interior", "backyard"],
  "overall_assessment": "Well-maintained 1990s home with updated kitchen...",
  "files_updated": ["enrichment_data.json"]
}
```

## Confidence Scoring Standard

Assign ONE overall confidence level per property assessment:

### High Confidence
**Criteria (ALL must be true):**
- Photos available for 6+ of 7 scoring categories
- Photo quality good (not blurry, well-lit)
- Multiple angles for major rooms (kitchen, master)
- Year built known (for era calibration)
- No heavy staging obscuring features

**Implications:**
- Scores reliable for tier assignment
- Can proceed to final scoring without flags
- Deal sheet presents scores without caveats

### Medium Confidence
**Criteria (ANY applies):**
- Photos available for 4-5 of 7 categories
- Some rooms only single photo
- Minor quality issues (dim lighting, wide angles)
- Heavy staging in some rooms
- One critical category unclear (kitchen OR master)

**Implications:**
- Scores directionally accurate
- Flag uncertain categories in output
- Deal sheet notes: "Some scores estimated from limited photos"

### Low Confidence
**Criteria (ANY applies):**
- Photos available for <4 categories
- Poor photo quality throughout
- Professional staging obscures all surfaces
- Critical categories missing (no kitchen OR no master)
- Cannot determine year_built for era calibration

**Implications:**
- Scores unreliable for tier assignment
- Flag property for in-person verification
- Deal sheet notes: "Visual assessment incomplete - verify in person"
- Consider scoring as 5.0 (neutral) for missing categories

### Confidence Output Format
```json
{
  "overall_confidence": "medium",
  "confidence_reasoning": "Kitchen well-documented (5 photos), master has only exterior door shot, no closet/bath visible",
  "categories_high_confidence": ["kitchen_layout", "natural_light", "aesthetics"],
  "categories_low_confidence": ["master_suite", "laundry_area"],
  "missing_categories": ["high_ceilings"],
  "recommendation": "In-person verification recommended for master suite scoring"
}
```

### Confidence Impact on Scoring
When confidence is LOW for a category:
1. Use default 5.0 score for missing categories
2. Document reason: "Score 5.0 assigned - no photos available"
3. Flag for research: Add to research_tasks.json
4. Do NOT let low-confidence scores drag down otherwise strong properties

## Best Practices

1. **Check folder lookup first** - Address hash may differ from calculated
2. **View all images** - Don't rely on first few
3. **Note missing rooms** - Flag what's not photographed
4. **Watch for staging** - Heavy staging may hide issues
5. **Use year_built context** - Calibrate expectations by era
6. **Create research tasks** - For missing roof/HVAC/pool ages
