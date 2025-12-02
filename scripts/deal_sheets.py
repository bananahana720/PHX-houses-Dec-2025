#!/usr/bin/env python3
"""
DEPRECATED: This module is deprecated and will be removed in a future version.
==============================================================================

Deal Sheet Generator for Phoenix Home Buying Analysis
Generates one-page HTML reports for each property with traffic light kill-switch indicators.

MIGRATION NOTICE:
================
Please use the modular package instead:

    python -m scripts.deal_sheets

This legacy monolithic file (1,057 lines) has been refactored into a modular package:

    scripts/deal_sheets/
    ├── __init__.py          # Package exports
    ├── __main__.py          # CLI entry point
    ├── generator.py         # Main orchestration
    ├── renderer.py          # HTML generation
    ├── templates.py         # Jinja2 templates
    ├── data_loader.py       # CSV/JSON loading
    └── utils.py             # Helpers

See scripts/deal_sheets/README.md for details on the refactoring.
"""

import json
import re
import warnings
from pathlib import Path

import pandas as pd
from jinja2 import Template

# Issue deprecation warning on module import
warnings.warn(
    "deal_sheets.py is deprecated. Use 'python -m scripts.deal_sheets' instead. "
    "See scripts/deal_sheets/README.md for migration details.",
    DeprecationWarning,
    stacklevel=2
)

# Import canonical kill switch evaluation function

# HTML Template for individual deal sheet
DEAL_SHEET_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deal Sheet: {{ property.full_address }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background: #ffffff;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }

        @media print {
            body {
                padding: 0;
            }
            .no-print {
                display: none;
            }
        }

        .header {
            border-bottom: 3px solid #2563eb;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
            color: #1e40af;
        }

        .header-meta {
            display: flex;
            gap: 30px;
            align-items: center;
            flex-wrap: wrap;
            font-size: 18px;
        }

        .header-meta .price {
            font-size: 24px;
            font-weight: 700;
            color: #059669;
        }

        .header-meta .score {
            font-size: 20px;
            font-weight: 600;
        }

        .tier-badge {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .tier-unicorn {
            background: linear-gradient(135deg, #a855f7, #ec4899);
            color: white;
        }

        .tier-contender {
            background: #3b82f6;
            color: white;
        }

        .tier-pass {
            background: #6b7280;
            color: white;
        }

        .section {
            margin-bottom: 25px;
            page-break-inside: avoid;
        }

        .section h2 {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #1e40af;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 6px;
        }

        .kill-switch-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .kill-switch-table th {
            background: #f3f4f6;
            padding: 10px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #d1d5db;
            font-size: 14px;
        }

        .kill-switch-table td {
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 14px;
        }

        .kill-switch-table tr:last-child td {
            border-bottom: none;
        }

        .status-indicator {
            display: inline-block;
            width: 80px;
            padding: 4px 0;
            text-align: center;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-green {
            background: #22c55e;
            color: white;
        }

        .status-red {
            background: #ef4444;
            color: white;
        }

        .status-yellow {
            background: #f59e0b;
            color: white;
        }

        .scorecard {
            background: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }

        .score-row {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            gap: 15px;
        }

        .score-row:last-child {
            margin-bottom: 0;
            padding-top: 12px;
            border-top: 2px solid #d1d5db;
            font-weight: 700;
        }

        .score-label {
            min-width: 100px;
            font-weight: 600;
            font-size: 14px;
        }

        .score-value {
            min-width: 80px;
            font-weight: 700;
            color: #1e40af;
            font-size: 14px;
        }

        .score-bar-container {
            flex: 1;
            height: 24px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }

        .score-bar {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #2563eb);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 8px;
        }

        .score-bar-percentage {
            color: white;
            font-size: 11px;
            font-weight: 700;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }

        .metric {
            background: #f9fafb;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #3b82f6;
        }

        .metric-label {
            font-size: 12px;
            color: #6b7280;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .metric-value {
            font-size: 18px;
            font-weight: 700;
            color: #1e40af;
        }

        .features {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .feature-column {
            flex: 1;
            min-width: 250px;
        }

        .feature-column h3 {
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #059669;
        }

        .feature-column.missing h3 {
            color: #dc2626;
        }

        .feature-column ul {
            list-style: none;
            padding-left: 0;
        }

        .feature-column li {
            padding: 4px 0;
            padding-left: 20px;
            position: relative;
            font-size: 14px;
        }

        .feature-column li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #059669;
            font-weight: 700;
        }

        .feature-column.missing li:before {
            content: "✗";
            color: #dc2626;
        }

        .back-link {
            display: inline-block;
            margin-bottom: 15px;
            color: #2563eb;
            text-decoration: none;
            font-weight: 600;
            padding: 8px 16px;
            border: 2px solid #2563eb;
            border-radius: 6px;
            transition: all 0.2s;
        }

        .back-link:hover {
            background: #2563eb;
            color: white;
        }

        .failure-notice {
            background: #fef2f2;
            border: 2px solid #ef4444;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }

        .failure-notice h3 {
            color: #dc2626;
            font-size: 16px;
            margin-bottom: 8px;
            font-weight: 700;
        }

        .failure-notice ul {
            margin-left: 20px;
            color: #7f1d1d;
        }
    </style>
</head>
<body>
    <a href="index.html" class="back-link no-print">← Back to All Properties</a>

    {% if property.kill_switch_passed != 'PASS' %}
    <div class="failure-notice">
        <h3>⚠️ KILL SWITCH FAILURES</h3>
        <ul>
        {% for failure in property.kill_switch_failures.split(';') if failure.strip() %}
            <li>{{ failure.strip() }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="header">
        <h1>{{ property.full_address }}</h1>
        <div class="header-meta">
            <span class="price">${{ "{:,.0f}".format(property['price']) }}</span>
            <span class="score">{{ property['total_score'] }}/600 pts</span>
            <span class="tier-badge tier-{{ property['tier'].lower() }}">{{ property['tier'] }}</span>
            <span style="color: #6b7280;">Rank #{{ int(property['rank']) }}</span>
        </div>
    </div>

    <div class="section">
        <h2>Kill Switch Status</h2>
        <table class="kill-switch-table">
            <thead>
                <tr>
                    <th>Criterion</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
            {% for name, status in kill_switches.items() %}
                <tr>
                    <td><strong>{{ name }}</strong></td>
                    <td>
                        <span class="status-indicator status-{{ status.color }}">
                            {{ status.label }}
                        </span>
                    </td>
                    <td>{{ status.description }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Scorecard</h2>
        <div class="scorecard">
            <div class="score-row">
                <div class="score-label">Location:</div>
                <div class="score-value">{{ "{:.1f}".format(property.score_location) }}/230</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: {{ (property.score_location / 230 * 100)|round(1) }}%">
                        <span class="score-bar-percentage">{{ (property.score_location / 230 * 100)|round(0)|int }}%</span>
                    </div>
                </div>
            </div>
            <div class="score-row">
                <div class="score-label">Systems:</div>
                <div class="score-value">{{ "{:.1f}".format(property.score_lot_systems) }}/180</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: {{ (property.score_lot_systems / 180 * 100)|round(1) }}%">
                        <span class="score-bar-percentage">{{ (property.score_lot_systems / 180 * 100)|round(0)|int }}%</span>
                    </div>
                </div>
            </div>
            <div class="score-row">
                <div class="score-label">Interior:</div>
                <div class="score-value">{{ "{:.1f}".format(property.score_interior) }}/190</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: {{ (property.score_interior / 190 * 100)|round(1) }}%">
                        <span class="score-bar-percentage">{{ (property.score_interior / 190 * 100)|round(0)|int }}%</span>
                    </div>
                </div>
            </div>
            <div class="score-row">
                <div class="score-label">TOTAL:</div>
                <div class="score-value">{{ property.total_score }}/600</div>
                <div class="score-bar-container">
                    <div class="score-bar" style="width: {{ (property.total_score / 600 * 100)|round(1) }}%">
                        <span class="score-bar-percentage">{{ (property.total_score / 600 * 100)|round(0)|int }}%</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Key Metrics</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-label">Price/Sqft</div>
                <div class="metric-value">${{ "{:.2f}".format(property.price_per_sqft) }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Living Area</div>
                <div class="metric-value">{{ "{:,}".format(int(property.sqft)) }} sqft</div>
            </div>
            <div class="metric">
                <div class="metric-label">Commute Time</div>
                <div class="metric-value">{{ int(property.commute_minutes) }} min</div>
            </div>
            <div class="metric">
                <div class="metric-label">School Rating</div>
                <div class="metric-value">{{ property.school_rating }}/10</div>
            </div>
            <div class="metric">
                <div class="metric-label">Property Tax</div>
                <div class="metric-value">${{ "{:,}".format(int(property.tax_annual)) }}/yr</div>
            </div>
            <div class="metric">
                <div class="metric-label">Grocery Distance</div>
                <div class="metric-value">{{ property.distance_to_grocery_miles }} mi</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Feature Highlights</h2>
        <div class="features">
            <div class="feature-column">
                <h3>PRESENT</h3>
                <ul>
                {% for feature in features.present %}
                    <li>{{ feature }}</li>
                {% endfor %}
                </ul>
            </div>
            <div class="feature-column missing">
                <h3>MISSING/UNKNOWN</h3>
                <ul>
                {% for feature in features.missing %}
                    <li>{{ feature }}</li>
                {% endfor %}
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""

# HTML Template for index page
INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phoenix Home Deal Sheets - Master List</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background: #f3f4f6;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header {
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 32px;
            font-weight: 700;
            color: #1e40af;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 16px;
            color: #6b7280;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-card h3 {
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            opacity: 0.9;
        }

        .stat-card .value {
            font-size: 32px;
            font-weight: 700;
        }

        .properties-table {
            width: 100%;
            border-collapse: collapse;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .properties-table thead {
            background: #f3f4f6;
        }

        .properties-table th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #d1d5db;
            font-size: 14px;
            color: #374151;
        }

        .properties-table td {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 14px;
        }

        .properties-table tbody tr:hover {
            background: #f9fafb;
        }

        .properties-table tbody tr.failed {
            background: #fef2f2;
        }

        .properties-table tbody tr.failed:hover {
            background: #fee2e2;
        }

        .rank-badge {
            display: inline-block;
            width: 40px;
            height: 40px;
            line-height: 40px;
            text-align: center;
            border-radius: 50%;
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            color: white;
            font-weight: 700;
            font-size: 16px;
        }

        .rank-badge.top3 {
            background: linear-gradient(135deg, #10b981, #059669);
        }

        .tier-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .tier-unicorn {
            background: linear-gradient(135deg, #a855f7, #ec4899);
            color: white;
        }

        .tier-contender {
            background: #3b82f6;
            color: white;
        }

        .tier-pass {
            background: #6b7280;
            color: white;
        }

        .address-link {
            color: #2563eb;
            text-decoration: none;
            font-weight: 600;
        }

        .address-link:hover {
            text-decoration: underline;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
        }

        .status-pass {
            background: #dcfce7;
            color: #166534;
        }

        .status-fail {
            background: #fee2e2;
            color: #991b1b;
        }

        .score {
            font-weight: 700;
            color: #1e40af;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Phoenix Home Deal Sheets</h1>
            <p>Automated property analysis with traffic light kill-switch indicators</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Properties</h3>
                <div class="value">{{ total_properties }}</div>
            </div>
            <div class="stat-card">
                <h3>Passed Filters</h3>
                <div class="value">{{ passed_properties }}</div>
            </div>
            <div class="stat-card">
                <h3>Failed Filters</h3>
                <div class="value">{{ failed_properties }}</div>
            </div>
            <div class="stat-card">
                <h3>Avg Score (Passed)</h3>
                <div class="value">{{ "{:.1f}".format(avg_score_passed) }}</div>
            </div>
        </div>

        <table class="properties-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Address</th>
                    <th>City</th>
                    <th>Price</th>
                    <th>Score</th>
                    <th>Tier</th>
                    <th>Status</th>
                    <th>Deal Sheet</th>
                </tr>
            </thead>
            <tbody>
            {% for prop in properties %}
                <tr class="{{ 'failed' if prop.kill_switch_passed != 'PASS' else '' }}">
                    <td>
                        <span class="rank-badge {{ 'top3' if prop.rank <= 3 else '' }}">
                            {{ prop.rank }}
                        </span>
                    </td>
                    <td>{{ prop.full_address.split(',')[0] }}</td>
                    <td>{{ prop.city }}</td>
                    <td>${{ "{:,.0f}".format(prop.price) }}</td>
                    <td class="score">{{ prop.total_score }}</td>
                    <td>
                        <span class="tier-badge tier-{{ prop.tier.lower() }}">
                            {{ prop.tier }}
                        </span>
                    </td>
                    <td>
                        <span class="status-badge status-{{ 'pass' if prop.kill_switch_passed == 'PASS' else 'fail' }}">
                            {{ prop.kill_switch_passed }}
                        </span>
                    </td>
                    <td>
                        <a href="{{ prop.filename }}" class="address-link">View Details →</a>
                    </td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


def slugify(text):
    """Convert text to URL-friendly slug."""
    # Extract street address (first part before comma)
    street = text.split(',')[0].lower()
    # Remove special characters and replace spaces with underscores
    slug = re.sub(r'[^\w\s-]', '', street)
    slug = re.sub(r'[-\s]+', '_', slug)
    return slug


def extract_features(row):
    """Extract present and missing features from property data."""
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
        present.append('City sewer')
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


def generate_deal_sheet(row, output_dir):
    """Generate a single deal sheet HTML file."""
    # Create filename slug
    slug = slugify(row['full_address'])
    filename = f"{row['rank']:02d}_{slug}.html"
    filepath = output_dir / filename

    # Clean up NaN values in the row for template rendering
    row_dict = {}
    for key, value in row.items():
        # Check for NaN - pandas is already imported at module level
        if isinstance(value, float) and pd.isna(value):
            # Replace NaN with appropriate defaults
            if 'distance' in key or 'minutes' in key:
                row_dict[key] = 0
            elif 'rating' in key or 'age' in key or 'annual' in key:
                row_dict[key] = 0
            else:
                row_dict[key] = 'N/A'
        else:
            row_dict[key] = value

    # Convert back to Series for consistent access
    row_clean = pd.Series(row_dict)

    # Evaluate kill switches using canonical function
    # Returns dict with kill switch results and '_summary' key
    kill_switches = evaluate_kill_switches_for_display(row_clean)

    # Remove the summary key since template doesn't use it
    kill_switches.pop('_summary', None)

    # Extract features
    features = extract_features(row_clean)

    # Render template
    template = Template(DEAL_SHEET_TEMPLATE)
    html = template.render(
        property=row_clean,
        kill_switches=kill_switches,
        features=features,
        int=int  # Make int() available in template
    )

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    return filename


def generate_index(df, output_dir):
    """Generate index.html master list."""
    # Add filename column
    df['filename'] = df.apply(
        lambda row: f"{row['rank']:02d}_{slugify(row['full_address'])}.html",
        axis=1
    )

    # Calculate stats
    total_properties = len(df)
    passed_properties = (df['kill_switch_passed'] == 'PASS').sum()
    failed_properties = total_properties - passed_properties
    avg_score_passed = df[df['kill_switch_passed'] == 'PASS']['total_score'].mean()

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


def main():
    """Main execution function."""
    # Issue deprecation warning at runtime
    print("=" * 70)
    print("WARNING: This script is deprecated!")
    print("=" * 70)
    print("Please use instead:")
    print("    python -m scripts.deal_sheets")
    print("")
    print("The legacy deal_sheets.py file will be removed in a future version.")
    print("See scripts/deal_sheets/README.md for migration details.")
    print("=" * 70)
    print("Continuing with legacy implementation...\n")

    # Get the directory of this script
    base_dir = Path(__file__).parent

    # Define paths
    ranked_csv = base_dir / 'phx_homes_ranked.csv'
    enrichment_json = base_dir / 'enrichment_data.json'
    output_dir = base_dir / 'deal_sheets'

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print("Loading data...")
    # Load ranked homes CSV
    df = pd.read_csv(ranked_csv)

    # Load enrichment data
    with open(enrichment_json) as f:
        enrichment_data = json.load(f)

    # Create lookup dictionary for enrichment data
    enrichment_lookup = {item['full_address']: item for item in enrichment_data}

    # Merge enrichment data into dataframe
    for idx, row in df.iterrows():
        address = row['full_address']
        if address in enrichment_lookup:
            enrich = enrichment_lookup[address]
            for key, value in enrich.items():
                if key not in df.columns:
                    df.at[idx, key] = value

    print(f"Generating deal sheets for {len(df)} properties...")

    # Generate individual deal sheets
    for idx, row in df.iterrows():
        filename = generate_deal_sheet(row, output_dir)
        print(f"  [{row['rank']:2d}/{len(df)}] Generated: {filename}")

    # Generate index page
    print("\nGenerating index.html...")
    generate_index(df, output_dir)

    print(f"\n[OK] Complete! Generated {len(df)} deal sheets in: {output_dir}")
    print(f"[OK] Open {output_dir / 'index.html'} to view the master list")

    # Print sample stats
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"Total Properties:        {len(df)}")
    print(f"Passed Kill Switches:    {(df['kill_switch_passed'] == 'PASS').sum()}")
    print(f"Failed Kill Switches:    {(df['kill_switch_passed'] != 'PASS').sum()}")
    print(f"Average Score (Passed):  {df[df['kill_switch_passed'] == 'PASS']['total_score'].mean():.1f}")
    print(f"Average Score (All):     {df['total_score'].mean():.1f}")
    print(f"Top Score:               {df['total_score'].max():.1f} (Rank #{df['rank'].min()})")

    # Show top 3
    print("\n" + "="*60)
    print("TOP 3 PROPERTIES")
    print("="*60)
    for idx, row in df.head(3).iterrows():
        status = "PASS" if row['kill_switch_passed'] == 'PASS' else "FAIL"
        print(f"\n#{row['rank']}: {row['full_address']}")
        print(f"  Score: {row['total_score']}/600 | Status: {status}")
        print(f"  Price: ${row['price']:,.0f} | {row['city']}")


if __name__ == '__main__':
    main()
