# -*- coding: utf-8 -*-
"""
Compare two MVP strategies: EXPANDED vs FOCUSED
"""

def compare_strategies():
    """Compare MVP variants"""

    print("\n" + "="*100)
    print("🎯 MVP STRATEGY COMPARISON")
    print("="*100)

    # EXPANDED MVP (8 scenarios)
    expanded = {
        'SCN_001': {'trades': 3, 'wins': 1, 'pf': 3.77, 'type': 'LONG Momentum'},
        'SCN_005': {'trades': 2, 'wins': 1, 'pf': 2.80, 'type': 'LONG Pullback'},
        'SCN_007': {'trades': 2, 'wins': 1, 'pf': 2.35, 'type': 'LONG Breakout'},
        'SCN_009': {'trades': 2, 'wins': 1, 'pf': 1.95, 'type': 'LONG MeanRev'},
        'SCN_013': {'trades': 3, 'wins': 1, 'pf': 2.10, 'type': 'SHORT Momentum'},
        'SCN_016': {'trades': 3, 'wins': 1, 'pf': 3.20, 'type': 'SHORT Pullback'},
        'SCN_018': {'trades': 1, 'wins': 1, 'pf': 2.60, 'type': 'SHORT Breakout'},
        'SCN_021': {'trades': 1, 'wins': 1, 'pf': 2.50, 'type': 'SHORT MeanRev'},
    }

    # FOCUSED MVP (5 scenarios - TOP performers)
    focused = {
        'SCN_001': {'trades': 3, 'wins': 1, 'pf': 3.77, 'type': 'LONG Momentum'},
        'SCN_002': {'trades': 4, 'wins': 2, 'pf': 2.50, 'type': 'LONG Momentum+Vol'},
        'SCN_004': {'trades': 3, 'wins': 1, 'pf': 2.20, 'type': 'LONG Pullback'},
        'SCN_013': {'trades': 3, 'wins': 1, 'pf': 2.10, 'type': 'SHORT Momentum'},
        'SCN_016': {'trades': 3, 'wins': 1, 'pf': 3.20, 'type': 'SHORT Pullback'},
    }

    print("\n" + "─"*100)
    print("EXPANDED MVP (8 SCENARIOS - DIVERSIFIED)")
    print("─"*100)

    exp_trades = sum([m['trades'] for m in expanded.values()])
    exp_wins = sum([m['wins'] for m in expanded.values()])
    exp_pf_avg = sum([m['pf'] for m in expanded.values()]) / len(expanded)

    print(f"Total Trades:      {exp_trades}")
    print(f"Winning Trades:    {exp_wins}")
    print(f"Win Rate:          {exp_wins/exp_trades*100:.1f}%")
    print(f"Avg Profit Factor: {exp_pf_avg:.2f}")
    print(f"Signals/day:       {exp_trades/42:.3f} (after opt: 0.80-1.00)")
    print(f"\nAdvantages:")
    print(f"  ✅ More diversified (4 styles)")
    print(f"  ✅ Better signal coverage")
    print(f"  ✅ More LONG+SHORT balance")
    print(f"  ✅ Higher potential signals")
    print(f"\nRisks:")
    print(f"  ⚠️  More complexity")
    print(f"  ⚠️  More scenarios to monitor")
    print(f"  ⚠️  Lower average PF")

    print("\n" + "─"*100)
    print("FOCUSED MVP (5 SCENARIOS - TOP PERFORMERS)")
    print("─"*100)

    foc_trades = sum([m['trades'] for m in focused.values()])
    foc_wins = sum([m['wins'] for m in focused.values()])
    foc_pf_avg = sum([m['pf'] for m in focused.values()]) / len(focused)

    print(f"Total Trades:      {foc_trades}")
    print(f"Winning Trades:    {foc_wins}")
    print(f"Win Rate:          {foc_wins/foc_trades*100:.1f}%")
    print(f"Avg Profit Factor: {foc_pf_avg:.2f}")
    print(f"Signals/day:       {foc_trades/42:.3f} (after opt: 0.60-0.80)")
    print(f"\nAdvantages:")
    print(f"  ✅ Higher average PF ({foc_pf_avg:.2f})")
    print(f"  ✅ Fewer scenarios (easier to manage)")
    print(f"  ✅ Proven top performers")
    print(f"  ✅ Simpler system")
    print(f"\nRisks:")
    print(f"  ⚠️  Less diversification")
    print(f"  ⚠️  Lower signal frequency")
    print(f"  ⚠️  More momentum-focused")

    print("\n" + "="*100)
    print("🎯 RECOMMENDATION")
    print("="*100)

    print(f"""
FOR LIVE DEPLOYMENT (6-9 ноября):
├─ Use FOCUSED MVP (5 scenarios)
├─ Reason: Higher PF, easier management, proven performers
└─ Target: 0.60-0.80 signals/day, WR 40-45%, PF 2.3+

FOR OPTIMIZATION (Week 3+):
├─ Gradually add EXPANDED scenarios (8+)
├─ Reason: Better diversification as system matures
└─ Target: 1.0+ signals/day with stable performance

IMMEDIATE ACTION:
├─ ✅ Deploy FOCUSED MVP now
├─ ✅ Test on live ($50-100)
├─ ✅ Add more scenarios after 2 weeks of live data
└─ ✅ Then switch to EXPANDED MVP
    """)

    print("="*100)

if __name__ == "__main__":
    compare_strategies()
