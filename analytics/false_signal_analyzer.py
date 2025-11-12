"""
False Signal Analyzer
Анализатор ложных сигналов для детального разбора проигрышных сделок
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class FalseSignalAnalyzer:
    """
    Анализатор ложных сигналов из backtest результатов
    """

    def __init__(self, trades_csv_path: str = None, trades_df: pd.DataFrame = None):
        """
        Args:
            trades_csv_path: Путь к CSV файлу с сделками
            trades_df: Или напрямую DataFrame
        """
        if trades_csv_path:
            self.trades = pd.read_csv(trades_csv_path)
        elif trades_df is not None:
            self.trades = trades_df
        else:
            raise ValueError("Необходим trades_csv_path или trades_df")

        self.total_trades = len(self.trades)
        self.losses = self.trades[self.trades['pnl'] < 0]
        self.wins = self.trades[self.trades['pnl'] > 0]

    def analyze_losing_trades(self) -> Dict:
        """Анализ проигрышных сделок"""
        if len(self.losses) == 0:
            return {
                'total_losses': 0,
                'message': 'Нет проигрышных сделок!'
            }

        analysis = {
            'total_losses': len(self.losses),
            'total_trades': self.total_trades,
            'loss_rate': (len(self.losses) / self.total_trades) * 100,
            'avg_loss': self.losses['pnl'].mean(),
            'worst_loss': self.losses['pnl'].min(),
            'total_loss_amount': self.losses['pnl'].sum(),
            'scenarios_with_losses': self.losses['scenario'].unique().tolist(),
            'common_exit_reason': self.losses['exit_reason'].mode()[0] if len(self.losses) > 0 else None,
            'exit_reasons_breakdown': self.losses['exit_reason'].value_counts().to_dict(),
        }

        return analysis

    def analyze_by_scenario(self) -> pd.DataFrame:
        """Анализ по сценариям"""
        scenario_stats = self.trades.groupby('scenario').agg({
            'pnl': ['count', 'sum', 'mean', lambda x: (x > 0).sum()]
        })
        scenario_stats.columns = ['total_trades', 'total_pnl', 'avg_pnl', 'wins']
        scenario_stats['losses'] = scenario_stats['total_trades'] - scenario_stats['wins']
        scenario_stats['win_rate'] = (scenario_stats['wins'] / scenario_stats['total_trades'] * 100).round(1)

        # Сортируем по худшим
        scenario_stats = scenario_stats.sort_values('win_rate', ascending=True)

        return scenario_stats

    def identify_false_signal_patterns(self) -> Dict:
        """Идентификация паттернов ложных сигналов"""
        patterns = {
            'stop_loss_hits': len(self.losses[self.losses['exit_reason'] == 'STOP_LOSS']),
            'signal_exit_losses': len(self.losses[self.losses['exit_reason'] == 'SIGNAL_EXIT']),
            'backtest_end_losses': len(self.losses[self.losses['exit_reason'] == 'BACKTEST_END']),
        }

        # Анализ confidence для проигрышных сделок
        if 'confidence' in self.losses.columns:
            patterns['avg_confidence_losses'] = self.losses['confidence'].mean() if self.losses['confidence'].dtype != 'object' else None
            patterns['avg_confidence_wins'] = self.wins['confidence'].mean() if self.wins['confidence'].dtype != 'object' else None

        return patterns

    def get_worst_scenarios(self, top_n: int = 5) -> List[Dict]:
        """Получить топ-N худших сценариев"""
        scenario_stats = self.analyze_by_scenario()
        worst = scenario_stats.head(top_n)

        result = []
        for scenario_id, row in worst.iterrows():
            result.append({
                'scenario': scenario_id,
                'total_trades': int(row['total_trades']),
                'wins': int(row['wins']),
                'losses': int(row['losses']),
                'win_rate': row['win_rate'],
                'total_pnl': row['total_pnl'],
                'avg_pnl': row['avg_pnl']
            })

        return result

    def print_detailed_report(self):
        """Печать детального отчёта"""
        print("\n" + "=" * 80)
        print("  ❌ FALSE SIGNALS ANALYSIS")
        print("=" * 80)

        # 1. Общая статистика
        loss_analysis = self.analyze_losing_trades()
        print(f"\n1️⃣ ОБЩАЯ СТАТИСТИКА:")
        print(f"├─ Total Trades: {loss_analysis['total_trades']}")
        print(f"├─ False Signals: {loss_analysis['total_losses']}")
        print(f"├─ Loss Rate: {loss_analysis['loss_rate']:.1f}%")
        print(f"├─ Avg Loss: ${loss_analysis['avg_loss']:.2f}")
        print(f"├─ Worst Loss: ${loss_analysis['worst_loss']:.2f}")
        print(f"└─ Total Loss Amount: ${loss_analysis['total_loss_amount']:.2f}")

        # 2. Причины выхода
        print(f"\n2️⃣ EXIT REASONS BREAKDOWN:")
        for reason, count in loss_analysis['exit_reasons_breakdown'].items():
            pct = (count / loss_analysis['total_losses']) * 100
            print(f"├─ {reason}: {count} ({pct:.1f}%)")

        # 3. Худшие сценарии
        print(f"\n3️⃣ WORST SCENARIOS (Top 5):")
        worst_scenarios = self.get_worst_scenarios(5)
        for i, scenario in enumerate(worst_scenarios, 1):
            print(f"{i}. {scenario['scenario']}: {scenario['wins']}/{scenario['total_trades']} ({scenario['win_rate']:.1f}%) | ${scenario['total_pnl']:.0f}")

        # 4. Паттерны ложных сигналов
        patterns = self.identify_false_signal_patterns()
        print(f"\n4️⃣ FALSE SIGNAL PATTERNS:")
        print(f"├─ Stop Loss hits: {patterns['stop_loss_hits']}")
        print(f"├─ Signal Exit losses: {patterns['signal_exit_losses']}")
        print(f"└─ Backtest End losses: {patterns['backtest_end_losses']}")

        if patterns.get('avg_confidence_losses'):
            print(f"\n5️⃣ CONFIDENCE ANALYSIS:")
            print(f"├─ Avg Confidence (Losses): {patterns['avg_confidence_losses']:.3f}")
            print(f"└─ Avg Confidence (Wins): {patterns['avg_confidence_wins']:.3f}")

        print("\n" + "=" * 80 + "\n")

    def save_detailed_report(self, output_path: str):
        """Сохранить детальный отчёт в CSV"""
        scenario_stats = self.analyze_by_scenario()
        scenario_stats.to_csv(output_path)
        print(f"💾 Detailed report saved to: {output_path}")


# ============================================
# STANDALONE USAGE
# ============================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python false_signal_analyzer.py <trades_csv_path>")
        print("Example: python false_signal_analyzer.py tests/results/backtest_full_sim_20251101_175113.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    print(f"\n🔍 Analyzing false signals from: {csv_path}\n")

    analyzer = FalseSignalAnalyzer(trades_csv_path=csv_path)
    analyzer.print_detailed_report()

    # Сохраняем детальный отчёт
    output_path = csv_path.replace('.csv', '_false_signals_analysis.csv')
    analyzer.save_detailed_report(output_path)

