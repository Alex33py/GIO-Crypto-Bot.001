"""
🔬 SCENARIO ANALYZER v2.0
Комплексный анализ результатов бектеста
Профессиональная диагностика перед оптимизацией

Использование:
    python -m analytics.scenario_analyzer
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime

class ScenarioAnalyzer:
    """Анализирует результаты бектеста по сценариям"""

    def __init__(self, backtest_results_dir="tests/results"):
        self.results_dir = backtest_results_dir
        self.trades_df = None
        self.analysis = None

    def load_results(self):
        """Загрузить последний CSV из results"""
        try:
            csv_files = list(Path(self.results_dir).glob("backtest_full_sim_*.csv"))
            if not csv_files:
                print("❌ CSV не найдены в tests/results/")
                return False

            latest_csv = max(csv_files, key=os.path.getctime)
            self.trades_df = pd.read_csv(latest_csv)
            print(f"✅ Загружен: {latest_csv.name}")
            print(f"   Trades: {len(self.trades_df)}")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False

    def analyze_scenarios(self):
        """Анализ каждого сценария"""
        if self.trades_df is None:
            return False

        try:
            grouped = self.trades_df.groupby("scenario")

            # ✅ ИСПРАВЛЕНО: правильный расчет wins
            analysis_data = {
                "trades": grouped.size(),
                "total_pnl": grouped["pnl"].sum(),
                "avg_pnl": grouped["pnl"].mean(),
                "wins": grouped["pnl"].apply(lambda x: (x > 0).sum()),  # ← ИСПРАВЛЕНО
            }

            self.analysis = pd.DataFrame(analysis_data).round(2)

            # Win Rate
            self.analysis["win_rate"] = (
                self.analysis["wins"] / self.analysis["trades"] * 100
            ).round(1)

            # Profit Factor
            self.analysis["avg_win"] = grouped["pnl"].apply(
                lambda x: x[x > 0].mean() if (x > 0).any() else 0
            ).round(2)
            self.analysis["avg_loss"] = grouped["pnl"].apply(
                lambda x: abs(x[x <= 0].mean()) if (x <= 0).any() else 0
            ).round(2)
            self.analysis["profit_factor"] = (
                self.analysis["avg_win"] / self.analysis["avg_loss"]
            ).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)

            self.analysis = self.analysis.sort_values("win_rate", ascending=False)
            print("✅ Анализ завершен!")
            return True

        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            import traceback
            traceback.print_exc()
            return False

    def print_full_report(self):
        """Подробный отчет"""
        if self.analysis is None:
            return

        print("\n" + "=" * 120)
        print("🔬 ПОЛНЫЙ АНАЛИЗ СЦЕНАРИЕВ")
        print("=" * 120)

        # ✅ Работающие
        working = self.analysis[self.analysis["win_rate"] >= 50]
        print(f"\n✅ РАБОТАЮЩИЕ ({len(working)} шт, WR >= 50%):")
        if len(working) > 0:
            print(working)
        else:
            print("Нет")

        # ⚠️ Нейтральные
        neutral = self.analysis[
            (self.analysis["win_rate"] >= 20) &
            (self.analysis["win_rate"] < 50)
        ]
        print(f"\n⚠️ НЕЙТРАЛЬНЫЕ ({len(neutral)} шт, WR 20-50%):")
        if len(neutral) > 0:
            print(neutral)
        else:
            print("Нет")

        # ❌ Убыточные
        bad = self.analysis[self.analysis["win_rate"] < 20]
        print(f"\n❌ УБЫТОЧНЫЕ ({len(bad)} шт, WR < 20%):")
        if len(bad) > 0:
            print(bad)
        else:
            print("Нет")

        print("\n" + "=" * 120)

    def save_report(self):
        """Сохранить результаты"""
        try:
            os.makedirs("analysis", exist_ok=True)
            self.analysis.to_csv("analysis/scenario_analysis.csv")
            print("\n💾 Сохранено: analysis/scenario_analysis.csv")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False

    def run(self):
        """Запустить анализ"""
        print("\n🔬 SCENARIO ANALYZER v2.0")
        print("=" * 120)

        if not self.load_results():
            return False
        if not self.analyze_scenarios():
            return False

        self.print_full_report()
        self.save_report()

        print("✅ Анализ завершен!\n")
        return True

if __name__ == "__main__":
    analyzer = ScenarioAnalyzer()
    analyzer.run()
