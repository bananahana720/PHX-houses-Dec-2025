"""Deal sheet reporter for generating HTML property analysis reports.

This module provides the DealSheetReporter class for generating comprehensive
HTML deal sheets that include scoring breakdowns, kill-switch results, and
property recommendations.

Implements the Reporter interface for E7 integration.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import Reporter

if TYPE_CHECKING:
    from ..domain.entities import Property
    from ..domain.value_objects import ScoreBreakdown


class DealSheetReporter(Reporter):
    """Generate HTML deal sheets for property analysis results.

    Implements the Reporter interface pattern for HTML deal sheet output.
    Designed for E7 (Deal Sheet Generation) integration with comprehensive
    property analysis presentation.

    The deal sheet includes:
    - Property overview (address, price, specs)
    - Score breakdown by section (A/B/C)
    - Tier classification with visual indicators
    - Kill-switch verdict summary
    - Key strengths and improvement opportunities
    - Cost analysis summary

    Attributes:
        template_path: Path to HTML template file (E7.S1 will implement)

    Example:
        reporter = DealSheetReporter()
        reporter.generate(properties, Path("output/deal_sheets"))
    """

    def __init__(self, template_path: Path | None = None) -> None:
        """Initialize the DealSheetReporter.

        Args:
            template_path: Optional path to custom HTML template.
                          Defaults to built-in template (E7.S1).
        """
        self.template_path = template_path

    def generate(self, properties: list[Property], output_path: Path) -> None:
        """Generate deal sheet HTML for properties.

        Creates comprehensive HTML deal sheets for each property in the list,
        including score breakdowns, tier classifications, and recommendations.

        Args:
            properties: Properties with scores and kill-switch verdicts.
                       Each property should have score_breakdown populated.
            output_path: Directory path where HTML deal sheets will be written.
                        One file per property: {address_slug}.html

        Raises:
            NotImplementedError: E7.S1 will implement this method.
            ValueError: If properties list is empty.
            IOError: If output_path cannot be written.

        Note:
            This is a stub for E7 integration. Full implementation in E7.S1.
        """
        raise NotImplementedError(
            "DealSheetReporter.generate() will be implemented in E7.S1. "
            "See docs/epics/epic-7-reporting-output.md for requirements."
        )

    def format_score_breakdown(self, breakdown: ScoreBreakdown) -> dict:
        """Prepare ScoreBreakdown for HTML template rendering.

        Transforms a ScoreBreakdown value object into a dictionary format
        suitable for Jinja2/HTML template rendering. Includes section scores,
        percentages, tier information, and visual styling hints.

        Args:
            breakdown: ScoreBreakdown value object with populated scores.

        Returns:
            dict: Template-ready dictionary containing:
                - sections: List of section dicts with scores/percentages
                - total: Overall score and percentage
                - tier: Tier classification with styling info
                - chart_data: Data formatted for radar/bar chart rendering

        Raises:
            NotImplementedError: E7.S1 will implement this method.

        Example:
            data = reporter.format_score_breakdown(property.score_breakdown)
            # Returns:
            # {
            #     "sections": [
            #         {"name": "Location", "letter": "A", "score": 187.5,
            #          "max": 250, "percentage": 75.0, "color": "#4CAF50"},
            #         ...
            #     ],
            #     "total": {"score": 453.75, "max": 605, "percentage": 75.0},
            #     "tier": {"name": "Contender", "emoji": "medal",
            #              "color": "#2196F3", "description": "..."},
            #     "chart_data": {...}
            # }

        Note:
            This is a stub for E7 integration. Full implementation in E7.S1.
        """
        raise NotImplementedError(
            "DealSheetReporter.format_score_breakdown() will be implemented in E7.S1."
        )

    def generate_single(self, property_: Property, output_path: Path) -> Path:
        """Generate deal sheet HTML for a single property.

        Convenience method for generating a single property's deal sheet.

        Args:
            property_: Property entity with score_breakdown populated.
            output_path: Directory path where HTML file will be written.

        Returns:
            Path: Full path to generated HTML file.

        Raises:
            NotImplementedError: E7.S1 will implement this method.

        Note:
            This is a stub for E7 integration. Full implementation in E7.S1.
        """
        raise NotImplementedError(
            "DealSheetReporter.generate_single() will be implemented in E7.S1."
        )


# Note: ScoringExplainer integration
#
# The ScoringExplainer class (in services/scoring/explanation.py) provides
# human-readable explanations for property scores. For E7 deal sheet integration:
#
#     from phx_home_analysis.services.scoring.explanation import (
#         ScoringExplainer,
#         FullScoreExplanation,
#     )
#
#     explainer = ScoringExplainer()
#     explanation = explainer.explain(property, score_breakdown)
#
#     # For HTML templates
#     explanation_dict = explanation.to_dict()
#
#     # For markdown reports
#     explanation_text = explanation.to_text()
#
# See Also:
#     - services/scoring/explanation.py: Full implementation
#     - docs/schemas/score_breakdown_schema.md: Schema documentation
