"""Confidence display utilities for reports and UI."""

from enum import Enum


class ConfidenceLevel(Enum):
    """Human-readable confidence levels."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @classmethod
    def from_score(cls, confidence: float) -> "ConfidenceLevel":
        """Convert confidence score to level.

        Args:
            confidence: Float from 0.0 to 1.0.

        Returns:
            ConfidenceLevel enum.
        """
        if confidence >= 0.90:
            return cls.HIGH
        elif confidence >= 0.70:
            return cls.MEDIUM
        else:
            return cls.LOW

    @property
    def color(self) -> str:
        """Get color indicator for confidence level.

        Returns:
            Color name for UI display.
        """
        colors = {
            ConfidenceLevel.HIGH: "green",
            ConfidenceLevel.MEDIUM: "yellow",
            ConfidenceLevel.LOW: "red",
        }
        return colors[self]

    @property
    def badge(self) -> str:
        """Get badge text for confidence level.

        Returns:
            Badge text for reports.
        """
        badges = {
            ConfidenceLevel.HIGH: "",  # No badge needed
            ConfidenceLevel.MEDIUM: "Verify",
            ConfidenceLevel.LOW: "Unverified",
        }
        return badges[self]


def format_confidence(confidence: float, include_badge: bool = True) -> str:
    """Format confidence score for display.

    Args:
        confidence: Float from 0.0 to 1.0.
        include_badge: Whether to include badge text.

    Returns:
        Formatted string (e.g., "High (0.95)" or "Medium (0.82) [Verify]").
    """
    level = ConfidenceLevel.from_score(confidence)
    score_str = f"{confidence:.2f}"

    parts = [level.value, f"({score_str})"]
    if include_badge and level.badge:
        parts.append(f"[{level.badge}]")

    return " ".join(parts)


def get_confidence_html(confidence: float) -> str:
    """Generate HTML badge for confidence display.

    Args:
        confidence: Float from 0.0 to 1.0.

    Returns:
        HTML string with colored badge.
    """
    level = ConfidenceLevel.from_score(confidence)
    badge_text = level.badge or "Verified"

    return f'<span class="confidence-badge confidence-{level.color}">{badge_text}</span>'
