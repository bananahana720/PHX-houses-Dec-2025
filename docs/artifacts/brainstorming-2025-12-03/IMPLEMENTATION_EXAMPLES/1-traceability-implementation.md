# 1. TRACEABILITY IMPLEMENTATION

### 1.1 Add Field-Level Metadata to enrichment_data.json

#### Before (Current):
```json
{
  "full_address": "123 Main St",
  "lot_sqft": 9387,
  "year_built": 1983,
  "_last_updated": "2025-12-03T03:24:41"
}
```

#### After (With Provenance):
```json
{
  "_schema_version": "2.0.0",
  "full_address": "123 Main St",
  "lot_sqft": {
    "value": 9387,
    "source": "maricopa_assessor_api",
    "phase": "phase0_county",
    "confidence": 0.95,
    "extracted_at": "2025-12-03T03:24:56",
    "validated_by": "extract_county_data.py",
    "lineage_id": "phase0_county_run_20251203_abc123"
  },
  "year_built": {
    "value": 1983,
    "source": "maricopa_assessor_api",
    "phase": "phase0_county",
    "confidence": 0.95,
    "extracted_at": "2025-12-03T03:24:56",
    "validated_by": "extract_county_data.py"
  },
  "orientation": {
    "value": "south",
    "source": "satellite_visual_estimate",
    "phase": "phase1_map",
    "confidence": 0.65,
    "extracted_at": "2025-12-03T05:30:00",
    "validated_by": "map-analyzer",
    "notes": "Medium confidence - satellite imagery only"
  },
  "_metadata": {
    "last_modified": "2025-12-03T05:30:00",
    "last_modified_by": "map-analyzer",
    "modification_count": 3,
    "lineage_chain": [
      "phase0_county_run_20251203_abc123",
      "phase1_map_run_20251203_def456"
    ]
  }
}
```

#### Python Implementation:

```python
# src/phx_home_analysis/domain/value_objects.py

@dataclass
class FieldMetadata:
    """Metadata for a single enriched field."""
    value: Any
    source: str  # "maricopa_assessor_api", "zillow_scrape", "satellite_visual", "manual"
    phase: str   # "phase0_county", "phase1_map", "phase2_images", etc.
    confidence: float  # 0.0 - 1.0
    extracted_at: datetime
    validated_by: str  # Script name or agent name
    notes: str | None = None
    lineage_id: str | None = None  # Link to extraction run

    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.80

    def is_medium_confidence(self) -> bool:
        return 0.60 <= self.confidence < 0.80

    def is_low_confidence(self) -> bool:
        return self.confidence < 0.60

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "source": self.source,
            "phase": self.phase,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat(),
            "validated_by": self.validated_by,
            "notes": self.notes,
            "lineage_id": self.lineage_id
        }


# Enhanced EnrichmentData class
@dataclass
class EnrichmentDataWithMetadata:
    """Property enrichment with field-level provenance tracking."""
    full_address: str

    # Instead of: lot_sqft: int | None
    # Do: lot_sqft: FieldMetadata | int | None (backward compatible)

    _fields_metadata: dict[str, FieldMetadata] = field(default_factory=dict)
    _last_modified: datetime | None = None
    _last_modified_by: str | None = None

    def set_field_with_metadata(
        self,
        field_name: str,
        value: Any,
        source: str,
        phase: str,
        confidence: float,
        validated_by: str,
        notes: str | None = None
    ) -> None:
        """Set a field with full provenance metadata."""
        metadata = FieldMetadata(
            value=value,
            source=source,
            phase=phase,
            confidence=confidence,
            extracted_at=datetime.now(timezone.utc),
            validated_by=validated_by,
            notes=notes
        )
        self._fields_metadata[field_name] = metadata
        setattr(self, field_name, value)
        self._last_modified = datetime.now(timezone.utc)
        self._last_modified_by = validated_by

    def get_field_metadata(self, field_name: str) -> FieldMetadata | None:
        """Retrieve metadata for a field."""
        return self._fields_metadata.get(field_name)

    def get_high_confidence_fields(self) -> list[str]:
        """List all fields with high confidence."""
        return [
            field for field, metadata in self._fields_metadata.items()
            if metadata.is_high_confidence()
        ]

    def to_dict_with_metadata(self) -> dict:
        """Serialize including metadata."""
        result = {"_schema_version": "2.0.0", "full_address": self.full_address}

        # Add each field with metadata
        for field_name, metadata in self._fields_metadata.items():
            result[field_name] = metadata.to_dict()

        # Add fields without explicit metadata (backward compatibility)
        for field_name in self.__dataclass_fields__:
            if field_name not in result and field_name != "_fields_metadata":
                value = getattr(self, field_name, None)
                if value is not None:
                    result[field_name] = value

        result["_metadata"] = {
            "last_modified": self._last_modified.isoformat() if self._last_modified else None,
            "last_modified_by": self._last_modified_by
        }
        return result
```

### 1.2 Create Scoring Lineage Capture

```python
# src/phx_home_analysis/services/scoring/lineage.py

@dataclass
class ScoringStrategyResult:
    """Result from a single scoring strategy."""
    strategy_name: str
    phase: str
    points_awarded: float
    max_possible: float
    input_fields: dict[str, Any]
    reasoning: str
    notes: str | None = None

    @property
    def percent_of_max(self) -> float:
        return (self.points_awarded / self.max_possible * 100) if self.max_possible > 0 else 0


@dataclass
class SectionScoringLineage:
    """Scoring lineage for one section (Location, Systems, Interior)."""
    section_name: str
    total_points: float
    max_possible: float
    strategies: list[ScoringStrategyResult]

    def to_dict(self) -> dict:
        return {
            "section": self.section_name,
            "total": self.total_points,
            "max_possible": self.max_possible,
            "percentage": self.total_points / self.max_possible * 100,
            "strategies": [
                {
                    "name": s.strategy_name,
                    "phase": s.phase,
                    "points": s.points_awarded,
                    "max": s.max_possible,
                    "percent": s.percent_of_max,
                    "reasoning": s.reasoning,
                    "inputs": s.input_fields,
                    "notes": s.notes
                }
                for s in self.strategies
            ]
        }


@dataclass
class CompleteScoringLineage:
    """Complete scoring lineage for a property."""
    property_address: str
    scoring_run_id: str
    scored_at: datetime
    sections: list[SectionScoringLineage]
    total_score: float
    max_possible: float
    tier: str

    def to_dict(self) -> dict:
        return {
            "address": self.property_address,
            "run_id": self.scoring_run_id,
            "scored_at": self.scored_at.isoformat(),
            "sections": [s.to_dict() for s in self.sections],
            "total_score": self.total_score,
            "max_possible": self.max_possible,
            "tier": self.tier
        }


# Modified PropertyScorer to capture lineage
class ExplainablePropertyScorer(PropertyScorer):
    """PropertyScorer that tracks scoring lineage."""

    def score(self, property: Property) -> tuple[float, CompleteScoringLineage]:
        """Score property and return lineage explaining the score."""
        import uuid
        from datetime import datetime, timezone

        run_id = str(uuid.uuid4())
        sections_lineage = []

        # Score each section
        location_lineage = self._score_section_location(property, run_id)
        systems_lineage = self._score_section_systems(property, run_id)
        interior_lineage = self._score_section_interior(property, run_id)

        sections_lineage = [location_lineage, systems_lineage, interior_lineage]

        total_score = sum(s.total_points for s in sections_lineage)
        tier = TierClassifier().classify(total_score)

        lineage = CompleteScoringLineage(
            property_address=property.full_address,
            scoring_run_id=run_id,
            scored_at=datetime.now(timezone.utc),
            sections=sections_lineage,
            total_score=total_score,
            max_possible=600,
            tier=tier.value
        )

        # Store lineage on property for persistence
        property.scoring_lineage = lineage

        return total_score, lineage

    def _score_section_location(self, property: Property, run_id: str) -> SectionScoringLineage:
        """Score location section with detailed lineage."""
        strategies_lineage = []
        total = 0.0

        # School district strategy
        school_score = SchoolDistrictScorer().score(property)
        school_result = ScoringStrategyResult(
            strategy_name="SchoolDistrictScorer",
            phase="phase1_map",
            points_awarded=school_score,
            max_possible=45,
            input_fields={"school_rating": property.school_rating},
            reasoning=f"GreatSchools {property.school_rating}/10 → {school_score}/45 points",
        )
        strategies_lineage.append(school_result)
        total += school_score

        # Safety strategy
        safety_score = CrimeIndexScorer().score(property)
        safety_result = ScoringStrategyResult(
            strategy_name="CrimeIndexScorer",
            phase="phase1_map",
            points_awarded=safety_score,
            max_possible=50,
            input_fields={
                "violent_crime_index": property.violent_crime_index,
                "property_crime_index": property.property_crime_index
            },
            reasoning=f"Crime index (60% violent + 40% property) → {safety_score}/50 points"
        )
        strategies_lineage.append(safety_result)
        total += safety_score

        # ... repeat for all location strategies ...

        return SectionScoringLineage(
            section_name="Location & Environment",
            total_points=total,
            max_possible=230,
            strategies=strategies_lineage
        )
```

---
