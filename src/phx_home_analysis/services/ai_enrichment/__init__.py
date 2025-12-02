"""AI-assisted field inference and triage for missing property data.

This package provides tools for identifying missing property fields and
attempting to infer their values through multiple sources before falling
back to AI inference.

Key Components:
- FieldTagger: Identifies missing required fields
- FieldInferencer: Orchestrates the inference workflow
- ConfidenceScorer: Calculates confidence scores for inferences
- ConfidenceLevel: Enum for categorizing confidence (HIGH, MEDIUM, LOW)
- FieldInference: Data class for individual field inference results
- TriageResult: Aggregated results for a property's missing fields

Triage Workflow:
1. FieldTagger identifies missing fields
2. FieldInferencer attempts programmatic resolution:
   a. Web scraping (Zillow, Redfin)
   b. Maricopa County Assessor API
3. Fields that can't be resolved programmatically are marked for AI inference
4. ConfidenceScorer evaluates the reliability of all inferences

Example:
    >>> from phx_home_analysis.services.ai_enrichment import (
    ...     FieldTagger, FieldInferencer, ConfidenceScorer
    ... )
    >>>
    >>> # Identify missing fields
    >>> tagger = FieldTagger()
    >>> missing = tagger.tag_missing_fields({"beds": 4, "baths": None})
    >>>
    >>> # Attempt inference
    >>> inferencer = FieldInferencer()
    >>> results = await inferencer.infer_fields(
    ...     {"beds": 4, "baths": None},
    ...     "123 Main St, Phoenix, AZ 85001"
    ... )
    >>>
    >>> # Score confidence
    >>> scorer = ConfidenceScorer()
    >>> scored = scorer.score_multiple_inferences(results)
"""

from .confidence_scorer import ConfidenceScorer
from .field_inferencer import FieldInferencer, FieldTagger
from .models import ConfidenceLevel, FieldInference, TriageResult

__all__ = [
    # Models
    "ConfidenceLevel",
    "FieldInference",
    "TriageResult",
    # Field Inference
    "FieldTagger",
    "FieldInferencer",
    # Confidence Scoring
    "ConfidenceScorer",
]
