"""
STAGE 1 BACKTEST: Full Simulation - Complete Market Data
Бектест с полной симуляцией рыночных данных для всех 100 сценариев
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Импортируем реальный matcher и симулятор
from core.scenario_matcher import UnifiedScenarioMatcher as ScenarioMatcher
from tests.market_data_simulator import MarketDataSimulator


class FullSimulationBacktest:
    """Бектест с полной симуляцией рыночных данных"""

    def __init__(self):
        # Параметры
        self.symbol = "BTC/USDT"
        self.timeframe = "1h"
        self.period_days = 30
        self.initial_capital = 10000
        self.position_size = 0.02

        # Инициализируем matcher
        try:
            self.matcher = ScenarioMatcher()
            print("✅ ScenarioMatcher инициализирован")
            # DEBUG
            print(f"🔍 DEBUG: matcher class = {type(self.matcher)}")
            print(
                f"🔍 DEBUG: matcher.__class__.__name__ = {self.matcher.__class__.__name__}"
            )

        except Exception as e:
            print(f"⚠️ Ошибка инициализации ScenarioMatcher: {e}")
            self.matcher = None

        # Инициализируем симулятор
        self.simulator = MarketDataSimulator(seed=42)
        print("✅ MarketDataSimulator инициализирован")

        # Загружаем сценарии
        self.scenarios = self.load_scenarios_from_json()

        # Биржа
        self.exchange = ccxt.binance(
            {"enableRateLimit": True, "options": {"defaultType": "future"}}
        )

        # Результаты
        self.trades = []
        self.current_capital = self.initial_capital
        self.open_position = None
        self.signal_stats = {}  # Статистика по сигналам

        print(f"✅ Full Simulation Backtest initialized")
        print(f"💰 Capital: ${self.initial_capital:,.0f}")
        print(f"📊 Testing: {len(self.scenarios)} scenarios")

    def load_scenarios_from_json(self):
        """Загрузка сценариев из JSON"""
        try:
            possible_paths = [
                "gio_scenarios_112_final_v3.json",
                "data/scenarios/gio_scenarios_112_final_v3.json",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        scenarios_data = json.load(f)
                    print(f"✅ JSON loaded from: {path}")

                    scenarios = []
                    if (
                        isinstance(scenarios_data, dict)
                        and "scenarios" in scenarios_data
                    ):
                        scenarios_list = scenarios_data["scenarios"]
                    elif isinstance(scenarios_data, list):
                        scenarios_list = scenarios_data
                    else:
                        scenarios_list = []

                    for scenario in scenarios_list:
                        scenario_id = scenario.get("id", "")
                        if scenario_id:
                            scenarios.append(scenario)

                    print(f"✅ Parsed {len(scenarios)} scenarios")
                    return scenarios

            print("⚠️ JSON not found")
            return []
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return []

    async def fetch_data(self):
        """Загрузка исторических данных"""
        print(f"\n📥 Fetching {self.period_days} days of {self.symbol}...")

        since = self.exchange.parse8601(
            (datetime.now() - timedelta(days=self.period_days)).isoformat()
        )

        all_candles = []
        while True:
            try:
                candles = await self.exchange.fetch_ohlcv(
                    self.symbol, self.timeframe, since=since, limit=1000
                )
                if not candles:
                    break
                all_candles.extend(candles)
                since = candles[-1][0] + 1
                if len(candles) < 1000:
                    break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                break

        df = pd.DataFrame(
            all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        print(f"✅ Loaded {len(df)} candles")
        return df

    def calculate_indicators(self, df, idx):
        """Расчёт индикаторов"""
        lookback = min(100, idx)
        data = df.iloc[max(0, idx - lookback) : idx + 1]

        # RSI
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50

        # Volume
        avg_volume = data["volume"].rolling(window=20).mean().iloc[-1]
        current_volume = data["volume"].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # ADX (упрощённый)
        adx = 25 + (volume_ratio - 1) * 20

        # Momentum
        momentum = data["close"].pct_change(5).iloc[-1] if len(data) >= 5 else 0

        return {
            "rsi": current_rsi,
            "volume_ratio": volume_ratio,
            "adx": adx,
            "momentum": momentum,
        }

    async def get_signal_from_matcher(self, df, idx, indicators):
        """Получение сигнала с полной симуляцией данных"""
        try:
            if not self.matcher:
                return None

            # Генерируем ПОЛНЫЕ рыночные данные через симулятор
            full_market_data = self.simulator.generate_full_market_data(
                df, idx, indicators
            )

            # Вызываем matcher с полными данными
            signal = self.matcher.match_scenario(
                symbol=self.symbol,
                market_data=full_market_data,
                indicators=full_market_data["indicators"],
                mtf_trends=full_market_data["mtf_trends"],
                volume_profile=full_market_data["volume_profile"],
                news_sentiment=full_market_data["news_sentiment"],
                veto_checks=full_market_data["veto_checks"],
            )

            # Статистика сигналов
            if signal:
                scenario_id = (
                    signal.get("scenario_id")
                    or signal.get("scenario")
                    or signal.get("id")
                    or "UNKNOWN"
                )
                self.signal_stats[scenario_id] = (
                    self.signal_stats.get(scenario_id, 0) + 1
                )

            return signal

        except Exception as e:
            print(f"⚠️ Matcher error: {e}")
            return None

    def execute_trade(self, signal, price, timestamp):
        """Выполнение сделки"""
        if not isinstance(signal, dict):
            return

        signal_type = (
            signal.get("type")
            or signal.get("direction")
            or signal.get("side")
            or "LONG"
        )

        scenario_id = (
            signal.get("scenario_id")
            or signal.get("scenario")
            or signal.get("id")
            or "UNKNOWN"
        )

        confidence = signal.get("confidence", "medium")

        # Закрываем противоположную позицию
        if self.open_position:
            if self.open_position["type"] != signal_type:
                self.close_position(price, timestamp, "SIGNAL_EXIT")

        # Открываем новую
        if not self.open_position:
            position_value = self.current_capital * self.position_size
            size = position_value / price

            self.open_position = {
                "type": signal_type,
                "scenario": scenario_id,
                "entry_price": price,
                "size": size,
                "entry_time": timestamp,
                "confidence": confidence,
                "stop_loss": (
                    price * 0.97 if signal_type.upper() == "LONG" else price * 1.03
                ),
                "take_profit": (
                    price * 1.05 if signal_type.upper() == "LONG" else price * 0.95
                ),
            }

    def close_position(self, price, timestamp, reason):
        """Закрытие позиции"""
        if not self.open_position:
            return

        pos = self.open_position

        if pos["type"] == "LONG":
            pnl = (price - pos["entry_price"]) * pos["size"]
        else:
            pnl = (pos["entry_price"] - price) * pos["size"]

        self.current_capital += pnl
        pnl_pct = (pnl / (pos["entry_price"] * pos["size"])) * 100

        self.trades.append(
            {
                "scenario": pos["scenario"],
                "type": pos["type"],
                "entry_time": pos["entry_time"],
                "exit_time": timestamp,
                "entry_price": pos["entry_price"],
                "exit_price": price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "confidence": pos["confidence"],
                "exit_reason": reason,
            }
        )

        self.open_position = None

    def check_stop_take(self, price, timestamp):
        """Проверка SL/TP"""
        if not self.open_position:
            return

        pos = self.open_position

        if pos["type"] == "LONG":
            if price <= pos["stop_loss"]:
                self.close_position(pos["stop_loss"], timestamp, "STOP_LOSS")
            elif price >= pos["take_profit"]:
                self.close_position(pos["take_profit"], timestamp, "TAKE_PROFIT")
        else:
            if price >= pos["stop_loss"]:
                self.close_position(pos["stop_loss"], timestamp, "STOP_LOSS")
            elif price <= pos["take_profit"]:
                self.close_position(pos["take_profit"], timestamp, "TAKE_PROFIT")

    async def run(self):
        """Основной цикл"""
        print("\n🚀 Starting Full Simulation Backtest...\n")

        df = await self.fetch_data()

        warmup = 100
        print(f"🔥 Warming up ({warmup} candles)...")
        print(f"📊 Testing on {len(df) - warmup} candles...\n")

        for i in range(warmup, len(df)):
            current_candle = df.iloc[i]
            price = current_candle["close"]
            timestamp = current_candle["timestamp"]

            self.check_stop_take(price, timestamp)

            indicators = self.calculate_indicators(df, i)

            # Получаем сигнал с полной симуляцией
            signal = await self.get_signal_from_matcher(df, i, indicators)

            if signal:
                self.execute_trade(signal, price, timestamp)

            if i % 100 == 0:
                progress = ((i - warmup) / (len(df) - warmup)) * 100
                print(
                    f"⏳ {progress:.1f}% | Trades: {len(self.trades)} | Capital: ${self.current_capital:,.0f} | Signals: {sum(self.signal_stats.values())}"
                )

        if self.open_position:
            final_price = df.iloc[-1]["close"]
            final_time = df.iloc[-1]["timestamp"]
            self.close_position(final_price, final_time, "BACKTEST_END")

        print("\n✅ Backtest completed!\n")

        self.print_results()
        self.save_results()

    def print_results(self):
        """Вывод результатов"""
        if not self.trades:
            print("❌ No trades executed")
            print(f"\n📊 Generated Signals: {sum(self.signal_stats.values())}")
            if self.signal_stats:
                print("\nTop 10 scenarios by signals:")
                sorted_signals = sorted(
                    self.signal_stats.items(), key=lambda x: x[1], reverse=True
                )[:10]
                for sc, count in sorted_signals:
                    print(f"  {sc}: {count} signals")
            return

        df_trades = pd.DataFrame(self.trades)

        total_trades = len(df_trades)
        wins = df_trades[df_trades["pnl"] > 0]
        losses = df_trades[df_trades["pnl"] <= 0]

        win_rate = len(wins) / total_trades * 100
        total_pnl = df_trades["pnl"].sum()
        roi = (self.current_capital - self.initial_capital) / self.initial_capital * 100

        avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses["pnl"].mean()) if len(losses) > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

        by_scenario = df_trades.groupby("scenario").agg(
            {"pnl": ["count", "sum", lambda x: (x > 0).sum()]}
        )
        by_scenario.columns = ["trades", "pnl", "wins"]
        by_scenario["win_rate"] = (
            by_scenario["wins"] / by_scenario["trades"] * 100
        ).round(1)
        by_scenario = by_scenario.sort_values("win_rate", ascending=False)

        print("=" * 70)
        print(f"  🎯 FULL SIMULATION BACKTEST - {len(self.scenarios)} SCENARIOS")
        print("=" * 70)
        print(f"\n📊 OVERALL:")
        print(f"├─ Trades: {total_trades} ({len(wins)} wins, {len(losses)} losses)")
        print(f"├─ Win Rate: {win_rate:.1f}% {'✅' if win_rate >= 55 else '❌'}")
        print(f"├─ Total PnL: ${total_pnl:,.2f}")
        print(f"├─ ROI: {roi:.2f}%")
        print(f"├─ Avg Win: ${avg_win:,.2f}")
        print(f"├─ Avg Loss: ${avg_loss:,.2f}")
        print(
            f"└─ Profit Factor: {profit_factor:.2f} {'✅' if profit_factor >= 1.5 else '❌'}"
        )

        print(f"\n📊 SIGNAL STATS:")
        print(f"├─ Total Signals Generated: {sum(self.signal_stats.values())}")
        print(f"├─ Unique Scenarios: {len(self.signal_stats)}")
        print(
            f"└─ Signals to Trades Ratio: {total_trades / max(sum(self.signal_stats.values()), 1):.2f}"
        )

        print(f"\n📈 TOP 10 BEST PERFORMERS:")
        for i, (sc, row) in enumerate(by_scenario.head(10).iterrows(), 1):
            status = "✅" if row["win_rate"] >= 55 else "⚠️"
            print(
                f"{i}. {status} {sc}: {int(row['wins'])}/{int(row['trades'])} ({row['win_rate']:.1f}%) | ${row['pnl']:,.0f}"
            )

        print(f"\n📉 TOP 10 WORST PERFORMERS:")
        for i, (sc, row) in enumerate(by_scenario.tail(10).iterrows(), 1):
            print(
                f"{i}. ❌ {sc}: {int(row['wins'])}/{int(row['trades'])} ({row['win_rate']:.1f}%) | ${row['pnl']:,.0f}"
            )

        print("\n" + "=" * 70 + "\n")

    def save_results(self):
        """Сохранение результатов"""
        os.makedirs("tests/results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.trades:
            df_trades = pd.DataFrame(self.trades)
            csv_path = f"tests/results/backtest_full_sim_{timestamp}.csv"
            df_trades.to_csv(csv_path, index=False)

            by_scenario = df_trades.groupby("scenario").agg(
                {"pnl": ["count", "sum", lambda x: (x > 0).sum()]}
            )
            by_scenario.columns = ["trades", "total_pnl", "wins"]
            by_scenario["win_rate"] = (
                by_scenario["wins"] / by_scenario["trades"] * 100
            ).round(1)

            scenario_csv = f"tests/results/scenarios_full_sim_{timestamp}.csv"
            by_scenario.to_csv(scenario_csv)

            print(f"💾 All trades: {csv_path}")
            print(f"💾 Scenario summary: {scenario_csv}")

        # Сохраняем статистику сигналов
        if self.signal_stats:
            signal_stats_df = pd.DataFrame(
                list(self.signal_stats.items()), columns=["scenario", "signals"]
            )
            signal_stats_csv = f"tests/results/signal_stats_{timestamp}.csv"
            signal_stats_df.to_csv(signal_stats_csv, index=False)
            print(f"💾 Signal stats: {signal_stats_csv}")

    async def cleanup(self):
        """Закрытие соединений"""
        await self.exchange.close()


async def main():
    backtest = FullSimulationBacktest()
    try:
        await backtest.run()
    finally:
        await backtest.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
