#!/usr/bin/env python3
"""
Generate All Visualizations Runner

Generates all property analysis visualizations in parallel:
- Golden Zone Map (existing)
- Flood Zone Map (new)
- Crime Heatmap (new)
- Value Spotter Chart (existing)
- Radar Comparison Chart (existing)

Usage:
    python scripts/generate_all_visualizations.py
    python scripts/generate_all_visualizations.py --skip golden,value
"""

import argparse
import concurrent.futures
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

VISUALIZATIONS = {
    "golden": {
        "name": "Golden Zone Map",
        "script": "scripts/golden_zone_map.py",
        "output": "reports/html/golden_zone_map.html",
    },
    "map": {
        "name": "Interactive Property Map",
        "script": "scripts/generate_map.py",
        "output": "reports/html/golden_zone_map.html",
    },
    "flood": {
        "name": "Flood Zone Map",
        "script": "scripts/generate_flood_map.py",
        "output": "reports/html/flood_zone_map.html",
    },
    "crime": {
        "name": "Crime Heatmap",
        "script": "scripts/generate_crime_heatmap.py",
        "output": "reports/html/crime_heatmap.html",
    },
    "value": {
        "name": "Value Spotter Chart",
        "script": "scripts/value_spotter.py",
        "output": "reports/html/value_spotter.html",
    },
    "radar": {
        "name": "Radar Comparison Chart",
        "script": "scripts/radar_charts.py",
        "output": "reports/html/radar_comparison.html",
    },
}


def run_visualization(key: str, config: dict, project_root: Path) -> tuple[str, bool, str]:
    """Run a single visualization script.

    Returns:
        Tuple of (key, success, message) for thread-safe result collection
    """
    script_path = project_root / config["script"]

    if not script_path.exists():
        return (key, False, f"Script not found: {script_path}")

    try:
        logger.info("[%s] Starting: %s...", key, config['name'])
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            output_path = project_root / config["output"]
            if output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                msg = f"Generated: {config['output']} ({size_kb:.1f} KB)"
            else:
                msg = "Completed (output location may vary)"
            return (key, True, msg)
        else:
            error_msg = result.stderr[:200] if result.stderr else "Unknown error"
            return (key, False, f"Exit code {result.returncode}: {error_msg}")

    except subprocess.TimeoutExpired:
        return (key, False, "Timed out after 120 seconds")
    except Exception as e:
        return (key, False, str(e))


def main():
    from phx_home_analysis.logging_config import setup_logging
    setup_logging()

    parser = argparse.ArgumentParser(description="Generate all property visualizations")
    parser.add_argument(
        "--skip",
        help="Comma-separated list of visualizations to skip (e.g., 'golden,value')",
        default="",
    )
    parser.add_argument(
        "--only",
        help="Comma-separated list of visualizations to run (e.g., 'flood,crime')",
        default="",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run visualizations sequentially instead of in parallel",
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    # Determine which visualizations to run
    skip_list = set(args.skip.lower().split(",")) if args.skip else set()
    only_list = set(args.only.lower().split(",")) if args.only else set()

    to_run = []
    for key in VISUALIZATIONS.keys():
        if skip_list and key in skip_list:
            continue
        if only_list and key not in only_list:
            continue
        to_run.append(key)

    if not to_run:
        logger.warning("No visualizations selected to run.")
        return 1

    mode = "sequentially" if args.sequential else "in parallel (4 workers)"
    logger.info("Generating %d visualizations %s...", len(to_run), mode)

    results = {}

    if args.sequential:
        # Sequential execution (original behavior)
        for key in to_run:
            config = VISUALIZATIONS[key]
            _, success, msg = run_visualization(key, config, project_root)
            results[key] = success
            if success:
                logger.info("[%s] %s", key, msg)
            else:
                logger.error("[%s] FAILED - %s", key, msg)
    else:
        # Parallel execution with ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(run_visualization, key, VISUALIZATIONS[key], project_root): key
                for key in to_run
            }

            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                try:
                    _, success, msg = future.result()
                    results[key] = success
                    if success:
                        logger.info("[%s] %s", key, msg)
                    else:
                        logger.error("[%s] FAILED - %s", key, msg)
                except Exception as e:
                    results[key] = False
                    logger.error("[%s] FAILED - %s", key, e)

    # Summary
    successes = sum(1 for s in results.values() if s)
    failures = len(results) - successes

    logger.info("=" * 60)
    logger.info("Summary: %d/%d visualizations generated successfully", successes, len(results))

    if failures > 0:
        logger.warning("Failed visualizations:")
        for key, success in results.items():
            if not success:
                logger.warning("  - %s (%s)", VISUALIZATIONS[key]['name'], key)

    logger.info("Output directory: reports/html/")
    logger.info("=" * 60)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    exit(main())
