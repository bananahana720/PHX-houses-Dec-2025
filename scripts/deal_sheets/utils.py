"""Utility functions for deal sheet generation.

Contains:
- slugify(): Convert address to URL-friendly slug
- extract_features(): Extract present/missing features from property data
"""

import re
import pandas as pd


def slugify(text):
    """Convert text to URL-friendly slug.

    Args:
        text: Full address string (e.g., "123 Main St, Phoenix, AZ 85001")

    Returns:
        URL-friendly slug (e.g., "123_main_st")
    """
    # Handle None or NaN
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return "unknown_address"

    # Convert to string if needed
    text = str(text)

    # Extract street address (first part before comma)
    street = text.split(',')[0].lower()
    # Remove special characters and replace spaces with underscores
    slug = re.sub(r'[^\w\s-]', '', street)
    slug = re.sub(r'[-\s]+', '_', slug)
    return slug


def extract_features(row):
    """Extract present and missing features from property data.

    Analyzes property row data to identify:
    - Present features (pool, solar, garage, etc.)
    - Missing features (highlighted in red in deal sheet)

    Args:
        row: pandas Series or dict with property data

    Returns:
        Dict with:
        - 'present': List of feature strings to display with checkmarks
        - 'missing': List of feature strings to display with X marks
    """
    present = []
    missing = []

    # Pool
    if row.get('has_pool'):
        present.append('Pool')
    else:
        missing.append('Pool')

    # Solar
    solar_status = row.get('solar_status')
    if solar_status == 'owned':
        present.append('Solar (owned)')
    elif solar_status == 'leased':
        present.append('Solar (leased)')
    elif solar_status == 'none':
        missing.append('Solar panels')
    else:
        missing.append('Solar (unknown)')

    # Garage
    garage = row.get('garage_spaces')
    if garage and garage >= 3:
        present.append(f'{int(garage)}-car garage')
    elif garage and garage >= 2:
        present.append('2-car garage')

    # Bedrooms
    beds = row.get('beds')
    if beds and beds > 4:
        present.append(f'{int(beds)} bedrooms')

    # Bathrooms
    baths = row.get('baths')
    if baths and baths > 2:
        present.append(f'{baths} bathrooms')

    # HVAC age (if known)
    hvac_age = row.get('hvac_age')
    if hvac_age is not None and not pd.isna(hvac_age):
        if hvac_age == 0:
            present.append('New HVAC')
        elif hvac_age <= 5:
            present.append(f'HVAC {int(hvac_age)} years old')
        elif hvac_age > 10:
            missing.append(f'HVAC needs replacement ({int(hvac_age)} years)')

    # Roof age (if known)
    roof_age = row.get('roof_age')
    if roof_age is not None and not pd.isna(roof_age):
        if roof_age == 0:
            present.append('New roof')
        elif roof_age <= 5:
            present.append(f'Roof {int(roof_age)} years old')
        elif roof_age > 15:
            missing.append(f'Roof needs replacement ({int(roof_age)} years)')

    # Default features if lists are too short
    if len(present) < 3:
        present.append(f'City sewer')
        present.append(f'{int(row.get("sqft", 0)):,} sqft living area')

    if len(missing) < 2:
        if not row.get('has_pool'):
            missing.append('Pool')
        if hvac_age is None or pd.isna(hvac_age):
            missing.append('HVAC age (unknown)')

    return {
        'present': present,
        'missing': missing
    }
