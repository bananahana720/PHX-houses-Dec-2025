"""Rendering functions for deal sheet HTML generation.

Contains:
- generate_deal_sheet(): Render individual property deal sheet
- generate_index(): Render master index page
"""


import pandas as pd
from jinja2 import Template

from scripts.lib.kill_switch import (
    SEVERITY_FAIL_THRESHOLD,
    SEVERITY_WARNING_THRESHOLD,
    evaluate_kill_switches_for_display,
)
from src.phx_home_analysis.services.cost_estimation.rates import (
    DOWN_PAYMENT_DEFAULT,
    LOAN_TERM_30YR_MONTHS,
    MORTGAGE_RATE_30YR,
    POOL_TOTAL_MONTHLY,
)

from .templates import DEAL_SHEET_TEMPLATE, INDEX_TEMPLATE
from .utils import extract_features, slugify


def calculate_monthly_cost(row_dict: dict) -> float:
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
    price_num = row_dict.get('price_num') or row_dict.get('price', 0)
    if isinstance(price_num, str):
        # Handle formatted price like "$475,000"
        price_num = int(price_num.replace('$', '').replace(',', ''))

    # Mortgage (30-year fixed, standard down payment)
    loan_amount = max(0, price_num - DOWN_PAYMENT_DEFAULT)
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
    if tax_annual and not pd.isna(tax_annual):
        total += float(tax_annual) / 12

    # HOA fee
    hoa_fee = row_dict.get('hoa_fee')
    if hoa_fee and not pd.isna(hoa_fee) and hoa_fee > 0:
        total += float(hoa_fee)

    # Solar lease
    solar_lease = row_dict.get('solar_lease_monthly')
    if solar_lease and not pd.isna(solar_lease) and solar_lease > 0:
        total += float(solar_lease)

    # Pool maintenance estimate (service + energy costs)
    has_pool = row_dict.get('has_pool')
    if has_pool and not pd.isna(has_pool) and has_pool:
        total += POOL_TOTAL_MONTHLY

    return total


def generate_deal_sheet(row, output_dir):
    """Generate a single deal sheet HTML file.

    Args:
        row: pandas Series with property data
        output_dir: Path object for output directory

    Returns:
        Generated filename (for index linking)
    """
    # Create filename slug
    slug = slugify(row['full_address'])
    filename = f"{int(row['rank']):02d}_{slug}.html"
    filepath = output_dir / filename

    # Clean up NaN values in the row for template rendering
    # Keep None for kill switch evaluation, replace with display values later
    row_dict = {}
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

    # Map CSV field names to expected template names
    if 'commute_min' in row_dict and 'commute_minutes' not in row_dict:
        row_dict['commute_minutes'] = row_dict['commute_min']
    if 'price_num' in row_dict and 'price' not in row_dict:
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
        price_val = row_dict.get('price_num') or row_dict.get('price', 0)
        if isinstance(price_val, str):
            price_val = int(price_val.replace('$', '').replace(',', ''))
        sqft_val = row_dict.get('sqft', 0)
        if sqft_val and sqft_val > 0:
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

    # NOW replace None with display values for template rendering
    if 'tax_annual' not in row_dict or row_dict['tax_annual'] is None:
        row_dict['tax_annual'] = 0
    if 'distance_to_grocery_miles' not in row_dict or row_dict['distance_to_grocery_miles'] is None:
        row_dict['distance_to_grocery_miles'] = 0

    for key, value in row_dict.items():
        if value is None:
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


def generate_index(df, output_dir):
    """Generate index.html master list.

    Args:
        df: pandas DataFrame with all properties
        output_dir: Path object for output directory
    """
    # Add filename column
    df['filename'] = df.apply(
        lambda row: f"{int(row['rank']):02d}_{slugify(row['full_address'])}.html",
        axis=1
    )

    # Calculate stats
    # Use kill_switch_status field from CSV if available
    ks_field = 'kill_switch_status' if 'kill_switch_status' in df.columns else 'kill_switch_passed'
    total_properties = len(df)
    passed_properties = (df[ks_field] == 'PASS').sum()
    failed_properties = total_properties - passed_properties
    avg_score_passed = df[df[ks_field] == 'PASS']['total_score'].mean()

    # Ensure kill_switch_passed column exists for template
    if 'kill_switch_passed' not in df.columns and 'kill_switch_status' in df.columns:
        df['kill_switch_passed'] = df['kill_switch_status']

    # Extract city from full_address if not present
    if 'city' not in df.columns:
        df['city'] = df['full_address'].apply(
            lambda addr: addr.split(',')[1].strip() if ',' in addr and len(addr.split(',')) > 1 else 'Unknown'
        )

    # Extract price if not present or ensure it's numeric
    if 'price' not in df.columns and 'price_num' in df.columns:
        df['price'] = df['price_num']
    elif 'price' in df.columns and df['price'].dtype == 'object':
        # Price is a string like "$625,000", use price_num if available
        if 'price_num' in df.columns:
            df['price'] = df['price_num']

    # Render template
    template = Template(INDEX_TEMPLATE)
    html = template.render(
        total_properties=total_properties,
        passed_properties=passed_properties,
        failed_properties=failed_properties,
        avg_score_passed=avg_score_passed,
        properties=df.to_dict('records')
    )

    # Write file
    filepath = output_dir / 'index.html'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
