"""Quality metrics and data lineage tracking service.

This module provides tools for assessing data quality across the property
analysis pipeline, including field-level lineage tracking and quality scoring.

Quality System Overview:
- Field Lineage: Track where each piece of data originated
- Quality Scoring: Assess completeness and confidence levels
- CI/CD Integration: Quality gates for automated pipelines

Quality Formula:
    overall_score = (completeness * 0.6) + (high_confidence_pct * 0.4)

Where:
- completeness = percentage of required fields present
- high_confidence_pct = percentage of fields with confidence >= 0.8

Usage:
    from phx_home_analysis.services.quality import (
        QualityMetricsCalculator,
        LineageTracker,
        DataSource,
        QualityScore,
    )

    # Track field lineage
    tracker = LineageTracker()
    tracker.record_field(
        property_hash="ef7cd95f",
        field_name="lot_sqft",
        source=DataSource.ASSESSOR_API,
        confidence=0.95,
        original_value=9500
    )
    tracker.save()

    # Calculate quality metrics
    calculator = QualityMetricsCalculator()
    score = calculator.calculate(
        property_data={"address": "123 Main St", "beds": 4, ...},
        field_confidences=tracker.get_all_confidences("ef7cd95f")
    )

    # Check quality gate
    if score.overall_score >= 0.95:
        print("Data quality gate passed!")
"""

from .audit_log import AuditAction, AuditEntry, AuditLog
from .confidence_display import ConfidenceLevel, format_confidence, get_confidence_html
from .lineage import LineageTracker
from .metrics import QualityMetricsCalculator, calculate_property_quality
from .models import DataSource, FieldLineage, QualityScore
from .provenance_service import ProvenanceService

__all__ = [
    # Models
    "DataSource",
    "FieldLineage",
    "QualityScore",
    # Audit logging
    "AuditAction",
    "AuditEntry",
    "AuditLog",
    # Lineage tracking
    "LineageTracker",
    # Quality metrics
    "QualityMetricsCalculator",
    "calculate_property_quality",
    # Provenance tracking
    "ProvenanceService",
    # Confidence display
    "ConfidenceLevel",
    "format_confidence",
    "get_confidence_html",
]
