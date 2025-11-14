# -*- coding: utf-8 -*-
"""
ДЕНЬ 5: COMPLETE GRID SEARCH OPTIMIZER
Расширенная версия с RSI, ADX, Volume + полной статистикой
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import json
from itertools import product

import ccxt.async_support as ccxt
from core.scenario_matcher import UnifiedScenarioMatcher as ScenarioMatcher
from tests.market_data_simulator import MarketDataSimulator
from analytics.advanced_indicators import AdvancedIndicators


class GridSearchOptimizerDay5:
    """Полный Grid Search для Day 5"""

    def __init__(self):
        self.results = []
        self.best_config = None
        self.best_score = 0

    # ===== РАСШИРЕННАЯ КОНФИГУРАЦИЯ =====

    GRID_CONFIG = {
        'complete_optimization': {
            'sl_multiplier': [1.0, 1.2, 1.5],      # 3 варианта
            'tp_multiplier': [2.0, 2.5, 3.0, 3.5], # 4 варианта
            'min_adx': [20, 25, 28],               # 3 варианта
            'rsi_min': [35, 40],                   # 2 варианта
            'rsi_max': [65, 70],                   # 2 варианта
            'volume_mult': [0.8, 1.0, 1.2],        # 3 варианта
            'disabled_scenarios': [['SCN_024', 'SCN_023']]
        },
    }

    async def run_complete_search(self):
        """Запуск полной оптимизации"""

        print("\n" + "="*100)
        print("🚀 DAY 5: COMPLETE GRID SEARCH OPTIMIZATION")
        print("="*100 + "\n")

        grid = self.GRID_CONFIG['complete_optimization']

        # Генерация всех комбинаций
        sl_mults = grid['sl_multiplier']
        tp_mults = grid['tp_multiplier']
        adx_vals = grid['min_adx']
        rsi_mins = grid['rsi_min']
        rsi_maxs = grid['rsi_max']
        vol_mults = grid['volume_mult']
        disabled = grid['disabled_scenarios'][0]

        configs = []
        for sl_price, tp, adx, rsi_min, rsi_max, vol in product(
            sl_mults, tp_mults, adx_vals, rsi_mins, rsi_maxs, vol_mults
        ):
            if rsi_min >= rsi_max:
                continue

            configs.append({
                'sl_multiplier': sl_price,
                'tp_multiplier': tp,
                'min_adx': adx,
                'rsi_min': rsi_min,
                'rsi_max': rsi_max,
                'volume_mult': vol,
                'disabled_scenarios': disabled,
            })

        total = len(configs)
        print(f"📊 Generated {total} configurations to test")
        print(f"⏰ Estimated time: {total * 2:.0f} seconds (~{total * 2 / 60:.0f} minutes)\n")

        # Запускаем тесты
        for i, config in enumerate(configs, 1):
            print(f"⏳ [{i}/{total}] Testing config:")
            print(f"   SL={config['sl_multiplier']:.1f}x, TP={config['tp_multiplier']:.1f}x, "
                  f"ADX={config['min_adx']}, RSI={config['rsi_min']}-{config['rsi_max']}, "
                  f"Vol={config['volume_mult']:.1f}x")

            # Backtest
            result = await self._run_backtest_with_config(config)

            # Scoring system
            score = self._calculate_score(result)

            self.results.append({
                'config': config,
                'result': result,
                'score': score,
                'timestamp': datetime.now()
            })

            print(f"   ├─ WR: {result['win_rate']:.1f}% | PF: {result['profit_factor']:.2f} | "
                  f"Sharpe: {result['sharpe']:.2f} | Score: {score:.2f}")

            if score > self.best_score:
                self.best_score = score
                self.best_config = config
                print(f"   └─ ✅ NEW BEST! (Score: {score:.2f})")
            else:
                print(f"   └─ Score: {score:.2f}")

            print()

        return self._analyze_results()

    async def _run_backtest_with_config(self, config):
        """Запуск backtest с конкретной конфигурацией"""

        symbol = "BTC/USDT"
        timeframe = "1h"
        period_days = 30
        initial_capital = 10000
        position_size = 0.02

        # Параметры из config
        sl_mult = config['sl_multiplier']
        tp_mult = config['tp_multiplier']
        min_adx = config['min_adx']
        rsi_min = config['rsi_min']
        rsi_max = config['rsi_max']
        volume_mult = config['volume_mult']
        disabled = config['disabled_scenarios']

        # Компоненты
        matcher = ScenarioMatcher()
        simulator = MarketDataSimulator(seed=42)
        exchange = ccxt.binance({
            "enableRateLimit": True,
            "options": {"defaultType": "future"}
        })

        # Загрузка данных
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
                    pnl_pct = (pnl / (pos["entry_price"] * pos["size"])) * 100

                    trades.append({
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "exit_reason": "SL" if hit_sl else "TP"
                    })

                    open_position = None

            # Generate signal
            full_market_data = simulator.generate_full_market_data(df, i, {})

            highs = full_market_data.get('highs', [])
            lows = full_market_data.get('lows', [])
            closes = full_market_data.get('closes', [])

            # ADX
            if len(closes) >= 15:
                adx_result = AdvancedIndicators.calculate_adx(
                    highs=highs, lows=lows, closes=closes, period=14
                )
                full_market_data['indicators']['adx'] = adx_result.get('adx', 0)

            # RSI (simplified)
            if len(closes) >= 15:
                close_series = pd.Series(closes)
                delta = close_series.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = -delta.where(delta < 0, 0).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                full_market_data['indicators']['rsi'] = rsi.iloc[-1] if not rsi.empty else 50

            signal = matcher.match_scenario(
                symbol=symbol,
                market_data=full_market_data,
                indicators=full_market_data["indicators"],
                mtf_trends=full_market_data["mtf_trends"],
                volume_profile=full_market_data["volume_profile"],
                news_sentiment=full_market_data["news_sentiment"],
                veto_checks=full_market_data["veto_checks"],
            )

            # ФИЛЬТРЫ
            if signal:
                scenario_id = signal.get('scenario_id', '')

                # Disabled scenarios
                if scenario_id in disabled:
                    signal = None

                # ADX filter
                if signal and full_market_data['indicators'].get('adx', 0) < min_adx:
                    signal = None

                # RSI filter
                if signal:
                    rsi_val = full_market_data['indicators'].get('rsi', 50)
                    if rsi_val < rsi_min or rsi_val > rsi_max:
                        signal = None

                # Volume filter
                if signal:
                    vol_ratio = current_candle['volume'] / df['volume'].rolling(20).mean().iloc[i]
                    if vol_ratio < volume_mult:
                        signal = None

            # Execute trade
            if signal and not open_position:
                signal_type = signal.get("type", "LONG")
                atr = signal.get("atr", 100)

                if signal_type.upper() == "LONG":
                    stop_loss = price - (atr * sl_mult)
                    take_profit = price + (atr * tp_mult)
                else:
                    stop_loss = price + (atr * sl_mult)
                    take_profit = price - (atr * tp_mult)

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

        # Анализ
        if not trades:
            return {
                'profit_factor': 0,
                'win_rate': 0,
                'total_trades': 0,
                'roi': 0,
                'sharpe': 0,
                'avg_win': 0,
                'avg_loss': 0,
            }

        df_trades = pd.DataFrame(trades)
        wins = df_trades[df_trades['pnl'] > 0]
        losses = df_trades[df_trades['pnl'] <= 0]

        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 1
        pf = (wins['pnl'].sum() / abs(losses['pnl'].sum())) if len(losses) > 0 and losses['pnl'].sum() != 0 else 0

        win_rate = (len(wins) / len(df_trades)) * 100
        roi = ((current_capital - initial_capital) / initial_capital) * 100

        # Sharpe Ratio
        returns = df_trades['pnl_pct']
        sharpe = (returns.mean() / returns.std()) if returns.std() > 0 else 0

        return {
            'profit_factor': pf,
            'win_rate': win_rate,
            'total_trades': len(df_trades),
            'roi': roi,
            'sharpe': sharpe,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pnl': df_trades['pnl'].sum(),
        }

    def _calculate_score(self, result):
        """Комплексный scoring: WR + PF + Sharpe"""
        wr = result['win_rate']
        pf = result['profit_factor']
        sharpe = result['sharpe']

        # Normalize
        wr_norm = wr / 50  # Target 50%
        pf_norm = pf / 1.5  # Target 1.5
        sharpe_norm = sharpe / 1.5  # Target 1.5

        # Weighted score
        score = wr_norm * 0.4 + pf_norm * 0.35 + sharpe_norm * 0.25

        return score

    def _analyze_results(self):
        """Анализ результатов"""

        print("\n" + "="*100)
        print("📊 GRID SEARCH RESULTS ANALYSIS - DAY 5")
        print("="*100 + "\n")

        # Сортировка по score
        sorted_results = sorted(
            self.results,
            key=lambda x: x['score'],
            reverse=True
        )

        print("🏆 TOP 10 CONFIGURATIONS:\n")

        for rank, item in enumerate(sorted_results[:10], 1):
            config = item['config']
            result = item['result']
            score = item['score']

            print(f"{rank}. SL={config['sl_multiplier']:.1f}x, TP={config['tp_multiplier']:.1f}x, "
                  f"ADX={config['min_adx']}, RSI={config['rsi_min']}-{config['rsi_max']}, "
                  f"Vol={config['volume_mult']:.1f}x")
            print(f"   ├─ Score: {score:.2f} ⭐")
            print(f"   ├─ Win Rate: {result['win_rate']:.1f}%")
            print(f"   ├─ Profit Factor: {result['profit_factor']:.2f}")
            print(f"   ├─ Sharpe Ratio: {result['sharpe']:.2f}")
            print(f"   ├─ ROI: {result['roi']:.2f}%")
            print(f"   ├─ Trades: {result['total_trades']}")
            print(f"   └─ Avg Win/Loss: ${result['avg_win']:.2f} / ${result['avg_loss']:.2f}\n")

        # Best config
        print(f"✅ BEST CONFIGURATION (Score: {self.best_score:.2f}):")
        print(f"   {self.best_config}\n")

        # Save
        self._save_results(sorted_results)

        return sorted_results[0] if sorted_results else None

    def _save_results(self, results):
        """Сохранение результатов"""

        os.makedirs('data/optimization', exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV
        data = []
        for item in results:
            row = item['config'].copy()
            row['disabled_scenarios'] = ','.join(row['disabled_scenarios'])
            row.update(item['result'])
            row['score'] = item['score']
            data.append(row)

        df = pd.DataFrame(data)
        csv_path = f"data/optimization/day5_grid_search_{timestamp}.csv"
        df.to_csv(csv_path, index=False)

        # Best params JSON
        best = results[0]
        best_config = {
            "version": "v3.5-DAY5-OPTIMIZED",
            "timestamp": timestamp,
            "best_params": best['config'],
            "metrics": best['result'],
            "score": best['score']
        }

        json_path = "data/optimization/day5_best_params.json"
        with open(json_path, "w") as f:
            json.dump(best_config, f, indent=2)

        print(f"💾 Results saved:")
        print(f"   CSV: {csv_path}")
        print(f"   JSON: {json_path}\n")


async def main():
    """Main entry point"""

    optimizer = GridSearchOptimizerDay5()

    print("\n🚀 DAY 5: COMPLETE OPTIMIZATION")
    print("⏰ Estimated time: 30-60 minutes")
    print("📊 Testing: SL/TP + ADX + RSI + Volume\n")

    input("Press Enter to start...")

    await optimizer.run_complete_search()

    print("\n✅ DAY 5 OPTIMIZATION COMPLETE!")
    print("📋 Check: data/optimization/day5_best_params.json")


if __name__ == "__main__":
    asyncio.run(main())
