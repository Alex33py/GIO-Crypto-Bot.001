"""
Grid Search Optimizer for GIO.BOT - Phase 2: SL/TP Optimization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import json

import ccxt.async_support as ccxt
from core.scenario_matcher import UnifiedScenarioMatcher as ScenarioMatcher
from tests.market_data_simulator import MarketDataSimulator


class GridSearchOptimizer:
    """Grid search для оптимизации параметров"""

    def __init__(self):
        self.results = []
        self.best_config = None
        self.best_pf = 0

    # ===== КОНФИГУРАЦИИ СЕТКИ =====

    GRID_CONFIG = {
        # Phase 1: ADX + Disabled (COMPLETED)
        'quick_wins': {
            'adx_min': [20, 25, 30],
            'disabled_scenarios': [
                ['SCN_024', 'SCN_023'],
                ['SCN_024', 'SCN_023', 'SCN_018'],
            ]
        },

        # ✅ Phase 2: SL/TP Optimization (NEW!)
        'sl_tp_optimization': {
            'sl_multiplier': [1.2, 1.5, 1.8, 2.0],
            'tp_multiplier': [3.0, 3.5, 4.0, 4.5],
            'disabled_scenarios': [['SCN_024', 'SCN_023']],
        },

        # Phase 3: Fine-tuning (LATER)
        'volume_ratio': {
            'volume_ratio_min': [1.0, 1.2, 1.5, 2.0],
            'disabled_scenarios': [['SCN_024', 'SCN_023']],
        }
    }

    # ===== GRID SEARCH МЕТОДЫ =====

    async def run_grid_search(self, grid_type='sl_tp_optimization'):
        """Запуск grid search"""

        print(f"\n🔍 Starting Grid Search: {grid_type}")
        print("=" * 70)

        grid = self.GRID_CONFIG[grid_type]
        configs = self._generate_configs(grid)

        print(f"📊 Generated {len(configs)} configurations to test\n")

        for i, config in enumerate(configs, 1):
            print(f"⏳ Testing config {i}/{len(configs)}")
            print(f"   Config: {config}")

            # Запускаем backtest с этой конфигурацией
            result = await self._run_backtest_with_config(config)

            # Сохраняем результат
            self.results.append({
                'config': config,
                'result': result,
                'timestamp': datetime.now()
            })

            # Обновляем best config
            pf = result.get('profit_factor', 0)
            wr = result.get('win_rate', 0)

            print(f"   ├─ Profit Factor: {pf:.2f}")
            print(f"   ├─ Win Rate: {wr:.1f}%")
            print(f"   ├─ Trades: {result.get('total_trades', 0)}")
            print(f"   └─ ROI: {result.get('roi', 0):.2f}%")

            if pf > self.best_pf:
                self.best_pf = pf
                self.best_config = config
                print(f"   ✅ NEW BEST! (PF {pf:.2f})")

            print()

        return self._analyze_results()

    def _generate_configs(self, grid):
        """Генерирует все комбинации параметров"""
        import itertools

        keys = list(grid.keys())
        values = list(grid.values())

        configs = []
        for combo in itertools.product(*values):
            config = dict(zip(keys, combo))
            configs.append(config)

        return configs

    async def _run_backtest_with_config(self, config):
        """Запускает backtest с конкретной конфигурацией"""

        symbol = "BTC/USDT"
        timeframe = "1h"
        period_days = 30
        initial_capital = 10000
        position_size = 0.02

        # ✅ ПРИМЕНЯЕМ КОНФИГУРАЦИЮ
        sl_multiplier = config.get('sl_multiplier', 1.5)
        tp_multiplier = config.get('tp_multiplier', 3.5)
        disabled_scenarios = config.get('disabled_scenarios', ['SCN_024', 'SCN_023'])

        # Инициализируем компоненты
        matcher = ScenarioMatcher()
        simulator = MarketDataSimulator(seed=42)
        exchange = ccxt.binance({
            "enableRateLimit": True,
            "options": {"defaultType": "future"}
        })

        # Загружаем данные
        since = exchange.parse8601(
            (datetime.now() - pd.Timedelta(days=period_days)).isoformat()
        )

        all_candles = []
        while True:
            try:
                candles = await exchange.fetch_ohlcv(
                    symbol, timeframe, since=since, limit=1000
                )
                if not candles:
                    break
                all_candles.extend(candles)
                since = candles[-1][0] + 1
                if len(candles) < 1000:
                    break
            except Exception:
                break

        df = pd.DataFrame(
            all_candles,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # Backtest loop
        trades = []
        current_capital = initial_capital
        open_position = None

        warmup = 100

        for i in range(warmup, len(df)):
            current_candle = df.iloc[i]
            price = current_candle["close"]
            timestamp = current_candle["timestamp"]

            # Check SL/TP
            if open_position:
                pos = open_position
                hit_sl = False
                hit_tp = False

                if pos["type"] == "LONG":
                    if price <= pos["stop_loss"]:
                        hit_sl = True
                    elif price >= pos["take_profit"]:
                        hit_tp = True
                else:
                    if price >= pos["stop_loss"]:
                        hit_sl = True
                    elif price <= pos["take_profit"]:
                        hit_tp = True

                if hit_sl or hit_tp:
                    # Close position
                    if pos["type"] == "LONG":
                        exit_price = pos["stop_loss"] if hit_sl else pos["take_profit"]
                        pnl = (exit_price - pos["entry_price"]) * pos["size"]
                    else:
                        exit_price = pos["stop_loss"] if hit_sl else pos["take_profit"]
                        pnl = (pos["entry_price"] - exit_price) * pos["size"]

                    current_capital += pnl

                    trades.append({
                        "pnl": pnl,
                        "exit_reason": "STOP_LOSS" if hit_sl else "TAKE_PROFIT"
                    })

                    open_position = None

            # Get signal
            full_market_data = simulator.generate_full_market_data(df, i, {})

            from analytics.advanced_indicators import AdvancedIndicators

            highs = full_market_data.get('highs', [])
            lows = full_market_data.get('lows', [])
            closes = full_market_data.get('closes', [])

            if len(closes) >= 15:
                adx_result = AdvancedIndicators.calculate_adx(
                    highs=highs, lows=lows, closes=closes, period=14
                )
                full_market_data['indicators']['adx'] = adx_result.get('adx', 0)

            signal = matcher.match_scenario(
                symbol=symbol,
                market_data=full_market_data,
                indicators=full_market_data["indicators"],
                mtf_trends=full_market_data["mtf_trends"],
                volume_profile=full_market_data["volume_profile"],
                news_sentiment=full_market_data["news_sentiment"],
                veto_checks=full_market_data["veto_checks"],
            )

            # Фильтр по disabled scenarios
            if signal:
                scenario_id = signal.get('scenario_id', '')
                if scenario_id in disabled_scenarios:
                    signal = None

            # Execute trade с НОВЫМИ SL/TP
            if signal and not open_position:
                signal_type = signal.get("type", "LONG")
                atr = signal.get("atr", 100)

                # ✅ ПРИМЕНЯЕМ КОНФИГУРАЦИЮ SL/TP
                if signal_type.upper() == "LONG":
                    stop_loss = price - (atr * sl_multiplier)
                    take_profit = price + (atr * tp_multiplier)
                else:
                    stop_loss = price + (atr * sl_multiplier)
                    take_profit = price - (atr * tp_multiplier)

                position_value = current_capital * position_size
                size = position_value / price

                open_position = {
                    "type": signal_type,
                    "entry_price": price,
                    "size": size,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                }

        await exchange.close()

        # Анализ результатов
        if not trades:
            return {
                'profit_factor': 0,
                'win_rate': 0,
                'total_trades': 0,
                'total_pnl': 0,
                'roi': 0,
                'avg_win': 0,
                'avg_loss': 0
            }

        df_trades = pd.DataFrame(trades)
        wins = df_trades[df_trades['pnl'] > 0]
        losses = df_trades[df_trades['pnl'] <= 0]

        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 0
        pf = avg_win / avg_loss if avg_loss > 0 else 0

        win_rate = len(wins) / len(df_trades) * 100 if len(df_trades) > 0 else 0
        total_pnl = df_trades['pnl'].sum()
        roi = (current_capital - initial_capital) / initial_capital * 100

        return {
            'profit_factor': pf,
            'win_rate': win_rate,
            'total_trades': len(df_trades),
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'roi': roi
        }

    def _analyze_results(self):
        """Анализирует результаты grid search"""

        print("\n" + "=" * 70)
        print("📊 GRID SEARCH RESULTS ANALYSIS")
        print("=" * 70)

        # Сортируем по Profit Factor
        sorted_results = sorted(
            self.results,
            key=lambda x: x['result'].get('profit_factor', 0),
            reverse=True
        )

        # Топ 10 конфигураций
        print("\n🏆 TOP 10 CONFIGURATIONS:\n")

        for rank, item in enumerate(sorted_results[:10], 1):
            config = item['config']
            result = item['result']

            sl = config.get('sl_multiplier', '?')
            tp = config.get('tp_multiplier', '?')

            print(f"{rank}. SL={sl}x, TP={tp}x (RR={tp/sl if isinstance(sl, (int,float)) and isinstance(tp, (int,float)) else '?'})")
            print(f"   ├─ Profit Factor: {result.get('profit_factor', 0):.2f}")
            print(f"   ├─ Win Rate: {result.get('win_rate', 0):.1f}%")
            print(f"   ├─ Avg Win: ${result.get('avg_win', 0):.2f}")
            print(f"   ├─ Avg Loss: ${result.get('avg_loss', 0):.2f}")
            print(f"   ├─ Trades: {result.get('total_trades', 0)}")
            print(f"   └─ ROI: {result.get('roi', 0):.2f}%\n")

        # Лучшая конфигурация
        if self.best_config:
            print(f"\n✅ BEST CONFIGURATION:")
            print(f"   Profit Factor: {self.best_pf:.2f} ⭐")
            print(f"   Config: {self.best_config}")

        # Сохраняем результаты
        self._save_results(sorted_results)

        return sorted_results[0] if sorted_results else None

    def _save_results(self, results):
        """Сохраняет результаты grid search"""

        os.makedirs('tests/results/grid_search', exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV результаты
        data = []
        for item in results:
            row = item['config'].copy()

            # Flatten disabled_scenarios list
            if 'disabled_scenarios' in row and isinstance(row['disabled_scenarios'], list):
                row['disabled_scenarios'] = ','.join(row['disabled_scenarios'])

            row.update(item['result'])
            data.append(row)

        df = pd.DataFrame(data)
        csv_path = f"tests/results/grid_search/sl_tp_grid_{timestamp}.csv"
        df.to_csv(csv_path, index=False)

        print(f"\n💾 Results saved: {csv_path}")

        return csv_path


async def main():
    """Main entry point"""

    optimizer = GridSearchOptimizer()

    # ✅ Phase 2: SL/TP Optimization
    print("\n🚀 PHASE 2: SL/TP Optimization (16 configs)")
    print("⏰ This will take ~60-90 minutes\n")

    await optimizer.run_grid_search('sl_tp_optimization')


if __name__ == "__main__":
    asyncio.run(main())
