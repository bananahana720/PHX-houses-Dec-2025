#!/usr/bin/env python3
"""Analyze renovation cost components across all properties."""

import csv
from collections import Counter

# Load data
with open('renovation_gap_report.csv') as f:
    data = list(csv.DictReader(f))

# Filter to PASSING only
passing = [r for r in data if r['kill_switch_passed'] == 'PASS']

print("="*80)
print("RENOVATION COST BREAKDOWN ANALYSIS")
print("="*80)
print(f"\nAnalyzing {len(passing)} PASSING properties")

# Count properties by cost category
roof_counts = Counter()
hvac_counts = Counter()
pool_counts = Counter()
plumbing_counts = Counter()
kitchen_counts = Counter()

for r in passing:
    roof_counts[int(float(r['roof_cost']))] += 1
    hvac_counts[int(float(r['hvac_cost']))] += 1
    pool_counts[int(float(r['pool_cost']))] += 1
    plumbing_counts[int(float(r['plumbing_cost']))] += 1
    kitchen_counts[int(float(r['kitchen_cost']))] += 1

print("\n" + "-"*80)
print("ROOF REPLACEMENT COSTS")
print("-"*80)
for cost in sorted(roof_counts.keys()):
    count = roof_counts[cost]
    pct = (count / len(passing)) * 100
    label = {
        0: "No work needed (age < 10 years)",
        5000: "Minor repairs (age 10-15 years)",
        8000: "Unknown age (contingency)",
        10000: "Partial replacement (age 15-20 years)",
        18000: "Full replacement (age > 20 years)"
    }.get(cost, "Other")
    print(f"  ${cost:>6,}: {count:>2} properties ({pct:>4.1f}%) - {label}")

print("\n" + "-"*80)
print("HVAC REPLACEMENT COSTS (Arizona: 12-15 year lifespan)")
print("-"*80)
for cost in sorted(hvac_counts.keys()):
    count = hvac_counts[cost]
    pct = (count / len(passing)) * 100
    label = {
        0: "No work needed (age < 8 years)",
        3000: "Potential repairs (age 8-12 years)",
        4000: "Unknown age (contingency)",
        8000: "Replacement needed (age > 12 years)"
    }.get(cost, "Other")
    print(f"  ${cost:>6,}: {count:>2} properties ({pct:>4.1f}%) - {label}")

print("\n" + "-"*80)
print("POOL EQUIPMENT COSTS")
print("-"*80)
for cost in sorted(pool_counts.keys()):
    count = pool_counts[cost]
    pct = (count / len(passing)) * 100
    label = {
        0: "No pool",
        3000: "Pump/filter replacement (age 5-10 years)",
        5000: "Unknown age (contingency)",
        8000: "Full equipment overhaul (age > 10 years)"
    }.get(cost, "Other")
    print(f"  ${cost:>6,}: {count:>2} properties ({pct:>4.1f}%) - {label}")

print("\n" + "-"*80)
print("PLUMBING/ELECTRICAL COSTS (by build year)")
print("-"*80)
for cost in sorted(plumbing_counts.keys()):
    count = plumbing_counts[cost]
    pct = (count / len(passing)) * 100
    label = {
        0: "Modern (built 2000+)",
        2000: "Potential updates (built 1990-1999)",
        5000: "Inspection needed (built 1980-1989)",
        10000: "Galvanized pipes/old wiring (built < 1980)"
    }.get(cost, "Other")
    print(f"  ${cost:>6,}: {count:>2} properties ({pct:>4.1f}%) - {label}")

print("\n" + "-"*80)
print("KITCHEN UPDATE COSTS (older homes with neutral scores)")
print("-"*80)
for cost in sorted(kitchen_counts.keys()):
    count = kitchen_counts[cost]
    pct = (count / len(passing)) * 100
    label = {
        0: "No update needed (modern or already updated)",
        15000: "Full update needed (built < 1990, neutral score)"
    }.get(cost, "Other")
    print(f"  ${cost:>6,}: {count:>2} properties ({pct:>4.1f}%) - {label}")

# Average costs
avg_costs = {
    'Roof': sum(float(r['roof_cost']) for r in passing) / len(passing),
    'HVAC': sum(float(r['hvac_cost']) for r in passing) / len(passing),
    'Pool': sum(float(r['pool_cost']) for r in passing) / len(passing),
    'Plumbing': sum(float(r['plumbing_cost']) for r in passing) / len(passing),
    'Kitchen': sum(float(r['kitchen_cost']) for r in passing) / len(passing),
}

print("\n" + "="*80)
print("AVERAGE COSTS PER COMPONENT (PASSING properties only)")
print("="*80)
for component, avg in sorted(avg_costs.items(), key=lambda x: x[1], reverse=True):
    print(f"  {component:<12}: ${avg:>8,.0f}")

total_avg = sum(avg_costs.values())
print(f"\n  {'TOTAL AVG':<12}: ${total_avg:>8,.0f}")
print("="*80)
