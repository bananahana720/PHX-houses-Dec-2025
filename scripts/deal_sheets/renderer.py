"""Rendering functions for deal sheet HTML generation.

Contains:
- generate_deal_sheet(): Render individual property deal sheet
- generate_index(): Render master index page with dynamic JSON loading
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import pandas as pd
from jinja2 import Template

from scripts.lib.kill_switch import (
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    evaluate_kill_switches_for_display,
)
from src.phx_home_analysis.config.constants import FILENAME_RANK_PADDING
from src.phx_home_analysis.services.cost_estimation.rates import (
    DOWN_PAYMENT_DEFAULT,
    LOAN_TERM_30YR_MONTHS,
    MORTGAGE_RATE_30YR,
    POOL_TOTAL_MONTHLY,
)

from .templates import DEAL_SHEET_TEMPLATE, INDEX_TEMPLATE
from .utils import extract_features, slugify


def _format_rank(rank: int) -> str:
    """Format rank number with zero-padding for filenames.

    Uses FILENAME_RANK_PADDING to ensure consistent filename ordering.

    Args:
        rank: Property rank number

    Returns:
        Zero-padded rank string (e.g., "01", "02", ...)
    """
    return str(rank).zfill(FILENAME_RANK_PADDING)


class PropertyRow(TypedDict, total=False):
    """Type definition for property row dictionary.

    Uses total=False since most fields are optional depending on data availability.
    """

    # Core identifiers
    full_address: str
    rank: int | float

    # Price fields
    price: int | float | str | None
    price_num: int | float | None
    price_per_sqft: float | None

    # Property characteristics
    beds: int | float | None
    baths: float | None
    sqft: int | float | None
    lot_sqft: int | float | None
    year_built: int | float | None
    garage_spaces: int | float | None
    has_pool: bool | None

    # Financial fields
    tax_annual: float | None
    hoa_fee: float | None
    solar_lease_monthly: float | None

    # Kill switch fields
    kill_switch_status: str | None
    kill_switch_passed: str | None
    kill_switch_failures: str | None
    sewer_type: str | None

    # Score fields
    total_score: float | None
    score_location: float | None
    score_lot_systems: float | None
    score_interior: float | None
    section_a_score: float | None
    section_b_score: float | None
    section_c_score: float | None
    tier: str | None

    # Location/commute
    city: str | None
    latitude: float | None
    longitude: float | None
    commute_minutes: float | None
    commute_min: float | None
    school_rating: float | None
    distance_to_grocery_miles: float | None
    distance_to_highway_miles: float | None

    # Interior assessment scores
    kitchen_layout_score: float | None
    master_suite_score: float | None
    natural_light_score: float | None
    high_ceilings_score: float | None
    fireplace_present: bool | float | None
    laundry_area_score: float | None
    aesthetics_score: float | None
    backyard_utility_score: float | None
    safety_neighborhood_score: float | None
    parks_walkability_score: float | None

    # System ages
    pool_equipment_age: float | None
    roof_age: float | None
    hvac_age: float | None

    # Solar status
    solar_status: str | None


def calculate_monthly_cost(row_dict: dict[str, object]) -> float:
    """Calculate estimated monthly cost for a property.

    Includes:
    - Mortgage payment (30-year fixed, uses rates from cost_estimation.rates)
    - Property tax (annual / 12)
    - HOA fee
    - Solar lease (if applicable)
    - Pool maintenance estimate (if pool present)

    Args:
        row_dict: Dictionary with property data

    Returns:
        Total estimated monthly cost
    """
    total = 0.0

    # Get price
    price_num = row_dict.get('price_num') or row_dict.get('price', 0) or 0
    if isinstance(price_num, str):
        # Handle formatted price like "$475,000"
        price_num = int(price_num.replace('$', '').replace(',', ''))
    elif not isinstance(price_num, (int, float)):
        price_num = 0

    # Mortgage (30-year fixed, standard down payment)
    loan_amount = max(0, int(price_num) - DOWN_PAYMENT_DEFAULT)
    if loan_amount > 0:
        monthly_rate = MORTGAGE_RATE_30YR / 12
        num_payments = LOAN_TERM_30YR_MONTHS
        if monthly_rate > 0:
            mortgage = loan_amount * (
                monthly_rate * (1 + monthly_rate) ** num_payments
            ) / ((1 + monthly_rate) ** num_payments - 1)
        else:
            mortgage = loan_amount / num_payments
        total += mortgage

    # Property tax (annual / 12)
    tax_annual = row_dict.get('tax_annual')
    if tax_annual is not None and not pd.isna(tax_annual):
        try:
            total += float(str(tax_annual)) / 12
        except (ValueError, TypeError):
            pass

    # HOA fee
    hoa_fee = row_dict.get('hoa_fee')
    if hoa_fee is not None and not pd.isna(hoa_fee):
        try:
            hoa_float = float(str(hoa_fee))
            if hoa_float > 0:
                total += hoa_float
        except (ValueError, TypeError):
            pass

    # Solar lease
    solar_lease = row_dict.get('solar_lease_monthly')
    if solar_lease is not None and not pd.isna(solar_lease):
        try:
            lease_float = float(str(solar_lease))
            if lease_float > 0:
                total += lease_float
        except (ValueError, TypeError):
            pass

    # Pool maintenance estimate (service + energy costs)
    has_pool = row_dict.get('has_pool')
    if has_pool and not pd.isna(has_pool) and has_pool:
        total += POOL_TOTAL_MONTHLY

    return total


def generate_deal_sheet(row: pd.Series, output_dir: Path) -> str:
    """Generate a single deal sheet HTML file.

    Args:
        row: pandas Series with property data
        output_dir: Path object for output directory

    Returns:
        Generated filename (for index linking)
    """
    # Create filename slug
    slug = slugify(row['full_address'])
    filename = f"{_format_rank(int(row['rank']))}_{slug}.html"
    filepath = output_dir / filename

    # Clean up NaN values in the row for template rendering
    # Keep None for kill switch evaluation, replace with display values later
    row_dict: dict[str, object] = {}
    for key, value in row.items():
        # Check for NaN - pandas is already imported at module level
        if isinstance(value, float) and pd.isna(value):
            # Keep None for kill switch fields, use 0 for numeric fields
            if key in ['hoa_fee', 'sewer_type', 'garage_spaces', 'lot_sqft', 'year_built']:
                row_dict[key] = None
            elif 'distance' in key or 'minutes' in key or 'rating' in key or 'age' in key or 'annual' in key:
                row_dict[key] = 0
            else:
                row_dict[key] = None
        else:
            row_dict[key] = value

    # Convert numeric string fields to proper types (CSV stores everything as strings)
    numeric_fields = [
        'price_num', 'beds', 'baths', 'sqft', 'price_per_sqft', 'lot_sqft',
        'year_built', 'garage_spaces', 'tax_annual', 'hoa_fee', 'commute_minutes',
        'school_rating', 'distance_to_grocery_miles', 'distance_to_highway_miles',
        'solar_lease_monthly', 'pool_equipment_age', 'roof_age', 'hvac_age',
        'kitchen_layout_score', 'master_suite_score', 'natural_light_score',
        'high_ceilings_score', 'fireplace_present', 'laundry_area_score',
        'aesthetics_score', 'backyard_utility_score', 'safety_neighborhood_score',
        'parks_walkability_score', 'score_location', 'score_lot_systems',
        'score_interior', 'total_score', 'rank', 'latitude', 'longitude'
    ]
    for field in numeric_fields:
        if field in row_dict and row_dict[field] is not None:
            val = row_dict[field]
            if isinstance(val, str) and val.strip() and val.strip().lower() not in ('n/a', 'nan', ''):
                try:
                    row_dict[field] = float(val.replace(',', ''))
                except ValueError:
                    row_dict[field] = None
            elif isinstance(val, str):
                row_dict[field] = None

    # Map CSV fields to template expectations
    # CSV has 'kill_switch_status' (PASS/FAIL), template expects 'kill_switch_passed'
    if 'kill_switch_status' in row_dict:
        row_dict['kill_switch_passed'] = row_dict['kill_switch_status']

    # Template expects 'kill_switch_failures' as semicolon-separated string
    # We need to evaluate kill switches to get failure messages
    from scripts.lib.kill_switch import evaluate_kill_switches
    verdict, severity, failure_msgs, _ = evaluate_kill_switches(row_dict)
    row_dict['kill_switch_failures'] = '; '.join(failure_msgs) if failure_msgs else ''

    # Map score fields to template expectations (handle both old and new column names)
    if 'section_a_score' in row_dict and 'score_location' not in row_dict:
        row_dict['score_location'] = row_dict['section_a_score']
    if 'section_b_score' in row_dict and 'score_lot_systems' not in row_dict:
        row_dict['score_lot_systems'] = row_dict['section_b_score']
    if 'section_c_score' in row_dict and 'score_interior' not in row_dict:
        row_dict['score_interior'] = row_dict['section_c_score']

    # Ensure score fields are numeric (they might be strings from CSV/merge)
    score_fields = ['score_location', 'score_lot_systems', 'score_interior', 'total_score']
    for field in score_fields:
        val = row_dict.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ''):
            row_dict[field] = 0.0
        elif isinstance(val, str):
            try:
                row_dict[field] = float(val)
            except ValueError:
                row_dict[field] = 0.0

    # Map CSV field names to expected template names
    if 'commute_min' in row_dict and 'commute_minutes' not in row_dict:
        row_dict['commute_minutes'] = row_dict['commute_min']
    # Template expects 'price' to be numeric for formatting; use price_num
    if 'price_num' in row_dict:
        row_dict['price'] = row_dict['price_num']

    # Ensure interior assessment scores are available for display
    interior_fields = [
        'kitchen_layout_score', 'master_suite_score', 'natural_light_score',
        'high_ceilings_score', 'fireplace_present', 'laundry_area_score',
        'aesthetics_score', 'backyard_utility_score', 'safety_neighborhood_score',
        'parks_walkability_score'
    ]
    for field in interior_fields:
        if field not in row_dict:
            row_dict[field] = None

    # Add missing fields with defaults if not present
    if 'price_per_sqft' not in row_dict and 'sqft' in row_dict:
        # Use price_num (int) for calculation, not price (might be formatted string)
        raw_price = row_dict.get('price_num') or row_dict.get('price', 0)
        price_val: float
        if isinstance(raw_price, str):
            price_val = float(raw_price.replace('$', '').replace(',', ''))
        elif isinstance(raw_price, (int, float)):
            price_val = float(raw_price)
        else:
            price_val = 0.0
        raw_sqft = row_dict.get('sqft', 0)
        sqft_val = float(raw_sqft) if isinstance(raw_sqft, (int, float)) else 0.0
        if sqft_val > 0:
            row_dict['price_per_sqft'] = price_val / sqft_val
        else:
            row_dict['price_per_sqft'] = 0

    # Calculate monthly cost BEFORE replacing None with display values
    monthly_cost = calculate_monthly_cost(row_dict)

    # Evaluate kill switches BEFORE replacing None with display values
    # Kill switches expect None/numeric values
    kill_switches = evaluate_kill_switches_for_display(row_dict)

    # Extract summary from kill_switches for template
    ks_summary = kill_switches.pop("_summary", {})
    ks_verdict = ks_summary.get("verdict", "PASS")
    ks_severity = ks_summary.get("severity_score", 0.0)
    ks_has_hard_failure = ks_summary.get("has_hard_failure", False)

    # Helper to check for None, NaN, or empty string
    def is_empty(val: object) -> bool:
        if val is None:
            return True
        if isinstance(val, float) and pd.isna(val):
            return True
        if isinstance(val, str) and val.strip() == '':
            return True
        return False

    # NOW replace None/empty with display values for template rendering
    if 'tax_annual' not in row_dict or is_empty(row_dict['tax_annual']):
        row_dict['tax_annual'] = 0
    if 'distance_to_grocery_miles' not in row_dict or is_empty(row_dict['distance_to_grocery_miles']):
        row_dict['distance_to_grocery_miles'] = 0

    for key, value in row_dict.items():
        if is_empty(value):
            # Use 'N/A' for string fields, 0 for numeric
            if 'distance' in key or 'minutes' in key or 'rating' in key or 'age' in key or 'annual' in key or 'sqft' in key:
                row_dict[key] = 0
            else:
                row_dict[key] = 'N/A'

    # Convert back to Series for consistent access
    row_clean = pd.Series(row_dict)

    # Extract features
    features = extract_features(row_clean)

    # Render template
    template = Template(DEAL_SHEET_TEMPLATE)
    html = template.render(
        property=row_clean,
        kill_switches=kill_switches,
        features=features,
        ks_verdict=ks_verdict,
        ks_severity=ks_severity,
        ks_has_hard_failure=ks_has_hard_failure,
        severity_fail_threshold=SEVERITY_FAIL_THRESHOLD,
        severity_warning_threshold=SEVERITY_WARNING_THRESHOLD,
        monthly_cost=monthly_cost,  # For budget warning badge
        int=int  # Make int() available in template
    )

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    return filename


def generate_index(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate index.html and data.json for dynamic loading.

    Creates:
    - data.json: Property data + metadata for JavaScript fetch
    - index.html: JS shell that dynamically loads data.json

    Args:
        df: pandas DataFrame with all properties
        output_dir: Path object for output directory
    """
    import json
    from datetime import datetime

    # Add filename column
    df['filename'] = df.apply(
        lambda row: f"{_format_rank(int(row['rank']))}_{slugify(row['full_address'])}.html",
        axis=1
    )

    # Calculate stats
    # Use kill_switch_status field from CSV if available
    ks_field = 'kill_switch_status' if 'kill_switch_status' in df.columns else 'kill_switch_passed'
    total_properties = len(df)

    # Normalize status values for comparison (handle 'PASS', 'true', True, etc.)
    def is_passed(val: object) -> bool:
        return str(val).lower() in ('pass', 'true', '1')

    passed_mask = df[ks_field].apply(is_passed)
    passed_count = int(passed_mask.sum())
    failed_count = total_properties - passed_count

    # Calculate avg score for passed properties
    passed_df = df[passed_mask]
    if len(passed_df) > 0:
        # Convert scores to numeric, handling various formats
        scores = pd.to_numeric(passed_df['total_score'], errors='coerce')
        avg_score = scores.mean()
        avg_score_passed = round(avg_score, 1) if not pd.isna(avg_score) else 0.0
    else:
        avg_score_passed = 0.0

    # Extract city from full_address if not present
    if 'city' not in df.columns:
        df['city'] = df['full_address'].apply(
            lambda addr: addr.split(',')[1].strip() if ',' in addr and len(addr.split(',')) > 1 else 'Unknown'
        )

    # Ensure price is numeric
    if 'price' not in df.columns and 'price_num' in df.columns:
        df['price'] = df['price_num']
    elif 'price' in df.columns and df['price'].dtype == 'object':
        if 'price_num' in df.columns:
            df['price'] = df['price_num']

    # Build properties list for JSON
    properties = []
    for _, row in df.iterrows():
        # Get price value safely
        price_val = row.get('price_num') or row.get('price', 0)
        if isinstance(price_val, str):
            price_val = float(price_val.replace('$', '').replace(',', '') or 0)

        # Get score safely
        score_val = row.get('total_score', 0)
        if pd.isna(score_val) or score_val == '' or score_val is None:
            score_val = 0.0
        else:
            try:
                score_val = float(score_val)
            except (ValueError, TypeError):
                score_val = 0.0

        # Get status - normalize to PASS/FAIL
        raw_status = row.get(ks_field, 'UNKNOWN')
        if str(raw_status).lower() in ('pass', 'true', '1'):
            status = 'PASS'
        elif str(raw_status).lower() in ('fail', 'false', '0'):
            status = 'FAIL'
        else:
            status = str(raw_status)

        properties.append({
            'rank': int(row['rank']),
            'address': str(row['full_address']).split(',')[0],
            'full_address': str(row['full_address']),
            'city': str(row.get('city', 'Unknown')),
            'price': float(price_val),
            'total_score': float(score_val),
            'tier': str(row.get('tier', 'pass')).lower(),
            'status': status,
            'filename': row['filename']
        })

    # Build data.json structure
    data_json = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_properties': total_properties,
            'passed_properties': passed_count,
            'failed_properties': failed_count,
            'avg_score_passed': avg_score_passed
        },
        'properties': properties
    }

    # Write data.json
    json_path = output_dir / 'data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data_json, f, indent=2)

    # Render HTML template (JS shell - no data passed)
    template = Template(INDEX_TEMPLATE)
    html = template.render()

    # Write index.html
    filepath = output_dir / 'index.html'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
