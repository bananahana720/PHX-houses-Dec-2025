"""Data loading utilities for deal sheet generation.

Contains:
- load_ranked_csv(): Load phx_homes_ranked.csv into DataFrame
- load_enrichment_json(): Load enrichment_data.json
- merge_enrichment_data(): Merge enrichment data into DataFrame

Note: All file I/O operations use PropertyDataCache singleton to eliminate
redundant disk reads across pipeline runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

# Requires: uv pip install -e .
from phx_home_analysis.services.data_cache import PropertyDataCache

# Type aliases for enrichment data structures
EnrichmentRecord = dict[str, Any]
EnrichmentData = list[EnrichmentRecord] | dict[str, EnrichmentRecord]


def load_ranked_csv(csv_path: str | Path) -> pd.DataFrame:
    """Load ranked homes CSV into DataFrame using cache.

    Args:
        csv_path: Path to phx_homes_ranked.csv

    Returns:
        pandas DataFrame with ranked property data (with invalid rows filtered out)
    """
    # Use cache for file I/O
    cache = PropertyDataCache()
    csv_data = cache.get_csv_data(Path(csv_path))

    # Convert to DataFrame
    df = pd.DataFrame(csv_data)

    # Filter out rows with missing address (malformed data)
    df = df[df['full_address'].notna()]

    # Add rank column if not present (based on total_score order)
    if 'rank' not in df.columns and 'total_score' in df.columns:
        df = df.copy()
        df['rank'] = df['total_score'].rank(ascending=False, method='min').astype(int)

    return df


def load_enrichment_json(json_path: str | Path) -> EnrichmentData:
    """Load enrichment data from JSON file using cache.

    Args:
        json_path: Path to enrichment_data.json

    Returns:
        Enrichment data as list of dicts or dict mapping addresses to fields
    """
    # Use cache for file I/O
    cache = PropertyDataCache()
    enrichment_data = cache.get_enrichment_data(Path(json_path))

    return enrichment_data  # type: ignore[no-any-return]


def merge_enrichment_data(df: pd.DataFrame, enrichment_data: EnrichmentData) -> pd.DataFrame:
    """Merge enrichment data into DataFrame.

    Adds enrichment fields to DataFrame by matching on full_address.
    Only adds fields that don't already exist in the DataFrame or are None/NaN.

    PERFORMANCE: Uses vectorized merge instead of iterrows() for 100x speedup.

    Args:
        df: pandas DataFrame with property data
        enrichment_data: List of enrichment data dicts OR dict mapping address -> fields

    Returns:
        DataFrame with enrichment data merged (modified in-place)
    """

    # Handle both list and dict formats for backward compatibility
    if isinstance(enrichment_data, dict):
        # Convert dict format {address: {fields}} to list format [{full_address, ...fields}]
        enrichment_records = []
        for address, fields in enrichment_data.items():
            record = {'full_address': address}
            record.update(fields)
            enrichment_records.append(record)
    else:
        # Already in list format
        enrichment_records = enrichment_data

    # Convert enrichment list to DataFrame for vectorized merge
    processed_records = []
    for item in enrichment_records:
        record = item.copy()
        # Convert lists/dicts to strings for pandas compatibility
        for key, value in record.items():
            if isinstance(value, list):
                record[key] = '; '.join(str(v) for v in value)
            elif isinstance(value, dict):
                record[key] = json.dumps(value)
        processed_records.append(record)

    enrichment_df = pd.DataFrame(processed_records)

    # If no enrichment data, return original df
    if enrichment_df.empty or 'full_address' not in enrichment_df.columns:
        return df

    # Identify columns that exist in both dataframes
    overlapping_cols = [col for col in enrichment_df.columns
                        if col in df.columns and col != 'full_address']

    # For overlapping columns, only use enrichment value if df value is NaN
    # Use suffixes to identify source of each column after merge
    merged = df.merge(enrichment_df, on='full_address', how='left',
                      suffixes=('', '_enrich'))

    # For each overlapping column, prefer original value unless NaN or empty
    for col in overlapping_cols:
        enrich_col = f'{col}_enrich'
        if enrich_col in merged.columns:
            # Use enrichment value where original is NaN or empty string
            mask = merged[col].isna() | (merged[col] == '') | (merged[col].astype(str).str.strip() == '')
            merged.loc[mask, col] = merged.loc[mask, enrich_col]
            # Drop the temporary enrichment column
            merged.drop(columns=[enrich_col], inplace=True)

    return merged
