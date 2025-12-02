"""Main entry point for deal sheet generation.

Orchestrates:
- Data loading (CSV + JSON)
- Individual deal sheet generation
- Index page generation
- Summary statistics
"""

from pathlib import Path

from .data_loader import load_enrichment_json, load_ranked_csv, merge_enrichment_data
from .renderer import generate_deal_sheet, generate_index


def generate_deal_sheets(base_dir=None):
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

    print("Loading data...")
    # Load ranked homes CSV
    df = load_ranked_csv(ranked_csv)

    # Load enrichment data
    enrichment_data = load_enrichment_json(enrichment_json)

    # Merge enrichment data into dataframe
    df = merge_enrichment_data(df, enrichment_data)

    print(f"Generating deal sheets for {len(df)} properties...")

    # Generate individual deal sheets
    errors = []
    for idx, row in df.iterrows():
        try:
            filename = generate_deal_sheet(row, output_dir)
            print(f"  [{int(row['rank']):2d}/{len(df)}] Generated: {filename}")
        except Exception as e:
            errors.append((int(row['rank']), row.get('full_address', 'Unknown'), str(e)))
            print(f"  [{int(row['rank']):2d}/{len(df)}] ERROR: {e}")

    if errors:
        print(f"\n[WARN] {len(errors)} properties failed to generate:")

    # Generate index page
    print("\nGenerating index.html...")
    generate_index(df, output_dir)

    print(f"\n[OK] Complete! Generated {len(df)} deal sheets in: {output_dir}")
    print(f"[OK] Open {output_dir / 'index.html'} to view the master list")

    # Print sample stats
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    # Use kill_switch_status field from CSV
    ks_field = 'kill_switch_status' if 'kill_switch_status' in df.columns else 'kill_switch_passed'
    print(f"Total Properties:        {len(df)}")
    print(f"Passed Kill Switches:    {(df[ks_field] == 'PASS').sum()}")
    print(f"Failed Kill Switches:    {(df[ks_field] != 'PASS').sum()}")
    # Convert total_score to numeric (may have strings after merge)
    import pandas as pd
    df['total_score'] = pd.to_numeric(df['total_score'], errors='coerce')
    passed_avg = df[df[ks_field] == 'PASS']['total_score'].mean()
    all_avg = df['total_score'].mean()
    top_score = df['total_score'].max()
    print(f"Average Score (Passed):  {passed_avg:.1f}" if pd.notna(passed_avg) else "Average Score (Passed):  N/A")
    print(f"Average Score (All):     {all_avg:.1f}" if pd.notna(all_avg) else "Average Score (All):     N/A")
    print(f"Top Score:               {top_score:.1f} (Rank #{int(df['rank'].min())})" if pd.notna(top_score) else "Top Score:               N/A")

    # Show top 3
    print("\n" + "="*60)
    print("TOP 3 PROPERTIES")
    print("="*60)
    for idx, row in df.head(3).iterrows():
        status = "PASS" if row[ks_field] == 'PASS' else "FAIL"
        print(f"\n#{int(row['rank'])}: {row['full_address']}")
        print(f"  Score: {row['total_score']}/600 | Status: {status}")
        # Get price from price_num if price not available
        price = row.get('price_num', row.get('price', 0))
        # Convert price to numeric if it's a string (e.g., "$354,000")
        if isinstance(price, str):
            price = float(price.replace('$', '').replace(',', '')) if price else 0
        city = row.get('city', row['full_address'].split(',')[1].strip() if ',' in row['full_address'] else 'Unknown')
        print(f"  Price: ${price:,.0f} | {city}")

    return output_dir


def main():
    """Main execution function."""
    generate_deal_sheets()


if __name__ == '__main__':
    main()
