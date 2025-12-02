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

    SECTION A: LOCATION & ENVIRONMENT (230 pts max)
    -----------------------------------------------

    school_district (50 pts max):
        GreatSchools rating (1-10 scale) × 5
        Example: Rating 8 = 40 points
        Data source: GreatSchools.org

    quietness (40 pts max):
        Distance to nearest highway/freeway
        Scoring logic:
            - < 0.25 miles: 0 pts (highway noise)
            - 0.25-0.5 miles: 8 pts (moderate noise)
            - 0.5-1.0 miles: 24 pts (acceptable)
            - 1.0-2.0 miles: 36 pts (quiet)
            - > 2.0 miles: 40 pts (very quiet)
        Data source: Google Maps

    safety (50 pts max):
        Manual neighborhood assessment based on:
        - Crime statistics
        - Street lighting
        - Neighborhood upkeep
        - Visible security measures
        Scoring: 0-50 scale, default 25 (neutral)

    supermarket_proximity (30 pts max):
        Distance to nearest preferred grocery store
        Scoring logic:
            - < 0.5 miles: 30 pts (walking distance)
            - 0.5-1.0 miles: 26 pts (very close)
            - 1.0-2.0 miles: 19 pts (close)
            - 2.0-3.0 miles: 11 pts (moderate)
            - > 3.0 miles: 4 pts (far)
        Data source: Google Maps

    parks_walkability (30 pts max):
        Manual assessment of:
        - Parks within 1 mile
        - Sidewalk availability
        - Bike lanes
        - Trail access
        Scoring: 0-30 scale, default 15 (neutral)

    sun_orientation (30 pts max):
        Impact on cooling costs
        Scoring logic:
            - North-facing: 30 pts (best, minimal sun)
            - East-facing: 25 pts (morning sun only)
            - South-facing: 15 pts (moderate sun)
            - West-facing: 0 pts (afternoon sun, high cooling costs)
        Data source: Google Maps satellite view

    SECTION B: LOT & SYSTEMS (180 pts max)
    ---------------------------------------

    roof_condition (50 pts max):
        Age and condition of roof
        Scoring logic:
            - New/replaced (0-5 years): 50 pts
            - Good condition (6-10 years): 40 pts
            - Fair condition (11-15 years): 25 pts
            - Aging (16-20 years): 10 pts
            - Replacement needed (>20 years): 0 pts
        Note: Arizona heat reduces roof lifespan vs national average

    backyard_utility (40 pts max):
        Estimated usable backyard space
        Scoring logic:
            - Calculate: lot_sqft - house_sqft - front_yard_estimate
            - Large usable (>4000 sqft): 40 pts
            - Medium (2000-4000 sqft): 30 pts
            - Small (1000-2000 sqft): 20 pts
            - Minimal (<1000 sqft): 10 pts
        Factors: Pool, covered patio, landscaping

    plumbing_electrical (40 pts max):
        Based on year_built and upgrade evidence
        Scoring logic:
            - Recent build (2010+): 40 pts
            - Modern (2000-2009): 35 pts
            - Updated (1990-1999): 25 pts
            - Aging (1980-1989): 15 pts
            - Old (<1980): 5 pts
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

    cost_efficiency (30 pts max):
        Estimated monthly cost efficiency (NEW)
        Scoring logic:
            - $3,000/mo or less: 30 pts (very affordable)
            - $3,500/mo: 22 pts (affordable)
            - $4,000/mo: 15 pts (at budget)
            - $4,500/mo: 7 pts (stretching)
            - $5,000+/mo: 0 pts (exceeds target)
        Includes: mortgage, taxes, HOA, solar lease, pool maintenance
        Note: Captures total ownership cost beyond purchase price

    SECTION C: INTERIOR & FEATURES (190 pts max)
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

    master_suite (40 pts max):
        Visual inspection of primary bedroom
        Scoring factors:
            - Bedroom size
            - Closet space (walk-in preferred)
            - Bathroom quality (dual sinks, separate tub/shower)
            - Privacy (separated from other bedrooms)
        Scoring: 0-40 scale, default 20 (neutral)
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

    high_ceilings (30 pts max):
        Ceiling height assessment
        Scoring logic:
            - Vaulted/cathedral: 30 pts
            - 10+ feet: 25 pts
            - 9 feet: 15 pts
            - 8 feet (standard): 10 pts
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

    # SECTION A: LOCATION & ENVIRONMENT (230 pts)
    school_district: int = 50
    quietness: int = 40  # reduced from 50
    safety: int = 50
    supermarket_proximity: int = 30  # reduced from 40
    parks_walkability: int = 30
    sun_orientation: int = 30

    # SECTION B: LOT & SYSTEMS (180 pts)
    roof_condition: int = 50  # restored to spec (unchanged from original)
    backyard_utility: int = 40
    plumbing_electrical: int = 40
    pool_condition: int = 20  # reduced from 30 (pool burden now in cost_efficiency)
    cost_efficiency: int = 30  # NEW: monthly cost efficiency scoring (reduced to maintain 180 total)

    # SECTION C: INTERIOR & FEATURES (190 pts)
    kitchen_layout: int = 40
    master_suite: int = 40
    natural_light: int = 30
    high_ceilings: int = 30
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
            + self.safety
            + self.supermarket_proximity
            + self.parks_walkability
            + self.sun_orientation
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
            + self.safety
            + self.supermarket_proximity
            + self.parks_walkability
            + self.sun_orientation
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
