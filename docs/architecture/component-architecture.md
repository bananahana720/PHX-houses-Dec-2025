# Component Architecture

### Domain Layer (`src/phx_home_analysis/domain/`)

#### Entities

```python
@dataclass
class Property:
    """Central domain entity representing a property for analysis."""
    address: Address
    price: int | None = None
    beds: int | None = None
    baths: float | None = None
    sqft: int | None = None
    lot_sqft: int | None = None
    year_built: int | None = None
    garage_spaces: int | None = None
    has_pool: bool | None = None
    sewer_type: SewerType = SewerType.UNKNOWN
    orientation: Orientation = Orientation.UNKNOWN
    hoa_fee: int | None = None

    # Enriched fields
    school_rating: float | None = None
    crime_index: int | None = None
    walk_score: int | None = None
    flood_zone: FloodZone = FloodZone.UNKNOWN

    # Assessment fields
    kill_switch_verdict: KillSwitchVerdict | None = None
    score_breakdown: ScoreBreakdown | None = None
    tier: Tier | None = None

@dataclass(frozen=True)
class Address:
    """Immutable address value object."""
    street: str
    city: str
    state: str
    zip_code: str

    @property
    def full(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"

    @property
    def normalized(self) -> str:
        return self.full.lower().replace(",", "").replace(".", "")
```

#### Value Objects

```python
@dataclass(frozen=True)
class ScoreBreakdown:
    """Immutable scoring result container."""
    section_a: float  # Location & Environment (max 250)
    section_b: float  # Lot & Systems (max 175)
    section_c: float  # Interior & Features (max 180)

    @property
    def total(self) -> float:
        return self.section_a + self.section_b + self.section_c

    @property
    def percentage(self) -> float:
        return (self.total / 605) * 100

@dataclass(frozen=True)
class KillSwitchResult:
    """Result of kill-switch evaluation."""
    verdict: KillSwitchVerdict
    failed_criteria: list[str]
    details: dict[str, Any]
```

#### Enums

```python
class Tier(Enum):
    UNICORN = "unicorn"      # >484 pts (80% of 605)
    CONTENDER = "contender"  # 363-484 pts (60-80% of 605)
    PASS = "pass"            # <363 pts (<60% of 605)

class KillSwitchVerdict(Enum):
    PASS = "pass"       # All criteria satisfied
    FAIL = "fail"       # One or more HARD criteria failed
    WARNING = "warning" # Pass but with concerns (future use)

class SewerType(Enum):
    CITY = "city"
    SEPTIC = "septic"
    UNKNOWN = "unknown"

class Orientation(Enum):
    NORTH = "north"   # Best: 25 pts
    EAST = "east"     # Good: 18.75 pts
    SOUTH = "south"   # Moderate: 12.5 pts
    WEST = "west"     # Worst: 0 pts (high cooling costs)
    UNKNOWN = "unknown"

class FloodZone(Enum):
    X = "X"           # Minimal risk
    X_SHADED = "X500" # 500-year flood
    A = "A"           # 100-year flood (high risk)
    AE = "AE"         # 100-year with base elevation
    VE = "VE"         # Coastal high hazard
    UNKNOWN = "unknown"
```

### Service Layer (`src/phx_home_analysis/services/`)

#### Kill-Switch Service

```python
class KillSwitchFilter:
    """Orchestrates 5 HARD + 4 SOFT kill-switch criteria per PRD."""

    def __init__(self):
        self.hard_criteria = [
            HoaKillSwitch(),        # HOA must be $0
            SolarKillSwitch(),      # Solar must not be leased
            BedroomsKillSwitch(),   # Beds >= 4
            BathroomsKillSwitch(),  # Baths >= 2
            SqftKillSwitch(),       # Sqft > 1800
        ]

        self.soft_criteria = [
            SewerKillSwitch(),      # City sewer (severity: 2.5)
            YearKillSwitch(),       # Year <= 2023 (severity: 2.0)
            GarageKillSwitch(),     # >= 2 indoor spaces (severity: 1.5)
            LotSizeKillSwitch(),    # 7k-15k sqft (severity: 1.0)
        ]

    def evaluate(self, property: Property) -> KillSwitchResult:
        failed = []
        details = {}

        for criterion in self.criteria:
            result = criterion.evaluate(property)
            details[criterion.name] = result
            if not result.passed:
                failed.append(criterion.name)

        verdict = (
            KillSwitchVerdict.PASS if len(failed) == 0
            else KillSwitchVerdict.FAIL
        )

        return KillSwitchResult(
            verdict=verdict,
            failed_criteria=failed,
            details=details
        )

class HoaKillSwitch:
    """HOA must be exactly $0. PRD FR9: HARD criterion."""
    name = "hoa"

    def evaluate(self, property: Property) -> CriterionResult:
        if property.hoa_fee is None:
            # Assume no HOA if not specified
            return CriterionResult(passed=True, value=0, note="Assumed $0")

        passed = property.hoa_fee == 0
        return CriterionResult(
            passed=passed,
            value=property.hoa_fee,
            note="FAIL: HOA fee present" if not passed else "PASS"
        )

class SqftKillSwitch:
    """House SQFT must be >1800. PRD FR9: HARD criterion (NEW)."""
    name = "sqft"
    threshold = 1800

    def evaluate(self, property: Property) -> CriterionResult:
        if property.sqft is None:
            return CriterionResult(
                passed=False,
                value=None,
                note="FAIL: SQFT unknown"
            )

        passed = property.sqft > self.threshold
        return CriterionResult(
            passed=passed,
            value=property.sqft,
            note=f"{'PASS' if passed else 'FAIL'}: {property.sqft} sqft"
        )
```

#### Scoring Service

```python
class PropertyScorer:
    """Orchestrates 605-point scoring across 22 strategies."""

    def __init__(self, weights: ScoringWeights):
        self.weights = weights
        self.strategies = {
            # Section A: Location (250 pts)
            'school_district': SchoolDistrictScorer(),
            'quietness': QuietnessScorer(),
            'crime_index': CrimeIndexScorer(),
            'supermarket': SupermarketScorer(),
            'parks_walkability': ParksWalkabilityScorer(),
            'orientation': OrientationScorer(),
            'flood_risk': FloodRiskScorer(),
            'walk_transit': WalkTransitScorer(),
            'air_quality': AirQualityScorer(),

            # Section B: Systems (175 pts)
            'roof_condition': RoofConditionScorer(),
            'backyard_utility': BackyardUtilityScorer(),
            'plumbing_electrical': PlumbingElectricalScorer(),
            'pool_condition': PoolConditionScorer(),
            'cost_efficiency': CostEfficiencyScorer(),
            'solar_status': SolarStatusScorer(),

            # Section C: Interior (180 pts)
            'kitchen_layout': KitchenLayoutScorer(),
            'master_suite': MasterSuiteScorer(),
            'natural_light': NaturalLightScorer(),
            'high_ceilings': HighCeilingsScorer(),
            'fireplace': FireplaceScorer(),
            'laundry_area': LaundryAreaScorer(),
            'aesthetics': AestheticsScorer(),
        }

    def score(self, property: Property) -> ScoreBreakdown:
        section_a = self._score_section_a(property)
        section_b = self._score_section_b(property)
        section_c = self._score_section_c(property)

        return ScoreBreakdown(
            section_a=section_a,
            section_b=section_b,
            section_c=section_c
        )

    def _apply_strategy(self, name: str, property: Property) -> float:
        """Apply strategy and scale by weight."""
        strategy = self.strategies[name]
        raw_score = strategy.score(property)  # 0-10 scale
        weight = getattr(self.weights, name)
        return raw_score * (weight / 10)
```

### Repository Layer

```python
class JsonEnrichmentRepository:
    """Repository for enrichment_data.json (LIST format)."""

    def __init__(self, path: Path):
        self.path = path

    def load_all(self) -> list[dict]:
        """Load all properties. Returns LIST of dicts."""
        if not self.path.exists():
            return []
        with open(self.path) as f:
            return json.load(f)  # LIST!

    def find_by_address(self, address: str) -> dict | None:
        """Find property by address. O(n) lookup."""
        data = self.load_all()
        normalized = self._normalize(address)
        return next(
            (p for p in data if self._normalize(p["full_address"]) == normalized),
            None
        )

    def save_all(self, data: list[dict]) -> None:
        """Atomic save with backup."""
        backup_path = self.path.with_suffix('.json.bak')
        if self.path.exists():
            shutil.copy(self.path, backup_path)

        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)
```

### Pipeline Layer

```python
class AnalysisPipeline:
    """Main orchestrator for property analysis workflow."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        enrichment_repo: EnrichmentRepository,
        kill_switch_filter: KillSwitchFilter,
        scorer: PropertyScorer,
        tier_classifier: TierClassifier
    ):
        self.property_repo = property_repo
        self.enrichment_repo = enrichment_repo
        self.kill_switch_filter = kill_switch_filter
        self.scorer = scorer
        self.tier_classifier = tier_classifier

    def run(self) -> PipelineResult:
        """Execute complete pipeline."""

        # Phase 1: Load properties from CSV
        properties = self.property_repo.load_all()

        # Phase 2: Merge with enrichment data
        enrichment_data = self.enrichment_repo.load_all()
        properties = self._merge_enrichment(properties, enrichment_data)

        # Phase 3: Kill-switch filtering
        passed_properties = []
        failed_properties = []

        for prop in properties:
            result = self.kill_switch_filter.evaluate(prop)
            prop.kill_switch_verdict = result.verdict

            if result.verdict == KillSwitchVerdict.PASS:
                passed_properties.append(prop)
            else:
                failed_properties.append(prop)

        # Phase 4: Score passed properties
        for prop in passed_properties:
            prop.score_breakdown = self.scorer.score(prop)

        # Phase 5: Classify into tiers
        for prop in passed_properties:
            prop.tier = self.tier_classifier.classify(prop.score_breakdown.total)

        return PipelineResult(
            all_properties=properties,
            passed=passed_properties,
            failed=failed_properties,
            unicorns=[p for p in passed_properties if p.tier == Tier.UNICORN],
            contenders=[p for p in passed_properties if p.tier == Tier.CONTENDER],
            passes=[p for p in passed_properties if p.tier == Tier.PASS]
        )
```

---
