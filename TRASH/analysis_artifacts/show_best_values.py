#!/usr/bin/env python3
"""Quick summary of best true value properties."""

import csv

# Load data
with open('renovation_gap_report.csv') as f:
    data = list(csv.DictReader(f))

# Filter to PASSING only
passing = [r for r in data if r['kill_switch_passed'] == 'PASS']

print(f"Total PASSING properties: {len(passing)}")
print("\nTop 10 PASSING properties by TRUE COST (move-in ready price):")
print("="*100)

sorted_passing = sorted(passing, key=lambda x: float(x['true_cost']))

for i, r in enumerate(sorted_passing[:10], 1):
    addr = r['address'][:50]
    true_cost = float(r['true_cost'])
    reno = float(r['total_renovation'])
    delta = float(r['price_delta_pct'])
    tier = r['tier']
    score = float(r['total_score'])

    print(f"{i:2d}. {addr:<50} | Tier: {tier:<10} | Score: {score:>5.1f}")
    print(f"    True Cost: ${true_cost:>10,.0f} | Renovation: ${reno:>6,.0f} (+{delta:>4.1f}%)")
    print()
