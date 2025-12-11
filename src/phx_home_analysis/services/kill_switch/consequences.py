"""Consequence mapping and failure explanation generation.

This module provides human-readable consequence messages for kill-switch failures,
mapping technical criterion results to actionable impact statements.

Usage:
    from phx_home_analysis.services.kill_switch import (
        ConsequenceMapper,
        FailureExplanation,
        MultiFailureSummary,
        generate_warning_card_html,
        generate_warning_cards_html,
    )

    # Get consequence for a failed criterion
    mapper = ConsequenceMapper()
    consequence = mapper.get_consequence("no_hoa", actual=150, required=0)
    # "HOA fee of $150/month adds $1800 annually to housing costs"

    # Create failure explanation
    failure = mapper.create_failure_explanation(
        criterion_name="no_hoa",
        actual=150,
        required=0,
        is_hard=True,
        severity=0.0,
    )

    # Generate HTML warning card
    html = generate_warning_card_html(failure)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# =============================================================================
# CONSEQUENCE TEMPLATES (E3.S4 - AC1)
# =============================================================================

CONSEQUENCE_TEMPLATES: dict[str, str] = {
    "no_hoa": "HOA fee of ${actual}/month adds ${annual} annually to housing costs",
    "city_sewer": (
        "Septic system requires ~$300-500/year maintenance and eventual $10k-30k replacement"
    ),
    "min_bedrooms": (
        "Only {actual} bedrooms vs {required} minimum limits family use and resale value"
    ),
    "min_bathrooms": ("Only {actual} bathrooms vs {required} minimum impacts daily family use"),
    "min_sqft": (
        "{actual:,} sqft is {diff:,} sqft below {required:,} minimum living space requirement"
    ),
    "min_garage": "Only {actual} garage space(s) vs {required} minimum indoor parking",
    "lot_size": "Lot size {actual:,} sqft is outside {min:,}-{max:,} sqft preferred range",
    "no_new_build": "Year {actual} build may have construction quality/warranty concerns",
    "no_solar_lease": (
        "Solar lease transfers ${monthly}/month obligation (~${annual}/year) to buyer"
    ),
}

DISPLAY_NAMES: dict[str, str] = {
    "no_hoa": "HOA Restriction",
    "city_sewer": "City Sewer Required",
    "min_bedrooms": "Minimum Bedrooms",
    "min_bathrooms": "Minimum Bathrooms",
    "min_sqft": "Minimum Square Footage",
    "min_garage": "Garage Spaces",
    "lot_size": "Lot Size Range",
    "no_new_build": "No New Construction",
    "no_solar_lease": "No Solar Lease",
}

REQUIREMENT_DESCRIPTIONS: dict[str, str] = {
    "no_hoa": "Must be $0/month",
    "city_sewer": "Must have city sewer connection",
    "min_bedrooms": "Minimum 4 bedrooms",
    "min_bathrooms": "Minimum 2 bathrooms",
    "min_sqft": "Minimum 1,800 sqft",
    "min_garage": "Minimum 2 garage spaces",
    "lot_size": "Between 7,000 and 15,000 sqft",
    "no_new_build": "Built before 2024",
    "no_solar_lease": "No active solar lease",
}


# =============================================================================
# FAILURE EXPLANATION DATACLASS (E3.S4 - AC2)
# =============================================================================


@dataclass
class FailureExplanation:
    """Detailed explanation of a single kill-switch failure.

    Combines technical criterion data with human-readable consequence
    information for clear user communication.

    Attributes:
        criterion_name: Internal identifier (e.g., "no_hoa", "city_sewer")
        display_name: Human-friendly name (e.g., "HOA Restriction")
        requirement: What was required (e.g., "Must be $0/month")
        actual_value: What property actually has (e.g., "$150/month")
        consequence: Human-readable impact statement
        is_hard: True for criteria that cause instant fail
        severity: Severity value (0.0 for instant-fail criteria)

    Example:
        failure = FailureExplanation(
            criterion_name="no_hoa",
            display_name="HOA Restriction",
            requirement="Must be $0/month",
            actual_value="$150/month",
            consequence="HOA fee of $150/month adds $1800 annually to housing costs",
            is_hard=True,
            severity=0.0,
        )
        print(failure)  # Human-readable summary
        print(failure.to_dict())  # JSON-serializable dict
    """

    criterion_name: str
    display_name: str
    requirement: str
    actual_value: str
    consequence: str
    is_hard: bool
    severity: float

    # Alias for backward compatibility with code using weight
    @property
    def weight(self) -> float:
        """Alias for severity (backward compatibility)."""
        return self.severity

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields suitable for JSON export.

        Example:
            >>> failure.to_dict()
            {
                "criterion_name": "no_hoa",
                "display_name": "HOA Restriction",
                "requirement": "Must be $0/month",
                "actual_value": "$150/month",
                "consequence": "HOA fee of $150/month adds $1800 annually...",
                "is_hard": True,
                "severity": 0.0,
                "type": "INSTANT_FAIL"
            }
        """
        return {
            "criterion_name": self.criterion_name,
            "display_name": self.display_name,
            "requirement": self.requirement,
            "actual_value": self.actual_value,
            "consequence": self.consequence,
            "is_hard": self.is_hard,
            "severity": self.severity,
            "type": "INSTANT_FAIL" if self.is_hard else "WEIGHTED",
        }

    def __str__(self) -> str:
        """Human-readable format for display.

        Returns:
            Formatted string showing criterion failure details.

        Example:
            >>> print(failure)
            [INSTANT_FAIL] HOA Restriction: $150/month (Required: Must be $0/month)
            Impact: HOA fee of $150/month adds $1800 annually to housing costs
        """
        type_label = "INSTANT_FAIL" if self.is_hard else f"WEIGHTED (severity {self.severity})"
        lines = [
            f"[{type_label}] {self.display_name}: {self.actual_value} "
            f"(Required: {self.requirement})",
            f"Impact: {self.consequence}",
        ]
        return "\n".join(lines)

    @classmethod
    def from_criterion_result(
        cls,
        criterion_name: str,
        actual: Any,
        required: Any,
        is_hard: bool,
        severity: float,
        mapper: "ConsequenceMapper | None" = None,
    ) -> "FailureExplanation":
        """Factory method to create FailureExplanation from criterion result data.

        Args:
            criterion_name: Internal criterion identifier
            actual: Actual property value
            required: Required value or bound
            is_hard: Whether this is an instant-fail criterion
            severity: Severity value for weighted criteria (0.0 for HARD criteria)
            mapper: Optional ConsequenceMapper instance (creates default if None)

        Returns:
            FailureExplanation with all fields populated

        Example:
            >>> failure = FailureExplanation.from_criterion_result(
            ...     criterion_name="no_hoa",
            ...     actual=150,
            ...     required=0,
            ...     is_hard=True,
            ...     severity=0.0,
            ... )
        """
        if mapper is None:
            mapper = ConsequenceMapper()

        display_name = mapper.get_display_name(criterion_name)
        requirement = mapper.get_requirement_description(criterion_name)
        actual_value = mapper.format_actual_value(criterion_name, actual)
        consequence = mapper.get_consequence(criterion_name, actual, required)

        return cls(
            criterion_name=criterion_name,
            display_name=display_name,
            requirement=requirement,
            actual_value=actual_value,
            consequence=consequence,
            is_hard=is_hard,
            severity=severity,
        )


# =============================================================================
# MULTI-FAILURE SUMMARY DATACLASS (E3.S4 - AC3)
# =============================================================================


@dataclass
class MultiFailureSummary:
    """Aggregate summary of multiple kill-switch failures.

    Provides structured breakdown with instant-fail failures first, then
    weighted failures sorted by weight (highest first).

    Attributes:
        total_criteria: Total criteria evaluated (typically 9)
        failed_count: Number of failed criteria
        hard_failures: List of instant-fail criterion failures (sorted by name)
        soft_failures: List of weighted criterion failures (sorted by weight desc)
        summary_text: Human-readable summary (e.g., "Failed 3 of 9 criteria")
        timestamp: When the summary was generated

    Example:
        summary = MultiFailureSummary(
            total_criteria=9,
            failed_count=2,
            hard_failures=[hoa_failure],
            soft_failures=[sewer_failure],
            summary_text="Failed 2 of 9 criteria (1 instant-fail, 1 weighted)",
        )
    """

    total_criteria: int
    failed_count: int
    hard_failures: list[FailureExplanation]
    soft_failures: list[FailureExplanation]
    summary_text: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_hard_failures(self) -> bool:
        """Check if there are any instant-fail criterion failures.

        Returns:
            True if at least one instant-fail failure exists.
        """
        return len(self.hard_failures) > 0

    @property
    def has_soft_failures(self) -> bool:
        """Check if there are any weighted criterion failures.

        Returns:
            True if at least one weighted failure exists.
        """
        return len(self.soft_failures) > 0

    @property
    def total_soft_weight(self) -> float:
        """Calculate total weight from weighted failures.

        Returns:
            Sum of weight values from all weighted failures.
        """
        return sum(f.weight for f in self.soft_failures)

    # Alias for backward compatibility
    @property
    def total_soft_severity(self) -> float:
        """Alias for total_soft_weight (backward compatibility)."""
        return self.total_soft_weight

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all fields suitable for JSON export.
        """
        return {
            "total_criteria": self.total_criteria,
            "failed_count": self.failed_count,
            "hard_failures": [f.to_dict() for f in self.hard_failures],
            "soft_failures": [f.to_dict() for f in self.soft_failures],
            "summary_text": self.summary_text,
            "timestamp": self.timestamp.isoformat(),
            "has_hard_failures": self.has_hard_failures,
            "has_soft_failures": self.has_soft_failures,
            "total_soft_weight": self.total_soft_weight,
        }

    def to_text(self) -> str:
        """Generate markdown-formatted text output.

        Returns:
            Multi-line markdown string with structured failure breakdown.

        Example:
            ## Kill-Switch Failure Summary

            **Failed 2 of 9 criteria (1 instant-fail, 1 weighted)**

            ### Instant-Fail Failures (Disqualification)
            - **HOA Restriction**: $150/month (Required: Must be $0/month)
              Impact: HOA fee of $150/month adds $1800 annually...

            ### Weighted Failures (Severity: 2.5)
            - **City Sewer Required** [severity 2.5]: septic (Required: Must have city sewer)
              Impact: Septic system requires ~$300-500/year maintenance...
        """
        lines = ["## Kill-Switch Failure Summary", "", f"**{self.summary_text}**", ""]

        if self.hard_failures:
            lines.append("### Instant-Fail Failures (Disqualification)")
            for f in self.hard_failures:
                lines.append(
                    f"- **{f.display_name}**: {f.actual_value} (Required: {f.requirement})"
                )
                lines.append(f"  Impact: {f.consequence}")
            lines.append("")

        if self.soft_failures:
            lines.append(f"### Weighted Failures (Total Severity: {self.total_soft_severity:.1f})")
            for f in self.soft_failures:
                lines.append(
                    f"- **{f.display_name}** [severity {f.severity}]: {f.actual_value} "
                    f"(Required: {f.requirement})"
                )
                lines.append(f"  Impact: {f.consequence}")
            lines.append("")

        return "\n".join(lines)

    def to_html(self) -> str:
        """Generate HTML output with warning cards.

        Returns:
            HTML string with styled warning cards for all failures.
        """
        return generate_warning_cards_html(
            self.hard_failures + self.soft_failures,
            include_summary_header=True,
            summary=self,
        )


# =============================================================================
# CONSEQUENCE MAPPER CLASS (E3.S4 - AC1)
# =============================================================================


class ConsequenceMapper:
    """Maps criterion failures to human-readable consequences.

    Provides template-based consequence generation with variable substitution
    for creating actionable failure impact statements.

    Usage:
        mapper = ConsequenceMapper()

        # Get consequence with template substitution
        consequence = mapper.get_consequence("no_hoa", actual=150, required=0)
        # "HOA fee of $150/month adds $1800 annually to housing costs"

        # Create complete failure explanation
        failure = mapper.create_failure_explanation(
            criterion_name="city_sewer",
            actual="septic",
            required="city",
            is_hard=False,
            severity=2.5,
        )

    Attributes:
        _templates: Dictionary of consequence templates by criterion name
        _display_names: Dictionary of human-friendly display names
        _requirements: Dictionary of requirement descriptions
    """

    def __init__(
        self,
        templates: dict[str, str] | None = None,
        display_names: dict[str, str] | None = None,
        requirements: dict[str, str] | None = None,
    ):
        """Initialize ConsequenceMapper with optional custom templates.

        Args:
            templates: Custom consequence templates (uses defaults if None)
            display_names: Custom display names (uses defaults if None)
            requirements: Custom requirement descriptions (uses defaults if None)
        """
        self._templates = templates or CONSEQUENCE_TEMPLATES.copy()
        self._display_names = display_names or DISPLAY_NAMES.copy()
        self._requirements = requirements or REQUIREMENT_DESCRIPTIONS.copy()

    def get_consequence(
        self,
        criterion_name: str,
        actual: Any,
        required: Any,
        **kwargs: Any,
    ) -> str:
        """Generate consequence text from template.

        Substitutes template variables with actual values. Handles special
        calculations like annual costs from monthly values.

        Args:
            criterion_name: Internal criterion identifier
            actual: Actual property value
            required: Required value or bound
            **kwargs: Additional template variables (min, max, monthly, etc.)

        Returns:
            Human-readable consequence string

        Example:
            >>> mapper.get_consequence("no_hoa", actual=150, required=0)
            "HOA fee of $150/month adds $1800 annually to housing costs"

            >>> mapper.get_consequence("min_sqft", actual=1600, required=1800)
            "1,600 sqft is 200 sqft below 1,800 minimum living space requirement"
        """
        template = self._templates.get(criterion_name)
        if template is None:
            return f"Criterion {criterion_name} failed: actual={actual}, required={required}"

        # Build substitution variables
        variables: dict[str, Any] = {
            "actual": actual,
            "required": required,
            **kwargs,
        }

        # Calculate derived values based on criterion type
        if criterion_name == "no_hoa":
            # Calculate annual HOA cost
            try:
                monthly = float(actual) if actual is not None else 0
                variables["annual"] = int(monthly * 12)
            except (ValueError, TypeError):
                variables["annual"] = "unknown"

        elif criterion_name == "min_sqft":
            # Calculate sqft difference
            try:
                actual_sqft = int(actual) if actual is not None else 0
                required_sqft = int(required) if required is not None else 1800
                variables["diff"] = required_sqft - actual_sqft
            except (ValueError, TypeError):
                variables["diff"] = "unknown"

        elif criterion_name == "lot_size":
            # Ensure min/max are provided
            variables.setdefault("min", 7000)
            variables.setdefault("max", 15000)

        elif criterion_name == "no_solar_lease":
            # Calculate annual solar lease cost
            try:
                monthly = float(kwargs.get("monthly", 150))
                variables["monthly"] = int(monthly)
                variables["annual"] = int(monthly * 12)
            except (ValueError, TypeError):
                variables["monthly"] = 150
                variables["annual"] = 1800

        # Format the template with variables
        try:
            return template.format(**variables)
        except (KeyError, ValueError) as e:
            # Fallback if template formatting fails
            return f"Criterion {criterion_name} failed: {e}"

    def get_display_name(self, criterion_name: str) -> str:
        """Get human-friendly display name for criterion.

        Args:
            criterion_name: Internal criterion identifier

        Returns:
            Human-friendly display name

        Example:
            >>> mapper.get_display_name("no_hoa")
            "HOA Restriction"
        """
        return self._display_names.get(criterion_name, criterion_name.replace("_", " ").title())

    def get_requirement_description(self, criterion_name: str) -> str:
        """Get requirement description for criterion.

        Args:
            criterion_name: Internal criterion identifier

        Returns:
            Human-readable requirement description

        Example:
            >>> mapper.get_requirement_description("min_bedrooms")
            "Minimum 4 bedrooms"
        """
        return self._requirements.get(criterion_name, f"Criterion {criterion_name}")

    def format_actual_value(self, criterion_name: str, actual: Any) -> str:
        """Format actual value for display.

        Applies criterion-specific formatting (currency, units, etc.).

        Args:
            criterion_name: Internal criterion identifier
            actual: Raw actual value

        Returns:
            Formatted string for display

        Example:
            >>> mapper.format_actual_value("no_hoa", 150)
            "$150/month"
            >>> mapper.format_actual_value("min_sqft", 1600)
            "1,600 sqft"
        """
        if actual is None:
            return "Unknown"

        if criterion_name == "no_hoa":
            return f"${actual}/month"
        elif criterion_name in ("min_sqft", "lot_size"):
            try:
                return f"{int(actual):,} sqft"
            except (ValueError, TypeError):
                return f"{actual} sqft"
        elif criterion_name in ("min_bedrooms", "min_bathrooms", "min_garage"):
            return str(actual)
        elif criterion_name == "no_new_build":
            return f"Year {actual}"
        elif criterion_name == "city_sewer":
            return str(actual).lower()
        elif criterion_name == "no_solar_lease":
            return str(actual)
        else:
            return str(actual)

    def create_failure_explanation(
        self,
        criterion_name: str,
        actual: Any,
        required: Any,
        is_hard: bool,
        severity: float,
        **kwargs: Any,
    ) -> FailureExplanation:
        """Create complete FailureExplanation for a criterion failure.

        Args:
            criterion_name: Internal criterion identifier
            actual: Actual property value
            required: Required value or bound
            is_hard: Whether this is an instant-fail criterion
            severity: Severity value for weighted criteria (0.0 for HARD criteria)
            **kwargs: Additional context (min, max, monthly, etc.)

        Returns:
            FailureExplanation with all fields populated

        Example:
            >>> failure = mapper.create_failure_explanation(
            ...     criterion_name="no_hoa",
            ...     actual=150,
            ...     required=0,
            ...     is_hard=True,
            ...     severity=0.0,
            ... )
        """
        return FailureExplanation(
            criterion_name=criterion_name,
            display_name=self.get_display_name(criterion_name),
            requirement=self.get_requirement_description(criterion_name),
            actual_value=self.format_actual_value(criterion_name, actual),
            consequence=self.get_consequence(criterion_name, actual, required, **kwargs),
            is_hard=is_hard,
            severity=severity,
        )


# =============================================================================
# MULTI-FAILURE SUMMARY FACTORY (E3.S4 - AC3)
# =============================================================================


def generate_multi_failure_summary(
    failures: list[FailureExplanation],
    total_criteria: int = 9,
) -> MultiFailureSummary:
    """Generate MultiFailureSummary from list of failures.

    Separates instant-fail and weighted failures, sorts weighted by weight
    descending, and generates summary text.

    Args:
        failures: List of FailureExplanation objects
        total_criteria: Total criteria evaluated (default: 9)

    Returns:
        MultiFailureSummary with categorized and sorted failures

    Example:
        >>> failures = [hoa_failure, sewer_failure, garage_failure]
        >>> summary = generate_multi_failure_summary(failures)
        >>> print(summary.summary_text)
        "Failed 3 of 9 criteria (1 instant-fail, 2 weighted)"
    """
    # Separate instant-fail and weighted failures
    hard_failures = [f for f in failures if f.is_hard]
    soft_failures = [f for f in failures if not f.is_hard]

    # Sort instant-fail failures by criterion name (alphabetical)
    hard_failures.sort(key=lambda f: f.criterion_name)

    # Sort weighted failures by weight descending (highest first)
    soft_failures.sort(key=lambda f: f.weight, reverse=True)

    # Generate summary text
    failed_count = len(failures)
    hard_count = len(hard_failures)
    soft_count = len(soft_failures)

    if failed_count == 0:
        summary_text = f"Passed all {total_criteria} criteria"
    else:
        parts = []
        if hard_count > 0:
            parts.append(f"{hard_count} instant-fail")
        if soft_count > 0:
            parts.append(f"{soft_count} weighted")
        breakdown = ", ".join(parts)
        summary_text = f"Failed {failed_count} of {total_criteria} criteria ({breakdown})"

    return MultiFailureSummary(
        total_criteria=total_criteria,
        failed_count=failed_count,
        hard_failures=hard_failures,
        soft_failures=soft_failures,
        summary_text=summary_text,
    )


# =============================================================================
# HTML WARNING CARD GENERATOR (E3.S4 - AC4)
# =============================================================================


def generate_warning_card_html(
    failure: FailureExplanation,
    include_aria: bool = True,
) -> str:
    """Generate HTML warning card for a single failure.

    Creates a styled card with red border for instant-fail failures,
    orange border for weighted failures. Includes ARIA attributes
    for accessibility.

    Args:
        failure: FailureExplanation to render
        include_aria: Include ARIA attributes for accessibility (default: True)

    Returns:
        HTML string for warning card

    Example:
        >>> html = generate_warning_card_html(hoa_failure)
        >>> print(html)
        <div class="kill-switch-warning-card kill-switch-hard"
             role="alert" aria-labelledby="ks-title-no_hoa">
          <div class="ks-header">
            <span class="ks-icon" aria-hidden="true">X</span>
            <h4 id="ks-title-no_hoa" class="ks-title">HOA Restriction</h4>
            <span class="ks-badge ks-badge-hard">INSTANT FAIL</span>
          </div>
          ...
        </div>
    """
    # Determine styling based on failure type
    type_class = "kill-switch-hard" if failure.is_hard else "kill-switch-soft"
    border_color = "#dc3545" if failure.is_hard else "#fd7e14"
    bg_color = "#fff5f5" if failure.is_hard else "#fff8f0"
    badge_text = "INSTANT FAIL" if failure.is_hard else f"WEIGHTED ({failure.severity})"
    badge_class = "ks-badge-hard" if failure.is_hard else "ks-badge-soft"
    icon = "X" if failure.is_hard else "!"

    # Build ARIA attributes
    title_id = f"ks-title-{failure.criterion_name}"
    aria_attrs = ""
    if include_aria:
        aria_attrs = f' role="alert" aria-labelledby="{title_id}"'

    # Escape user data to prevent XSS
    from html import escape

    safe_display_name = escape(failure.display_name)
    safe_requirement = escape(failure.requirement)
    safe_actual_value = escape(failure.actual_value)
    safe_consequence = escape(failure.consequence)

    # Build HTML with escaped user data
    html = f'''<div class="kill-switch-warning-card {type_class}" style="border: 2px solid {border_color}; border-radius: 8px; padding: 16px; margin-bottom: 12px; background-color: {bg_color};"{aria_attrs}>
  <div class="ks-header" style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
    <span class="ks-icon" style="font-weight: bold; font-size: 18px; color: {border_color};" aria-hidden="true">{icon}</span>
    <h4 id="{title_id}" class="ks-title" style="margin: 0; flex-grow: 1; font-size: 16px;">{safe_display_name}</h4>
    <span class="ks-badge {badge_class}" style="padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; background-color: {border_color}; color: white;">{badge_text}</span>
  </div>
  <div class="ks-body">
    <p class="ks-requirement" style="margin: 4px 0;"><strong>Required:</strong> {safe_requirement}</p>
    <p class="ks-actual" style="margin: 4px 0;"><strong>Actual:</strong> {safe_actual_value}</p>
    <p class="ks-consequence" style="margin: 8px 0 0 0; font-style: italic; color: #666;"><strong>Impact:</strong> {safe_consequence}</p>
  </div>
</div>'''

    return html


def generate_warning_cards_html(
    failures: list[FailureExplanation],
    include_summary_header: bool = True,
    summary: MultiFailureSummary | None = None,
) -> str:
    """Generate complete HTML with all warning cards.

    Args:
        failures: List of FailureExplanation objects to render
        include_summary_header: Include summary header section (default: True)
        summary: Optional MultiFailureSummary for header text

    Returns:
        HTML string with all warning cards

    Example:
        >>> html = generate_warning_cards_html([hoa_failure, sewer_failure])
    """
    cards = [generate_warning_card_html(f) for f in failures]

    # Build header if requested
    header = ""
    if include_summary_header:
        hard_count = sum(1 for f in failures if f.is_hard)
        soft_count = len(failures) - hard_count

        if summary:
            header_text = summary.summary_text
        else:
            parts = []
            if hard_count > 0:
                parts.append(f"{hard_count} instant-fail")
            if soft_count > 0:
                parts.append(f"{soft_count} weighted")
            if parts:
                header_text = f"Kill-Switch Failures: {', '.join(parts)}"
            else:
                header_text = "No Kill-Switch Failures"

        header = f"""<div class="kill-switch-summary" style="margin-bottom: 16px; padding: 12px; background-color: #f8f9fa; border-radius: 8px;">
  <h3 style="margin: 0 0 8px 0; font-size: 18px;">Kill-Switch Evaluation</h3>
  <p style="margin: 0; font-weight: bold;">{header_text}</p>
</div>
"""

    # Combine header and cards
    return header + "\n".join(cards)


# =============================================================================
# VERDICT EXPLAINER INTEGRATION (E3.S4 - AC5)
# =============================================================================


def explain_with_consequences(
    criterion_results: list[Any],
    property_data: dict[str, Any] | None = None,
    mapper: ConsequenceMapper | None = None,
    total_criteria: int = 9,
) -> MultiFailureSummary:
    """Generate MultiFailureSummary with consequences from criterion results.

    This function integrates with VerdictExplainer by converting CriterionResult
    objects into FailureExplanation objects with full consequence information.

    Args:
        criterion_results: List of CriterionResult objects from VerdictExplainer
        property_data: Optional property data dict for additional context
        mapper: Optional ConsequenceMapper (creates default if None)
        total_criteria: Total criteria evaluated (default: 9)

    Returns:
        MultiFailureSummary with categorized failures and consequences

    Example:
        from phx_home_analysis.services.kill_switch import (
            VerdictExplainer,
            CriterionResult,
            explain_with_consequences,
        )

        explainer = VerdictExplainer()
        # ... build criterion_results from filter evaluation ...

        summary = explain_with_consequences(criterion_results)
        print(summary.to_text())
        print(summary.to_html())
    """
    if mapper is None:
        mapper = ConsequenceMapper()

    property_data = property_data or {}

    # Convert CriterionResult objects to FailureExplanation objects
    failures: list[FailureExplanation] = []

    for cr in criterion_results:
        # Skip passed criteria
        if cr.passed:
            continue

        # Extract actual/required values from property_data if available
        actual = _extract_actual_value(cr.name, property_data)
        required = _extract_required_value(cr.name)

        # Build additional kwargs for specific criteria
        kwargs = _build_consequence_kwargs(cr.name, property_data)

        # Create failure explanation
        failure = mapper.create_failure_explanation(
            criterion_name=cr.name,
            actual=actual,
            required=required,
            is_hard=cr.is_hard,
            severity=cr.severity if hasattr(cr, "severity") else 0.0,
            **kwargs,
        )
        failures.append(failure)

    return generate_multi_failure_summary(failures, total_criteria)


def _extract_actual_value(
    criterion_name: str,
    property_data: dict[str, Any],
) -> Any:
    """Extract actual value from property data.

    Args:
        criterion_name: Criterion identifier
        property_data: Property data dictionary

    Returns:
        Actual property value or "unknown" if not found
    """
    # Map criterion names to property data keys
    key_mapping = {
        "no_hoa": "hoa_fee",
        "city_sewer": "sewer_type",
        "min_bedrooms": "beds",
        "min_bathrooms": "baths",
        "min_sqft": "sqft",
        "min_garage": "garage_spaces",
        "lot_size": "lot_sqft",
        "no_new_build": "year_built",
        "no_solar_lease": "solar_status",
    }

    key = key_mapping.get(criterion_name)
    if key and key in property_data:
        return property_data[key]

    return "unknown"


def _extract_required_value(criterion_name: str) -> Any:
    """Get required value for a criterion.

    Args:
        criterion_name: Criterion identifier

    Returns:
        Required value or bound
    """
    required_values = {
        "no_hoa": 0,
        "city_sewer": "city",
        "min_bedrooms": 4,
        "min_bathrooms": 2,
        "min_sqft": 1800,
        "min_garage": 2,
        "lot_size": "7000-15000",
        "no_new_build": 2023,
        "no_solar_lease": "owned",
    }
    return required_values.get(criterion_name, "unknown")


def _build_consequence_kwargs(
    criterion_name: str,
    property_data: dict[str, Any],
) -> dict[str, Any]:
    """Build additional kwargs for consequence template substitution.

    Args:
        criterion_name: Criterion identifier
        property_data: Property data dictionary

    Returns:
        Additional kwargs for template substitution
    """
    kwargs: dict[str, Any] = {}

    if criterion_name == "lot_size":
        kwargs["min"] = 7000
        kwargs["max"] = 15000

    elif criterion_name == "no_solar_lease":
        # Estimate monthly solar lease cost
        kwargs["monthly"] = property_data.get("solar_monthly", 150)

    return kwargs


# =============================================================================
# CSS STYLES (for external stylesheet reference)
# =============================================================================

WARNING_CARD_CSS = """
/* Kill-Switch Warning Card Styles */
.kill-switch-warning-card {
  border: 2px solid;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.kill-switch-hard {
  border-color: #dc3545;
  background-color: #fff5f5;
}

.kill-switch-soft {
  border-color: #fd7e14;
  background-color: #fff8f0;
}

.ks-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.ks-icon {
  font-weight: bold;
  font-size: 18px;
}

.kill-switch-hard .ks-icon {
  color: #dc3545;
}

.kill-switch-soft .ks-icon {
  color: #fd7e14;
}

.ks-title {
  margin: 0;
  flex-grow: 1;
  font-size: 16px;
}

.ks-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.ks-badge-hard {
  background-color: #dc3545;
}

.ks-badge-soft {
  background-color: #fd7e14;
}

.ks-body p {
  margin: 4px 0;
}

.ks-consequence {
  margin-top: 8px;
  font-style: italic;
  color: #666;
}

/* Accessibility: ensure text indicators complement color */
.kill-switch-hard .ks-header::before {
  content: "[INSTANT_FAIL] ";
  position: absolute;
  left: -9999px;
}

.kill-switch-soft .ks-header::before {
  content: "[WEIGHTED] ";
  position: absolute;
  left: -9999px;
}
"""
