"""Scoring explanation generator.

This module provides human-readable explanations for property scores, helping
users understand WHY each criterion scored what it did, what would improve the
score, and how the property compares to ideal values.

Explanation objects are dataclasses that can be converted to markdown text
or JSON-serializable dictionaries for use in reports and APIs.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ...config.scoring_weights import ScoringWeights, TierThresholds
from ...domain.enums import FloodZone, Orientation, SolarStatus

if TYPE_CHECKING:
    from ...domain.entities import Property
    from ...domain.value_objects import Score, ScoreBreakdown


# -----------------------------------------------------------------------------
# Explanation Data Classes
# -----------------------------------------------------------------------------


@dataclass
class ScoreExplanation:
    """Explanation for a single score criterion.

    Attributes:
        criterion: Criterion name (e.g., "School District Rating")
        score: Actual weighted score achieved
        max_score: Maximum possible weighted score
        percentage: Score as percentage of max (0-100)
        raw_value: Underlying data value (e.g., "8.5/10", "North-facing")
        reasoning: Human-readable explanation of why this score was given
        improvement_tip: Actionable advice for improving this score (optional)
    """

    criterion: str
    score: float
    max_score: float
    percentage: float
    raw_value: str | None
    reasoning: str
    improvement_tip: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Export as JSON-serializable dictionary.

        Returns:
            Dictionary with all explanation fields
        """
        return {
            "criterion": self.criterion,
            "score": round(self.score, 1),
            "max_score": round(self.max_score, 1),
            "percentage": round(self.percentage, 1),
            "raw_value": self.raw_value,
            "reasoning": self.reasoning,
            "improvement_tip": self.improvement_tip,
        }


@dataclass
class SectionExplanation:
    """Explanation for a scoring section (A, B, or C).

    Attributes:
        section: Section name ("Location & Environment", "Lot & Systems", "Interior & Features")
        section_letter: Single letter identifier ("A", "B", or "C")
        total_score: Sum of weighted scores in this section
        max_score: Maximum possible score for this section
        percentage: Score as percentage of max (0-100)
        criteria: List of individual criterion explanations
        summary: One-sentence section summary
        strengths: List of high-scoring criteria (>70%)
        weaknesses: List of low-scoring criteria (<50%)
    """

    section: str
    section_letter: str
    total_score: float
    max_score: float
    percentage: float
    criteria: list[ScoreExplanation]
    summary: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Export as JSON-serializable dictionary.

        Returns:
            Dictionary with all section explanation fields
        """
        return {
            "section": self.section,
            "section_letter": self.section_letter,
            "total_score": round(self.total_score, 1),
            "max_score": round(self.max_score, 1),
            "percentage": round(self.percentage, 1),
            "criteria": [c.to_dict() for c in self.criteria],
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


@dataclass
class FullScoreExplanation:
    """Complete property score explanation.

    Provides a comprehensive explanation of a property's total score including
    section breakdowns, tier classification, and improvement opportunities.

    Attributes:
        address: Property address for identification
        total_score: Sum of all weighted scores
        max_score: Maximum possible total score (605)
        tier: Classification tier (Unicorn/Contender/Pass)
        tier_threshold: Points needed to achieve this tier
        next_tier: Next tier up (if not already Unicorn)
        points_to_next_tier: Points needed to reach next tier
        sections: List of section explanations (A, B, C)
        summary: Overall narrative summary
        top_strengths: Best-scoring criteria across all sections
        key_improvements: Most impactful areas for improvement
    """

    address: str
    total_score: float
    max_score: float
    tier: str
    tier_threshold: float
    next_tier: str | None
    points_to_next_tier: float | None
    sections: list[SectionExplanation]
    summary: str
    top_strengths: list[str] = field(default_factory=list)
    key_improvements: list[str] = field(default_factory=list)

    def to_text(self) -> str:
        """Generate markdown-formatted explanation text.

        Returns:
            Complete markdown explanation suitable for reports
        """
        lines = []

        # Header with score and tier
        pct = (self.total_score / self.max_score) * 100
        lines.append(f"## Property Score: {self.total_score:.0f}/{self.max_score:.0f} ({pct:.0f}%) - {self.tier.upper()}")
        lines.append("")

        # Tier context
        if self.next_tier and self.points_to_next_tier:
            lines.append(f"**{self.points_to_next_tier:.0f} points from {self.next_tier} tier** - {self.summary}")
        else:
            lines.append(f"**Top tier achieved** - {self.summary}")
        lines.append("")

        # Section breakdowns
        for section in self.sections:
            lines.append(f"### Section {section.section_letter}: {section.section} ({section.total_score:.0f}/{section.max_score:.0f} pts, {section.percentage:.0f}%)")
            lines.append(section.summary)
            lines.append("")

            # Criteria table
            lines.append("| Criterion | Score | Details |")
            lines.append("|-----------|-------|---------|")
            for criterion in section.criteria:
                score_text = f"{criterion.score:.0f}/{criterion.max_score:.0f} ({criterion.percentage:.0f}%)"
                lines.append(f"| {criterion.criterion} | {score_text} | {criterion.reasoning} |")
            lines.append("")

            # Improvement tips for this section
            low_scores = [c for c in section.criteria if c.percentage < 50 and c.improvement_tip]
            if low_scores:
                tip = low_scores[0]
                lines.append(f"**To improve:** {tip.improvement_tip}")
                lines.append("")

        # Key takeaways
        if self.top_strengths:
            lines.append("### Top Strengths")
            for strength in self.top_strengths[:3]:
                lines.append(f"- {strength}")
            lines.append("")

        if self.key_improvements:
            lines.append("### Key Improvement Opportunities")
            for improvement in self.key_improvements[:3]:
                lines.append(f"- {improvement}")
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export as JSON-serializable dictionary.

        Returns:
            Complete explanation as nested dictionary
        """
        return {
            "address": self.address,
            "total_score": round(self.total_score, 1),
            "max_score": round(self.max_score, 1),
            "percentage": round((self.total_score / self.max_score) * 100, 1),
            "tier": self.tier,
            "tier_threshold": round(self.tier_threshold, 1),
            "next_tier": self.next_tier,
            "points_to_next_tier": round(self.points_to_next_tier, 1) if self.points_to_next_tier else None,
            "sections": [s.to_dict() for s in self.sections],
            "summary": self.summary,
            "top_strengths": self.top_strengths,
            "key_improvements": self.key_improvements,
        }


# -----------------------------------------------------------------------------
# Explanation Generator
# -----------------------------------------------------------------------------


class ScoringExplainer:
    """Generates human-readable scoring explanations.

    The ScoringExplainer takes a PropertyScorer's results and generates
    detailed explanations for each criterion, section, and overall score.

    Example:
        >>> scorer = PropertyScorer()
        >>> breakdown = scorer.score(property)
        >>> explainer = ScoringExplainer()
        >>> explanation = explainer.explain(property, breakdown)
        >>> print(explanation.to_text())
    """

    # Explanation templates for each criterion
    # Keys: 'high' (>70%), 'medium' (40-70%), 'low' (<40%)
    # Plus 'improvement' for actionable advice
    CRITERION_TEMPLATES: dict[str, dict[str, str]] = {
        "School District Rating": {
            "high": "Excellent schools ({raw_value}) - families pay premium for this district",
            "medium": "Good schools ({raw_value}) - solid educational options nearby",
            "low": "School ratings could be better ({raw_value}) - may want to research specific schools",
            "improvement": "Higher-rated school districts available in Gilbert, Chandler, Paradise Valley",
            "unknown": "School rating data unavailable - research district manually",
        },
        "Noise Level": {
            "high": "Very quiet location - minimal noise impact from traffic and highways",
            "medium": "Moderate noise levels - acceptable for most buyers",
            "low": "Higher noise area - close to highways or busy roads ({raw_value})",
            "improvement": "Properties >2 miles from highways score higher for quietness",
            "unknown": "Noise data unavailable - visit property at different times to assess",
        },
        "Quietness/Noise Level": {
            "high": "Very quiet location ({raw_value} miles from highway) - minimal traffic noise",
            "medium": "Moderate distance from highways ({raw_value} miles) - some traffic noise possible",
            "low": "Close to highway ({raw_value} miles) - expect traffic noise, especially during commute hours",
            "improvement": "Properties >2 miles from highways score highest for quietness",
            "unknown": "Highway distance unknown - check Google Maps for proximity to major roads",
        },
        "Crime Index": {
            "high": "Very safe area ({raw_value}) with low crime rates - desirable for families",
            "medium": "Average safety ({raw_value}) for the Phoenix metro area",
            "low": "Higher crime area ({raw_value}) - verify specific neighborhood data and trends",
            "improvement": "Consider areas like Gilbert, Chandler, North Scottsdale for lower crime",
            "unknown": "Crime data unavailable - research neighborhood safety on NeighborhoodScout or AreaVibes",
        },
        "Supermarket Proximity": {
            "high": "Excellent grocery access ({raw_value} miles) - walking distance to stores",
            "medium": "Good grocery access ({raw_value} miles) - short drive to stores",
            "low": "Far from grocery stores ({raw_value} miles) - plan for longer shopping trips",
            "improvement": "Properties within 1 mile of grocery stores score highest",
            "unknown": "Grocery distance unknown - check Google Maps for nearby Fry's, Safeway, Sprouts",
        },
        "Parks & Walkability": {
            "high": "Excellent walkability with parks, sidewalks, and trail access nearby",
            "medium": "Average walkability - some parks and sidewalks in the area",
            "low": "Limited walkability - few parks or sidewalks nearby",
            "improvement": "Properties near city parks and with sidewalk infrastructure score higher",
            "unknown": "Walkability data unavailable - check for parks and sidewalks during visit",
        },
        "Sun Orientation": {
            "high": "Optimal orientation ({raw_value}) - minimizes afternoon sun exposure and cooling costs",
            "medium": "Moderate orientation ({raw_value}) - balanced sun exposure throughout day",
            "low": "West-facing ({raw_value}) - highest cooling costs due to intense afternoon sun",
            "improvement": "North-facing properties score highest (25pts vs 0pts for west-facing)",
            "unknown": "Orientation unknown - check satellite view to determine facade direction",
        },
        "Flood Risk": {
            "high": "Minimal flood risk ({raw_value}) - no flood insurance required",
            "medium": "Moderate flood risk ({raw_value}) - 500-year flood zone, insurance recommended",
            "low": "High flood risk ({raw_value}) - flood insurance required, potential damage concerns",
            "improvement": "Properties in Zone X (minimal risk) score highest and avoid insurance costs",
            "unknown": "Flood zone unknown - check FEMA flood maps for official designation",
        },
        "Walk/Transit": {
            "high": "Excellent walkability and transit access ({raw_value}) - car-optional lifestyle possible",
            "medium": "Moderate walkability ({raw_value}) - some amenities within walking distance",
            "low": "Car-dependent location ({raw_value}) - limited walking and transit options",
            "improvement": "Downtown Phoenix, Tempe, and Old Town Scottsdale have highest walk/transit scores",
            "unknown": "Walk Score data unavailable - check WalkScore.com for detailed analysis",
        },
        "Air Quality": {
            "high": "Good air quality ({raw_value} AQI) - healthy environment for outdoor activities",
            "medium": "Moderate air quality ({raw_value} AQI) - generally acceptable with occasional issues",
            "low": "Poor air quality ({raw_value} AQI) - may affect sensitive individuals",
            "improvement": "Properties away from freeways and industrial areas have better air quality",
            "unknown": "Air quality data unavailable - check EPA AirNow for local AQI readings",
        },
        "Roof Condition/Age": {
            "high": "New/recently replaced roof ({raw_value} years old) - no near-term replacement needed",
            "medium": "Roof in fair condition ({raw_value} years old) - monitor for wear, budget for future",
            "low": "Aging roof ({raw_value} years old) - replacement likely needed soon ($8-15K typical)",
            "improvement": "AZ heat shortens roof life to 15-20 years; newer roofs score higher",
            "unknown": "Roof age unknown - request inspection during due diligence",
        },
        "Backyard Utility": {
            "high": "Large usable backyard - excellent outdoor living space",
            "medium": "Average backyard size - adequate outdoor space",
            "low": "Limited backyard - minimal outdoor entertaining area",
            "improvement": "Larger lots (7k-15k sqft) with covered patios score highest",
            "unknown": "Backyard size unknown - verify lot square footage and layout during showing",
        },
        "Plumbing/Electrical Systems": {
            "high": "Modern systems ({raw_value} build) - copper plumbing, updated electrical panels",
            "medium": "Systems showing age ({raw_value} build) - may need updates in 10-15 years",
            "low": "Older systems ({raw_value} build) - budget for potential upgrades",
            "improvement": "Post-2000 builds have modern 200A service and copper plumbing",
            "unknown": "Build year unknown - verify electrical panel and plumbing materials",
        },
        "Pool Condition": {
            "high": "Pool equipment in excellent condition ({raw_value} years old) - low maintenance burden",
            "medium": "Pool equipment aging ({raw_value} years old) - budget for equipment replacement",
            "low": "Pool equipment needs replacement ({raw_value} years old) - expect $3-8K costs soon",
            "improvement": "Pool equipment lasts 7-10 years in AZ; newer equipment reduces costs",
            "no_pool": "No pool - neutral score (no maintenance burden but no amenity either)",
            "unknown": "Pool equipment age unknown - request pool inspection during due diligence",
        },
        "Cost Efficiency": {
            "high": "Very affordable ({raw_value}/month) - well within target budget range",
            "medium": "At budget ({raw_value}/month) - manageable monthly costs",
            "low": "Above budget ({raw_value}/month) - stretching monthly affordability",
            "improvement": "Total monthly cost includes mortgage, taxes, insurance, HOA, pool, solar lease",
            "unknown": "Cost estimate unavailable - calculate mortgage + property tax + HOA + utilities",
        },
        "Solar Status": {
            "high": "Owned solar panels - valuable asset that reduces utility costs",
            "medium": "No solar - neutral impact, no burden or benefit",
            "low": "Leased solar - monthly payment obligation and potential transfer complications",
            "improvement": "Owned solar adds 4-7% to home value; leased solar is a liability",
            "unknown": "Solar status unknown - verify ownership vs lease with seller/listing agent",
        },
        "Kitchen Layout": {
            "high": "Excellent kitchen - modern, open layout with ample counter space",
            "medium": "Adequate kitchen - functional layout with room for updates",
            "low": "Dated kitchen - closed layout, limited counter space, may need renovation",
            "improvement": "Open concept kitchens with islands and modern appliances score highest",
            "unknown": "Kitchen assessment pending - review photos or visit to evaluate",
        },
        "Master Suite": {
            "high": "Spacious master suite - large bedroom, walk-in closet, luxurious bath",
            "medium": "Adequate master - standard size with acceptable closet and bath",
            "low": "Small master suite - limited space, basic closet and bathroom",
            "improvement": "Look for dual sinks, separate tub/shower, and walk-in closets",
            "unknown": "Master suite assessment pending - review photos or visit to evaluate",
        },
        "Natural Light": {
            "high": "Abundant natural light - large windows, skylights, bright interior",
            "medium": "Adequate natural light - standard windows, reasonably bright",
            "low": "Limited natural light - small windows, darker interior",
            "improvement": "Skylights and larger windows significantly improve natural light scores",
            "unknown": "Natural light assessment pending - visit property during daytime",
        },
        "High Ceilings": {
            "high": "Vaulted/high ceilings ({raw_value}) - spacious, open feel",
            "medium": "Standard ceilings ({raw_value}) - typical residential height",
            "low": "Low ceilings ({raw_value}) - may feel cramped",
            "improvement": "Vaulted or 10ft+ ceilings score highest for open, airy feel",
            "unknown": "Ceiling height unknown - verify during showing or from listing details",
        },
        "Fireplace": {
            "high": "Gas fireplace present - adds ambiance and convenience",
            "medium": "Wood-burning fireplace - aesthetic feature, less convenient",
            "low": "No fireplace - not a major factor in AZ climate",
            "improvement": "Fireplaces add ambiance; gas is preferred for convenience",
            "unknown": "Fireplace presence unknown - check listing details or photos",
        },
        "Laundry Area": {
            "high": "Dedicated laundry room - convenient, separated from living areas",
            "medium": "Laundry closet - functional but limited space",
            "low": "Garage laundry only - less convenient, exposed to temperature extremes",
            "improvement": "Dedicated indoor laundry rooms with sinks score highest",
            "unknown": "Laundry setup unknown - verify location during showing",
        },
        "Overall Aesthetics": {
            "high": "Beautiful, modern finishes - move-in ready with contemporary appeal",
            "medium": "Average appearance - functional but may benefit from updates",
            "low": "Dated aesthetics - needs cosmetic updates to modernize",
            "improvement": "Updated flooring, paint, and fixtures significantly improve aesthetics",
            "unknown": "Aesthetics assessment pending - review photos or visit to evaluate",
        },
    }

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        thresholds: TierThresholds | None = None,
    ) -> None:
        """Initialize ScoringExplainer with configuration.

        Args:
            weights: Scoring weights configuration. If None, uses defaults.
            thresholds: Tier thresholds configuration. If None, uses defaults.
        """
        self._weights = weights or ScoringWeights()
        self._thresholds = thresholds or TierThresholds()

    def explain(
        self,
        property: "Property",
        breakdown: "ScoreBreakdown",
    ) -> FullScoreExplanation:
        """Generate complete explanation for a property's scores.

        Args:
            property: Property entity with all data fields
            breakdown: ScoreBreakdown with all calculated scores

        Returns:
            FullScoreExplanation with detailed explanations for each criterion
        """
        # Calculate tier information
        tier, tier_threshold, next_tier, points_to_next = self._determine_tier_info(
            breakdown.total_score
        )

        # Build section explanations
        sections = [
            self._explain_section(
                "Location & Environment",
                "A",
                breakdown.location_scores,
                self._weights.section_a_max,
                property,
            ),
            self._explain_section(
                "Lot & Systems",
                "B",
                breakdown.systems_scores,
                self._weights.section_b_max,
                property,
            ),
            self._explain_section(
                "Interior & Features",
                "C",
                breakdown.interior_scores,
                self._weights.section_c_max,
                property,
            ),
        ]

        # Identify top strengths and improvement opportunities
        all_criteria = []
        for section in sections:
            all_criteria.extend(section.criteria)

        top_strengths = [
            f"{c.criterion}: {c.reasoning}"
            for c in sorted(all_criteria, key=lambda x: x.percentage, reverse=True)
            if c.percentage >= 70
        ][:5]

        key_improvements = [
            f"{c.criterion}: {c.improvement_tip}"
            for c in sorted(all_criteria, key=lambda x: x.percentage)
            if c.percentage < 50 and c.improvement_tip
        ][:5]

        # Generate overall summary
        summary = self._generate_summary(breakdown.total_score, tier, sections)

        # Get address
        address = getattr(property, "full_address", None) or getattr(property, "address", "Unknown")

        return FullScoreExplanation(
            address=str(address),
            total_score=breakdown.total_score,
            max_score=float(self._weights.total_possible_score),
            tier=tier,
            tier_threshold=tier_threshold,
            next_tier=next_tier,
            points_to_next_tier=points_to_next,
            sections=sections,
            summary=summary,
            top_strengths=top_strengths,
            key_improvements=key_improvements,
        )

    def _explain_section(
        self,
        section_name: str,
        section_letter: str,
        scores: list["Score"],
        max_score: int,
        property: "Property",
    ) -> SectionExplanation:
        """Generate explanation for a scoring section.

        Args:
            section_name: Full section name
            section_letter: Single letter identifier (A, B, C)
            scores: List of Score value objects in this section
            max_score: Maximum possible score for this section
            property: Property entity for raw value lookups

        Returns:
            SectionExplanation with all criterion details
        """
        total_score = sum(s.weighted_score for s in scores)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        criteria = [
            self._explain_criterion(score, property)
            for score in scores
        ]

        # Identify strengths and weaknesses
        strengths = [c.criterion for c in criteria if c.percentage >= 70]
        weaknesses = [c.criterion for c in criteria if c.percentage < 50]

        # Generate section summary
        if percentage >= 75:
            summary = f"Excellent {section_name.lower()} with strong scores across criteria."
        elif percentage >= 60:
            summary = f"Good {section_name.lower()} with some areas for improvement."
        elif percentage >= 45:
            summary = f"Average {section_name.lower()} with notable weaknesses to consider."
        else:
            summary = f"Below average {section_name.lower()} - significant concerns in this area."

        return SectionExplanation(
            section=section_name,
            section_letter=section_letter,
            total_score=total_score,
            max_score=float(max_score),
            percentage=percentage,
            criteria=criteria,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    def _explain_criterion(
        self,
        score: "Score",
        property: "Property",
    ) -> ScoreExplanation:
        """Generate explanation for a single criterion.

        Args:
            score: Score value object with criterion details
            property: Property entity for raw value lookup

        Returns:
            ScoreExplanation with reasoning and improvement tips
        """
        criterion = score.criterion
        weighted_score = score.weighted_score
        max_score = score.weight
        percentage = score.percentage

        # Get raw value from property
        raw_value = self._get_raw_value(criterion, property)

        # Determine level and get template
        templates = self.CRITERION_TEMPLATES.get(criterion, {})

        if raw_value is None and "unknown" in templates:
            reasoning = templates["unknown"]
        elif percentage >= 70:
            reasoning = templates.get("high", "Strong score for this criterion")
        elif percentage >= 40:
            reasoning = templates.get("medium", "Average score for this criterion")
        else:
            reasoning = templates.get("low", "Below average for this criterion")

        # Special handling for pool with no pool
        if criterion == "Pool Condition" and not getattr(property, "has_pool", True):
            reasoning = templates.get("no_pool", "No pool - neutral score")

        # Format reasoning with raw value if present
        if raw_value is not None and "{raw_value}" in reasoning:
            reasoning = reasoning.format(raw_value=raw_value)
        elif "{raw_value}" in reasoning:
            reasoning = reasoning.replace(" ({raw_value})", "").replace("{raw_value}", "")

        improvement_tip = templates.get("improvement")

        return ScoreExplanation(
            criterion=criterion,
            score=weighted_score,
            max_score=max_score,
            percentage=percentage,
            raw_value=str(raw_value) if raw_value is not None else None,
            reasoning=reasoning,
            improvement_tip=improvement_tip,
        )

    def _get_raw_value(self, criterion: str, property: "Property") -> Any:
        """Extract raw data value for a criterion from property.

        Maps criterion names to property field values for display.

        Args:
            criterion: Criterion name
            property: Property entity

        Returns:
            Raw value for display, or None if unavailable
        """
        # Mapping of criterion names to property attributes and formatting
        field_mappings: dict[str, tuple[str, str | None]] = {
            "School District Rating": ("school_rating", "{}/10"),
            "Quietness/Noise Level": ("distance_to_highway_miles", "{:.1f}"),
            "Noise Level": ("noise_score", "{}/100"),
            "Crime Index": ("violent_crime_index", "{}"),  # Will composite with property_crime
            "Supermarket Proximity": ("distance_to_grocery_miles", "{:.1f}"),
            "Parks & Walkability": ("parks_walkability_score", "{}/10"),
            "Sun Orientation": ("orientation", None),  # Special handling
            "Flood Risk": ("flood_zone", None),  # Special handling
            "Walk/Transit": ("walk_score", "{}"),
            "Air Quality": ("air_quality_aqi", "{}"),
            "Roof Condition/Age": ("roof_age", "{}"),
            "Backyard Utility": ("backyard_utility_score", "{}/10"),
            "Plumbing/Electrical Systems": ("year_built", "{}"),
            "Pool Condition": ("pool_equipment_age", "{}"),
            "Cost Efficiency": (None, None),  # Special handling for monthly_costs
            "Solar Status": ("solar_status", None),  # Special handling
            "Kitchen Layout": ("kitchen_layout_score", "{}/10"),
            "Master Suite": ("master_suite_score", "{}/10"),
            "Natural Light": ("natural_light_score", "{}/10"),
            "High Ceilings": ("high_ceilings_score", None),
            "Fireplace": ("fireplace_present", None),
            "Laundry Area": ("laundry_area_score", "{}/10"),
            "Overall Aesthetics": ("aesthetics_score", "{}/10"),
        }

        if criterion not in field_mappings:
            return None

        field_name, format_str = field_mappings[criterion]

        # Special cases
        if criterion == "Sun Orientation":
            orientation = getattr(property, "orientation", None)
            if isinstance(orientation, Orientation):
                return orientation.value.capitalize()
            elif orientation:
                return str(orientation).capitalize()
            return None

        if criterion == "Flood Risk":
            zone = getattr(property, "flood_zone", None)
            if isinstance(zone, FloodZone):
                return f"Zone {zone.value.upper()}"
            elif zone:
                return f"Zone {str(zone).upper()}"
            return None

        if criterion == "Solar Status":
            status = getattr(property, "solar_status", None)
            if isinstance(status, SolarStatus):
                return status.value.capitalize()
            elif status:
                return str(status).capitalize()
            return None

        if criterion == "Cost Efficiency":
            monthly_costs = getattr(property, "monthly_costs", None)
            if monthly_costs and isinstance(monthly_costs, dict):
                total = sum(monthly_costs.values())
                return f"${total:,.0f}"
            return None

        if criterion == "Crime Index":
            violent = getattr(property, "violent_crime_index", None)
            property_crime = getattr(property, "property_crime_index", None)
            if violent is not None and property_crime is not None:
                composite = (violent * 0.6) + (property_crime * 0.4)
                return f"{composite:.0f}/100 safety index"
            elif violent is not None:
                return f"{violent:.0f}/100 violent crime index"
            return None

        if criterion == "Fireplace":
            has_fireplace = getattr(property, "fireplace_present", None)
            if has_fireplace is True:
                return "Yes"
            elif has_fireplace is False:
                return "No"
            return None

        if criterion == "High Ceilings":
            score = getattr(property, "high_ceilings_score", None)
            if score is not None:
                if score >= 9:
                    return "Vaulted/cathedral"
                elif score >= 7:
                    return "10+ feet"
                elif score >= 5:
                    return "9 feet"
                elif score >= 3:
                    return "8 feet standard"
                else:
                    return "<8 feet"
            return None

        # Standard field lookup
        if field_name is None:
            return None

        value = getattr(property, field_name, None)
        if value is None:
            return None

        if format_str:
            try:
                return format_str.format(value)
            except (ValueError, TypeError):
                return str(value)
        return value

    def _determine_tier_info(
        self, total: float
    ) -> tuple[str, float, str | None, float | None]:
        """Determine tier classification and points to next tier.

        Args:
            total: Total weighted score

        Returns:
            Tuple of (tier_name, tier_threshold, next_tier, points_to_next)
        """
        if total > self._thresholds.unicorn_min:
            return ("Unicorn", float(self._thresholds.unicorn_min), None, None)
        elif total >= self._thresholds.contender_min:
            points_to_unicorn = self._thresholds.unicorn_min - total + 1
            return (
                "Contender",
                float(self._thresholds.contender_min),
                "Unicorn",
                points_to_unicorn,
            )
        else:
            points_to_contender = self._thresholds.contender_min - total
            return (
                "Pass",
                0.0,
                "Contender",
                points_to_contender,
            )

    def _generate_summary(
        self,
        total_score: float,
        tier: str,
        sections: list[SectionExplanation],
    ) -> str:
        """Generate overall narrative summary.

        Args:
            total_score: Total weighted score
            tier: Tier classification
            sections: List of section explanations

        Returns:
            One-sentence summary of property quality
        """
        # Find strongest and weakest sections
        sorted_sections = sorted(sections, key=lambda s: s.percentage, reverse=True)
        strongest = sorted_sections[0]
        weakest = sorted_sections[-1]

        if tier == "Unicorn":
            return f"Exceptional property with standout {strongest.section.lower()}"
        elif tier == "Contender":
            if weakest.percentage < 50:
                return f"Strong candidate with {weakest.section.lower()} as primary improvement area"
            else:
                return "Strong candidate with balanced scores across all sections"
        else:
            return f"Meets minimum criteria but lacks standout features; {weakest.section.lower()} is the main concern"
