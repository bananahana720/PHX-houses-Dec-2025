"""
PHX Home Buying Analysis Pipeline
==================================
Orchestrates data enrichment, kill switch filtering, and weighted scoring
for Phoenix area home listings.

Usage:
    python phx_home_analyzer.py
"""

import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from lib.kill_switch import apply_kill_switch  # noqa: E402

from src.phx_home_analysis.domain.value_objects import ScoreBreakdown  # noqa: E402
from src.phx_home_analysis.services.scoring import PropertyScorer  # noqa: E402

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Property:
    """Complete property record with all enrichment fields."""

    # Original listing data
    street: str = ""
    city: str = ""
    state: str = "AZ"
    zip_code: str = ""
    price: int = 0
    beds: int = 0
    baths: float = 0.0
    sqft: int = 0
    price_per_sqft: float = 0.0
    full_address: str = ""

    # County Assessor enrichment
    lot_sqft: int | None = None
    year_built: int | None = None
    garage_spaces: int | None = None
    sewer_type: str | None = None  # "city" or "septic"
    tax_annual: float | None = None

    # HOA data
    hoa_fee: float | None = None  # None = unknown, 0 = no HOA

    # Geo-spatial enrichment
    commute_minutes: int | None = None  # To Desert Ridge
    school_district: str | None = None
    school_rating: float | None = None  # 1-10 GreatSchools
    orientation: str | None = None  # N, S, E, W, NE, NW, SE, SW
    distance_to_grocery_miles: float | None = None
    distance_to_highway_miles: float | None = None
    flood_zone: str | None = None

    # Arizona-specific
    solar_status: str | None = None  # "owned", "leased", "none"
    solar_lease_monthly: float | None = None
    has_pool: bool | None = None
    pool_equipment_age: int | None = None

    # Condition data
    roof_age: int | None = None
    hvac_age: int | None = None

    # Interior assessment fields (from enrichment_data.json, 0-10 scale)
    kitchen_layout_score: float | None = None
    master_suite_score: float | None = None
    natural_light_score: float | None = None
    high_ceilings_score: float | None = None
    fireplace_present: bool | None = None
    laundry_area_score: float | None = None
    aesthetics_score: float | None = None
    backyard_utility_score: float | None = None
    safety_neighborhood_score: float | None = None
    parks_walkability_score: float | None = None

    # Kill switch results
    kill_switch_passed: bool | None = None
    kill_switch_failures: list[str] = field(default_factory=list)

    # Scoring results (populated by PropertyScorer)
    score_breakdown: ScoreBreakdown | None = None
    score_location: float = 0.0
    score_lot_systems: float = 0.0
    score_interior: float = 0.0
    total_score: float = 0.0
    tier: str = ""  # "Unicorn", "Contender", "Pass"


# =============================================================================
# KILL SWITCH FILTERS (Pass/Fail)
# =============================================================================
# NOTE: Kill switch logic is now consolidated in scripts/lib/kill_switch.py
# Import: from lib.kill_switch import apply_kill_switch


# =============================================================================
# WEIGHTED SCORING (Using Canonical PropertyScorer Service)
# =============================================================================
# NOTE: Scoring logic is now consolidated in src/phx_home_analysis/services/scoring/
# This section provides an adapter to use the canonical service with local Property

# Global scorer instance (created lazily)
_scorer: PropertyScorer | None = None


def _get_scorer() -> PropertyScorer:
    """Get or create the global PropertyScorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = PropertyScorer()
    return _scorer


def _convert_to_domain_property(prop: Property):
    """Convert local Property to domain Property for scoring.

    The PropertyScorer expects the domain Property entity with specific
    attribute names. This adapter creates a minimal object with the
    required attributes.
    """
    from src.phx_home_analysis.domain.entities import Property as DomainProperty
    from src.phx_home_analysis.domain.enums import Orientation

    # Parse orientation string to enum
    orientation_enum = None
    if prop.orientation:
        orientation_enum = Orientation.from_string(prop.orientation)

    # Create domain Property with required fields
    domain_prop = DomainProperty(
        street=prop.street,
        city=prop.city,
        state=prop.state,
        zip_code=prop.zip_code,
        full_address=prop.full_address,
        price=f"${prop.price:,}" if prop.price else "$0",
        price_num=prop.price,
        beds=prop.beds,
        baths=prop.baths,
        sqft=prop.sqft,
        price_per_sqft_raw=prop.price_per_sqft,
        # Enrichment data
        lot_sqft=prop.lot_sqft,
        year_built=prop.year_built,
        garage_spaces=prop.garage_spaces,
        hoa_fee=prop.hoa_fee,  # Keep as float for precision
        school_rating=prop.school_rating,
        orientation=orientation_enum,
        distance_to_grocery_miles=prop.distance_to_grocery_miles,
        distance_to_highway_miles=prop.distance_to_highway_miles,
        roof_age=prop.roof_age,
        hvac_age=prop.hvac_age,
        has_pool=prop.has_pool,
        pool_equipment_age=prop.pool_equipment_age,
        # Interior assessment fields (Section C scoring)
        kitchen_layout_score=prop.kitchen_layout_score,
        master_suite_score=prop.master_suite_score,
        natural_light_score=prop.natural_light_score,
        high_ceilings_score=prop.high_ceilings_score,
        fireplace_present=prop.fireplace_present,
        laundry_area_score=prop.laundry_area_score,
        aesthetics_score=prop.aesthetics_score,
        backyard_utility_score=prop.backyard_utility_score,
        safety_neighborhood_score=prop.safety_neighborhood_score,
        parks_walkability_score=prop.parks_walkability_score,
        # Kill switch results must be set for tier classification
        kill_switch_passed=prop.kill_switch_passed or False,
        kill_switch_failures=prop.kill_switch_failures or [],
    )

    return domain_prop


def calculate_weighted_score(prop: Property) -> Property:
    """Calculate full weighted score using canonical PropertyScorer service.

    Converts the local Property to a domain Property, applies scoring via
    the canonical PropertyScorer service, then maps results back.

    Args:
        prop: Local Property dataclass

    Returns:
        Same Property with scoring attributes populated
    """
    scorer = _get_scorer()

    # Convert to domain Property and score
    domain_prop = _convert_to_domain_property(prop)
    score_breakdown = scorer.score(domain_prop)

    # Map ScoreBreakdown back to local Property attributes
    prop.score_breakdown = score_breakdown
    prop.score_location = score_breakdown.location_total
    prop.score_lot_systems = score_breakdown.systems_total
    prop.score_interior = score_breakdown.interior_total
    prop.total_score = score_breakdown.total_score

    # Assign tier based on score and kill switch status (600 pts max)
    # Unicorn: >480 (80%), Contender: 360-480 (60-80%), Pass: <360 (<60%)
    if not prop.kill_switch_passed:
        prop.tier = "Failed"
    elif prop.total_score > 480:
        prop.tier = "Unicorn"
    elif prop.total_score >= 360:
        prop.tier = "Contender"
    else:
        prop.tier = "Pass"

    return prop


# =============================================================================
# DATA LOADING AND ENRICHMENT
# =============================================================================

def load_listings(csv_path: str) -> list[Property]:
    """Load listings from CSV file."""
    properties = []

    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prop = Property(
                street=row.get('street', ''),
                city=row.get('city', ''),
                state=row.get('state', 'AZ'),
                zip_code=row.get('zip', ''),
                price=int(row.get('price_num', 0)),
                beds=int(row.get('beds', 0)),
                baths=float(row.get('baths', 0)),
                sqft=int(row.get('sqft', 0)),
                price_per_sqft=float(row.get('price_per_sqft', 0)),
                full_address=row.get('full_address', ''),
            )
            properties.append(prop)

    return properties


def enrich_from_manual_data(properties: list[Property], enrichment_path: str) -> list[Property]:
    """Merge manual enrichment data with Pydantic validation.

    Loads enrichment_data.json, validates each entry using EnrichmentDataSchema,
    and merges validated data into Property objects.

    Args:
        properties: List of Property objects to enrich
        enrichment_path: Path to enrichment_data.json

    Returns:
        Properties with enrichment data merged (validation errors logged)
    """
    from pydantic import ValidationError

    from src.phx_home_analysis.validation.schemas import EnrichmentDataSchema

    enrichment_file = Path(enrichment_path)
    if not enrichment_file.exists():
        return properties

    with open(enrichment_file, encoding='utf-8') as f:
        enrichment_data = json.load(f)

    # Validate and create lookup by address
    enrichment_lookup: dict[str, dict] = {}
    validation_errors = 0

    for item in enrichment_data:
        try:
            # Validate using Pydantic schema
            validated = EnrichmentDataSchema(**item)
            # Convert validated model to dict (excludes None values by default)
            enrichment_lookup[validated.full_address] = validated.model_dump(exclude_none=True)
        except ValidationError as e:
            validation_errors += 1
            address = item.get('full_address', 'UNKNOWN')
            print(f"  WARNING: Validation error for {address}: {e.error_count()} error(s)")
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                print(f"    - {field}: {error['msg']}")

    if validation_errors > 0:
        print(f"  {validation_errors} enrichment entries had validation errors")

    # Merge validated enrichment data into properties
    for prop in properties:
        if prop.full_address in enrichment_lookup:
            data = enrichment_lookup[prop.full_address]
            # Update property with validated enrichment data
            for key, value in data.items():
                if hasattr(prop, key) and value is not None:
                    setattr(prop, key, value)

    return properties


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def generate_enrichment_template(properties: list[Property], output_path: str):
    """Generate JSON template for manual data enrichment."""
    template = []

    for prop in properties:
        template.append({
            "full_address": prop.full_address,
            "price": prop.price,
            "beds": prop.beds,
            "baths": prop.baths,
            "sqft": prop.sqft,
            "# COUNTY ASSESSOR DATA": "---",
            "lot_sqft": None,
            "year_built": None,
            "garage_spaces": None,
            "sewer_type": None,  # "city" or "septic"
            "tax_annual": None,
            "# HOA DATA": "---",
            "hoa_fee": None,  # 0 = no HOA, number = monthly fee
            "# GEO-SPATIAL DATA": "---",
            "commute_minutes": None,
            "school_district": None,
            "school_rating": None,
            "orientation": None,  # N, S, E, W, NE, NW, SE, SW
            "distance_to_grocery_miles": None,
            "distance_to_highway_miles": None,
            "# ARIZONA SPECIFIC": "---",
            "solar_status": None,  # "owned", "leased", "none"
            "solar_lease_monthly": None,
            "has_pool": None,
            "pool_equipment_age": None,
            "# CONDITION DATA": "---",
            "roof_age": None,
            "hvac_age": None,
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)

    print(f"Generated enrichment template: {output_path}")


def generate_ranked_csv(properties: list[Property], output_path: str):
    """Generate ranked CSV with all data and scores."""

    # Sort by total score descending
    ranked = sorted(properties, key=lambda p: p.total_score, reverse=True)

    fieldnames = [
        # Rankings and summary
        'rank', 'tier', 'total_score', 'kill_switch_passed',
        # Address and basic listing
        'full_address', 'city', 'price', 'beds', 'baths', 'sqft', 'price_per_sqft',
        # County/assessor data
        'lot_sqft', 'year_built', 'garage_spaces', 'sewer_type', 'hoa_fee', 'tax_annual',
        # Geographic data
        'commute_minutes', 'school_rating', 'orientation',
        'distance_to_grocery_miles', 'distance_to_highway_miles',
        # Arizona-specific
        'solar_status', 'solar_lease_monthly', 'has_pool', 'pool_equipment_age',
        # Condition data
        'roof_age', 'hvac_age',
        # Section scores (for audit trail)
        'score_location', 'score_lot_systems', 'score_interior',
        # Interior assessment scores (Section C inputs - 190 pts)
        'kitchen_layout_score', 'master_suite_score', 'natural_light_score',
        'high_ceilings_score', 'fireplace_present', 'laundry_area_score',
        'aesthetics_score',
        # Location/systems assessment scores (Section A & B inputs)
        'backyard_utility_score', 'safety_neighborhood_score', 'parks_walkability_score',
        # Kill switch details
        'kill_switch_failures'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rank, prop in enumerate(ranked, 1):
            row = {
                # Rankings and summary
                'rank': rank,
                'tier': prop.tier,
                'total_score': round(prop.total_score, 1),
                'kill_switch_passed': 'PASS' if prop.kill_switch_passed else 'FAIL',
                # Address and basic listing
                'full_address': prop.full_address,
                'city': prop.city,
                'price': prop.price,
                'beds': prop.beds,
                'baths': prop.baths,
                'sqft': prop.sqft,
                'price_per_sqft': round(prop.price_per_sqft, 2) if prop.price_per_sqft else '',
                # County/assessor data
                'lot_sqft': prop.lot_sqft or '',
                'year_built': prop.year_built or '',
                'garage_spaces': prop.garage_spaces or '',
                'sewer_type': prop.sewer_type or '',
                'hoa_fee': prop.hoa_fee if prop.hoa_fee is not None else '',
                'tax_annual': prop.tax_annual or '',
                # Geographic data
                'commute_minutes': prop.commute_minutes or '',
                'school_rating': prop.school_rating or '',
                'orientation': prop.orientation or '',
                'distance_to_grocery_miles': prop.distance_to_grocery_miles or '',
                'distance_to_highway_miles': prop.distance_to_highway_miles or '',
                # Arizona-specific
                'solar_status': prop.solar_status or '',
                'solar_lease_monthly': prop.solar_lease_monthly or '',
                'has_pool': prop.has_pool if prop.has_pool is not None else '',
                'pool_equipment_age': prop.pool_equipment_age or '',
                # Condition data
                'roof_age': prop.roof_age or '',
                'hvac_age': prop.hvac_age or '',
                # Section scores
                'score_location': round(prop.score_location, 1),
                'score_lot_systems': round(prop.score_lot_systems, 1),
                'score_interior': round(prop.score_interior, 1),
                # Interior assessment scores (Section C inputs)
                'kitchen_layout_score': prop.kitchen_layout_score or '',
                'master_suite_score': prop.master_suite_score or '',
                'natural_light_score': prop.natural_light_score or '',
                'high_ceilings_score': prop.high_ceilings_score or '',
                'fireplace_present': prop.fireplace_present if prop.fireplace_present is not None else '',
                'laundry_area_score': prop.laundry_area_score or '',
                'aesthetics_score': prop.aesthetics_score or '',
                # Location/systems assessment scores
                'backyard_utility_score': prop.backyard_utility_score or '',
                'safety_neighborhood_score': prop.safety_neighborhood_score or '',
                'parks_walkability_score': prop.parks_walkability_score or '',
                # Kill switch details
                'kill_switch_failures': '; '.join(prop.kill_switch_failures) if prop.kill_switch_failures else ''
            }
            writer.writerow(row)

    print(f"Generated ranked output: {output_path}")


def print_summary(properties: list[Property]):
    """Print analysis summary to console."""

    passed = [p for p in properties if p.kill_switch_passed]
    failed = [p for p in properties if not p.kill_switch_passed]

    print("\n" + "=" * 70)
    print("PHX HOME ANALYSIS SUMMARY")
    print("=" * 70)

    print(f"\nTotal Properties Analyzed: {len(properties)}")
    print(f"Passed Kill Switch: {len(passed)}")
    print(f"Failed Kill Switch: {len(failed)}")

    if passed:
        # Sort by score
        ranked = sorted(passed, key=lambda p: p.total_score, reverse=True)

        unicorns = [p for p in ranked if p.tier == "Unicorn"]
        contenders = [p for p in ranked if p.tier == "Contender"]

        print(f"\nUnicorns (>480 pts): {len(unicorns)}")
        print(f"Contenders (360-480 pts): {len(contenders)}")

        print("\n" + "-" * 70)
        print("TOP 5 PROPERTIES")
        print("-" * 70)

        for i, prop in enumerate(ranked[:5], 1):
            print(f"\n#{i} [{prop.tier}] Score: {prop.total_score:.0f}")
            print(f"   {prop.full_address}")
            print(f"   ${prop.price:,} | {prop.beds}bd/{prop.baths}ba | {prop.sqft:,} sqft")
            print(f"   Location: {prop.score_location:.0f} | Systems: {prop.score_lot_systems:.0f} | Interior: {prop.score_interior:.0f}")

    if failed:
        print("\n" + "-" * 70)
        print("KILL SWITCH FAILURES")
        print("-" * 70)
        for prop in failed:
            print(f"\n   {prop.full_address}")
            print(f"   Failures: {', '.join(prop.kill_switch_failures)}")

    print("\n" + "=" * 70)


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def main():
    """Run the full analysis pipeline."""

    # Paths
    base_dir = Path(__file__).parent
    input_csv = base_dir / "phx_homes.csv"
    enrichment_json = base_dir / "enrichment_data.json"
    output_template = base_dir / "enrichment_template.json"
    output_ranked = base_dir / "phx_homes_ranked.csv"

    print("PHX Home Buying Analysis Pipeline")
    print("=" * 50)

    # Step 1: Load listings
    print("\n[1/5] Loading listings...")
    properties = load_listings(str(input_csv))
    print(f"      Loaded {len(properties)} properties")

    # Step 2: Generate enrichment template (if needed)
    if not enrichment_json.exists():
        print("\n[2/5] Generating enrichment template...")
        generate_enrichment_template(properties, str(output_template))
        print(f"      Please fill in: {output_template}")
        print("      Then rename to: enrichment_data.json")
        print("      And re-run this script.")
    else:
        print("\n[2/5] Loading enrichment data...")
        properties = enrich_from_manual_data(properties, str(enrichment_json))
        print("      Enrichment data merged")

    # Step 3: Apply kill switch
    print("\n[3/5] Applying kill switch filters...")
    properties = [apply_kill_switch(p) for p in properties]
    passed = sum(1 for p in properties if p.kill_switch_passed)
    print(f"      {passed}/{len(properties)} passed all criteria")

    # Step 4: Calculate scores
    print("\n[4/5] Calculating weighted scores...")
    properties = [calculate_weighted_score(p) for p in properties]

    # Step 5: Generate outputs
    print("\n[5/5] Generating outputs...")
    generate_ranked_csv(properties, str(output_ranked))

    # Print summary
    print_summary(properties)

    return properties


if __name__ == "__main__":
    main()
