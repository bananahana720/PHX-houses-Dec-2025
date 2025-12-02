"""Scoring weights and tier thresholds for PHX Home Analysis.

This module defines the weighted scoring system used to rank properties that
pass all kill-switch criteria. Properties are scored across three categories:
Location & Environment, Lot & Systems, and Interior & Features.

Total possible score: 600 points
Note: Section A totals 250 points (not 150) based on specified individual weights.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringWeights:
    """Weighted scoring system for property evaluation.

    Properties are scored across three major categories with a maximum
    possible score of 600 points. Only properties that pass all kill-switch
    criteria in BuyerProfile are scored.

    SECTION A: LOCATION & ENVIRONMENT (250 pts max)
    -----------------------------------------------

    school_district (45 pts max):
        GreatSchools rating (1-10 scale) × 4.5
        Example: Rating 8 = 36 points
        Data source: GreatSchools.org

    quietness (30 pts max):
        Distance to nearest highway/freeway
        Scoring logic:
            - < 0.25 miles: 0 pts (highway noise)
            - 0.25-0.5 miles: 6 pts (moderate noise)
            - 0.5-1.0 miles: 18 pts (acceptable)
            - 1.0-2.0 miles: 27 pts (quiet)
            - > 2.0 miles: 30 pts (very quiet)
        Data source: Google Maps

    crime_index (50 pts max):
        Automated crime index data (0-100, 100=safest)
        Composite: 60% violent crime + 40% property crime
        Scoring logic:
            - Index 90-100: 45-50 pts (safest)
            - Index 70-89: 35-44 pts (safe)
            - Index 50-69: 25-34 pts (moderate)
            - Index 30-49: 15-24 pts (elevated)
            - Index 0-29: 0-14 pts (high risk)
        Data source: BestPlaces, AreaVibes, NeighborhoodScout
        Note: Replaces manual safety assessment

    supermarket_proximity (25 pts max):
        Distance to nearest preferred grocery store
        Scoring logic:
            - < 0.5 miles: 25 pts (walking distance)
            - 0.5-1.0 miles: 20 pts (very close)
            - 1.0-2.0 miles: 15 pts (close)
            - 2.0-3.0 miles: 8 pts (moderate)
            - > 3.0 miles: 3 pts (far)
        Data source: Google Maps

    parks_walkability (25 pts max):
        Manual assessment of:
        - Parks within 1 mile
        - Sidewalk availability
        - Bike lanes
        - Trail access
        Scoring: 0-25 scale, default 12.5 (neutral)

    sun_orientation (25 pts max):
        Impact on cooling costs
        Scoring logic:
            - North-facing: 25 pts (best, minimal sun)
            - East-facing: 18.75 pts (morning sun only)
            - South-facing: 12.5 pts (moderate sun)
            - West-facing: 0 pts (afternoon sun, high cooling costs)
        Data source: Google Maps satellite view

    flood_risk (25 pts max):
        FEMA flood zone classification
        Scoring logic:
            - Zone X (minimal risk): 25 pts
            - Zone X-Shaded (500-year): 20 pts
            - Zone A/AE/AH/AO (100-year): 5-7.5 pts
            - Zone VE (coastal hazard): 0 pts
            - Unknown: 12.5 pts (neutral)
        Data source: FEMA National Flood Hazard Layer
        Note: High-risk zones require flood insurance

    walk_transit (25 pts max):
        Walk Score, Transit Score, Bike Score composite
        Weighting: 40% walk, 40% transit, 20% bike
        Scoring logic:
            - Score 90-100: 22.5-25 pts (walker's paradise)
            - Score 70-89: 17.5-22 pts (very walkable)
            - Score 50-69: 12.5-17 pts (somewhat walkable)
            - Score 25-49: 6-12 pts (car-dependent)
            - Score 0-24: 0-6 pts (car-required)
        Data source: WalkScore.com API

    SECTION B: LOT & SYSTEMS (170 pts max)
    ---------------------------------------

    roof_condition (45 pts max):
        Age and condition of roof
        Scoring logic:
            - New/replaced (0-5 years): 45 pts
            - Good condition (6-10 years): 36 pts
            - Fair condition (11-15 years): 22.5 pts
            - Aging (16-20 years): 9 pts
            - Replacement needed (>20 years): 0 pts
        Note: Arizona heat reduces roof lifespan vs national average

    backyard_utility (35 pts max):
        Estimated usable backyard space
        Scoring logic:
            - Calculate: lot_sqft - house_sqft - front_yard_estimate
            - Large usable (>4000 sqft): 35 pts
            - Medium (2000-4000 sqft): 26.25 pts
            - Small (1000-2000 sqft): 17.5 pts
            - Minimal (<1000 sqft): 8.75 pts
        Factors: Pool, covered patio, landscaping

    plumbing_electrical (35 pts max):
        Based on year_built and upgrade evidence
        Scoring logic:
            - Recent build (2010+): 35 pts
            - Modern (2000-2009): 30.6 pts
            - Updated (1990-1999): 21.9 pts
            - Aging (1980-1989): 13.1 pts
            - Old (<1980): 4.4 pts
        Look for: Copper plumbing, 200A service, updated panels

    pool_condition (20 pts max):
        Pool equipment age and condition (if pool present)
        Scoring logic:
            - No pool: 10 pts (neutral, no burden)
            - New equipment (0-3 years): 20 pts
            - Good condition (4-7 years): 17 pts
            - Fair condition (8-12 years): 10 pts
            - Needs replacement (>12 years): 3 pts
        Note: Pool equipment fails faster in AZ heat/sun
              Pool operating costs now captured in cost_efficiency

    cost_efficiency (35 pts max):
        Estimated monthly cost efficiency
        Scoring logic:
            - $3,000/mo or less: 35 pts (very affordable)
            - $3,500/mo: 25.7 pts (affordable)
            - $4,000/mo: 17.5 pts (at budget)
            - $4,500/mo: 8.2 pts (stretching)
            - $5,000+/mo: 0 pts (exceeds target)
        Includes: mortgage, taxes, HOA, solar lease, pool maintenance
        Note: Captures total ownership cost beyond purchase price

    SECTION C: INTERIOR & FEATURES (180 pts max)
    ---------------------------------------------

    kitchen_layout (40 pts max):
        Visual inspection of kitchen design
        Scoring factors:
            - Open concept vs closed
            - Island/counter space
            - Modern appliances
            - Pantry size
            - Natural light
        Scoring: 0-40 scale, default 20 (neutral)
        Data source: Listing photos

    master_suite (35 pts max):
        Visual inspection of primary bedroom
        Scoring factors:
            - Bedroom size
            - Closet space (walk-in preferred)
            - Bathroom quality (dual sinks, separate tub/shower)
            - Privacy (separated from other bedrooms)
        Scoring: 0-35 scale, default 17.5 (neutral)
        Data source: Listing photos

    natural_light (30 pts max):
        Visual assessment of windows and lighting
        Scoring factors:
            - Number and size of windows
            - Skylights
            - Room brightness in photos
            - Open floor plan
        Scoring: 0-30 scale, default 15 (neutral)
        Data source: Listing photos

    high_ceilings (25 pts max):
        Ceiling height assessment
        Scoring logic:
            - Vaulted/cathedral: 25 pts
            - 10+ feet: 20.8 pts
            - 9 feet: 12.5 pts
            - 8 feet (standard): 8.3 pts
            - < 8 feet: 0 pts
        Data source: Listing description/photos

    fireplace (20 pts max):
        Presence and quality of fireplace
        Scoring logic:
            - Gas fireplace in living area: 20 pts
            - Wood-burning fireplace: 15 pts
            - Decorative only: 5 pts
            - No fireplace: 0 pts
        Note: Less critical in AZ but adds ambiance
        Data source: Listing photos/description

    laundry_area (20 pts max):
        Laundry room quality and location
        Scoring logic:
            - Dedicated room upstairs: 20 pts
            - Dedicated room (any floor): 15 pts
            - Laundry closet: 10 pts
            - Garage only: 5 pts
            - No dedicated space: 0 pts
        Data source: Listing photos

    aesthetics (10 pts max):
        Overall subjective appeal
        Scoring factors:
            - Curb appeal
            - Interior finishes
            - Color scheme
            - Modern vs dated
        Scoring: 0-10 scale, default 5 (neutral)
        Data source: Listing photos
    """

    # SECTION A: LOCATION & ENVIRONMENT (250 pts)
    school_district: int = 45
    quietness: int = 30
    crime_index: int = 50  # REPLACES safety
    supermarket_proximity: int = 25
    parks_walkability: int = 25
    sun_orientation: int = 25
    flood_risk: int = 25  # NEW
    walk_transit: int = 25  # NEW

    # SECTION B: LOT & SYSTEMS (170 pts)
    roof_condition: int = 45
    backyard_utility: int = 35
    plumbing_electrical: int = 35
    pool_condition: int = 20
    cost_efficiency: int = 35

    # SECTION C: INTERIOR & FEATURES (180 pts)
    kitchen_layout: int = 40
    master_suite: int = 35
    natural_light: int = 30
    high_ceilings: int = 25
    fireplace: int = 20
    laundry_area: int = 20
    aesthetics: int = 10

    @property
    def total_possible_score(self) -> int:
        """Calculate total possible score from all weights.

        Returns:
            Sum of all scoring weights (should be 600)
        """
        return (
            # Section A: Location & Environment
            self.school_district
            + self.quietness
            + self.crime_index
            + self.supermarket_proximity
            + self.parks_walkability
            + self.sun_orientation
            + self.flood_risk
            + self.walk_transit
            # Section B: Lot & Systems
            + self.roof_condition
            + self.backyard_utility
            + self.plumbing_electrical
            + self.pool_condition
            + self.cost_efficiency
            # Section C: Interior & Features
            + self.kitchen_layout
            + self.master_suite
            + self.natural_light
            + self.high_ceilings
            + self.fireplace
            + self.laundry_area
            + self.aesthetics
        )

    @property
    def section_a_max(self) -> int:
        """Maximum points for Section A: Location & Environment."""
        return (
            self.school_district
            + self.quietness
            + self.crime_index
            + self.supermarket_proximity
            + self.parks_walkability
            + self.sun_orientation
            + self.flood_risk
            + self.walk_transit
        )

    @property
    def section_b_max(self) -> int:
        """Maximum points for Section B: Lot & Systems."""
        return (
            self.roof_condition
            + self.backyard_utility
            + self.plumbing_electrical
            + self.pool_condition
            + self.cost_efficiency
        )

    @property
    def section_c_max(self) -> int:
        """Maximum points for Section C: Interior & Features."""
        return (
            self.kitchen_layout
            + self.master_suite
            + self.natural_light
            + self.high_ceilings
            + self.fireplace
            + self.laundry_area
            + self.aesthetics
        )


@dataclass(frozen=True)
class TierThresholds:
    """Tier classification thresholds for scored properties.

    Properties are classified into tiers based on their total score:
    - Unicorn: Exceptional properties worth immediate action
    - Contender: Strong properties worth serious consideration
    - Pass: Properties that meet minimum criteria but lack standout features

    Thresholds are calibrated to the 600-point scoring scale
    (Section A: 230 pts, Section B: 180 pts, Section C: 190 pts).

    Attributes:
        unicorn_min: Minimum score for Unicorn tier (>480 points, 80% of max)
        contender_min: Minimum score for Contender tier (360-480 points, 60-80% of max)
        pass_max: Maximum score for Pass tier (<360 points, <60% of max)
    """

    unicorn_min: int = 480  # Exceptional - immediate action (80%+ of 600)
    contender_min: int = 360  # Strong - serious consideration (60-80% of 600)
    pass_max: int = 359  # Meets minimums but unremarkable (<60% of 600)

    def classify(self, score: float) -> str:
        """Classify a property based on its total score.

        Args:
            score: Total weighted score (0-600)

        Returns:
            Tier classification: "Unicorn", "Contender", or "Pass"
        """
        if score > self.unicorn_min:
            return "Unicorn"
        elif score >= self.contender_min:
            return "Contender"
        else:
            return "Pass"
