"""Immutable value objects for PHX Home Analysis domain.

Value objects are immutable data structures that encapsulate domain concepts
and provide computed properties based on their state.
"""

from dataclasses import dataclass

from .enums import RiskLevel


@dataclass(frozen=True)
class Address:
    """Immutable address value object.

    Represents a property's physical location with computed display formats.
    """

    street: str
    city: str
    state: str
    zip_code: str

    @property
    def full_address(self) -> str:
        """Complete formatted address.

        Returns:
            Full address string (e.g., "123 Main St, Phoenix, AZ 85001")
        """
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"

    @property
    def short_address(self) -> str:
        """Short address format (street and city only).

        Returns:
            Abbreviated address (e.g., "123 Main St, Phoenix")
        """
        return f"{self.street}, {self.city}"

    def __str__(self) -> str:
        """String representation uses full address format."""
        return self.full_address


@dataclass(frozen=True)
class Score:
    """Immutable score value object for weighted scoring system.

    Represents a single scoring criterion with base score, weight, and
    computed weighted value.
    """

    criterion: str
    base_score: float  # 0-10 scale
    weight: float  # Maximum possible points for this criterion
    note: str | None = None

    def __post_init__(self) -> None:
        """Validate score constraints."""
        if not 0 <= self.base_score <= 10:
            raise ValueError(f"base_score must be 0-10, got {self.base_score}")
        if self.weight < 0:
            raise ValueError(f"weight must be non-negative, got {self.weight}")

    @property
    def weighted_score(self) -> float:
        """Calculate weighted score based on base score and weight.

        Formula: (base_score / 10) * weight

        Returns:
            Weighted score (0 to weight maximum)
        """
        return (self.base_score / 10.0) * self.weight

    @property
    def max_possible(self) -> float:
        """Maximum possible score for this criterion.

        Returns:
            Weight value (maximum achievable points)
        """
        return self.weight

    @property
    def percentage(self) -> float:
        """Score as percentage of maximum possible.

        Returns:
            Percentage (0-100)
        """
        if self.weight == 0:
            return 0.0
        return (self.weighted_score / self.weight) * 100

    def __str__(self) -> str:
        """String representation shows criterion and weighted score."""
        return f"{self.criterion}: {self.weighted_score:.1f}/{self.weight} pts"


@dataclass(frozen=True)
class RiskAssessment:
    """Immutable risk assessment value object.

    Represents identified risks, concerns, or opportunities for a property.
    """

    category: str  # e.g., "Structural", "Financial", "Location"
    level: RiskLevel
    description: str
    mitigation: str | None = None

    @property
    def score(self) -> float:
        """Numeric score based on risk level.

        Returns:
            Float score from risk level (0-10 scale)
        """
        return self.level.score

    @property
    def is_high_risk(self) -> bool:
        """Whether this represents a high-risk concern.

        Returns:
            True if risk level is HIGH
        """
        return self.level == RiskLevel.HIGH

    def __str__(self) -> str:
        """String representation shows category, level, and description."""
        return f"[{self.category}] {self.level.value.upper()}: {self.description}"


@dataclass(frozen=True)
class ScoreBreakdown:
    """Immutable score breakdown value object.

    Aggregates scores across the three main scoring sections with
    computed totals and percentages.
    """

    location_scores: list[Score]  # Section A: Location & Environment (max 230 pts)
    systems_scores: list[Score]  # Section B: Lot & Systems (max 180 pts)
    interior_scores: list[Score]  # Section C: Interior & Features (max 190 pts)

    @property
    def location_total(self) -> float:
        """Total score for Location & Environment section.

        Returns:
            Sum of weighted scores (0-230 pts)
        """
        return sum(score.weighted_score for score in self.location_scores)

    @property
    def systems_total(self) -> float:
        """Total score for Lot & Systems section.

        Returns:
            Sum of weighted scores (0-180 pts)
        """
        return sum(score.weighted_score for score in self.systems_scores)

    @property
    def interior_total(self) -> float:
        """Total score for Interior & Features section.

        Returns:
            Sum of weighted scores (0-190 pts)
        """
        return sum(score.weighted_score for score in self.interior_scores)

    @property
    def total_score(self) -> float:
        """Total weighted score across all sections.

        Returns:
            Sum of all section totals (0-600 pts)
        """
        return self.location_total + self.systems_total + self.interior_total

    @property
    def location_percentage(self) -> float:
        """Location section score as percentage of maximum.

        Returns:
            Percentage (0-100)
        """
        return (self.location_total / 230) * 100

    @property
    def systems_percentage(self) -> float:
        """Systems section score as percentage of maximum.

        Returns:
            Percentage (0-100)
        """
        return (self.systems_total / 180) * 100

    @property
    def interior_percentage(self) -> float:
        """Interior section score as percentage of maximum.

        Returns:
            Percentage (0-100)
        """
        return (self.interior_total / 190) * 100

    @property
    def total_percentage(self) -> float:
        """Total score as percentage of maximum possible.

        Returns:
            Percentage (0-100)
        """
        return (self.total_score / 600) * 100

    def __str__(self) -> str:
        """String representation shows section totals and overall score."""
        return (
            f"Location: {self.location_total:.1f}/230 | "
            f"Systems: {self.systems_total:.1f}/180 | "
            f"Interior: {self.interior_total:.1f}/190 | "
            f"Total: {self.total_score:.1f}/600"
        )


@dataclass(frozen=True)
class RenovationEstimate:
    """Immutable renovation cost estimate value object.

    Tracks estimated costs across different renovation categories.
    All values in USD.
    """

    cosmetic: float = 0.0  # Paint, fixtures, minor updates
    kitchen: float = 0.0  # Kitchen renovation/updates
    bathrooms: float = 0.0  # Bathroom renovation/updates
    flooring: float = 0.0  # Flooring replacement
    hvac: float = 0.0  # HVAC replacement/repair
    roof: float = 0.0  # Roof replacement/repair
    pool: float = 0.0  # Pool equipment/resurfacing
    landscaping: float = 0.0  # Yard improvements
    other: float = 0.0  # Miscellaneous repairs

    def __post_init__(self) -> None:
        """Validate cost constraints."""
        costs = [
            self.cosmetic,
            self.kitchen,
            self.bathrooms,
            self.flooring,
            self.hvac,
            self.roof,
            self.pool,
            self.landscaping,
            self.other,
        ]
        for cost in costs:
            if cost < 0:
                raise ValueError(f"Renovation costs must be non-negative, got {cost}")

    @property
    def total(self) -> float:
        """Total estimated renovation cost.

        Returns:
            Sum of all category costs in USD
        """
        return (
            self.cosmetic
            + self.kitchen
            + self.bathrooms
            + self.flooring
            + self.hvac
            + self.roof
            + self.pool
            + self.landscaping
            + self.other
        )

    @property
    def major_items(self) -> list[tuple[str, float]]:
        """List of major renovation items (>$1000) sorted by cost.

        Returns:
            List of (category, cost) tuples for items over $1000, descending
        """
        items = [
            ("Cosmetic", self.cosmetic),
            ("Kitchen", self.kitchen),
            ("Bathrooms", self.bathrooms),
            ("Flooring", self.flooring),
            ("HVAC", self.hvac),
            ("Roof", self.roof),
            ("Pool", self.pool),
            ("Landscaping", self.landscaping),
            ("Other", self.other),
        ]
        major = [(name, cost) for name, cost in items if cost > 1000]
        return sorted(major, key=lambda x: x[1], reverse=True)

    def __str__(self) -> str:
        """String representation shows total cost."""
        return f"Total Renovation Estimate: ${self.total:,.0f}"


@dataclass(frozen=True)
class PerceptualHash:
    """Immutable perceptual hash value object for image deduplication.

    Stores multiple hash types for robust duplicate detection:
    - phash: Primary perceptual hash, robust to scaling/compression
    - dhash: Difference hash, good for detecting crops

    Uses Hamming distance to compare hashes - lower distance means
    more similar images.
    """

    phash: str  # 64-bit perceptual hash as hex string (16 chars)
    dhash: str  # 64-bit difference hash as hex string (16 chars)

    def __post_init__(self) -> None:
        """Validate hash format."""
        for hash_name, hash_value in [("phash", self.phash), ("dhash", self.dhash)]:
            if not isinstance(hash_value, str):
                raise ValueError(f"{hash_name} must be a string, got {type(hash_value)}")
            if len(hash_value) != 16:
                raise ValueError(
                    f"{hash_name} must be 16 hex characters, got {len(hash_value)}"
                )

    def hamming_distance(self, other: "PerceptualHash") -> int:
        """Calculate Hamming distance between phash values.

        The Hamming distance is the number of positions where corresponding
        bits differ. Lower distance = more similar images.

        Args:
            other: Another PerceptualHash to compare against

        Returns:
            Number of differing bits (0-64)
        """
        # Convert hex to binary and count differences
        int_self = int(self.phash, 16)
        int_other = int(other.phash, 16)
        xor_result = int_self ^ int_other
        return bin(xor_result).count("1")

    def is_similar_to(self, other: "PerceptualHash", threshold: int = 8) -> bool:
        """Check if two images are perceptually similar.

        Uses Hamming distance on phash with default threshold of 8.
        Typical thresholds:
        - 0: Exact match
        - 1-5: Very similar (minor compression differences)
        - 6-10: Similar (same image, different processing)
        - 11+: Different images

        Args:
            other: Hash to compare against
            threshold: Maximum Hamming distance to consider similar (default 8)

        Returns:
            True if images are likely duplicates
        """
        return self.hamming_distance(other) <= threshold

    def dhash_distance(self, other: "PerceptualHash") -> int:
        """Calculate Hamming distance between dhash values.

        Used as secondary confirmation for edge cases.

        Args:
            other: Another PerceptualHash to compare against

        Returns:
            Number of differing bits (0-64)
        """
        int_self = int(self.dhash, 16)
        int_other = int(other.dhash, 16)
        xor_result = int_self ^ int_other
        return bin(xor_result).count("1")

    def __str__(self) -> str:
        """String representation shows abbreviated hashes."""
        return f"pHash:{self.phash[:8]}... dHash:{self.dhash[:8]}..."


@dataclass(frozen=True)
class ImageMetadata:
    """Immutable metadata for a downloaded property image.

    Tracks all information about an image from download through processing.
    """

    image_id: str  # UUID or hash-based identifier
    property_address: str  # Links to Property.full_address
    source: str  # ImageSource value
    source_url: str  # Original download URL
    local_path: str  # Path to processed image (relative to images dir)
    original_path: str | None  # Path to raw image if preserved
    phash: str  # Perceptual hash for deduplication
    dhash: str  # Difference hash
    width: int
    height: int
    file_size_bytes: int
    status: str  # ImageStatus value
    downloaded_at: str  # ISO format timestamp
    processed_at: str | None = None  # ISO format timestamp
    is_duplicate: bool = False
    duplicate_of: str | None = None  # image_id of canonical image
    error_message: str | None = None

    @property
    def perceptual_hash(self) -> PerceptualHash:
        """Construct PerceptualHash value object from stored hashes.

        Returns:
            PerceptualHash instance
        """
        return PerceptualHash(phash=self.phash, dhash=self.dhash)

    @property
    def filename(self) -> str:
        """Extract filename from local path.

        Returns:
            Just the filename portion of local_path
        """
        return self.local_path.split("/")[-1].split("\\")[-1]

    @property
    def size_kb(self) -> float:
        """File size in kilobytes.

        Returns:
            Size in KB
        """
        return self.file_size_bytes / 1024

    def __str__(self) -> str:
        """String representation shows source and filename."""
        return f"[{self.source}] {self.filename} ({self.width}x{self.height})"
