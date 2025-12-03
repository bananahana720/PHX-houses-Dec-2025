"""
Sun Orientation Analysis for Phoenix Homes

Analyzes cooling cost impact based on property sun orientation in Arizona.
Generates mock orientation data from street addresses and creates visualizations.
"""

import json
import random
import re
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

# Orientation Lookup Table - Annual Cooling Cost Impact
COOLING_COST_IMPACT = {
    'N': 0,          # Best - baseline, minimal direct sun
    'NE': 100,       # Northeast - morning sun, cooler afternoons
    'E': 200,        # East - morning sun exposure
    'SE': 400,       # Southeast - moderate afternoon sun
    'S': 300,        # South - moderate cooling costs
    'SW': 400,       # Southwest - afternoon sun
    'W': 600,        # West - worst, high afternoon sun costs
    'NW': 100,       # Northwest - minimal direct afternoon sun
    'Unknown': 250   # Default middle estimate
}

# Color mapping for visualization (green = best, red = worst)
ORIENTATION_COLORS = {
    'N': '#2ecc71',      # Green - best
    'NE': '#52be80',     # Light green
    'NW': '#52be80',     # Light green
    'E': '#f9e79f',      # Yellow
    'S': '#f5b041',      # Orange
    'SE': '#e74c3c',     # Red-orange
    'SW': '#e74c3c',     # Red-orange
    'W': '#c0392b',      # Red - worst
    'Unknown': '#95a5a6' # Gray
}


def estimate_orientation_from_address(address: str) -> str:
    """
    Estimate property orientation based on street address patterns.

    Phoenix streets follow a grid pattern:
    - "N ##th" or "N ##th Way" - runs North-South, so houses face East or West
    - "W Name" streets - runs East-West, so houses face North or South
    - "E Name" streets - runs East-West, so houses face North or South

    Returns: Direction string (N, NE, E, SE, S, SW, W, NW, or Unknown)
    """

    # Extract street portion from full address
    parts = address.split(',')
    if not parts:
        return 'Unknown'

    street = parts[0].strip().upper()

    # Pattern: "N/S/E/W followed by numbers and "Way/Ave/St/Dr/Ln/Cir/Ct"

    # Check for "N ##th Way/Ave/St" pattern (North-South running streets)
    # Houses on N-S streets typically face E or W
    ns_street_match = re.search(r'\b([NS])\s+\d+(?:st|nd|rd|th)?\s+(way|ave|st|blvd|dr|ln|ct)\b', street, re.IGNORECASE)
    if ns_street_match:
        ns_street_match.group(1).upper()
        ns_street_match.group(2).upper()

        # Randomly choose E or W for North-South streets
        # (Without property photos, we can't determine exact orientation)
        house_faces = random.choice(['E', 'W'])
        return house_faces

    # Check for "W/E Name" pattern (East-West running streets)
    # Houses on E-W streets typically face N or S
    ew_street_match = re.search(r'\b([EW])\s+([A-Za-z\s]+?)(?:\s+(?:way|ave|st|blvd|dr|ln|ct|cir))\b', street, re.IGNORECASE)
    if ew_street_match:
        ew_street_match.group(1).upper()

        # West streets - houses likely face North (better for AZ)
        # East streets - houses likely face North (better for AZ)
        # Randomly choose N or S with bias toward N (more desirable)
        house_faces = random.choice(['N', 'N', 'S'])  # 2/3 chance North
        return house_faces

    # Default fallback: return Unknown
    return 'Unknown'


def generate_orientation_estimates(enrichment_data: list[dict]) -> dict[str, str]:
    """
    Generate orientation estimates for all properties.

    Returns dict mapping full_address -> estimated orientation
    """
    orientations = {}

    for property_data in enrichment_data:
        address = property_data.get('full_address', '')

        # If orientation already exists in data, use it
        if property_data.get('orientation'):
            orientations[address] = property_data['orientation']
        else:
            # Estimate from address pattern
            estimated = estimate_orientation_from_address(address)
            orientations[address] = estimated

    return orientations


def load_enrichment_data(filepath: str) -> list[dict]:
    """Load enrichment data from JSON file."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filepath} not found")
        return []


def load_ranked_homes(filepath: str) -> pd.DataFrame:
    """Load ranked homes from CSV file."""
    return pd.read_csv(filepath)


def save_orientation_estimates(estimates: dict[str, str], output_path: str) -> None:
    """Save orientation estimates to JSON file."""
    output_data = [
        {
            'full_address': address,
            'estimated_orientation': orientation,
            'cooling_cost_impact': COOLING_COST_IMPACT.get(orientation, 250)
        }
        for address, orientation in estimates.items()
    ]

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved orientation estimates to {output_path}")


def create_orientation_impact_csv(
    estimates: dict[str, str],
    ranked_homes: pd.DataFrame,
    output_path: str
) -> None:
    """Create CSV with address, orientation, cooling cost impact, and score adjustment."""

    rows = []
    for address, orientation in estimates.items():
        cooling_cost = COOLING_COST_IMPACT.get(orientation, 250)

        # Find this address in ranked homes to get score
        matched_home = ranked_homes[ranked_homes['full_address'] == address]
        if not matched_home.empty:
            score = matched_home.iloc[0]['total_score']
            tier = matched_home.iloc[0]['tier']
        else:
            score = None
            tier = None

        rows.append({
            'address': address,
            'estimated_orientation': orientation,
            'cooling_cost_impact_annual': f'${cooling_cost}',
            'property_score': score,
            'tier': tier
        })

    df = pd.DataFrame(rows)
    df = df.sort_values('cooling_cost_impact_annual', key=lambda x: x.str.replace('$', '').astype(int))

    df.to_csv(output_path, index=False)
    print(f"Saved impact analysis to {output_path}")


def create_visualization(estimates: dict[str, str], output_path: str) -> None:
    """Create bar chart showing distribution of orientations."""

    # Count orientations
    orientation_counts = {}
    for orientation in estimates.values():
        orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1

    # Sort orientations in compass order
    compass_order = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'Unknown']
    orientations_sorted = [o for o in compass_order if o in orientation_counts]
    counts = [orientation_counts[o] for o in orientations_sorted]
    colors = [ORIENTATION_COLORS.get(o, '#95a5a6') for o in orientations_sorted]

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 7))

    # Create bars
    bars = ax.bar(orientations_sorted, counts, color=colors, edgecolor='black', linewidth=1.5)

    # Customize plot
    ax.set_xlabel('Orientation', fontsize=14, fontweight='bold')
    ax.set_ylabel('Number of Properties', fontsize=14, fontweight='bold')
    ax.set_title('Phoenix Home Orientations\n(Green=Best for Arizona, Red=Highest Cooling Costs)',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_ylim(0, max(counts) + 1 if counts else 5)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels on bars
    for bar, count in zip(bars, counts, strict=False):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}',
                ha='center', va='bottom', fontweight='bold', fontsize=11)

    # Add legend with cooling costs
    legend_elements = []
    for orientation in compass_order:
        if orientation in estimates.values():
            cost = COOLING_COST_IMPACT.get(orientation, 250)
            color = ORIENTATION_COLORS.get(orientation, '#95a5a6')
            label = f'{orientation}: +${cost}/year'
            legend_elements.append(
                mpatches.Patch(facecolor=color, edgecolor='black', label=label)
            )

    ax.legend(handles=legend_elements, loc='upper right', fontsize=10, title='Annual Cooling Cost Impact')

    # Tight layout and save
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved visualization to {output_path}")
    plt.close()


def print_summary_stats(estimates: dict[str, str]) -> None:
    """Print summary statistics of orientation distribution."""

    print("\n" + "="*70)
    print("SUN ORIENTATION ANALYSIS SUMMARY")
    print("="*70)

    # Count by orientation
    orientation_counts = {}
    total_cooling_costs = {}

    for orientation in estimates.values():
        orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1
        cost = COOLING_COST_IMPACT.get(orientation, 250)
        if orientation not in total_cooling_costs:
            total_cooling_costs[orientation] = 0
        total_cooling_costs[orientation] += cost

    # Print distribution
    print(f"\nOrientation Distribution ({len(estimates)} properties):")
    print("-" * 70)

    compass_order = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'Unknown']
    for orientation in compass_order:
        if orientation in orientation_counts:
            count = orientation_counts[orientation]
            cost = COOLING_COST_IMPACT.get(orientation, 250)
            percentage = (count / len(estimates)) * 100
            print(f"  {orientation:8s}: {count:2d} properties ({percentage:5.1f}%)  |  " +
                  f"Annual cooling cost impact: ${cost}/property")

    # Calculate totals
    total_cost = sum(COOLING_COST_IMPACT.get(o, 250) for o in estimates.values())
    avg_cost = total_cost / len(estimates)

    print("\n" + "-" * 70)
    print(f"Total Portfolio Cooling Cost Impact: ${total_cost:,}/year")
    print(f"Average per Property: ${avg_cost:.0f}/year")

    # Identify best and worst orientations
    best_oriented = [o for o in estimates.values() if o == 'N']
    worst_oriented = [o for o in estimates.values() if o == 'W']

    print(f"\nBest Oriented (North-facing): {len(best_oriented)} properties (${COOLING_COST_IMPACT['N']}/year each)")
    print(f"Worst Oriented (West-facing): {len(worst_oriented)} properties (${COOLING_COST_IMPACT['W']}/year each)")

    if worst_oriented and best_oriented:
        savings_potential = len(worst_oriented) * (COOLING_COST_IMPACT['W'] - COOLING_COST_IMPACT['N'])
        print(f"\nCooling Cost Savings if ALL W-facing homes were N-facing: ${savings_potential:,}/year")

    print("="*70 + "\n")


def main():
    """Main analysis pipeline."""

    # Setup paths
    project_dir = Path(__file__).parent
    enrichment_file = project_dir / 'enrichment_data.json'
    ranked_homes_file = project_dir / 'phx_homes_ranked.csv'
    orientation_estimates_file = project_dir / 'orientation_estimates.json'
    orientation_impact_file = project_dir / 'orientation_impact.csv'
    visualization_file = project_dir / 'sun_orientation.png'

    print("\nLoading data...")

    # Load data
    enrichment_data = load_enrichment_data(str(enrichment_file))
    ranked_homes = load_ranked_homes(str(ranked_homes_file))

    if not enrichment_data:
        print("Error: Could not load enrichment data")
        return

    print(f"Loaded {len(enrichment_data)} properties from enrichment data")
    print(f"Loaded {len(ranked_homes)} properties from ranked homes")

    # Generate orientation estimates
    print("\nGenerating orientation estimates from street addresses...")
    orientation_estimates = generate_orientation_estimates(enrichment_data)

    # Save estimates
    save_orientation_estimates(orientation_estimates, str(orientation_estimates_file))

    # Create impact CSV
    print("Creating orientation impact analysis...")
    create_orientation_impact_csv(orientation_estimates, ranked_homes, str(orientation_impact_file))

    # Create visualization
    print("Creating visualization...")
    create_visualization(orientation_estimates, str(visualization_file))

    # Print summary
    print_summary_stats(orientation_estimates)

    print("\nAnalysis complete!")
    print("\nOutput files created:")
    print(f"  - {orientation_estimates_file}")
    print(f"  - {orientation_impact_file}")
    print(f"  - {visualization_file}")


if __name__ == '__main__':
    main()
