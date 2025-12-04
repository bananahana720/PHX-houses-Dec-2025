# DETAILED BUY-BOX COVERAGE ANALYSIS

### Vision Dimension → Implementation Mapping

#### LOCATION (Vision: commute, safety/vibe, amenities, schools, growth, zoning, flood/heat risk)
| Factor | Captured | How | Gap |
|--------|----------|-----|-----|
| Commute | YES | Distance to highways + work address input | Not monetized in cost |
| Safety/Vibe | YES | Crime index (automated), manual assessment | Subjective component weak |
| Schools | YES | GreatSchools rating + distance | No trend/growth trajectory |
| Amenities | YES | Supermarket distance, parks/walkability | Limited to grocery + parks |
| Growth Risk | NO | Not modeled | Major gap |
| Zoning | NO | Not captured | Major gap |
| Flood Risk | YES | FEMA zone classification | Good coverage |
| Heat Risk | PARTIAL | Orientation scoring (N=25, W=0) | Not explicit cost impact |

#### CONDITION (Vision: roof/foundation/HVAC/plumbing/electrical, layout fit, "bones over cosmetics")
| Factor | Captured | How | Gap |
|--------|----------|-----|-----|
| Roof | YES | Age-based (new=45pts, old=0pts) | Condition not verified visually often |
| Foundation | NO | Not modeled | Major gap |
| HVAC | NO | Not explicitly scored | Implicit in age, AZ-specific life risk |
| Plumbing | YES | Year-built inference (recent=35pts) | Material type not distinguished |
| Electrical | YES | Year-built inference | Panel capacity not checked |
| Layout Fit | PARTIAL | Kitchen, master, laundry only | Open concept, flow missing |
| Bones over Cosmetics | YES | Strategy uses age/systems, not finishes | Philosophy clear |

#### CLIMATE (Vision: desert heat, power usage, outdoor living, low-water landscaping)
| Factor | Captured | How | Gap |
|--------|----------|-----|-----|
| Desert Heat | PARTIAL | Orientation (W-facing penalty) | Not explicit kWh modeling |
| Power Usage | IMPLICIT | Orientation affects cooling cost | No solar offset modeling |
| Outdoor Living | PARTIAL | Backyard utility (sqft) + pool | Patio quality, shade not scored |
| Low-Water Landscape | NO | Not modeled | Major gap (xeriscape preference) |

#### ECONOMICS (Vision: property tax, HOA, utilities, insurance, commute cost, new vs older stock)
| Factor | Captured | How | Gap |
|--------|----------|-----|-----|
| Property Tax | YES | 0.66% effective rate applied | Not differentiated by district/special levies |
| HOA | YES | Hard kill-switch (must be $0) | Solar lease modeled as cost not asset |
| Utilities | YES | $0.08/sqft + baseline, AZ-specific | No solar offset or pool impact adjustment |
| Insurance | YES | $6.50 per $1k value | Flood insurance requirement captured but cost not |
| Commute Cost | IMPLICIT | Distance captured, not $cost/day | Gap - affects affordability |
| New vs Older | YES | Year-built soft criterion (prefer pre-2024) | Newer homes not penalized much (2.0 severity) |

#### RESALE (Vision: energy efficiency, outdoor spaces, pools, patios, parking, storage)
| Factor | Captured | How | Gap |
|--------|----------|-----|-----|
| Energy Efficiency | IMPLICIT | Age/orientation proxy | No explicit EE rating (HERS, Energy Star) |
| Outdoor Spaces | PARTIAL | Backyard utility (sqft), pool condition | Patio/covered area quality missing |
| Pools | YES | Equipment condition (3-20pts), cost ($200-400/mo) | Pool as liability vs asset debate unresolved |
| Patios | NO | Not explicitly scored | Part of backyard, not disaggregated |
| Parking | PARTIAL | Garage in kill-switch (≥2 spaces hard fail if ≤1) | Street parking quality not scored |
| Storage | PARTIAL | Laundry area captures utility | General storage (attic, closets) not quantified |

---
