"""Console reporter for PHX Home Analysis.

Generates formatted terminal output with ANSI color codes for visual clarity.
"""

from pathlib import Path

from ..domain.entities import Property
from ..domain.enums import RiskLevel, Tier
from .base import Reporter


class ConsoleReporter(Reporter):
    """Generate formatted console output with color coding.

    Prints property analysis results to terminal with ANSI color codes
    for tier classification and risk levels.

    Supports both compact summaries and detailed property listings.
    """

    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

    def __init__(self, use_color: bool = True, compact: bool = False) -> None:
        """Initialize console reporter.

        Args:
            use_color: If True, use ANSI color codes. Set False for plain text.
            compact: If True, use compact one-line-per-property format.
        """
        self.use_color = use_color
        self.compact = compact

    def generate(self, properties: list[Property], output_path: Path) -> None:
        """Generate console report (prints to stdout, ignores output_path).

        Args:
            properties: List of Property entities to display
            output_path: Ignored (console output goes to stdout)

        Raises:
            ValueError: If properties list is empty
        """
        if not properties:
            raise ValueError("Cannot generate console report from empty properties list")

        self.print_summary(properties)

    def print_summary(self, properties: list[Property]) -> None:
        """Print summary statistics and top properties.

        Args:
            properties: List of Property entities
        """
        # Calculate statistics
        total_properties = len(properties)
        passing = [p for p in properties if p.kill_switch_passed]
        failing = [p for p in properties if not p.kill_switch_passed]

        unicorns = [p for p in passing if p.tier == Tier.UNICORN]
        contenders = [p for p in passing if p.tier == Tier.CONTENDER]
        pass_tier = [p for p in passing if p.tier == Tier.PASS]

        # Print header
        self._print_header("Phoenix Home Analysis Summary")

        # Print tier distribution
        self._print_section("Tier Distribution")
        self._print_tier_line("Unicorn", len(unicorns), Tier.UNICORN)
        self._print_tier_line("Contender", len(contenders), Tier.CONTENDER)
        self._print_tier_line("Pass", len(pass_tier), Tier.PASS)
        self._print_tier_line("Failed", len(failing), Tier.FAILED)
        print(f"{'Total Properties:':<20} {total_properties}")
        print()

        # Print top 5 properties
        if passing:
            self._print_section("Top 5 Properties (by Score)")
            sorted_passing = sorted(passing, key=lambda p: p.total_score, reverse=True)
            for i, prop in enumerate(sorted_passing[:5], start=1):
                self._print_property_line(i, prop)

    def print_detailed(self, properties: list[Property]) -> None:
        """Print detailed property listings.

        Args:
            properties: List of Property entities
        """
        passing = [p for p in properties if p.kill_switch_passed]
        sorted_passing = sorted(passing, key=lambda p: p.total_score, reverse=True)

        self._print_header("Detailed Property Analysis")

        for rank, prop in enumerate(sorted_passing, start=1):
            self._print_property_detailed(rank, prop)
            print()

    def _print_header(self, title: str) -> None:
        """Print formatted header.

        Args:
            title: Header text
        """
        print()
        print("=" * 80)
        if self.use_color:
            print(f"{self.BOLD}{self.BLUE}{title}{self.RESET}")
        else:
            print(title)
        print("=" * 80)
        print()

    def _print_section(self, title: str) -> None:
        """Print section header.

        Args:
            title: Section title
        """
        if self.use_color:
            print(f"{self.BOLD}{title}{self.RESET}")
        else:
            print(title)
        print("-" * 40)

    def _print_tier_line(self, label: str, count: int, tier: Tier) -> None:
        """Print tier count line with color.

        Args:
            label: Tier label
            count: Number of properties in tier
            tier: Tier enum for color coding
        """
        color = self._get_tier_color(tier)
        if self.use_color:
            print(f"{label + ':':<20} {color}{count}{self.RESET}")
        else:
            print(f"{label + ':':<20} {count}")

    def _print_property_line(self, rank: int, prop: Property) -> None:
        """Print compact property line.

        Args:
            rank: Property rank
            prop: Property entity
        """
        tier_color = self._get_tier_color(prop.tier) if prop.tier else ""
        tier_label = prop.tier.label if prop.tier else "Unknown"

        if self.use_color:
            print(
                f"{rank:2d}. {tier_color}{tier_label:10}{self.RESET} "
                f"{prop.total_score:5.1f} pts | "
                f"{prop.price:>12} | "
                f"{prop.short_address}"
            )
        else:
            print(
                f"{rank:2d}. {tier_label:10} "
                f"{prop.total_score:5.1f} pts | "
                f"{prop.price:>12} | "
                f"{prop.short_address}"
            )

    def _print_property_detailed(self, rank: int, prop: Property) -> None:
        """Print detailed property information.

        Args:
            rank: Property rank
            prop: Property entity
        """
        tier_color = self._get_tier_color(prop.tier) if prop.tier else ""
        tier_label = prop.tier.label if prop.tier else "Unknown"

        if self.use_color:
            print(f"{self.BOLD}#{rank} - {prop.full_address}{self.RESET}")
            print(f"Tier: {tier_color}{tier_label}{self.RESET} | Score: {prop.total_score:.1f}/600")
        else:
            print(f"#{rank} - {prop.full_address}")
            print(f"Tier: {tier_label} | Score: {prop.total_score:.1f}/600")

        print(f"Price: {prop.price} | {prop.beds}bd/{prop.baths}ba | {prop.sqft:,} sqft")

        if prop.score_breakdown:
            print(
                f"Scores: Location {prop.score_breakdown.location_total:.1f}/230 | "
                f"Systems {prop.score_breakdown.systems_total:.1f}/180 | "
                f"Interior {prop.score_breakdown.interior_total:.1f}/190"
            )

        # Print high risks if any
        if prop.high_risks:
            print(f"{self.RED if self.use_color else ''}High Risks:{self.RESET if self.use_color else ''}")
            for risk in prop.high_risks:
                print(f"  - [{risk.category}] {risk.description}")

    def _get_tier_color(self, tier: Tier) -> str:
        """Get ANSI color code for tier.

        Args:
            tier: Tier enum

        Returns:
            ANSI color code string (empty if use_color is False)
        """
        if not self.use_color:
            return ""

        return {
            Tier.UNICORN: self.MAGENTA,
            Tier.CONTENDER: self.BLUE,
            Tier.PASS: self.GREEN,
            Tier.FAILED: self.RED,
        }.get(tier, self.RESET)

    def _get_risk_color(self, risk_level: RiskLevel) -> str:
        """Get ANSI color code for risk level.

        Args:
            risk_level: RiskLevel enum

        Returns:
            ANSI color code string (empty if use_color is False)
        """
        if not self.use_color:
            return ""

        return {
            RiskLevel.HIGH: self.RED,
            RiskLevel.MEDIUM: self.YELLOW,
            RiskLevel.LOW: self.GREEN,
            RiskLevel.POSITIVE: self.CYAN,
            RiskLevel.UNKNOWN: self.RESET,
        }.get(risk_level, self.RESET)
