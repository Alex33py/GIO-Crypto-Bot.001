"""
🎯 FULL BACKTEST WITH SCENARIOS v2.1 — FIXED!
РЕАЛЬНО использует gio_scenarios_v35_enhanced.json
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import ta
from scenario_engine import ScenarioEngine
from modules.cvd_calculator import CVDCalculator


class FullBacktestWithScenarios:
    """Полный бектест со всеми сценариями"""

    def __init__(self):
        self.df_1h = None
        self.df_4h = None
        self.df_funding = None
        self.df_oi = None
        self.trades = []

        # ← АБСОЛЮТНЫЙ ПУТЬ!
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, 'data', 'scenarios', 'gio_scenarios_v35_enhanced.json')

        print(f"🔍 Loading scenarios from: {json_path}")

        self.engine = ScenarioEngine(json_path)
        self.cvd_calculator = CVDCalculator(window=20)

    def load_data(self):
        """Загрузить ВСЕ данные"""
        print("\n📂 Загрузка данных...")

        try:
            self.df_1h = pd.read_csv("data/historical/BTCUSDT_1h_30d.csv")
            self.df_1h['timestamp'] = pd.to_datetime(self.df_1h['timestamp'])
            print(f"✅ 1h: {len(self.df_1h)} свечей")

            self.df_4h = pd.read_csv("data/historical/BTCUSDT_4h_30d.csv")
            self.df_4h['timestamp'] = pd.to_datetime(self.df_4h['timestamp'])
            print(f"✅ 4h: {len(self.df_4h)} свечей")

            self.df_funding = pd.read_csv("data/historical/BTCUSDT_funding_30d.csv")
            print(f"✅ Funding: {len(self.df_funding)} записей")

            self.df_oi = pd.read_csv("data/historical/BTCUSDT_oi_30d.csv")
            print(f"✅ OI: {len(self.df_oi)} записей")

            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False

    def calculate_features(self):
        """Рассчитать ВСЕ метрики"""
        print("\n📊 Рассчёт метрик...")

        if self.df_1h is None:
            return

        # === 1H МЕТРИКИ ===
        df = self.df_1h.copy()

        # 1. RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

        # 2. MACD
        macd_indicator = ta.trend.MACD(df['close'])
        df['macd'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()

        # 3. Bollinger Bands
        bb_indicator = ta.volatility.BollingerBands(df['close'])
        df['bb_high'] = bb_indicator.bollinger_hband()
        df['bb_mid'] = bb_indicator.bollinger_mavg()
        df['bb_low'] = bb_indicator.bollinger_lband()

        # 4. ATR
        atr_indicator = ta.volatility.AverageTrueRange(
            df['high'], df['low'], df['close']
        )
        df['atr'] = atr_indicator.average_true_range()

        # 5. ADX
        adx_indicator = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
        df['adx'] = adx_indicator.adx()

        # 6. Volume SMA
        df['volume_sma'] = df['volume'].rolling(window=20).mean()

        self.df_1h = df

        # === 4H МЕТРИКИ ===
        df_4h = self.df_4h.copy()

        # RSI для 4h
        df_4h['rsi'] = ta.momentum.RSIIndicator(df_4h['close'], window=14).rsi()

        # ADX для 4h
        df_4h['adx'] = ta.trend.ADXIndicator(df_4h['high'], df_4h['low'], df_4h['close']).adx()

        # Bollinger Bands для 4h
        bb_4h = ta.volatility.BollingerBands(df_4h['close'])
        df_4h['bb_high'] = bb_4h.bollinger_hband()
        df_4h['bb_mid'] = bb_4h.bollinger_mavg()
        df_4h['bb_low'] = bb_4h.bollinger_lband()

        self.df_4h = df_4h

       # CVD Calculation for 1h
        self.df_1h = self.cvd_calculator.calculate_cvd(self.df_1h)
        print("✅ CVD рассчитан!")

        print("✅ Метрики рассчитаны (1h + 4h)!")

    def _get_trend(self, rsi, price, ema) -> str:
        """Определить trend"""
        if rsi > 65:
            return 'overbought'
        elif rsi < 35:
            return 'oversold'
        elif price > ema:
            return 'bullish'
        elif price < ema:
            return 'bearish'
        else:
            return 'neutral'

    def _build_market_data(self, row_1h, row_4h) -> dict:
        """Построить market_data для Scenario Engine"""

        # EMA для трендов
        try:
            ema_1h = self.df_1h['close'].rolling(20).mean().iloc[-1]
        except:
            ema_1h = row_1h['close']

        try:
            ema_4h = self.df_4h['close'].rolling(20).mean().iloc[-1]
        except:
            ema_4h = row_4h['close']

        trend_1h = self._get_trend(row_1h['rsi'], row_1h['close'], ema_1h)
        trend_4h = self._get_trend(row_4h['rsi'], row_4h['close'], ema_4h)

        return {
            'trend_1h': trend_1h,
            'trend_4h': trend_4h,
            'trend_1d': 'neutral',
            'adx_1h': row_1h['adx'],
            'adx_4h': row_4h['adx'],

            # ← НОВЫЕ CVD МЕТРИКИ! =================
            'cvd_trend': row_1h['cvd_trend'],
            'cvd_slope': row_1h['cvd_slope'],
            'cvd_confirms': bool(row_1h['cvd_confirms']),
            'cvd_normalized': row_1h['cvd_normalized'],
            # =======================================

            'volume_strength': row_1h['volume'] / row_1h['volume_sma'] if row_1h['volume_sma'] > 0 else 1.0,
            'cluster_score': 0.65,
            'funding_condition': 'neutral',
            'oi_trend': 'stable',
            'ls_ratio': 1.0,
            'close': row_1h['close'],
            'volume': row_1h['volume']
        }

    def scenario_signal_generator(self):
        """РЕАЛЬНО использует 24 сценария из JSON!"""
        print("\n🎯 Генерация сигналов через Scenario Engine...")

        df = self.df_1h.copy()
        df_4h = self.df_4h.copy()
        trades = []
        position = None
        last_exit_bar = -1000

        # Счетчик для DEBUG
        debug_counter = 0

        for i in range(50, len(df)):
            row = df.iloc[i]

            # Найти соответствующую 4h свечу
            current_time = row['timestamp']
            df_4h_row = df_4h[df_4h['timestamp'] <= current_time]

            if df_4h_row.empty:
                continue

            row_4h = df_4h_row.iloc[-1]

            # === ВХОД: Генерировать сигнал через Scenario Engine ===
            if position is None:
                # Построить market_data
                market_data = self._build_market_data(row, row_4h)

                if debug_counter < 3:
                    print(f"\n🔍 DEBUG #{debug_counter + 1}:")
                    print(f"  Time: {row['timestamp']}")
                    print(f"  Market Data: {market_data}")
                    debug_counter += 1

                # Генерировать сигнал
                signal = self.engine.generate_signal(market_data)

                # ← ВЕРНУЛ МЯГКИЕ ФИЛЬТРЫ!
                if signal:
                    # ФИЛЬТР 1: ADX > 12 (очень слабый тренд достаточен)
                    if row['adx'] < 12:
                        if debug_counter <= 3:
                            print(f"  ⏭️  SKIP: ADX={row['adx']:.1f} (<12)")
                        signal = None

                    # ФИЛЬТР 2: RSI extreme ТОЛЬКО >78 или <22
                    elif signal['opinion'] == 'bullish' and row['rsi'] > 78:
                        if debug_counter <= 3:
                            print(f"  ⏭️  SKIP LONG: RSI={row['rsi']:.1f} (>78)")
                        signal = None

                    elif signal['opinion'] == 'bearish' and row['rsi'] < 22:
                        if debug_counter <= 3:
                            print(f"  ⏭️  SKIP SHORT: RSI={row['rsi']:.1f} (<22)")
                        signal = None

                # ← DEEP DEBUG ДЛЯ ПЕРВЫХ 3 ИТЕРАЦИЙ!
                if debug_counter <= 3:
                    if signal:
                        print(f"  ✅ Signal: {signal}")
                    else:
                        print(f"  ❌ No signal generated")

                        # Проверь ВСЕ сценарии вручную
                        print(f"\n  🔎 DEEP DEBUG - Checking all scenarios:")
                        valid_results = []

                        for scenario in self.engine.scenarios:
                            result = self.engine.evaluate_scenario(scenario, market_data)

                            # Покажи первые 5 сценариев
                            if len(valid_results) < 5:
                                print(f"\n     Scenario: {scenario['id']}")
                                print(f"       Opinion: {scenario['opinion']}")
                                print(f"       Score: {result['score']:.3f}")
                                print(f"       Met: {result['met_conditions']}/{result['total_conditions']}")
                                print(f"       Min required: {scenario.get('min_metrics', 3)}")
                                print(f"       Status: {scenario.get('status', 'unknown')}")
                                print(f"       Is valid: {result['is_valid']}")

                            if result['is_valid']:
                                valid_results.append(result)

                        print(f"\n     ✅ Total VALID scenarios: {len(valid_results)}")

                        if valid_results:
                            best_valid = max(valid_results, key=lambda x: x['score'])
                            print(f"     🏆 Best valid scenario:")
                            print(f"        {best_valid['scenario_id']}: score={best_valid['score']:.3f}")
                            print(f"        Opinion: {best_valid['opinion']}")

                # ← ОТКРЫТЬ ПОЗИЦИЮ если есть сигнал (LONG ИЛИ SHORT)!
                if signal:
                    if signal['opinion'] == 'bullish':
                        position = {
                            'entry_time': row['timestamp'],
                            'entry_price': row['close'],
                            'entry_rsi': row['rsi'],
                            'atr': row['atr'],
                            'scenario_id': signal['scenario_id'],
                            'confidence': signal['confidence'],
                            'score': signal['score'],
                            'highest_price': row['close'],
                            'lowest_price': row['close'],
                            'opinion': signal['opinion'],
                            'direction': 'LONG'
                        }
                        print(f"  🟢 LONG: {row['timestamp']} @ ${row['close']:.2f}")
                        print(f"     {signal['scenario_id']} | Score: {signal['score']:.3f} | {signal['confidence']}")

                    elif signal['opinion'] == 'bearish':
                        position = {
                            'entry_time': row['timestamp'],
                            'entry_price': row['close'],
                            'entry_rsi': row['rsi'],
                            'atr': row['atr'],
                            'scenario_id': signal['scenario_id'],
                            'confidence': signal['confidence'],
                            'score': signal['score'],
                            'lowest_price': row['close'],
                            'highest_price': row['close'],
                            'opinion': signal['opinion'],
                            'direction': 'SHORT'
                        }
                        print(f"  🔴 SHORT: {row['timestamp']} @ ${row['close']:.2f}")
                        print(f"     {signal['scenario_id']} | Score: {signal['score']:.3f} | {signal['confidence']}")

            # === ВЫХОД ===
            elif position is not None:
                atr = position['atr']
                direction = position.get('direction', 'LONG')

                if direction == 'LONG':
                    # Обновить highest price
                    if row['close'] > position['highest_price']:
                        position['highest_price'] = row['close']

                    # TP/SL
                    tp = position['entry_price'] + atr * 4.0
                    sl = position['entry_price'] - atr * 2.0

                    # Trailing
                    price_gain = position['highest_price'] - position['entry_price']
                    if price_gain > atr * 1.5:
                        trailing_sl = position['highest_price'] - atr * 1.0
                        sl = max(sl, trailing_sl)

                    should_close = (row['rsi'] > 75 or row['close'] >= tp or row['close'] <= sl)

                elif direction == 'SHORT':
                    # Обновить lowest price
                    if row['close'] < position['lowest_price']:
                        position['lowest_price'] = row['close']

                    # TP/SL ДЛЯ SHORT
                    tp = position['entry_price'] - atr * 4.0
                    sl = position['entry_price'] + atr * 2.0

                    # Trailing ДЛЯ SHORT
                    price_loss = position['entry_price'] - position['lowest_price']
                    if price_loss > atr * 1.5:
                        trailing_sl = position['lowest_price'] + atr * 1.0
                        sl = min(sl, trailing_sl)

                    should_close = (row['rsi'] < 25 or row['close'] <= tp or row['close'] >= sl)

                if should_close:
                    # PnL с учётом направления
                    if direction == 'LONG':
                        pnl = row['close'] - position['entry_price']
                        highest_lowest = position['highest_price']
                    else:  # SHORT
                        pnl = position['entry_price'] - row['close']
                        highest_lowest = position['lowest_price']

                    pnl_pct = (pnl / position['entry_price']) * 100

                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': row['timestamp'],
                        'entry_price': position['entry_price'],
                        'exit_price': row['close'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'entry_rsi': position['entry_rsi'],
                        'exit_rsi': row['rsi'],
                        'highest_lowest': highest_lowest,
                        'scenario_id': position['scenario_id'],
                        'confidence': position['confidence'],
                        'score': position['score'],
                        'direction': direction
                    })

                    exit_reason = (
                        "RSI>75" if (direction == 'LONG' and row['rsi'] > 75) else
                        "RSI<25" if (direction == 'SHORT' and row['rsi'] < 25) else
                        "TP" if (direction == 'LONG' and row['close'] >= tp) or (direction == 'SHORT' and row['close'] <= tp) else
                        "SL"
                    )
                    print(f"  🔴 EXIT {direction}: {row['timestamp']} @ ${row['close']:.2f} | PnL: ${pnl:.2f} ({pnl_pct:.2f}%) [{exit_reason}]")

                    last_exit_bar = i
                    position = None

        print(f"✅ Завершено {len(trades)} сделок")
        self.trades = trades
        return pd.DataFrame(trades)

    def analyze_results(self):
        """Анализ результатов"""
        print("\n" + "="*80)
        print("📊 РЕЗУЛЬТАТЫ БЕКТЕСТА")
        print("="*80)

        if not self.trades:
            print("❌ Нет сделок!")
            return

        df = pd.DataFrame(self.trades)

        total_trades = len(df)
        winning = len(df[df['pnl'] > 0])
        losing = len(df[df['pnl'] < 0])

        win_rate = (winning / total_trades * 100) if total_trades > 0 else 0

        total_profit = df[df['pnl'] > 0]['pnl'].sum()
        total_loss = abs(df[df['pnl'] < 0]['pnl'].sum())

        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0

        total_pnl = df['pnl'].sum()
        avg_pnl_pct = df['pnl_pct'].mean()

        max_win = df['pnl'].max()
        max_loss = df['pnl'].min()

        print(f"\n📈 СТАТИСТИКА:")
        print(f"{'Всего сделок:':<30} {total_trades}")
        print(f"{'Прибыльных:':<30} {winning} ({win_rate:.1f}%)")
        print(f"{'Убыточных:':<30} {losing}")
        print(f"\n💰 ПРОФИЛЬ:")
        print(f"{'Profit Factor:':<30} {profit_factor:.2f}")
        print(f"{'Total PnL:':<30} ${total_pnl:.2f}")
        print(f"{'Avg PnL %:':<30} {avg_pnl_pct:.2f}%")
        print(f"{'Max Win:':<30} ${max_win:.2f}")
        print(f"{'Max Loss:':<30} ${max_loss:.2f}")

        # Статистика по сценариям
        print(f"\n🎯 СЦЕНАРИИ:")
        scenario_stats = df['scenario_id'].value_counts()
        print(scenario_stats.head(10))

        print("\n" + "="*80)

        # Сохранить результаты
        os.makedirs("tests/results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        df.to_csv(f"tests/results/trades_{timestamp}.csv", index=False)
        print(f"💾 Сохранено: tests/results/trades_{timestamp}.csv")

    def run(self):
        """Запустить полный бектест"""
        print("\n" + "="*80)
        print("🚀 FULL BACKTEST WITH SCENARIOS v2.1 — FIXED!")
        print("="*80)

        if not self.load_data():
            return

        self.calculate_features()

        # ← ИСПОЛЬЗУЙ НОВУЮ ФУНКЦИЮ!
        trades_df = self.scenario_signal_generator()

        if len(trades_df) == 0:
            print("❌ Нет сделок!")
            return

        self.analyze_results()


if __name__ == "__main__":
    backtest = FullBacktestWithScenarios()
    backtest.run()
