"""Scoring display formatting utilities for reporters.

This module provides consistent formatting utilities for scores, percentages,
and tier classifications across all reporter implementations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..domain.value_objects import ScoreBreakdown

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TierDisplayInfo:
    """Display information for a tier classification.

    Provides consistent styling information for tier badges across
    all reporter formats (HTML, console, PDF).

    Attributes:
        name: Tier name (Unicorn, Contender, Pass, Failed)
        emoji: Unicode emoji for visual indicator
        color_hex: Hex color code for styling
        color_name: Named color for CSS classes
        description: Brief description of tier meaning
        css_class: CSS class name for HTML styling
    """

    name: str
    emoji: str
    color_hex: str
    color_name: str
    description: str
    css_class: str


class ScoringFormatter:
    """Utility class for scoring display formatting.

    Provides consistent formatting for scores, percentages, and tiers
    across all reporter implementations. Static methods ensure formatting
    consistency without requiring instance state.

    Usage:
        percentage_str = ScoringFormatter.format_section_percentage(187.5, 250)
        # Returns: "75.0%"

        tier_info = ScoringFormatter.format_tier_badge("Unicorn")
        # Returns: TierDisplayInfo(name="Unicorn", emoji="unicorn", ...)
    """

    # Tier display configurations
    TIER_CONFIGS: dict[str, TierDisplayInfo] = {
        "Unicorn": TierDisplayInfo(
            name="Unicorn",
            emoji="\U0001f984",  # unicorn
            color_hex="#9C27B0",
            color_name="purple",
            description="Top-tier property - rare exceptional find (>=80%)",
            css_class="tier-unicorn",
        ),
        "Contender": TierDisplayInfo(
            name="Contender",
            emoji="\U0001f3c5",  # medal
            color_hex="#2196F3",
            color_name="blue",
            description="Strong candidate - worth serious consideration (60-79%)",
            css_class="tier-contender",
        ),
        "Pass": TierDisplayInfo(
            name="Pass",
            emoji="\U00002705",  # check mark
            color_hex="#4CAF50",
            color_name="green",
            description="Meets minimum criteria - baseline acceptable (<60%)",
            css_class="tier-pass",
        ),
        "Failed": TierDisplayInfo(
            name="Failed",
            emoji="\U0000274c",  # cross mark
            color_hex="#F44336",
            color_name="red",
            description="Kill-switch failure - does not meet requirements",
            css_class="tier-failed",
        ),
    }

    # Section display configurations
    SECTION_CONFIGS: dict[str, dict] = {
        "A": {
            "name": "Location & Environment",
            "short_name": "Location",
            "max": 250,
            "color_hex": "#2196F3",
            "icon": "\U0001f4cd",  # pin
        },
        "B": {
            "name": "Lot & Systems",
            "short_name": "Systems",
            "max": 175,
            "color_hex": "#FF9800",
            "icon": "\U0001f3e0",  # house
        },
        "C": {
            "name": "Interior & Features",
            "short_name": "Interior",
            "max": 180,
            "color_hex": "#4CAF50",
            "icon": "\U0001f6cb",  # couch
        },
    }

    @staticmethod
    def format_section_percentage(score: float, max_score: float) -> str:
        """Format section score as percentage string.

        Args:
            score: Actual score achieved
            max_score: Maximum possible score for section

        Returns:
            Formatted percentage string with one decimal place.
            Returns "0.0%" if max_score is zero.

        Example:
            >>> ScoringFormatter.format_section_percentage(187.5, 250)
            "75.0%"
        """
        if max_score <= 0:
            return "0.0%"
        percentage = (score / max_score) * 100
        return f"{percentage:.1f}%"

    @staticmethod
    def format_tier_badge(tier: str) -> TierDisplayInfo:
        """Return tier display info (emoji, color, label).

        Args:
            tier: Tier name (Unicorn, Contender, Pass, Failed)

        Returns:
            TierDisplayInfo with styling and description for the tier.
            Returns Pass tier info if tier name is unrecognized (with warning logged).

        Example:
            >>> info = ScoringFormatter.format_tier_badge("Unicorn")
            >>> info.emoji
            '\\U0001F984'
            >>> info.color_hex
            '#9C27B0'
        """
        if tier not in ScoringFormatter.TIER_CONFIGS:
            logger.warning(
                "Unrecognized tier name '%s'. Valid tiers are: %s. Defaulting to 'Pass'.",
                tier,
                list(ScoringFormatter.TIER_CONFIGS.keys()),
            )
            return ScoringFormatter.TIER_CONFIGS["Pass"]
        return ScoringFormatter.TIER_CONFIGS[tier]

    @staticmethod
    def format_score_fraction(score: float, max_score: float) -> str:
        """Format score as fraction string.

        Args:
            score: Actual score achieved
            max_score: Maximum possible score

        Returns:
            Formatted fraction string (e.g., "187.5/250")

        Example:
            >>> ScoringFormatter.format_score_fraction(187.5, 250)
            "187.5/250"
        """
        return f"{score:.1f}/{max_score:.0f}"

    @staticmethod
    def format_points_to_tier(current_score: float, tier_threshold: float) -> str:
        """Format points needed to reach next tier.

        Args:
            current_score: Current total score
            tier_threshold: Threshold for next tier

        Returns:
            Formatted string showing points needed or achievement message.

        Example:
            >>> ScoringFormatter.format_points_to_tier(450, 484)
            "34 points to Unicorn"
        """
        points_needed = tier_threshold - current_score
        if points_needed <= 0:
            return "Tier achieved!"
        return f"{points_needed:.0f} points needed"

    @staticmethod
    def format_score_bar(score: float, max_score: float, width: int = 20) -> str:
        """Generate ASCII progress bar for score visualization.

        Args:
            score: Actual score achieved
            max_score: Maximum possible score
            width: Width of progress bar in characters

        Returns:
            ASCII progress bar string with percentage.

        Example:
            >>> ScoringFormatter.format_score_bar(187.5, 250)
            "[###############-----] 75%"
        """
        if max_score <= 0:
            return "[" + "-" * width + "] 0%"
        percentage = score / max_score
        filled = int(percentage * width)
        empty = width - filled
        percentage_display = int(percentage * 100)
        return f"[{'#' * filled}{'-' * empty}] {percentage_display}%"

    @staticmethod
    def get_section_info(section_letter: str) -> dict:
        """Get section display configuration.

        Args:
            section_letter: Section identifier (A, B, or C)

        Returns:
            Dictionary with section name, max score, color, and icon.
            Returns Section A info if letter is unrecognized.

        Example:
            >>> info = ScoringFormatter.get_section_info("A")
            >>> info["name"]
            "Location & Environment"
        """
        return ScoringFormatter.SECTION_CONFIGS.get(
            section_letter.upper(), ScoringFormatter.SECTION_CONFIGS["A"]
        )

    @staticmethod
    def format_breakdown_summary(breakdown: ScoreBreakdown) -> dict:
        """Format ScoreBreakdown as summary dictionary.

        Convenience method that combines section formatting with
        overall totals for template rendering.

        Args:
            breakdown: ScoreBreakdown value object

        Returns:
            Dictionary with formatted sections and totals suitable
            for template rendering.

        Example:
            summary = ScoringFormatter.format_breakdown_summary(breakdown)
            # Returns:
            # {
            #     "sections": [
            #         {"letter": "A", "name": "Location", "score": 187.5,
            #          "max": 250, "percentage": "75.0%", "bar": "[###..."}
            #         ...
            #     ],
            #     "total": {"score": 453.75, "max": 605, "percentage": "75.0%"}
            # }
        """
        sections = [
            {
                "letter": "A",
                "name": ScoringFormatter.SECTION_CONFIGS["A"]["short_name"],
                "full_name": ScoringFormatter.SECTION_CONFIGS["A"]["name"],
                "score": round(breakdown.location_total, 1),
                "max": breakdown.SECTION_A_MAX,
                "percentage": ScoringFormatter.format_section_percentage(
                    breakdown.location_total, breakdown.SECTION_A_MAX
                ),
                "bar": ScoringFormatter.format_score_bar(
                    breakdown.location_total, breakdown.SECTION_A_MAX
                ),
                "color": ScoringFormatter.SECTION_CONFIGS["A"]["color_hex"],
                "icon": ScoringFormatter.SECTION_CONFIGS["A"]["icon"],
            },
            {
                "letter": "B",
                "name": ScoringFormatter.SECTION_CONFIGS["B"]["short_name"],
                "full_name": ScoringFormatter.SECTION_CONFIGS["B"]["name"],
                "score": round(breakdown.systems_total, 1),
                "max": breakdown.SECTION_B_MAX,
                "percentage": ScoringFormatter.format_section_percentage(
                    breakdown.systems_total, breakdown.SECTION_B_MAX
                ),
                "bar": ScoringFormatter.format_score_bar(
                    breakdown.systems_total, breakdown.SECTION_B_MAX
                ),
                "color": ScoringFormatter.SECTION_CONFIGS["B"]["color_hex"],
                "icon": ScoringFormatter.SECTION_CONFIGS["B"]["icon"],
            },
            {
                "letter": "C",
                "name": ScoringFormatter.SECTION_CONFIGS["C"]["short_name"],
                "full_name": ScoringFormatter.SECTION_CONFIGS["C"]["name"],
                "score": round(breakdown.interior_total, 1),
                "max": breakdown.SECTION_C_MAX,
                "percentage": ScoringFormatter.format_section_percentage(
                    breakdown.interior_total, breakdown.SECTION_C_MAX
                ),
                "bar": ScoringFormatter.format_score_bar(
                    breakdown.interior_total, breakdown.SECTION_C_MAX
                ),
                "color": ScoringFormatter.SECTION_CONFIGS["C"]["color_hex"],
                "icon": ScoringFormatter.SECTION_CONFIGS["C"]["icon"],
            },
        ]

        return {
            "sections": sections,
            "total": {
                "score": round(breakdown.total_score, 1),
                "max": breakdown.TOTAL_MAX,
                "percentage": ScoringFormatter.format_section_percentage(
                    breakdown.total_score, breakdown.TOTAL_MAX
                ),
                "bar": ScoringFormatter.format_score_bar(
                    breakdown.total_score, breakdown.TOTAL_MAX, width=30
                ),
            },
        }

    @staticmethod
    def determine_tier(total_score: float, kill_switch_passed: bool = True) -> str:
        """Determine tier classification from score.

        Args:
            total_score: Total property score (0-605)
            kill_switch_passed: Whether property passed kill-switches

        Returns:
            Tier name string (Unicorn, Contender, Pass, or Failed)

        Example:
            >>> ScoringFormatter.determine_tier(490)
            "Unicorn"
            >>> ScoringFormatter.determine_tier(400, kill_switch_passed=False)
            "Failed"
        """
        if not kill_switch_passed:
            return "Failed"
        if total_score >= 484:
            return "Unicorn"
        if total_score >= 363:
            return "Contender"
        return "Pass"
