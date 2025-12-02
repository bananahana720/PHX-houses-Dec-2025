"""Image naming convention generator for categorized property images.

Generates consistent, parseable filenames that encode:
- Property hash (8 chars)
- Location category (ext, int, sys, feat)
- Subject type (kitchen, master, pool, etc.)
- Confidence score (00-99)
- Source (z=zillow, r=redfin, m=maricopa, p=phoenix_mls)
- Capture date (YYYYMMDD)
- Sequence number (for duplicates in same category)

Format: {hash}_{loc}_{subj}_{conf}_{src}_{date}[_{seq}].png
Example: ef7cd95f_int_kitchen_95_z_20241201.png
         ef7cd95f_int_kitchen_95_z_20241201_02.png (second kitchen image)
"""

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .categorizer import CategoryResult, ImageLocation, ImageSubject

# Source code mapping
SOURCE_CODES = {
    "zillow": "z",
    "redfin": "r",
    "maricopa_assessor": "m",
    "phoenix_mls": "p",
    "unknown": "u",
}

SOURCE_NAMES = {v: k for k, v in SOURCE_CODES.items()}


@dataclass
class ImageName:
    """Structured image filename with encoded metadata.

    Attributes:
        property_hash: 8-character property identifier
        location: Location category code (ext, int, sys, feat)
        subject: Subject type (kitchen, master, pool, etc.)
        confidence: Confidence score 0-99
        source: Source code (z, r, m, p)
        capture_date: Date image was captured/listed
        sequence: Sequence number for multiple images in same category
        extension: File extension (default .png)
    """

    property_hash: str
    location: str
    subject: str
    confidence: int
    source: str
    capture_date: date
    sequence: int = 0
    extension: str = ".png"

    def __post_init__(self) -> None:
        """Validate components."""
        if len(self.property_hash) != 8:
            raise ValueError(f"property_hash must be 8 chars, got {len(self.property_hash)}")
        if not 0 <= self.confidence <= 99:
            raise ValueError(f"confidence must be 0-99, got {self.confidence}")
        if len(self.source) != 1:
            raise ValueError(f"source must be single char, got '{self.source}'")

    def __str__(self) -> str:
        """Generate filename string.

        Returns:
            Filename like 'ef7cd95f_int_kitchen_95_z_20241201.png'
        """
        parts = [
            self.property_hash,
            self.location,
            self.subject,
            f"{self.confidence:02d}",
            self.source,
            self.capture_date.strftime("%Y%m%d"),
        ]
        if self.sequence > 0:
            parts.append(f"{self.sequence:02d}")

        return "_".join(parts) + self.extension

    @property
    def filename(self) -> str:
        """Alias for __str__ for clarity.

        Returns:
            Filename string
        """
        return str(self)

    @property
    def relative_path(self) -> str:
        """Generate path relative to property directory.

        Returns:
            Path like 'ef7cd95f/ef7cd95f_int_kitchen_95_z_20241201.png'
        """
        return f"{self.property_hash}/{self.filename}"

    @property
    def source_name(self) -> str:
        """Get full source name from code.

        Returns:
            Source name like 'zillow', 'redfin', etc.
        """
        return SOURCE_NAMES.get(self.source, "unknown")

    @property
    def location_enum(self) -> ImageLocation:
        """Get ImageLocation enum from code.

        Returns:
            ImageLocation enum value
        """
        return ImageLocation.from_string(self.location)

    @property
    def subject_enum(self) -> ImageSubject:
        """Get ImageSubject enum from string.

        Returns:
            ImageSubject enum value
        """
        return ImageSubject.from_string(self.subject)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "property_hash": self.property_hash,
            "location": self.location,
            "subject": self.subject,
            "confidence": self.confidence,
            "source": self.source,
            "capture_date": self.capture_date.isoformat(),
            "sequence": self.sequence,
            "extension": self.extension,
            "filename": self.filename,
        }

    @classmethod
    def parse(cls, filename: str) -> "ImageName":
        """Parse filename back to ImageName components.

        Args:
            filename: Filename like 'ef7cd95f_int_kitchen_95_z_20241201.png'
                      or 'ef7cd95f_int_kitchen_95_z_20241201_02.png'

        Returns:
            ImageName instance

        Raises:
            ValueError: If filename format is invalid
        """
        # Remove path if present
        if "/" in filename or "\\" in filename:
            filename = Path(filename).name

        # Remove extension
        stem, ext = filename.rsplit(".", 1) if "." in filename else (filename, "png")

        # Parse components
        parts = stem.split("_")

        # Minimum: hash_loc_subj_conf_src_date (6 parts)
        # Maximum: hash_loc_subj_conf_src_date_seq (7 parts)
        if len(parts) < 6:
            raise ValueError(f"Invalid filename format: {filename} (too few parts)")

        try:
            property_hash = parts[0]
            location = parts[1]
            subject = parts[2]
            confidence = int(parts[3])
            source = parts[4]
            capture_date = date(
                year=int(parts[5][:4]),
                month=int(parts[5][4:6]),
                day=int(parts[5][6:8]),
            )
            sequence = int(parts[6]) if len(parts) > 6 else 0

            return cls(
                property_hash=property_hash,
                location=location,
                subject=subject,
                confidence=confidence,
                source=source,
                capture_date=capture_date,
                sequence=sequence,
                extension=f".{ext}",
            )

        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid filename format: {filename} - {e}") from e

    @classmethod
    def from_category_result(
        cls,
        property_hash: str,
        category: CategoryResult,
        source: str,
        listing_date: date | None = None,
        sequence: int = 0,
    ) -> "ImageName":
        """Create ImageName from categorization result.

        Args:
            property_hash: 8-character property identifier
            category: CategoryResult from AI categorization
            source: Source identifier (zillow, redfin, etc.)
            listing_date: Date of listing (defaults to today)
            sequence: Sequence number if multiple in same category

        Returns:
            ImageName instance
        """
        source_code = SOURCE_CODES.get(source.lower(), "u")

        return cls(
            property_hash=property_hash,
            location=category.location.value,
            subject=category.subject.value,
            confidence=category.confidence_percent,
            source=source_code,
            capture_date=listing_date or date.today(),
            sequence=sequence,
        )


def generate_image_name(
    property_hash: str,
    category: CategoryResult,
    source: str,
    listing_date: date | None = None,
    existing_names: list[str] | None = None,
) -> ImageName:
    """Generate unique image name, handling collisions.

    If an image with the same category/source/date already exists,
    increments the sequence number to ensure uniqueness.

    Args:
        property_hash: 8-character property identifier
        category: CategoryResult from AI categorization
        source: Source identifier (zillow, redfin, etc.)
        listing_date: Date of listing (defaults to today)
        existing_names: List of existing filenames to check for collisions

    Returns:
        ImageName instance with unique filename
    """
    existing_names = existing_names or []
    existing_set = set(existing_names)

    # Start with sequence 0
    sequence = 0

    while True:
        image_name = ImageName.from_category_result(
            property_hash=property_hash,
            category=category,
            source=source,
            listing_date=listing_date,
            sequence=sequence,
        )

        if image_name.filename not in existing_set:
            return image_name

        sequence += 1

        # Safety limit to prevent infinite loops
        if sequence > 99:
            raise ValueError(
                f"Too many images in same category: {property_hash}_{category.location.value}_{category.subject.value}"
            )


def extract_category_from_filename(filename: str) -> tuple[str, str] | None:
    """Extract location and subject from filename.

    Args:
        filename: Filename to parse

    Returns:
        Tuple of (location, subject) or None if parsing fails
    """
    try:
        image_name = ImageName.parse(filename)
        return (image_name.location, image_name.subject)
    except ValueError:
        return None


def is_categorized_filename(filename: str) -> bool:
    """Check if filename follows categorized naming convention.

    Args:
        filename: Filename to check

    Returns:
        True if filename matches expected pattern
    """
    try:
        ImageName.parse(filename)
        return True
    except ValueError:
        return False


# Pattern for validating/matching categorized filenames
FILENAME_PATTERN = re.compile(
    r"^[a-f0-9]{8}_"  # property hash
    r"(ext|int|sys|feat)_"  # location
    r"[a-z_]+_"  # subject
    r"\d{2}_"  # confidence
    r"[zrmpu]_"  # source
    r"\d{8}"  # date
    r"(_\d{2})?"  # optional sequence
    r"\.(png|jpg|jpeg)$",  # extension
    re.IGNORECASE,
)


def matches_naming_pattern(filename: str) -> bool:
    """Quick regex check if filename matches naming pattern.

    Faster than full parsing for bulk filtering.

    Args:
        filename: Filename to check

    Returns:
        True if matches pattern
    """
    if "/" in filename or "\\" in filename:
        filename = Path(filename).name
    return bool(FILENAME_PATTERN.match(filename))
