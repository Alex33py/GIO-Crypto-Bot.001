"""
🔬 REAL DATA BACKTEST v3.0 - SIMPLE
Бектест с реальными данными БЕЗ ScenarioMatcher
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import json
from datetime import datetime

class SimpleRealDataBacktest:
    """Упрощённый бектест с реальными данными"""

    def __init__(self):
        self.data_1h = None
        self.data_4h = None
        self.scenarios = None
        self.results = []

        # Параметры
        self.capital = 10000.0
        self.position_size = 0.02  # 2%

    def load_data(self):
        """Загрузить данные"""
        print("\n📂 Загрузка данных...")

        try:
            # Загрузить CSV
            self.data_1h = pd.read_csv("data/historical/BTCUSDT_1h_30d.csv")
            self.data_4h = pd.read_csv("data/historical/BTCUSDT_4h_30d.csv")

            # Конвертировать timestamp
            self.data_1h["timestamp"] = pd.to_datetime(self.data_1h["timestamp"])
            self.data_4h["timestamp"] = pd.to_datetime(self.data_4h["timestamp"])

            print(f"✅ 1h: {len(self.data_1h)} свечей")
            print(f"✅ 4h: {len(self.data_4h)} свечей")

            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return False

    def load_scenarios(self):
        """Загрузить сценарии"""
        try:
            # ✅ Пытаемся загрузить ТОП-5 сценариев (приоритет)
            possible_paths = [
                "data/scenarios/gio_scenarios_top5_core.json",  # ← ТОП-5
                "data/scenarios/gio_scenarios_v35_enhanced.json",  # ← Fallback
            ]

            scenarios_loaded = False
            for path in possible_paths:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.scenarios = data["scenarios"]

                    print(f"✅ Загружено из: {path}")
                    print(f"✅ Сценариев: {len(self.scenarios)}\n")
                    scenarios_loaded = True
                    break
                except FileNotFoundError:
                    continue

            if not scenarios_loaded:
                print("❌ Не найден ни один файл сценариев!")
                return False

            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки сценариев: {e}")
            return False


    def run_backtest(self):
        """Запустить бектест"""
        print("="*80)
        print("🔬 ЗАПУСК УПРОЩЁННОГО БЕКТЕСТА С РЕАЛЬНЫМИ ДАННЫМИ")
        print("="*80 + "\n")

        trades_count = 0

        # Итерация по 1h свечам
        for i in range(100, len(self.data_1h)):
            candle_1h = self.data_1h.iloc[i]
            timestamp = candle_1h["timestamp"]

            # Простая логика: генерировать сделку каждые 20 свечей
            if i % 20 == 0:
                trades_count += 1

                # Случайное направление на основе индекса
                direction = "LONG" if i % 40 < 20 else "SHORT"

                entry_price = float(candle_1h["close"])

                # Простые TP/SL
                if direction == "LONG":
                    tp = entry_price * 1.02
                    sl_price = entry_price * 0.985
                else:
                    tp = entry_price * 0.98
                    sl_price = entry_price * 1.015

                # Поиск exit
                exit_price, exit_reason = self._find_exit(
                    i, entry_price, tp, sl_price, direction
                )

                # Расчёт PnL
                if direction == "LONG":
                    pnl_pct = (exit_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - exit_price) / entry_price

                pnl_usd = self.capital * self.position_size * pnl_pct

                # Сохранить результат
                self.results.append({
                    "timestamp": str(timestamp),
                    "scenario_id": f"SIMPLE_{trades_count}",
                    "direction": direction,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "pnl_pct": pnl_pct * 100,
                    "pnl_usd": pnl_usd
                })

                if trades_count % 10 == 0:
                    print(f"   Сделок: {trades_count}")

        print(f"\n✅ Всего сделок: {trades_count}")
        return True

    def _find_exit(self, start_idx, entry, tp, sl_price, direction):
        """Найти выход из сделки"""
        # Поиск TP/SL в следующих свечах
        for i in range(start_idx + 1, min(start_idx + 50, len(self.data_1h))):
            candle = self.data_1h.iloc[i]

            if direction == "LONG":
                if candle["high"] >= tp:
                    return tp, "TP"
                if candle["low"] <= sl_price:
                    return sl_price, "SL"
            else:
                if candle["low"] <= tp:
                    return tp, "TP"
                if candle["high"] >= sl_price:
                    return sl_price, "SL"

        # Если не нашли - закрытие по текущей цене
        return self.data_1h.iloc[min(start_idx + 50, len(self.data_1h) - 1)]["close"], "TIMEOUT"

    def save_results(self):
        """Сохранить результаты"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/results/backtest_simple_{timestamp}.csv"

        # Создать папку results если нет
        os.makedirs("tests/results", exist_ok=True)

        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)

        print(f"\n💾 Результаты сохранены: {filename}")

        # Статистика
        if len(df) == 0:
            print("\n⚠️ Нет сделок для анализа!")
            return

        total_trades = len(df)
        wins = len(df[df["pnl_usd"] > 0])
        losses = len(df[df["pnl_usd"] < 0])
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        total_pnl = df["pnl_usd"].sum()

        avg_win = df[df["pnl_usd"] > 0]["pnl_usd"].mean() if wins > 0 else 0
        avg_loss = abs(df[df["pnl_usd"] < 0]["pnl_usd"].mean()) if losses > 0 else 0
        profit_factor = (wins * avg_win) / (losses * avg_loss) if losses > 0 and avg_loss > 0 else 0

        print("\n" + "="*80)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("="*80)
        print(f"Всего сделок: {total_trades}")
        print(f"Прибыльных: {wins} ({win_rate:.1f}%)")
        print(f"Убыточных: {losses}")
        print(f"Средняя прибыль: ${avg_win:.2f}")
        print(f"Средний убыток: ${avg_loss:.2f}")
        print(f"Profit Factor: {profit_factor:.2f}")
        print(f"\nОбщий PnL: ${total_pnl:.2f}")
        print(f"ROI: {(total_pnl / self.capital * 100):.2f}%")
        print("="*80)

    def run(self):
        """Полный запуск"""
        if not self.load_data():
            return
        if not self.load_scenarios():
            return
        if not self.run_backtest():
            return

        self.save_results()

if __name__ == "__main__":
    backtest = SimpleRealDataBacktest()
    backtest.run()
