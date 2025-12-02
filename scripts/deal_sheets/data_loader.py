"""Data loading utilities for deal sheet generation.

Contains:
- load_ranked_csv(): Load phx_homes_ranked.csv into DataFrame
- load_enrichment_json(): Load enrichment_data.json
- merge_enrichment_data(): Merge enrichment data into DataFrame
"""

import json
from pathlib import Path
import pandas as pd


def load_ranked_csv(csv_path):
    """Load ranked homes CSV into DataFrame.

    Args:
        csv_path: Path to phx_homes_ranked.csv

    Returns:
        pandas DataFrame with ranked property data (with invalid rows filtered out)
    """
    import pandas as pd

    df = pd.read_csv(csv_path)

    # Filter out rows with missing rank or address (malformed data)
    df = df[df['rank'].notna() & df['full_address'].notna()]

    return df


def load_enrichment_json(json_path):
    """Load enrichment data from JSON file.

    Args:
        json_path: Path to enrichment_data.json

    Returns:
        List of enrichment data dicts
    """
    with open(json_path, 'r') as f:
        return json.load(f)


def merge_enrichment_data(df, enrichment_data):
    """Merge enrichment data into DataFrame.

    Adds enrichment fields to DataFrame by matching on full_address.
    Only adds fields that don't already exist in the DataFrame or are None/NaN.

    Args:
        df: pandas DataFrame with property data
        enrichment_data: List of enrichment data dicts

    Returns:
        DataFrame with enrichment data merged (modified in-place)
    """
    import pandas as pd

    # Create lookup dictionary for enrichment data
    enrichment_lookup = {item['full_address']: item for item in enrichment_data}

    # Merge enrichment data into dataframe
    for idx, row in df.iterrows():
        address = row['full_address']
        if address in enrichment_lookup:
            enrich = enrichment_lookup[address]
            for key, value in enrich.items():
                # Convert lists/dicts to strings for pandas compatibility
                if isinstance(value, list):
                    value = '; '.join(str(v) for v in value)
                elif isinstance(value, dict):
                    value = json.dumps(value)
                # Only add if column doesn't exist OR current value is None/NaN
                if key not in df.columns:
                    df.at[idx, key] = value
                elif key in df.columns and pd.isna(df.at[idx, key]):
                    df.at[idx, key] = value

    return df
