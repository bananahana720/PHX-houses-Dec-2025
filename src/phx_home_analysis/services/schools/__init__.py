"""School ratings extraction service."""

from .api_models import (
    AssignedSchoolsResult,
    SchoolFallbackResult,
    SchoolLevel,
    SchoolResult,
)
from .extractor import GreatSchoolsExtractor
from .models import SchoolData
from .ratings_client import SchoolRatingsClient, haversine_distance

__all__ = [
    # Legacy browser-based extractor
    "GreatSchoolsExtractor",
    "SchoolData",
    # API-based client (primary)
    "SchoolRatingsClient",
    "haversine_distance",
    # API models
    "SchoolLevel",
    "SchoolResult",
    "AssignedSchoolsResult",
    "SchoolFallbackResult",
]
