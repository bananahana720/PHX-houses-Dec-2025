"""Data integration services for merging multi-source property data.

This module provides field mapping and data merging capabilities to handle
inconsistencies between different data sources (county API, listings, manual
research). It ensures canonical field names and proper data precedence.
"""

from .field_mapper import FIELD_MAPPING, FieldMapper
from .merge_strategy import DataSourcePriority, MergeStrategy, merge_property_data

__all__ = [
    "FieldMapper",
    "FIELD_MAPPING",
    "MergeStrategy",
    "DataSourcePriority",
    "merge_property_data",
]
