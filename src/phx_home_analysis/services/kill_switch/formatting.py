"""Verdict formatting utilities for kill-switch results.

This module provides human-readable formatting for kill-switch verdicts
and comprehensive result breakdowns with accessibility support.

Usage:
    from phx_home_analysis.services.kill_switch import (
        format_verdict,
        format_result,
        KillSwitchResult,
    )

    # Simple verdict formatting
    print(format_verdict(KillSwitchVerdict.PASS))   # "PASS" with green circle
    print(format_verdict(KillSwitchVerdict.FAIL))   # "FAIL" with red circle

    # Full result breakdown
    print(format_result(result))          # With emoji
    print(format_result(result, plain_text=True))  # Without emoji
"""

from .base import SEVERITY_FAIL_THRESHOLD, KillSwitchVerdict
from .result import KillSwitchResult

# Emoji mapping for verdicts (accessible: always includes text)
VERDICT_EMOJI = {
    KillSwitchVerdict.PASS: "\U0001f7e2",  # Green circle
    KillSwitchVerdict.WARNING: "\U0001f7e1",  # Yellow circle
    KillSwitchVerdict.FAIL: "\U0001f534",  # Red circle
}

# Plain text alternatives (no emoji)
VERDICT_TEXT = {
    KillSwitchVerdict.PASS: "[PASS]",
    KillSwitchVerdict.WARNING: "[WARNING]",
    KillSwitchVerdict.FAIL: "[FAIL]",
}


def format_verdict(verdict: KillSwitchVerdict, plain_text: bool = False) -> str:
    """Format a verdict with emoji and text.

    Always includes text alongside emoji for screen reader compatibility.

    Args:
        verdict: The KillSwitchVerdict to format
        plain_text: If True, omit emoji for non-emoji environments

    Returns:
        Formatted string like "PASS" or "[PASS]"

    Example:
        >>> format_verdict(KillSwitchVerdict.PASS)
        'PASS'
        >>> format_verdict(KillSwitchVerdict.FAIL)
        'FAIL'
        >>> format_verdict(KillSwitchVerdict.WARNING, plain_text=True)
        '[WARNING]'
    """
    if plain_text:
        return VERDICT_TEXT[verdict]

    emoji = VERDICT_EMOJI[verdict]
    return f"{emoji} {verdict.value}"


def format_result(result: KillSwitchResult, plain_text: bool = False) -> str:
    """Format a complete kill-switch result with full breakdown.

    Generates a human-readable report with:
    - Verdict with emoji/text
    - Property identification and timestamp
    - HARD failures listed first (most critical)
    - SOFT failures with severity breakdown
    - Total severity score and threshold comparison

    Args:
        result: The KillSwitchResult to format
        plain_text: If True, omit emoji for non-emoji environments

    Returns:
        Multi-line formatted string suitable for display

    Example:
        >>> result = KillSwitchResult(...)
        >>> print(format_result(result))
        Kill-Switch Verdict: FAIL

        Property: 123 Main St, Phoenix, AZ
        Timestamp: 2025-12-10T14:30:00

        HARD Failures (Instant Fail):
          - no_hoa: Has HOA $150/month (required: $0)

        SOFT Failures (Severity: 3.5 >= 3.0):
          - city_sewer (severity 2.5): Has septic (required: city sewer)
          - lot_size (severity 1.0): Lot 6000 sqft (required: 7000-15000 sqft)

        Total Severity: 3.5 (threshold: 3.0)
        Verdict: FAIL
    """
    lines: list[str] = []

    # Header with verdict
    verdict_str = format_verdict(result.verdict, plain_text=plain_text)
    lines.append(f"Kill-Switch Verdict: {verdict_str}")
    lines.append("")

    # Property identification
    if result.property_address:
        lines.append(f"Property: {result.property_address}")
    lines.append(f"Timestamp: {result.timestamp.isoformat()}")
    lines.append("")

    # HARD failures (most impactful, listed first)
    hard_failures = result.hard_failures
    if hard_failures:
        lines.append("HARD Failures (Instant Fail):")
        for fc in hard_failures:
            lines.append(f"  - {fc.name}: {fc.actual_value} (required: {fc.required_value})")
        lines.append("")

    # SOFT failures (severity breakdown)
    soft_failures = result.soft_failures
    if soft_failures:
        threshold_comparison = (
            f">= {SEVERITY_FAIL_THRESHOLD}"
            if result.severity_score >= SEVERITY_FAIL_THRESHOLD
            else f"< {SEVERITY_FAIL_THRESHOLD}"
        )
        lines.append(
            f"SOFT Failures (Severity: {result.severity_score:.1f} {threshold_comparison}):"
        )
        # Sort by severity descending (most impactful first)
        sorted_soft = sorted(soft_failures, key=lambda x: x.severity, reverse=True)
        for fc in sorted_soft:
            lines.append(
                f"  - {fc.name} (severity {fc.severity}): {fc.actual_value} (required: {fc.required_value})"
            )
        lines.append("")

    # Summary footer
    if soft_failures or hard_failures:
        lines.append(
            f"Total Severity: {result.severity_score:.1f} (threshold: {SEVERITY_FAIL_THRESHOLD})"
        )
    else:
        lines.append("No failures detected.")

    lines.append(f"Verdict: {result.verdict.value}")

    return "\n".join(lines)


def format_verdict_short(verdict: KillSwitchVerdict) -> str:
    """Get a short verdict label for compact display.

    Args:
        verdict: The KillSwitchVerdict to format

    Returns:
        Short label string (PASS, WARNING, or FAIL)
    """
    return verdict.value


def format_severity_bar(
    severity: float, threshold: float = SEVERITY_FAIL_THRESHOLD, width: int = 10
) -> str:
    """Format severity as a visual bar indicator.

    Args:
        severity: The severity score to visualize
        threshold: The fail threshold for comparison
        width: Width of the bar in characters (default 10)

    Returns:
        Visual bar string showing severity level

    Example:
        >>> format_severity_bar(2.5, 3.0)
        '[########..] 2.5/3.0'
        >>> format_severity_bar(3.5, 3.0)
        '[##########] 3.5/3.0 EXCEEDED'
        >>> format_severity_bar(1.0, 0)
        '[??????????] 1.0/0.0 (invalid threshold)'
    """
    # Guard against zero/negative threshold
    if threshold <= 0:
        return f"[{'?' * width}] {severity:.1f}/0.0 (invalid threshold)"

    # Clamp severity to non-negative to prevent malformed bars
    severity = max(0.0, severity)

    # Calculate fill percentage (capped at 100%)
    fill_pct = min(severity / threshold, 1.0)
    filled = int(fill_pct * width)
    empty = width - filled

    bar = "#" * filled + "." * empty

    if severity >= threshold:
        return f"[{bar}] {severity:.1f}/{threshold:.1f} EXCEEDED"
    return f"[{bar}] {severity:.1f}/{threshold:.1f}"
