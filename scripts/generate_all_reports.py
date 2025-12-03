#!/usr/bin/env python3
"""
Generate All HTML Reports - Master Script
PHX Home Buying Analysis - Dec 2025

Generates all 5 HTML reports from current analysis data:
1. golden_zone_map.html - Geographic map with property locations
2. radar_comparison.html - Radar charts comparing top properties
3. value_spotter.html - Price vs score scatter plot
4. risk_report.html - Risk assessment for all properties
5. renovation_gap_report.html - Renovation cost analysis

Usage:
    python scripts/generate_all_reports.py
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Report generation scripts
REPORT_SCRIPTS = {
    'golden_zone_map': PROJECT_ROOT / 'scripts' / 'golden_zone_map.py',
    'radar_comparison': PROJECT_ROOT / 'scripts' / 'radar_charts.py',
    'value_spotter': PROJECT_ROOT / 'scripts' / 'value_spotter.py',
    'risk_report': PROJECT_ROOT / 'scripts' / 'risk_report.py',
    'renovation_gap_report': PROJECT_ROOT / 'scripts' / 'renovation_gap.py',
}

# Expected output files
OUTPUT_FILES = {
    'golden_zone_map': PROJECT_ROOT / 'reports' / 'html' / 'golden_zone_map.html',
    'radar_comparison': PROJECT_ROOT / 'reports' / 'html' / 'radar_comparison.html',
    'value_spotter': PROJECT_ROOT / 'reports' / 'html' / 'value_spotter.html',
    'risk_report': PROJECT_ROOT / 'reports' / 'html' / 'risk_report.html',
    'renovation_gap_report': PROJECT_ROOT / 'reports' / 'html' / 'renovation_gap_report.html',
}


def print_header():
    """Print script header with timestamp."""
    print("=" * 80)
    print("GENERATE ALL REPORTS - PHX HOME BUYING ANALYSIS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Root: {PROJECT_ROOT}")
    print()


def check_prerequisites():
    """Check if required data files exist."""
    print("Checking prerequisites...")

    required_files = [
        PROJECT_ROOT / 'data' / 'phx_homes_ranked.csv',
        PROJECT_ROOT / 'data' / 'enrichment_data.json',
        PROJECT_ROOT / 'data' / 'phx_homes.csv',
    ]

    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"  [OK] {file_path.name}")
        else:
            print(f"  [MISSING] {file_path.name}")
            all_exist = False

    print()
    return all_exist


def run_script(script_name, script_path):
    """Run a single report generation script."""
    print(f"Running {script_name}...")
    print(f"  Script: {script_path}")

    try:
        # Change to project root directory before running
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode == 0:
            print(f"  [SUCCESS] {script_name} completed successfully")
            return True
        else:
            print(f"  [FAILED] {script_name}")
            print(f"  Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {script_name} (exceeded 2 minutes)")
        return False
    except Exception as e:
        print(f"  [ERROR] {script_name}: {e}")
        return False


def verify_outputs():
    """Verify that all output files were created."""
    print("\nVerifying output files...")

    all_exist = True
    for _report_name, output_path in OUTPUT_FILES.items():
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"  [OK] {output_path.name} ({size:,} bytes)")
        else:
            print(f"  [MISSING] {output_path.name} - NOT CREATED!")
            all_exist = False

    print()
    return all_exist


def print_summary(results):
    """Print summary of report generation results."""
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful = sum(1 for success in results.values() if success)
    total = len(results)

    print(f"\nReports Generated: {successful}/{total}")
    print()

    for report_name, success in results.items():
        status = "[SUCCESS]" if success else "[FAILED]"
        print(f"  {status}: {report_name}")

    print()

    if successful == total:
        print("All reports generated successfully!")
        print(f"\nView reports in: {PROJECT_ROOT / 'reports' / 'html'}")
        return True
    else:
        print(f"WARNING: {total - successful} report(s) failed to generate.")
        return False


def main():
    """Main execution function."""
    print_header()

    # Check prerequisites
    if not check_prerequisites():
        print("ERROR: Missing required data files. Run analysis pipeline first.")
        return 1

    # Ensure output directory exists
    output_dir = PROJECT_ROOT / 'reports' / 'html'
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}\n")

    # Run each report generation script
    results = {}
    for report_name, script_path in REPORT_SCRIPTS.items():
        if not script_path.exists():
            print(f"WARNING: Script not found: {script_path}")
            results[report_name] = False
            continue

        results[report_name] = run_script(report_name, script_path)
        print()

    # Verify outputs
    verify_outputs()

    # Print summary
    success = print_summary(results)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
