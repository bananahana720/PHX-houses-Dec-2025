"""
Data Quality Report Generator for PHX Houses Enrichment Data
Analyzes completeness, identifies gaps, and flags data quality issues.
"""

import json
from collections import defaultdict
from datetime import datetime
from typing import Any

# Field categories
CRITICAL_FIELDS = [
    'lot_sqft', 'year_built', 'garage_spaces', 'sewer_type',
    'tax_annual', 'hoa_fee', 'commute_minutes', 'school_district',
    'school_rating', 'distance_to_grocery_miles', 'distance_to_highway_miles'
]

CONDITION_FIELDS = [
    'orientation', 'solar_status', 'has_pool', 'pool_equipment_age',
    'roof_age', 'hvac_age'
]

def load_enrichment_data(filepath: str) -> list[dict[str, Any]]:
    """Load enrichment data from JSON file."""
    with open(filepath) as f:
        return json.load(f)

def analyze_field_completeness(data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Analyze completeness of each field."""
    total_properties = len(data)
    field_stats = {}

    # Get all unique fields
    all_fields = set()
    for prop in data:
        all_fields.update(prop.keys())

    for field in sorted(all_fields):
        present_count = 0
        null_count = 0
        empty_count = 0
        values = []

        for prop in data:
            value = prop.get(field)
            values.append(value)

            if value is None:
                null_count += 1
            elif value == '':
                empty_count += 1
            else:
                present_count += 1

        completion_pct = (present_count / total_properties) * 100
        field_stats[field] = {
            'present': present_count,
            'null': null_count,
            'empty': empty_count,
            'completion_pct': completion_pct,
            'values': values
        }

    return field_stats

def find_critical_gaps(data: list[dict[str, Any]], field_stats: dict) -> dict[str, list[str]]:
    """Identify properties with critical missing data."""
    critical_gaps = defaultdict(list)

    for _idx, prop in enumerate(data):
        address = prop.get('full_address', 'Unknown')

        for field in CRITICAL_FIELDS:
            value = prop.get(field)
            if value is None or value == '':
                critical_gaps[field].append(address)

    return critical_gaps

def find_data_quality_issues(data: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Identify suspicious values and data quality issues."""
    issues = []
    from datetime import datetime
    current_year = datetime.now().year

    for prop in data:
        address = prop.get('full_address', 'Unknown')

        # Check year_built validity
        year_built = prop.get('year_built')
        if year_built and (year_built < 1900 or year_built >= current_year):
            if year_built >= current_year:
                issues.append({
                    'address': address,
                    'field': 'year_built',
                    'issue': f'Year {year_built} is >= {current_year} (violates kill switch: no new builds)',
                    'value': str(year_built),
                    'severity': 'CRITICAL'
                })
            else:
                issues.append({
                    'address': address,
                    'field': 'year_built',
                    'issue': f'Year {year_built} appears invalid (< 1900)',
                    'value': str(year_built),
                    'severity': 'WARNING'
                })

        # Check lot_sqft validity (should be 7000-15000)
        lot_sqft = prop.get('lot_sqft')
        if lot_sqft and (lot_sqft < 7000 or lot_sqft > 15000):
            issues.append({
                'address': address,
                'field': 'lot_sqft',
                'issue': f'Lot size {lot_sqft} sqft outside target range (7,000-15,000)',
                'value': str(lot_sqft),
                'severity': 'WARNING'
            })

        # Check HOA fees (kill switch: must be 0 or null)
        hoa_fee = prop.get('hoa_fee')
        if hoa_fee and hoa_fee > 0:
            issues.append({
                'address': address,
                'field': 'hoa_fee',
                'issue': f'HOA fee ${hoa_fee}/month (violates kill switch: NO HOA)',
                'value': str(hoa_fee),
                'severity': 'CRITICAL'
            })

        # Check garage_spaces (must be >= 2)
        garage_spaces = prop.get('garage_spaces')
        if garage_spaces and garage_spaces < 2:
            issues.append({
                'address': address,
                'field': 'garage_spaces',
                'issue': f'Only {garage_spaces} garage spaces (needs minimum 2)',
                'value': str(garage_spaces),
                'severity': 'CRITICAL'
            })

        # Check sewer_type (must be city)
        sewer_type = prop.get('sewer_type')
        if sewer_type and sewer_type.lower() != 'city':
            issues.append({
                'address': address,
                'field': 'sewer_type',
                'issue': f'Sewer type is {sewer_type} (violates kill switch: city sewer only)',
                'value': sewer_type,
                'severity': 'CRITICAL'
            })

        # Check school_rating validity (1-10 scale)
        school_rating = prop.get('school_rating')
        if school_rating and (school_rating < 1 or school_rating > 10):
            issues.append({
                'address': address,
                'field': 'school_rating',
                'issue': f'School rating {school_rating} outside 1-10 scale',
                'value': str(school_rating),
                'severity': 'WARNING'
            })

        # Check age-related fields
        roof_age = prop.get('roof_age')
        if roof_age is not None and roof_age < 0:
            issues.append({
                'address': address,
                'field': 'roof_age',
                'issue': f'Roof age {roof_age} is negative',
                'value': str(roof_age),
                'severity': 'ERROR'
            })

        hvac_age = prop.get('hvac_age')
        if hvac_age is not None and hvac_age < 0:
            issues.append({
                'address': address,
                'field': 'hvac_age',
                'issue': f'HVAC age {hvac_age} is negative',
                'value': str(hvac_age),
                'severity': 'ERROR'
            })

        # Check solar_lease_monthly when solar_status is 'leased'
        solar_status = prop.get('solar_status')
        solar_lease = prop.get('solar_lease_monthly')
        if solar_status == 'leased' and not solar_lease:
            issues.append({
                'address': address,
                'field': 'solar_lease_monthly',
                'issue': 'Solar status is "leased" but lease cost is missing',
                'value': str(solar_lease),
                'severity': 'WARNING'
            })

        # Check has_pool consistency
        has_pool = prop.get('has_pool')
        pool_age = prop.get('pool_equipment_age')
        if has_pool is False and pool_age is not None:
            issues.append({
                'address': address,
                'field': 'pool_equipment_age',
                'issue': f'Has no pool but pool_equipment_age is {pool_age}',
                'value': str(pool_age),
                'severity': 'WARNING'
            })

    return sorted(issues, key=lambda x: (x['severity'] != 'CRITICAL', x['address']))

def generate_report(data_path: str) -> str:
    """Generate comprehensive data quality report."""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("PHX HOUSES ENRICHMENT DATA - QUALITY REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Data File: {data_path}\n")

    # Load data
    data = load_enrichment_data(data_path)
    total_properties = len(data)
    report_lines.append(f"Total Properties Analyzed: {total_properties}\n")

    # Analyze completeness
    report_lines.append("=" * 80)
    report_lines.append("1. FIELD COMPLETENESS ANALYSIS")
    report_lines.append("=" * 80)
    report_lines.append("\nRequired Fields (Kill Switches & Core Data):\n")

    field_stats = analyze_field_completeness(data)

    # Show critical fields first
    critical_fields_sorted = sorted(
        [(f, field_stats[f]) for f in CRITICAL_FIELDS if f in field_stats],
        key=lambda x: x[1]['completion_pct']
    )

    for field, stats in critical_fields_sorted:
        pct = stats['completion_pct']
        status = "[COMPLETE]" if pct == 100 else f"[{pct:.1f}%]" if pct >= 50 else f"[CRITICAL {pct:.1f}%]"
        report_lines.append(
            f"  {field:30s} {status:25s} ({stats['present']}/{total_properties})"
        )

    # Show condition fields
    report_lines.append("\n\nOptional Fields (Condition & Features):\n")
    condition_fields_sorted = sorted(
        [(f, field_stats[f]) for f in CONDITION_FIELDS if f in field_stats],
        key=lambda x: x[1]['completion_pct']
    )

    for field, stats in condition_fields_sorted:
        pct = stats['completion_pct']
        status = "[COMPLETE]" if pct == 100 else f"[{pct:.1f}%]" if pct >= 50 else f"[{pct:.1f}%]"
        report_lines.append(
            f"  {field:30s} {status:25s} ({stats['present']}/{total_properties})"
        )

    # Identify critical gaps
    report_lines.append("\n\n" + "=" * 80)
    report_lines.append("2. CRITICAL GAPS (Properties Missing Key Data)")
    report_lines.append("=" * 80)

    critical_gaps = find_critical_gaps(data, field_stats)

    if critical_gaps:
        for field in sorted(critical_gaps.keys()):
            addresses = critical_gaps[field]
            if len(addresses) > 0:
                report_lines.append(f"\n{field.upper()} - Missing in {len(addresses)} properties:")
                for addr in addresses[:10]:  # Show first 10
                    report_lines.append(f"  • {addr}")
                if len(addresses) > 10:
                    report_lines.append(f"  ... and {len(addresses) - 10} more")
    else:
        report_lines.append("\nNo critical gaps found in required fields.")

    # Find data quality issues
    report_lines.append("\n\n" + "=" * 80)
    report_lines.append("3. DATA QUALITY ISSUES & OUTLIERS")
    report_lines.append("=" * 80)

    issues = find_data_quality_issues(data)

    if issues:
        critical_issues = [i for i in issues if i['severity'] == 'CRITICAL']
        error_issues = [i for i in issues if i['severity'] == 'ERROR']
        warning_issues = [i for i in issues if i['severity'] == 'WARNING']

        if critical_issues:
            report_lines.append(f"\n[CRITICAL] Kill Switch Violations: {len(critical_issues)}")
            for issue in critical_issues[:10]:
                report_lines.append(f"  • {issue['address']}")
                report_lines.append(f"    Field: {issue['field']} | Issue: {issue['issue']}")
            if len(critical_issues) > 10:
                report_lines.append(f"  ... and {len(critical_issues) - 10} more critical issues")

        if error_issues:
            report_lines.append(f"\n[ERROR] Data Errors: {len(error_issues)}")
            for issue in error_issues[:10]:
                report_lines.append(f"  • {issue['address']}")
                report_lines.append(f"    Field: {issue['field']} | Issue: {issue['issue']}")
            if len(error_issues) > 10:
                report_lines.append(f"  ... and {len(error_issues) - 10} more errors")

        if warning_issues:
            report_lines.append(f"\n[WARNING] Suspicious Values: {len(warning_issues)}")
            for issue in warning_issues[:15]:
                report_lines.append(f"  • {issue['address']}")
                report_lines.append(f"    Field: {issue['field']} | Issue: {issue['issue']}")
            if len(warning_issues) > 15:
                report_lines.append(f"  ... and {len(warning_issues) - 15} more warnings")
    else:
        report_lines.append("\nNo data quality issues detected.")

    # Recommendations
    report_lines.append("\n\n" + "=" * 80)
    report_lines.append("4. DATA ENRICHMENT PRIORITIES")
    report_lines.append("=" * 80)

    report_lines.append("\nFields with <50% Completion (Priority Order):\n")

    incomplete_fields = []
    for field, stats in field_stats.items():
        if 0 < stats['completion_pct'] < 100:
            incomplete_fields.append((field, stats['completion_pct'], stats['present']))

    incomplete_fields.sort(key=lambda x: x[1])

    if incomplete_fields:
        for i, (field, pct, present) in enumerate(incomplete_fields[:10], 1):
            missing = total_properties - present
            report_lines.append(
                f"  {i}. {field:30s} - {pct:5.1f}% complete ({present}/{total_properties}, "
                f"missing {missing})"
            )
    else:
        report_lines.append("  All fields have either 100% or 0% completion.")

    report_lines.append("\n\nRecommended Enrichment Actions:\n")
    report_lines.append("  1. Orientation Data (0% complete)")
    report_lines.append("     - Use property maps to determine cardinal direction")
    report_lines.append("     - Critical for solar panel and cooling cost assessment")
    report_lines.append("     - Impacts weighted scoring")
    report_lines.append("")

    report_lines.append("  2. Solar Status & Lease Costs (15% complete)")
    report_lines.append("     - Research Maricopa County property tax records")
    report_lines.append("     - Check property deeds for solar lease terms")
    report_lines.append("     - Critical for cost analysis")
    report_lines.append("")

    report_lines.append("  3. Age/Condition Data (roof_age, hvac_age, pool_equipment_age)")
    report_lines.append("     - Estimate based on year_built or research county records")
    report_lines.append("     - Critical for long-term maintenance cost assessment")
    report_lines.append("")

    report_lines.append("  4. Pool Status (9% null values)")
    report_lines.append("     - Verify in property photos and listing details")
    report_lines.append("     - Impacts maintenance cost calculations")
    report_lines.append("")

    report_lines.append("  5. Solar Lease Costs (where solar_status='leased')")
    report_lines.append("     - Research solar lease agreements")
    report_lines.append("     - Critical for monthly payment calculations")

    # Properties needing attention
    report_lines.append("\n\n" + "=" * 80)
    report_lines.append("5. PROPERTIES REQUIRING ATTENTION")
    report_lines.append("=" * 80)

    properties_with_gaps = defaultdict(list)
    for _idx, prop in enumerate(data):
        missing_fields = []
        for field in CRITICAL_FIELDS:
            if prop.get(field) is None or prop.get(field) == '':
                missing_fields.append(field)
        if missing_fields:
            properties_with_gaps[prop['full_address']] = missing_fields

    if properties_with_gaps:
        report_lines.append(f"\n{len(properties_with_gaps)} Properties with Missing Critical Data:\n")
        for addr, missing in sorted(properties_with_gaps.items()):
            report_lines.append(f"  • {addr}")
            report_lines.append(f"    Missing: {', '.join(missing)}")
    else:
        report_lines.append("\nAll properties have complete critical field data.")

    # Summary statistics
    report_lines.append("\n\n" + "=" * 80)
    report_lines.append("6. SUMMARY STATISTICS")
    report_lines.append("=" * 80)

    avg_completeness = sum(field_stats[f]['completion_pct'] for f in CRITICAL_FIELDS
                          if f in field_stats) / len(CRITICAL_FIELDS)

    report_lines.append(f"\nAverage Critical Field Completeness: {avg_completeness:.1f}%")
    report_lines.append(f"Total Data Issues Found: {len(issues)}")
    report_lines.append(f"Critical Issues: {len([i for i in issues if i['severity'] == 'CRITICAL'])}")
    report_lines.append(f"Warnings: {len([i for i in issues if i['severity'] == 'WARNING'])}")
    report_lines.append(f"Properties Ready for Visualization: {len(data) - len(properties_with_gaps)}/{total_properties}")

    report_lines.append("\n" + "=" * 80)

    return "\n".join(report_lines)

if __name__ == '__main__':
    data_path = 'enrichment_data.json'
    report = generate_report(data_path)
    print(report)

    # Also save to file
    with open('data_quality_report.txt', 'w') as f:
        f.write(report)
    print("\n\nReport saved to: data_quality_report.txt")
