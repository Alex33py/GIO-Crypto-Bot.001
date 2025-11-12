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
from tests.market_data_simulator_real import RealMarketDataSimulator



class FullSimulationBacktest:
    """Бектест с полной симуляцией рыночных данных"""

    def __init__(self):
        # Параметры
        self.symbol = "BTC/USDT"
        self.timeframe = "1h"
        self.period_days = 30
        self.initial_capital = 10000
        self.position_size = 0.12

        self.BACKTEST_MODE = "ALL"

        # Загружаем сценарии СНАЧАЛА!
        self.scenarios = self.load_scenarios_from_json()


        try:
            self.matcher = ScenarioMatcher()  # Пустой
            self.matcher.scenarios = self.scenarios  # ✅ ПРИСВАИВАЕМ СЦЕНАРИИ НАПРЯМУЮ!
            print(f"✅ ScenarioMatcher инициализирован с {len(self.scenarios)} сценариями")
            # DEBUG
            print(f"🔍 DEBUG: matcher.scenarios = {len(self.matcher.scenarios)} loaded")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации ScenarioMatcher: {e}")
            import traceback
            traceback.print_exc()
            self.matcher = None



         # ✅ Инициализируем RealMarketDataSimulator
        self.simulator = RealMarketDataSimulator(
            symbol="BTC/USDT",
            timeframe="1h",
            num_candles=720,  # 30 дней
            use_cache=True
        )

        # Показать статистику загруженных данных
        stats = self.simulator.get_statistics()
        print("="*60)
        print("СТАТИСТИКА РЕАЛЬНЫХ ДАННЫХ")
        print("="*60)
        print(f"Symbol: {stats['symbol']}")
        print(f"Timeframe: {stats['timeframe']}")
        print(f"Candles: {stats['candles']}")
        print(f"Period: {stats['start_date']} - {stats['end_date']}")
        print(f"Price Start: ${stats['price_start']:,.2f}")
        print(f"Price End: ${stats['price_end']:,.2f}")
        print(f"Price Average: ${stats['price_avg']:,.2f}")
        print(f"Price Min: ${stats['price_min']:,.2f}")
        print(f"Price Max: ${stats['price_max']:,.2f}")
        print(f"Volume Avg: {stats['volume_avg']:,.2f}")
        print(f"Data Source: {stats['data_source']}")
        print("="*60)


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
            # ✅ Приоритет: ТОП-5, затем v35_enhanced
            possible_paths = [
                "data/scenarios/gio_scenarios_top5_core.json",  # ← ТОП-5 (приоритет)
                "data/scenarios/gio_scenarios_v35_enhanced.json",  # ← Fallback на 24
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        scenarios_data = json.load(f)
                    print(f"✅ JSON loaded from: {path}")

                    scenarios = []
                    if isinstance(scenarios_data, dict) and "scenarios" in scenarios_data:
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

    async def get_signal_from_matcher(self, df, idx, indicators):
        """Получение сигнала с полной симуляцией данных"""
        try:
            if not self.matcher:
                return None

            # Генерируем ПОЛНЫЕ рыночные данные через симулятор
            full_market_data = self.simulator.generate_full_market_data(
                df, idx, indicators
            )

            # ✅ НОВОЕ: Вычисляем ADX из реальных OHLCV данных
            from analytics.advanced_indicators import AdvancedIndicators

            highs = full_market_data.get('highs', [])
            lows = full_market_data.get('lows', [])
            closes = full_market_data.get('closes', [])

            if len(closes) >= 15:  # Минимум для ADX
                adx_result = AdvancedIndicators.calculate_adx(
                    highs=highs,
                    lows=lows,
                    closes=closes,
                    period=14
                )

                # Обновляем indicators с реальным ADX
                full_market_data['indicators']['adx'] = adx_result.get('adx', 0)
                full_market_data['adx_data'] = adx_result  # Полные данные ADX

                # DEBUG: Показываем ADX для первых 5 свечей
                if idx < 105:  # warmup=100, показываем первые 5 после warmup
                    print(f"🔍 Candle {idx}: ADX={adx_result['adx']:.1f}, +DI={adx_result['plus_di']:.1f}, -DI={adx_result['minus_di']:.1f}, Strength={adx_result['trend_strength']}")

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
            import traceback
            traceback.print_exc()
            return None

    async def get_signal_from_matcher_real(self, candle_data, idx):
        """Получение сигнала с реальными данными"""
        try:
            if not self.matcher:
                print("❌ ERROR: Matcher is None!")
                return None

            from analytics.advanced_indicators import AdvancedIndicators

            ohlcv_history = candle_data.get('ohlcv', [])

            if len(ohlcv_history) >= 15:
                highs = [c['high'] for c in ohlcv_history]
                lows = [c['low'] for c in ohlcv_history]
                closes = [c['close'] for c in ohlcv_history]

                adx_result = AdvancedIndicators.calculate_adx(
                    highs=highs,
                    lows=lows,
                    closes=closes,
                    period=14
                )

                candle_data['indicators']['adx'] = adx_result.get('adx', 0)
                candle_data['adx_data'] = adx_result

                # Вычисляем тренд
                if adx_result['adx'] > 25:
                    trend = "bullish" if adx_result['plus_di'] > adx_result['minus_di'] else "bearish"
                else:
                    trend = "neutral"

                # ✅ ПРАВИЛЬНО: используем lowercase ключи
                candle_data['mtf_trends'] = {
                    "1h": trend.lower(),      # ← Убедитесь lowercase
                    "4h": (trend if adx_result['adx'] >= 25 else "neutral").lower(),
                    "1d": "neutral"
                }

                # ✅ ДОПОЛНИТЕЛЬНЫЙ DEBUG:
                if idx < 105:
                    print(f"🔍 Candle {idx}: ADX={adx_result['adx']:.1f}, MTF={trend.upper()}")
                    print(f"   ✅ MTF_TRENDS: {candle_data['mtf_trends']}")

            # ✅ Вызываем matcher
            signal = self.matcher.match_scenario(
                symbol=self.symbol,
                market_data=candle_data,
                indicators=candle_data.get("indicators", {}),
                mtf_trends=candle_data.get("mtf_trends", {}),
                volume_profile=candle_data.get("volume_profile", {}),
                news_sentiment=candle_data.get("news_sentiment", {}),
                veto_checks=candle_data.get("veto_checks", {"has_veto": False})
            )

            if signal:
                # ПРАВИЛЬНО - используем scenario_id
                direction = signal.get('direction', 'UNKNOWN')
                scenario = signal.get('scenario_id', 'UNKNOWN')
                print(f"🎯 Signal found: {direction} | Scenario: {scenario}")

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
            print(f"⚠️ Matcher error (real): {e}")
            import traceback
            traceback.print_exc()
            return None



    def execute_trade(self, signal, price, timestamp):
        """Выполнение сделки с динамическим фильтром сценариев"""
        print(f"🔍 DEBUG execute_trade: signal={signal}")
        if not isinstance(signal, dict):
            return

        scenario_id = (
            signal.get("scenario_id")
            or signal.get("scenario")
            or signal.get("id")
            or "UNKNOWN"
        )
        print(f"🔍 scenario_id={scenario_id}")
        parts = scenario_id.split("_")
        base_scenario_id = f"{parts[0]}_{parts[1]}"
        print(f"🔍 base_scenario_id={base_scenario_id}")

        # Экстрахируем базовый ID (убираем суффиксы типа "_MOMENTUM_LONG")
        parts = scenario_id.split("_")
        base_scenario_id = f"{parts[0]}_{parts[1]}"  # SCN_001 from SCN_001_MOMENTUM_LONG

                # ✅ ВСЕ СЦЕНАРИИ v3.5-enhanced (строки 185-209)
        ALL_SCENARIOS_V35 = {
            # LONG (12)
            "SCN_001", "SCN_002", "SCN_003", "SCN_004", "SCN_005", "SCN_006",
            "SCN_007", "SCN_008", "SCN_009", "SCN_010", "SCN_011", "SCN_012",
            # SHORT (12) - расширенный
            "SCN_013", "SCN_014", "SCN_015", "SCN_016", "SCN_017", "SCN_018",
            "SCN_019", "SCN_020", "SCN_021", "SCN_022", "SCN_023", "SCN_024",
        }

        BACKTEST_MODE = self.BACKTEST_MODE  # Читаем из __init__

        # Фильтр режима бектеста
        if BACKTEST_MODE == "ALL":
            # ✅ Разрешаем ВСЕ 24 сценария
            pass
        elif BACKTEST_MODE == "TOP_ONLY":
            # Только если нужен фильтр
            if base_scenario_id not in ALL_SCENARIOS_V35:
                return
        else:
            return



        confidence = signal.get("confidence", 0.5)
        if isinstance(confidence, str):
            confidence_map = {"low": 0.3, "medium": 0.5, "high": 0.7}
            confidence = confidence_map.get(confidence.lower(), 0.5)
        if not confidence or confidence == 0:
            confidence = 0.5

        signal_type = (
            signal.get("type")
            or signal.get("direction")
            or signal.get("side")
            or "LONG"
        )

        atr = signal.get("atr", 100)

        if signal_type.upper() == "LONG":
            stop_loss = signal.get("stop_loss", price - (atr * 1.5))
            take_profit = signal.get("tp1", price + (atr * 3.0))
        else:
            stop_loss = signal.get("stop_loss", price + (atr * 1.5))
            take_profit = signal.get("tp1", price - (atr * 3.0))


        if self.open_position:
            if self.open_position["type"] != signal_type:
                self.close_position(price, timestamp, "SIGNAL_EXIT")

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
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "atr": atr,
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
        print("\n🚀 Starting Full Simulation Backtest with REAL DATA...\n")

        # ✅ Используем данные из RealMarketDataSimulator
        # (данные уже загружены в __init__)
        total_candles = len(self.simulator.ohlcv_data)

        warmup = 100
        print(f"🔥 Warming up ({warmup} candles)...")
        print(f"📊 Testing on {total_candles - warmup} candles...\n")


        for i in range(warmup, total_candles):
            # ✅ Получаем данные из RealMarketDataSimulator
            candle_data = self.simulator.get_data(i)

            price = candle_data["close"]
            timestamp = candle_data["timestamp"]

            self.check_stop_take(price, timestamp)

            # Индикаторы уже в candle_data
            indicators = candle_data["indicators"]

            # Получаем сигнал с реальными данными
            signal = await self.get_signal_from_matcher_real(candle_data, i)

            if signal:
                self.execute_trade(signal, price, timestamp)

            if i % 100 == 0:
                progress = ((i - warmup) / (total_candles - warmup)) * 100
                print(
                    f"⏳ {progress:.1f}% | Trades: {len(self.trades)} | Capital: ${self.current_capital:,.0f} | Signals: {sum(self.signal_stats.values())}"
                )

        if self.open_position:
            # ✅ Последняя свеча из симулятора
            final_candle = self.simulator.get_data(total_candles - 1)
            final_price = final_candle["close"]
            final_time = final_candle["timestamp"]
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
