"""Domain enums with encapsulated business logic.

This module defines enums for the PHX Home Analysis domain with behavioral
properties that encapsulate business rules and prevent logic duplication.
"""

from enum import Enum


class RiskLevel(Enum):
    """Risk level classification with scoring and visualization properties."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    POSITIVE = "positive"
    UNKNOWN = "unknown"

    @property
    def score(self) -> float:
        """Score multiplier for risk assessment (0-10 scale).

        Returns:
            Float score where 0 is highest risk, 10 is most positive
        """
        return {
            RiskLevel.HIGH: 0.0,
            RiskLevel.MEDIUM: 5.0,
            RiskLevel.LOW: 7.5,
            RiskLevel.POSITIVE: 10.0,
            RiskLevel.UNKNOWN: 5.0,
        }[self]

    @property
    def css_class(self) -> str:
        """CSS class name for styling in reports.

        Returns:
            CSS class string for web rendering
        """
        return f"risk-{self.value}"

    @property
    def color(self) -> str:
        """Hex color code for visualization.

        Returns:
            Hex color string
        """
        return {
            RiskLevel.HIGH: "#dc3545",  # Red
            RiskLevel.MEDIUM: "#ffc107",  # Yellow
            RiskLevel.LOW: "#28a745",  # Green
            RiskLevel.POSITIVE: "#007bff",  # Blue
            RiskLevel.UNKNOWN: "#6c757d",  # Gray
        }[self]


class Tier(Enum):
    """Property tier classification based on total score.

    Tiers represent property quality/desirability (600 pts max):
    - UNICORN: >480 points (80%) - Exceptional properties
    - CONTENDER: 360-480 points (60-80%) - Strong candidates
    - PASS: <360 points (<60%) - Meets minimum criteria
    - FAILED: 0 points - Kill switch failure
    """

    UNICORN = "unicorn"
    CONTENDER = "contender"
    PASS = "pass"
    FAILED = "failed"

    @property
    def color(self) -> str:
        """Hex color code for tier visualization.

        Returns:
            Hex color string
        """
        return {
            Tier.UNICORN: "#9d4edd",  # Purple
            Tier.CONTENDER: "#3a86ff",  # Blue
            Tier.PASS: "#06d6a0",  # Teal
            Tier.FAILED: "#ef476f",  # Red
        }[self]

    @property
    def label(self) -> str:
        """Human-readable tier label.

        Returns:
            Display label for UI
        """
        return {
            Tier.UNICORN: "Unicorn",
            Tier.CONTENDER: "Contender",
            Tier.PASS: "Pass",
            Tier.FAILED: "Failed",
        }[self]

    @property
    def icon(self) -> str:
        """Unicode icon representing tier.

        Returns:
            Unicode emoji/symbol
        """
        return {
            Tier.UNICORN: "🦄",
            Tier.CONTENDER: "⭐",
            Tier.PASS: "✓",
            Tier.FAILED: "✗",
        }[self]

    @classmethod
    def from_score(cls, score: float, kill_switch_passed: bool) -> "Tier":
        """Classify tier based on total score and kill switch status.

        Args:
            score: Total weighted score (0-600)
            kill_switch_passed: Whether property passed all kill switches

        Returns:
            Tier classification
        """
        if not kill_switch_passed:
            return cls.FAILED

        if score > 480:
            return cls.UNICORN
        elif score >= 360:
            return cls.CONTENDER
        else:
            return cls.PASS


class SolarStatus(Enum):
    """Solar panel ownership status with cost implications."""

    OWNED = "owned"
    LEASED = "leased"
    NONE = "none"
    UNKNOWN = "unknown"

    @property
    def is_problematic(self) -> bool:
        """Whether solar status creates financial/legal complications.

        Leased solar creates monthly payment obligations and transfer complications.

        Returns:
            True if leased (problematic), False otherwise
        """
        return self == SolarStatus.LEASED

    @property
    def description(self) -> str:
        """Human-readable description of solar status.

        Returns:
            Status description
        """
        return {
            SolarStatus.OWNED: "Owned - Value add, transferable",
            SolarStatus.LEASED: "Leased - Monthly cost burden, transfer complications",
            SolarStatus.NONE: "No solar panels",
            SolarStatus.UNKNOWN: "Solar status unknown",
        }[self]


class SewerType(Enum):
    """Sewer system type with acceptability for buyer criteria."""

    CITY = "city"
    SEPTIC = "septic"
    UNKNOWN = "unknown"

    @property
    def is_acceptable(self) -> bool:
        """Whether sewer type meets buyer requirements.

        Kill switch: Only city sewer is acceptable.

        Returns:
            True if city sewer, False otherwise
        """
        return self == SewerType.CITY

    @property
    def description(self) -> str:
        """Human-readable description of sewer type.

        Returns:
            Sewer type description
        """
        return {
            SewerType.CITY: "City sewer - Municipal wastewater system",
            SewerType.SEPTIC: "Septic system - On-site waste treatment",
            SewerType.UNKNOWN: "Sewer type unknown",
        }[self]


class Orientation(Enum):
    """Property orientation (direction front/main facade faces).

    Orientation affects cooling costs in Phoenix climate:
    - West-facing: Highest cooling costs (afternoon sun)
    - North-facing: Best (minimal direct sun)
    - South-facing: Moderate cooling costs
    - East-facing: Morning sun, cooler afternoons
    """

    N = "north"
    S = "south"
    E = "east"
    W = "west"
    NE = "northeast"
    NW = "northwest"
    SE = "southeast"
    SW = "southwest"
    UNKNOWN = "unknown"

    @property
    def cooling_cost_multiplier(self) -> float:
        """Cooling cost multiplier relative to baseline.

        Returns:
            Multiplier where 1.0 is baseline, >1.0 is higher cost
        """
        return {
            Orientation.N: 0.85,  # Best case
            Orientation.NE: 0.90,
            Orientation.NW: 0.90,
            Orientation.E: 0.95,
            Orientation.S: 1.0,  # Baseline
            Orientation.SE: 1.05,
            Orientation.SW: 1.15,
            Orientation.W: 1.25,  # Worst case
            Orientation.UNKNOWN: 1.0,
        }[self]

    @property
    def base_score(self) -> float:
        """Base score for sun orientation criterion (0-10 scale).

        Part of Section A: Location & Environment (30 pts max).
        West-facing is penalized due to high Arizona cooling costs.

        Returns:
            Score on 0-10 scale where 10 is best (north), 0 is worst (west)
        """
        return {
            Orientation.N: 10.0,  # Best
            Orientation.NE: 8.5,
            Orientation.NW: 8.5,
            Orientation.E: 7.5,
            Orientation.S: 6.0,
            Orientation.SE: 5.0,
            Orientation.SW: 3.0,
            Orientation.W: 0.0,  # Worst
            Orientation.UNKNOWN: 5.0,  # Neutral
        }[self]

    @property
    def description(self) -> str:
        """Human-readable description of orientation impact.

        Returns:
            Orientation description with cooling impact
        """
        descriptions = {
            Orientation.N: "North-facing - Best for Arizona (minimal direct sun)",
            Orientation.NE: "Northeast-facing - Excellent (morning sun only)",
            Orientation.NW: "Northwest-facing - Excellent (minimal afternoon sun)",
            Orientation.E: "East-facing - Good (morning sun, cooler afternoons)",
            Orientation.S: "South-facing - Moderate cooling costs",
            Orientation.SE: "Southeast-facing - Moderate (some afternoon exposure)",
            Orientation.SW: "Southwest-facing - High cooling costs (afternoon sun)",
            Orientation.W: "West-facing - Highest cooling costs (intense afternoon sun)",
            Orientation.UNKNOWN: "Orientation unknown",
        }
        return descriptions[self]

    @classmethod
    def from_string(cls, value: str | None) -> "Orientation":
        """Parse orientation from string value.

        Args:
            value: String representation (e.g., 'N', 'north', 'NORTH')

        Returns:
            Orientation enum value, defaults to UNKNOWN if invalid
        """
        if not value:
            return cls.UNKNOWN

        value_normalized = value.strip().lower()

        mapping = {
            "n": cls.N,
            "north": cls.N,
            "s": cls.S,
            "south": cls.S,
            "e": cls.E,
            "east": cls.E,
            "w": cls.W,
            "west": cls.W,
            "ne": cls.NE,
            "northeast": cls.NE,
            "nw": cls.NW,
            "northwest": cls.NW,
            "se": cls.SE,
            "southeast": cls.SE,
            "sw": cls.SW,
            "southwest": cls.SW,
        }

        return mapping.get(value_normalized, cls.UNKNOWN)


class ImageSource(Enum):
    """Image source identifiers for property image extraction."""

    MARICOPA_ASSESSOR = "maricopa_assessor"
    PHOENIX_MLS = "phoenix_mls"
    ZILLOW = "zillow"
    REDFIN = "redfin"

    @property
    def display_name(self) -> str:
        """Human-readable source name.

        Returns:
            Display name for UI
        """
        return {
            ImageSource.MARICOPA_ASSESSOR: "Maricopa County Assessor",
            ImageSource.PHOENIX_MLS: "Phoenix MLS",
            ImageSource.ZILLOW: "Zillow",
            ImageSource.REDFIN: "Redfin",
        }[self]

    @property
    def base_url(self) -> str:
        """Base URL for the image source.

        Returns:
            Base URL string
        """
        return {
            ImageSource.MARICOPA_ASSESSOR: "https://mcassessor.maricopa.gov",
            ImageSource.PHOENIX_MLS: "https://phoenixmlssearch.com",
            ImageSource.ZILLOW: "https://www.zillow.com",
            ImageSource.REDFIN: "https://www.redfin.com",
        }[self]

    @property
    def requires_browser(self) -> bool:
        """Whether source requires browser automation (JavaScript).

        Returns:
            True if Playwright needed, False if simple HTTP works
        """
        return self in {ImageSource.ZILLOW, ImageSource.REDFIN}

    @property
    def rate_limit_seconds(self) -> float:
        """Recommended delay between requests to avoid rate limiting.

        Returns:
            Delay in seconds
        """
        return {
            ImageSource.MARICOPA_ASSESSOR: 2.0,  # Conservative for gov site
            ImageSource.PHOENIX_MLS: 1.0,
            ImageSource.ZILLOW: 0.5,
            ImageSource.REDFIN: 0.5,
        }[self]


class ImageStatus(Enum):
    """Image processing status for tracking extraction pipeline state."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        """Whether this is a final/completed state.

        Returns:
            True if image processing is complete (success or failure)
        """
        return self in {
            ImageStatus.PROCESSED,
            ImageStatus.DUPLICATE,
            ImageStatus.FAILED,
        }

    @property
    def is_success(self) -> bool:
        """Whether this represents successful processing.

        Returns:
            True if image was successfully processed
        """
        return self == ImageStatus.PROCESSED

    @property
    def description(self) -> str:
        """Human-readable status description.

        Returns:
            Status description
        """
        return {
            ImageStatus.PENDING: "Awaiting download",
            ImageStatus.DOWNLOADING: "Currently downloading",
            ImageStatus.DOWNLOADED: "Downloaded, awaiting processing",
            ImageStatus.PROCESSING: "Converting and standardizing",
            ImageStatus.PROCESSED: "Successfully processed",
            ImageStatus.DUPLICATE: "Duplicate detected and skipped",
            ImageStatus.FAILED: "Processing failed",
        }[self]


class FloodZone(Enum):
    """FEMA flood zone designations."""

    X = "x"  # Minimal flood risk (outside 500-year)
    X_SHADED = "x_shaded"  # Moderate (500-year flood zone)
    A = "a"  # High risk (100-year, no BFE)
    AE = "ae"  # High risk (100-year with BFE)
    AH = "ah"  # Shallow flooding
    AO = "ao"  # Sheet flow areas
    VE = "ve"  # Coastal high hazard
    UNKNOWN = "unknown"

    @property
    def risk_level(self) -> str:
        """Map zone to risk level.

        Returns:
            Risk level string: 'high', 'moderate', 'minimal', or 'unknown'
        """
        high_risk = {FloodZone.A, FloodZone.AE, FloodZone.AH, FloodZone.AO, FloodZone.VE}
        if self in high_risk:
            return "high"
        elif self == FloodZone.X_SHADED:
            return "moderate"
        elif self == FloodZone.X:
            return "minimal"
        return "unknown"

    @property
    def requires_insurance(self) -> bool:
        """Whether flood insurance is required.

        Returns:
            True if flood insurance is federally required
        """
        return self in {FloodZone.A, FloodZone.AE, FloodZone.AH, FloodZone.AO, FloodZone.VE}


class CrimeRiskLevel(Enum):
    """Crime risk classification."""

    LOW = "low"  # Index 80-100 (safest)
    MODERATE = "moderate"  # Index 50-79
    HIGH = "high"  # Index 20-49
    VERY_HIGH = "very_high"  # Index 0-19
    UNKNOWN = "unknown"

    @classmethod
    def from_index(cls, index: float | None) -> "CrimeRiskLevel":
        """Convert crime index (0-100, 100=safest) to risk level.

        Args:
            index: Crime safety index where 100 is safest, 0 is most dangerous

        Returns:
            CrimeRiskLevel classification
        """
        if index is None:
            return cls.UNKNOWN
        if index >= 80:
            return cls.LOW
        if index >= 50:
            return cls.MODERATE
        if index >= 20:
            return cls.HIGH
        return cls.VERY_HIGH


class PhaseStatus(str, Enum):
    """Status values for pipeline phases.

    Valid transitions:
    - NEW → pending
    - pending → in_progress | skipped
    - in_progress → completed | failed
    - failed → in_progress (retry)
    - completed → (terminal)
    - skipped → (terminal)
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkItemStatus(str, Enum):
    """Status values for work items.

    Valid transitions:
    - NEW → pending
    - pending → in_progress | blocked
    - in_progress → completed | failed | blocked
    - failed → in_progress (retry)
    - blocked → in_progress (unblock)
    - completed → (terminal)
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
