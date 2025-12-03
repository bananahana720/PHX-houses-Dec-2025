#!/usr/bin/env python3
"""Auto-refresh development server for PHX Home Analysis reports.

Usage:
    python scripts/serve_reports.py              # Start server with auto-refresh
    python scripts/serve_reports.py --no-regen   # Serve only, no regeneration
    python scripts/serve_reports.py --port 9000  # Custom port
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path

from livereload import Server

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_PAGE = "html/report_hub.html"


def regenerate_deal_sheets() -> None:
    """Regenerate deal sheets only."""
    print("[LiveReload] Regenerating deal sheets...")
    subprocess.run([sys.executable, "-m", "scripts.deal_sheets"], cwd=PROJECT_ROOT)


def regenerate_visualizations() -> None:
    """Regenerate all visualizations."""
    print("[LiveReload] Regenerating visualizations...")
    subprocess.run(
        [sys.executable, "scripts/generate_all_visualizations.py"],
        cwd=PROJECT_ROOT,
    )


def regenerate_all() -> None:
    """Regenerate everything."""
    regenerate_deal_sheets()
    regenerate_visualizations()


def main() -> None:
    """Start the LiveReload development server."""
    parser = argparse.ArgumentParser(description="PHX Reports LiveReload Server")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--no-regen", action="store_true", help="Disable auto-regeneration")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open browser")
    args = parser.parse_args()

    server = Server()

    if not args.no_regen:
        # Watch data files only → regenerate all reports
        server.watch(str(PROJECT_ROOT / "data/phx_homes_ranked.csv"), regenerate_all)
        server.watch(str(PROJECT_ROOT / "data/enrichment_data.json"), regenerate_all)

    # Always watch report outputs for browser refresh
    server.watch(str(PROJECT_ROOT / "reports/deal_sheets/*.html"))
    server.watch(str(PROJECT_ROOT / "reports/deal_sheets/*.json"))
    server.watch(str(PROJECT_ROOT / "reports/html/*.html"))

    print(f"Starting LiveReload server on http://localhost:{args.port}")
    print("Reports will auto-refresh when data files change.")
    print("\nQuick links:")
    print(f"  - Report Hub:    http://localhost:{args.port}/html/report_hub.html")
    print(f"  - Deal Sheets:   http://localhost:{args.port}/deal_sheets/")
    print(f"  - Value Spotter: http://localhost:{args.port}/html/value_spotter.html")

    # Open browser to Report Hub by default
    if not args.no_open:
        webbrowser.open(f"http://localhost:{args.port}/{DEFAULT_PAGE}")

    server.serve(
        root=str(PROJECT_ROOT / "reports"),
        port=args.port,
        host="localhost",
        open_url_delay=None,  # We handle browser opening manually above
    )


if __name__ == "__main__":
    main()
