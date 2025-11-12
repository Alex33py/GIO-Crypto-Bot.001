# -*- coding: utf-8 -*-
"""
Analyze individual scenario performance for MVP selection
"""

import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_scenarios_quick():
    """Quick analysis of current TOP-5"""

    print("\n" + "="*80)
    print("📊 QUICK SCENARIO ANALYSIS")
    print("="*80)

    # Load paper trading results (already have them!)
    paper_results = {
        'SCN_001': {'trades': 3, 'wins': 1, 'pf': 3.77, 'freq': 0.07},
        'SCN_002': {'trades': 4, 'wins': 2, 'pf': 2.50, 'freq': 0.09},
        'SCN_004': {'trades': 3, 'wins': 1, 'pf': 2.20, 'freq': 0.07},
        'SCN_013': {'trades': 3, 'wins': 1, 'pf': 2.10, 'freq': 0.07},
        'SCN_016': {'trades': 3, 'wins': 1, 'pf': 3.20, 'freq': 0.07},
    }

    print("\n🎯 CURRENT TOP-5 SCENARIOS:")
    print("─" * 80)
    print(f"{'Scenario':<12} {'Trades':<10} {'Win Rate':<15} {'PF':<10} {'Sig/Day':<12}")
    print("─" * 80)

    total_trades = 0
    total_wins = 0

    for scenario, metrics in paper_results.items():
        wr = metrics['wins'] / metrics['trades'] * 100 if metrics['trades'] > 0 else 0
        total_trades += metrics['trades']
        total_wins += metrics['wins']
        print(f"{scenario:<12} {metrics['trades']:<10} {wr:>6.1f}%{'':<8} {metrics['pf']:<10.2f} {metrics['freq']:<12.3f}")

    overall_wr = total_wins / total_trades * 100 if total_trades > 0 else 0
    overall_freq = sum([m['freq'] for m in paper_results.values()]) / len(paper_results)

    print("─" * 80)
    print(f"{'TOTAL':<12} {total_trades:<10} {overall_wr:>6.1f}%{'':<8} {0:<10} {overall_freq:<12.3f}")
    print("="*80)

    print("\n🎯 RECOMMENDATIONS FOR MVP:")
    print("─" * 80)
    print("✅ Keep: SCN_001, SCN_002, SCN_004 (all have PF > 2.0 and WR > 33%)")
    print("⚠️  Check: SCN_013, SCN_016 (low sample size, might be good)")
    print("\n✅ Next Step: Expand to TOP-10 scenarios")
    print("   └─ Test SCN_003, SCN_005, SCN_006, SCN_008, SCN_009, SCN_011")
    print("\n✅ MVP Ready When:")
    print("   ├─ 10-12 scenarios selected")
    print("   ├─ Combined signals/day: 0.70-1.00")
    print("   ├─ Portfolio WR: 38-42%")
    print("   └─ Portfolio PF: 2.2+")
    print("="*80)

if __name__ == "__main__":
    analyze_scenarios_quick()
