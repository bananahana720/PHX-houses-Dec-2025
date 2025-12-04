"""Main entry point for deal sheet generation.

Orchestrates:
- Data loading (CSV + JSON)
- Individual deal sheet generation
- Index page generation
- Summary statistics
"""

from __future__ import annotations

import logging
from pathlib import Path

from .data_loader import load_enrichment_json, load_ranked_csv, merge_enrichment_data
from .renderer import generate_deal_sheet, generate_index

logger = logging.getLogger(__name__)


def generate_deal_sheets(base_dir: Path | None = None) -> Path:
    """Generate all deal sheets and index page.

    Args:
        base_dir: Base directory (defaults to project root, 2 levels up from this script)

    Returns:
        Path to generated output directory
    """
    # Get the project root directory (2 levels up: scripts/deal_sheets -> scripts -> project_root)
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent

    # Define paths
    ranked_csv = base_dir / 'data' / 'phx_homes_ranked.csv'
    enrichment_json = base_dir / 'data' / 'enrichment_data.json'
    output_dir = base_dir / 'reports' / 'deal_sheets'

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    logger.info("Loading data...")
    # Load ranked homes CSV
    df = load_ranked_csv(ranked_csv)

    # Load enrichment data
    enrichment_data = load_enrichment_json(enrichment_json)

    # Merge enrichment data into dataframe
    df = merge_enrichment_data(df, enrichment_data)

    logger.info("Generating deal sheets for %d properties...", len(df))

    # Generate individual deal sheets
    errors = []
    for _, row in df.iterrows():
        try:
            filename = generate_deal_sheet(row, output_dir)
            logger.info("  [%2d/%d] Generated: %s", int(row['rank']), len(df), filename)
        except Exception as e:
            errors.append((int(row.get('rank', 0)), row.get('full_address', 'Unknown'), str(e)))
            logger.error("  [%2d/%d] ERROR: %s", int(row.get('rank', 0)), len(df), e)

    if errors:
        logger.warning("%d properties failed to generate", len(errors))

    # Generate index page
    logger.info("Generating index.html...")
    generate_index(df, output_dir)

    logger.info("Complete! Generated %d deal sheets in: %s", len(df), output_dir)
    logger.info("Open %s to view the master list", output_dir / 'index.html')

    # Log sample stats
    logger.info("=" * 60)
    logger.info("SUMMARY STATISTICS")
    logger.info("=" * 60)

    # Use kill_switch_status field from CSV
    ks_field = 'kill_switch_status' if 'kill_switch_status' in df.columns else 'kill_switch_passed'
    logger.info("Total Properties:        %d", len(df))
    logger.info("Passed Kill Switches:    %d", (df[ks_field] == 'PASS').sum())
    logger.info("Failed Kill Switches:    %d", (df[ks_field] != 'PASS').sum())
    # Convert total_score to numeric (may have strings after merge)
    import pandas as pd
    df['total_score'] = pd.to_numeric(df['total_score'], errors='coerce')
    passed_avg = df[df[ks_field] == 'PASS']['total_score'].mean()
    all_avg = df['total_score'].mean()
    top_score = df['total_score'].max()
    if pd.notna(passed_avg):
        logger.info("Average Score (Passed):  %.1f", passed_avg)
    else:
        logger.info("Average Score (Passed):  N/A")
    if pd.notna(all_avg):
        logger.info("Average Score (All):     %.1f", all_avg)
    else:
        logger.info("Average Score (All):     N/A")
    if pd.notna(top_score):
        logger.info("Top Score:               %.1f (Rank #%d)", top_score, int(df['rank'].min()))
    else:
        logger.info("Top Score:               N/A")

    # Show top 3
    logger.info("=" * 60)
    logger.info("TOP 3 PROPERTIES")
    logger.info("=" * 60)
    for _, row in df.head(3).iterrows():
        status = "PASS" if row.get(ks_field) == 'PASS' else "FAIL"
        logger.info("#%d: %s", int(row['rank']), row['full_address'])
        logger.info("  Score: %s/605 | Status: %s", row['total_score'], status)
        # Get price from price_num if price not available
        price = row.get('price_num') or row.get('price', 0)
        # Convert price to numeric if it's a string (e.g., "$354,000")
        if isinstance(price, str):
            price = float(price.replace('$', '').replace(',', '')) if price else 0
        city = row.get('city') or (row['full_address'].split(',')[1].strip() if ',' in row['full_address'] else 'Unknown')
        logger.info(f"  Price: ${price:,.0f} | {city}")

    return output_dir


def main() -> None:
    """Main execution function."""
    from phx_home_analysis.logging_config import setup_logging
    setup_logging()
    generate_deal_sheets()


if __name__ == '__main__':
    main()
