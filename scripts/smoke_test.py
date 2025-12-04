#!/usr/bin/env python
"""Pre-flight smoke test for external API connectivity.

Validates environment configuration and API reachability before
running the full property analysis pipeline.

Usage:
    python scripts/smoke_test.py           # Run all checks
    python scripts/smoke_test.py --quick   # Skip slow APIs
    python scripts/smoke_test.py --json    # Output as JSON
    python scripts/smoke_test.py --api county  # Run specific API check

Exit codes:
    0 - All critical checks passed
    1 - One or more critical checks failed
    2 - Configuration error (missing required env vars)

Environment Variables:
    MARICOPA_ASSESSOR_TOKEN - Required for County Assessor API
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class CheckStatus(Enum):
    """Status of a connectivity check."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    """Result of a single connectivity check.

    Attributes:
        name: Human-readable check name
        status: CheckStatus enum (pass, fail, skip)
        latency_ms: Response time in milliseconds (None if not measured)
        message: Status message for display
        critical: If True, failure blocks pipeline execution
    """

    name: str
    status: str  # "pass", "fail", "skip"
    latency_ms: float | None
    message: str
    critical: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


async def check_env_vars() -> CheckResult:
    """Check required environment variables are present.

    Returns:
        CheckResult with status and message about missing variables.
    """
    required_vars = ["MARICOPA_ASSESSOR_TOKEN"]

    missing_required = [v for v in required_vars if not os.getenv(v)]

    if missing_required:
        return CheckResult(
            name="Environment Variables",
            status="fail",
            latency_ms=None,
            message=f"Missing required: {', '.join(missing_required)}",
            critical=True,
        )

    return CheckResult(
        name="Environment Variables",
        status="pass",
        latency_ms=None,
        message="All required variables present",
        critical=True,
    )


async def check_county_assessor() -> CheckResult:
    """Check Maricopa County Assessor API connectivity.

    Makes a real API call with a known test address to verify
    authentication and basic functionality.

    Returns:
        CheckResult with API status and latency.
    """
    start = time.time()
    try:
        from phx_home_analysis.services.county_data import MaricopaAssessorClient

        token = os.getenv("MARICOPA_ASSESSOR_TOKEN")
        if not token:
            return CheckResult(
                name="County Assessor",
                status="skip",
                latency_ms=None,
                message="MARICOPA_ASSESSOR_TOKEN not set",
                critical=True,
            )

        async with MaricopaAssessorClient(
            token=token,
            rate_limit_seconds=0.1,
            timeout=10.0,
        ) as client:
            # Test with a known address
            parcel = await client.extract_for_address("4732 W Davis Rd")
            latency = (time.time() - start) * 1000

            if parcel and parcel.apn:
                return CheckResult(
                    name="County Assessor",
                    status="pass",
                    latency_ms=round(latency, 1),
                    message=f"OK (APN: {parcel.apn})",
                    critical=True,
                )
            else:
                return CheckResult(
                    name="County Assessor",
                    status="fail",
                    latency_ms=round(latency, 1),
                    message="API responded but no parcel data returned",
                    critical=True,
                )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return CheckResult(
            name="County Assessor",
            status="fail",
            latency_ms=round(latency, 1),
            message=str(e)[:100],  # Truncate long errors
            critical=True,
        )


async def check_arcgis_public() -> CheckResult:
    """Check ArcGIS public API (fallback) connectivity.

    Tests the no-auth fallback endpoint used when official API
    token is not available.

    Returns:
        CheckResult with API status and latency.
    """
    start = time.time()
    try:
        import httpx

        # Test ArcGIS REST API endpoint
        url = (
            "https://gis.mcassessor.maricopa.gov/arcgis/rest/services/"
            "MaricopaDynamicQueryService/MapServer"
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{url}?f=json")
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return CheckResult(
                    name="ArcGIS (Fallback)",
                    status="pass",
                    latency_ms=round(latency, 1),
                    message="OK",
                    critical=False,
                )
            else:
                return CheckResult(
                    name="ArcGIS (Fallback)",
                    status="fail",
                    latency_ms=round(latency, 1),
                    message=f"HTTP {response.status_code}",
                    critical=False,
                )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return CheckResult(
            name="ArcGIS (Fallback)",
            status="fail",
            latency_ms=round(latency, 1),
            message=str(e)[:100],
            critical=False,
        )


async def check_data_files() -> CheckResult:
    """Check required data files exist and are readable.

    Verifies:
    - enrichment_data.json exists
    - File is readable and valid JSON

    Returns:
        CheckResult with file status.
    """
    start = time.time()
    try:
        data_file = Path(__file__).parent.parent / "data" / "enrichment_data.json"

        if not data_file.exists():
            return CheckResult(
                name="Data Files",
                status="fail",
                latency_ms=None,
                message=f"enrichment_data.json not found at {data_file}",
                critical=True,
            )

        # Try to load JSON to verify it's valid
        with open(data_file, encoding="utf-8") as f:
            data = json.load(f)

        latency = (time.time() - start) * 1000

        # Check if data is reasonable
        if isinstance(data, list) and len(data) > 0:
            return CheckResult(
                name="Data Files",
                status="pass",
                latency_ms=round(latency, 1),
                message=f"enrichment_data.json exists ({len(data)} properties)",
                critical=True,
            )
        else:
            return CheckResult(
                name="Data Files",
                status="fail",
                latency_ms=round(latency, 1),
                message="enrichment_data.json is empty or invalid format",
                critical=True,
            )

    except json.JSONDecodeError as e:
        return CheckResult(
            name="Data Files",
            status="fail",
            latency_ms=None,
            message=f"enrichment_data.json is invalid JSON: {e}",
            critical=True,
        )
    except Exception as e:
        return CheckResult(
            name="Data Files",
            status="fail",
            latency_ms=None,
            message=str(e)[:100],
            critical=True,
        )


async def check_cache_directory() -> CheckResult:
    """Check API cache directory is writable.

    Verifies:
    - data/api_cache/ directory exists or can be created
    - Directory is writable

    Returns:
        CheckResult with cache directory status.
    """
    start = time.time()
    try:
        cache_dir = Path(__file__).parent.parent / "data" / "api_cache"

        # Try to create directory if it doesn't exist
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Try to write a test file
        test_file = cache_dir / ".smoke_test_write_check"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()  # Clean up

        latency = (time.time() - start) * 1000

        return CheckResult(
            name="Cache Directory",
            status="pass",
            latency_ms=round(latency, 1),
            message=f"Writable at {cache_dir}",
            critical=False,
        )

    except Exception as e:
        latency = (time.time() - start) * 1000
        return CheckResult(
            name="Cache Directory",
            status="fail",
            latency_ms=round(latency, 1),
            message=str(e)[:100],
            critical=False,
        )


async def run_all_checks(
    quick: bool = False,
    api_filter: str | None = None,
    timeout: float = 10.0,
) -> list[CheckResult]:
    """Run all smoke test checks in parallel.

    Args:
        quick: If True, skip slow API checks.
        api_filter: If provided, run only checks matching this API name.
        timeout: Per-check timeout in seconds.

    Returns:
        List of CheckResult objects.
    """
    # Build list of checks to run based on options
    checks = []

    # Always run env and data checks
    checks.append(check_env_vars())
    checks.append(check_data_files())
    checks.append(check_cache_directory())

    # Apply API filter if specified, otherwise respect quick mode
    if api_filter:
        filter_lower = api_filter.lower()
        if "county" in filter_lower:
            checks.append(check_county_assessor())
        if "arcgis" in filter_lower:
            checks.append(check_arcgis_public())
    elif not quick:
        # Run slow API checks if not in quick mode
        checks.append(check_county_assessor())
        checks.append(check_arcgis_public())

    # Execute checks in parallel with timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*checks, return_exceptions=True),
            timeout=timeout * len(checks),
        )

        # Convert exceptions to CheckResult
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    CheckResult(
                        name=f"Check {i + 1}",
                        status="fail",
                        latency_ms=None,
                        message=f"Exception: {str(result)[:100]}",
                        critical=True,
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    except asyncio.TimeoutError:
        return [
            CheckResult(
                name="Timeout",
                status="fail",
                latency_ms=None,
                message="Smoke test timed out",
                critical=True,
            )
        ]


def print_results_human(results: list[CheckResult], duration_ms: float) -> None:
    """Print results in human-readable format.

    Args:
        results: List of check results.
        duration_ms: Total duration in milliseconds.
    """
    print()
    print("=" * 60)
    print("PHX Houses Smoke Test Results")
    print("=" * 60)
    print()

    for r in results:
        icon = {
            "pass": "[OK]  ",
            "fail": "[FAIL]",
            "skip": "[SKIP]",
        }.get(r.status, "[????]")

        latency = f"{r.latency_ms:.0f}ms" if r.latency_ms else "N/A"
        critical = "(CRITICAL)" if r.critical else ""

        print(f"{icon} {r.name}: {r.message} [{latency}] {critical}")

    print()
    print("=" * 60)

    # Summary
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    skipped = sum(1 for r in results if r.status == "skip")

    overall = "PASS" if failed == 0 else "FAIL"
    print(f"Result: {overall} ({passed}/{len(results)} checks passed, {skipped} skipped)")
    print(f"Duration: {duration_ms:.0f}ms")
    print("=" * 60)


def print_results_json(results: list[CheckResult], duration_ms: float) -> None:
    """Print results in JSON format.

    Args:
        results: List of check results.
        duration_ms: Total duration in milliseconds.
    """
    from datetime import datetime, timezone

    output = {
        "status": "pass" if all(r.status != "fail" for r in results) else "fail",
        "checks": [r.to_dict() for r in results],
        "duration_ms": round(duration_ms, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(output, indent=2))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Pre-flight smoke test for external API connectivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip slow API connectivity checks",
    )
    parser.add_argument(
        "--api",
        type=str,
        metavar="NAME",
        help="Run only specific API check (county, arcgis)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        metavar="SEC",
        help="Per-check timeout in seconds (default: 10)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code: 0 (success), 1 (critical failure), 2 (config error)
    """
    args = parse_args()

    start_time = time.time()

    try:
        results = asyncio.run(
            run_all_checks(
                quick=args.quick,
                api_filter=args.api,
                timeout=args.timeout,
            )
        )

        duration_ms = (time.time() - start_time) * 1000

        # Print results
        if args.json:
            print_results_json(results, duration_ms)
        else:
            print_results_human(results, duration_ms)

        # Determine exit code
        critical_failures = [r for r in results if r.critical and r.status == "fail"]

        # Check for config errors (missing env vars)
        env_check = next((r for r in results if r.name == "Environment Variables"), None)
        if env_check and env_check.status == "fail":
            return 2  # Configuration error

        return 1 if critical_failures else 0

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
