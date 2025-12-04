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
import logging
from pathlib import Path

# Requires: uv pip install -e .
from lib.kill_switch import apply_kill_switch

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.services.scoring import PropertyScorer

logger = logging.getLogger(__name__)

# =============================================================================
# KILL SWITCH FILTERS (Pass/Fail)
# =============================================================================
# NOTE: Kill switch logic is now consolidated in scripts/lib/kill_switch.py
# Import: from lib.kill_switch import apply_kill_switch
# NOTE: Property entity is now imported from phx_home_analysis.domain.entities


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


def calculate_weighted_score(prop: Property) -> Property:
    """Calculate full weighted score using canonical PropertyScorer service.

    Args:
        prop: Domain Property entity

    Returns:
        Same Property with scoring attributes populated
    """
    from phx_home_analysis.domain.enums import Tier

    scorer = _get_scorer()

    # Score the domain Property directly (no conversion needed)
    score_breakdown = scorer.score(prop)

    # Update Property with scoring results
    prop.score_breakdown = score_breakdown

    # Assign tier based on score and kill switch status (600 pts max)
    # Uses the Tier enum's from_score class method for consistency
    prop.tier = Tier.from_score(score_breakdown.total_score, prop.kill_switch_passed)

    return prop


# =============================================================================
# DATA LOADING AND ENRICHMENT
# =============================================================================

def load_listings(csv_path: str) -> list[Property]:
    """Load listings from CSV file using cache.

    Creates domain Property entities with correct field names:
    - price: formatted string (e.g., "$475,000")
    - price_num: numeric value (int)
    - price_per_sqft_raw: from CSV calculation
    """
    from phx_home_analysis.services.data_cache import PropertyDataCache

    cache = PropertyDataCache()
    csv_data = cache.get_csv_data(Path(csv_path))

    properties = []
    for row in csv_data:
        price_num = int(row.get('price_num', 0))
        prop = Property(
            street=row.get('street', ''),
            city=row.get('city', ''),
            state=row.get('state', 'AZ'),
            zip_code=row.get('zip', ''),
            full_address=row.get('full_address', ''),
            # Domain Property uses price (formatted string) and price_num (int)
            price=row.get('price', f"${price_num:,}" if price_num else "$0"),
            price_num=price_num,
            beds=int(row.get('beds', 0)),
            baths=float(row.get('baths', 0)),
            sqft=int(row.get('sqft', 0)),
            price_per_sqft_raw=float(row.get('price_per_sqft', 0)),
        )
        properties.append(prop)

    return properties


def enrich_from_manual_data(properties: list[Property], enrichment_path: str) -> list[Property]:
    """Merge manual enrichment data with Pydantic validation.

    Loads enrichment_data.json using cache, validates each entry using
    EnrichmentDataSchema, and merges validated data into Property objects.

    Args:
        properties: List of Property objects to enrich
        enrichment_path: Path to enrichment_data.json

    Returns:
        Properties with enrichment data merged (validation errors logged)
    """
    from pydantic import ValidationError

    from phx_home_analysis.services.data_cache import PropertyDataCache
    from phx_home_analysis.validation.schemas import EnrichmentDataSchema

    enrichment_file = Path(enrichment_path)
    if not enrichment_file.exists():
        return properties

    # Load from cache
    cache = PropertyDataCache()
    enrichment_data = cache.get_enrichment_data(enrichment_file)

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
            logger.warning("Validation error for %s: %d error(s)", address, e.error_count())
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                logger.warning("  - %s: %s", field, error['msg'])

    if validation_errors > 0:
        logger.warning("%d enrichment entries had validation errors", validation_errors)

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
            "price": prop.price_num,  # Use numeric price for template
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

    logger.info("Generated enrichment template: %s", output_path)


def _enum_value(enum_val) -> str:
    """Extract string value from enum, or return empty string if None."""
    if enum_val is None:
        return ''
    # Handle enum types by getting .value
    if hasattr(enum_val, 'value'):
        return enum_val.value
    return str(enum_val)


def generate_ranked_csv(properties: list[Property], output_path: str):
    """Generate ranked CSV with all data and scores.

    Handles domain Property entity with:
    - price_num for numeric price
    - price_per_sqft computed property
    - Enum types for tier, sewer_type, solar_status, orientation
    - score_breakdown for section scores
    """
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
        # Interior assessment scores (Section C inputs - 180 pts)
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
            # Get section scores from score_breakdown (domain Property stores results here)
            sb = prop.score_breakdown
            score_location = sb.location_total if sb else 0.0
            score_lot_systems = sb.systems_total if sb else 0.0
            score_interior = sb.interior_total if sb else 0.0

            # Get tier label (Tier enum has .label property)
            tier_label = prop.tier.label if prop.tier else ''

            row = {
                # Rankings and summary
                'rank': rank,
                'tier': tier_label,
                'total_score': round(prop.total_score, 1),
                'kill_switch_passed': 'PASS' if prop.kill_switch_passed else 'FAIL',
                # Address and basic listing
                'full_address': prop.full_address,
                'city': prop.city,
                'price': prop.price_num,  # Numeric price for CSV
                'beds': prop.beds,
                'baths': prop.baths,
                'sqft': prop.sqft,
                'price_per_sqft': round(prop.price_per_sqft, 2) if prop.price_per_sqft else '',
                # County/assessor data
                'lot_sqft': prop.lot_sqft or '',
                'year_built': prop.year_built or '',
                'garage_spaces': prop.garage_spaces or '',
                'sewer_type': _enum_value(prop.sewer_type),
                'hoa_fee': prop.hoa_fee if prop.hoa_fee is not None else '',
                'tax_annual': prop.tax_annual or '',
                # Geographic data
                'commute_minutes': prop.commute_minutes or '',
                'school_rating': prop.school_rating or '',
                'orientation': _enum_value(prop.orientation),
                'distance_to_grocery_miles': prop.distance_to_grocery_miles or '',
                'distance_to_highway_miles': prop.distance_to_highway_miles or '',
                # Arizona-specific
                'solar_status': _enum_value(prop.solar_status),
                'solar_lease_monthly': prop.solar_lease_monthly or '',
                'has_pool': prop.has_pool if prop.has_pool is not None else '',
                'pool_equipment_age': prop.pool_equipment_age or '',
                # Condition data
                'roof_age': prop.roof_age or '',
                'hvac_age': prop.hvac_age or '',
                # Section scores (from score_breakdown)
                'score_location': round(score_location, 1),
                'score_lot_systems': round(score_lot_systems, 1),
                'score_interior': round(score_interior, 1),
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

    logger.info("Generated ranked output: %s", output_path)


def log_summary(properties: list[Property]):
    """Log analysis summary to console.

    Handles domain Property entity with:
    - price_num for numeric price
    - tier as Tier enum (use .label for display, compare with Tier enum values)
    - score_breakdown for section scores
    """
    from phx_home_analysis.domain.enums import Tier

    passed = [p for p in properties if p.kill_switch_passed]
    failed = [p for p in properties if not p.kill_switch_passed]

    logger.info("=" * 70)
    logger.info("PHX HOME ANALYSIS SUMMARY")
    logger.info("=" * 70)

    logger.info("Total Properties Analyzed: %d", len(properties))
    logger.info("Passed Kill Switch: %d", len(passed))
    logger.info("Failed Kill Switch: %d", len(failed))

    if passed:
        # Sort by score
        ranked = sorted(passed, key=lambda p: p.total_score, reverse=True)

        # Compare with Tier enum values (not strings)
        unicorns = [p for p in ranked if p.tier == Tier.UNICORN]
        contenders = [p for p in ranked if p.tier == Tier.CONTENDER]

        logger.info("Unicorns (>480 pts): %d", len(unicorns))
        logger.info("Contenders (360-480 pts): %d", len(contenders))

        logger.info("-" * 70)
        logger.info("TOP 5 PROPERTIES")
        logger.info("-" * 70)

        for i, prop in enumerate(ranked[:5], 1):
            # Use tier.label for display, price_num for numeric formatting
            tier_label = prop.tier.label if prop.tier else "Unknown"
            # Get section scores from score_breakdown
            sb = prop.score_breakdown
            score_location = sb.location_total if sb else 0.0
            score_lot_systems = sb.systems_total if sb else 0.0
            score_interior = sb.interior_total if sb else 0.0

            logger.info("#%d [%s] Score: %.0f", i, tier_label, prop.total_score)
            logger.info("   %s", prop.full_address)
            logger.info("   $%s | %dbd/%.1fba | %s sqft",
                       f"{prop.price_num:,}", prop.beds, prop.baths, f"{prop.sqft:,}")
            logger.info("   Location: %.0f | Systems: %.0f | Interior: %.0f",
                       score_location, score_lot_systems, score_interior)

    if failed:
        logger.info("-" * 70)
        logger.info("KILL SWITCH FAILURES")
        logger.info("-" * 70)
        for prop in failed:
            logger.info("   %s", prop.full_address)
            logger.info("   Failures: %s", ', '.join(prop.kill_switch_failures))

    logger.info("=" * 70)


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def main():
    """Run the full analysis pipeline."""
    from phx_home_analysis.logging_config import setup_logging
    setup_logging()

    # Paths
    base_dir = Path(__file__).parent
    input_csv = base_dir / "phx_homes.csv"
    enrichment_json = base_dir / "enrichment_data.json"
    output_template = base_dir / "enrichment_template.json"
    output_ranked = base_dir / "phx_homes_ranked.csv"

    logger.info("PHX Home Buying Analysis Pipeline")
    logger.info("=" * 50)

    # Step 1: Load listings
    logger.info("[1/5] Loading listings...")
    properties = load_listings(str(input_csv))
    logger.info("      Loaded %d properties", len(properties))

    # Step 2: Generate enrichment template (if needed)
    if not enrichment_json.exists():
        logger.info("[2/5] Generating enrichment template...")
        generate_enrichment_template(properties, str(output_template))
        logger.info("      Please fill in: %s", output_template)
        logger.info("      Then rename to: enrichment_data.json")
        logger.info("      And re-run this script.")
    else:
        logger.info("[2/5] Loading enrichment data...")
        properties = enrich_from_manual_data(properties, str(enrichment_json))
        logger.info("      Enrichment data merged")

    # Step 3: Apply kill switch
    logger.info("[3/5] Applying kill switch filters...")
    properties = [apply_kill_switch(p) for p in properties]
    passed = sum(1 for p in properties if p.kill_switch_passed)
    logger.info("      %d/%d passed all criteria", passed, len(properties))

    # Step 4: Calculate scores
    logger.info("[4/5] Calculating weighted scores...")
    properties = [calculate_weighted_score(p) for p in properties]

    # Step 5: Generate outputs
    logger.info("[5/5] Generating outputs...")
    generate_ranked_csv(properties, str(output_ranked))

    # Log summary
    log_summary(properties)

    return properties


if __name__ == "__main__":
    main()
