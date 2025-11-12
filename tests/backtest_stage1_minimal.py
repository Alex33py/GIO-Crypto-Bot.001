"""
STAGE 1 BACKTEST: Full Test - All Scenarios from JSON
Тестирование всех сценариев из gio_scenarios_100_with_features_v3.json
"""

import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os


class MinimalBacktest:
    """Бектест для всех сценариев из JSON"""

    def __init__(self):
        # Параметры
        self.symbol = "BTC/USDT"
        self.timeframe = "1h"
        self.period_days = 30
        self.initial_capital = 10000
        self.position_size = 0.02  # 2% на сделку

        # Загрузка сценариев из JSON
        self.scenarios = self.load_scenarios_from_json()

        print(f"📊 Loaded {len(self.scenarios)} scenarios from JSON")

        # Биржа
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })

        # Результаты
        self.trades = []
        self.current_capital = self.initial_capital
        self.open_position = None

        print("✅ Minimal Backtest initialized")
        print(f"💰 Capital: ${self.initial_capital:,.0f}")
        print(f"📊 Testing: {len(self.scenarios)} scenarios")

    def load_scenarios_from_json(self):
        """Загрузка сценариев из JSON файла"""
        try:
            # Возможные пути к JSON файлу
            possible_paths = [
                "gio_scenarios_100_with_features_v3.json",
                "data/scenarios/gio_scenarios_100_with_features_v3.json",
                "../data/scenarios/gio_scenarios_100_with_features_v3.json",
                "../../data/scenarios/gio_scenarios_100_with_features_v3.json"
            ]

            scenarios_data = None
            loaded_path = None

            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        scenarios_data = json.load(f)
                    loaded_path = path
                    print(f"✅ JSON loaded from: {path}")
                    break

            if not scenarios_data:
                print("⚠️ JSON file not found, using fallback scenario names")
                return self._get_fallback_scenarios()

            # Извлекаем сценарии из JSON
            scenarios = []

            # Формат: {"scenarios": [...]}
            if isinstance(scenarios_data, dict) and 'scenarios' in scenarios_data:
                for scenario in scenarios_data['scenarios']:
                    scenario_id = scenario.get('id', '')
                    direction = scenario.get('tactics', {}).get('direction', '')

                    if scenario_id:
                        # Сохраняем ID и направление для логики
                        scenarios.append({
                            'id': scenario_id,
                            'direction': direction,
                            'name': scenario_id  # Для совместимости
                        })

            # Формат: [{...}, {...}]
            elif isinstance(scenarios_data, list):
                for scenario in scenarios_data:
                    scenario_id = scenario.get('id', '')
                    direction = scenario.get('tactics', {}).get('direction', '')

                    if scenario_id:
                        scenarios.append({
                            'id': scenario_id,
                            'direction': direction,
                            'name': scenario_id
                        })

            print(f"✅ Parsed {len(scenarios)} scenarios from JSON")
            return scenarios if scenarios else self._get_fallback_scenarios()

        except Exception as e:
            print(f"⚠️ Error loading JSON: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_scenarios()

    def _get_fallback_scenarios(self):
        """Fallback: 12 базовых сценариев если JSON недоступен"""
        return [
            {'id': 'MM_BREAKOUT_TRAP', 'direction': 'short', 'name': 'MM_BREAKOUT_TRAP'},
            {'id': 'DISTRIBUTION_SHORT', 'direction': 'short', 'name': 'DISTRIBUTION_SHORT'},
            {'id': 'ACCUMULATION_LONG', 'direction': 'long', 'name': 'ACCUMULATION_LONG'},
            {'id': 'LIQUIDITY_GRAB_LONG', 'direction': 'long', 'name': 'LIQUIDITY_GRAB_LONG'},
            {'id': 'LIQUIDITY_GRAB_SHORT', 'direction': 'short', 'name': 'LIQUIDITY_GRAB_SHORT'},
            {'id': 'WYCKOFF_SPRING_LONG', 'direction': 'long', 'name': 'WYCKOFF_SPRING_LONG'},
            {'id': 'UPTHRUST_SHORT', 'direction': 'short', 'name': 'UPTHRUST_SHORT'},
            {'id': 'CONSOLIDATION_BREAKOUT', 'direction': 'long', 'name': 'CONSOLIDATION_BREAKOUT'},
            {'id': 'FALSE_BREAKOUT_REVERSAL', 'direction': 'short', 'name': 'FALSE_BREAKOUT_REVERSAL'},
            {'id': 'VOLUME_CLIMAX_REVERSAL', 'direction': 'short', 'name': 'VOLUME_CLIMAX_REVERSAL'},
            {'id': 'RANGE_BOUND_FADE', 'direction': 'short', 'name': 'RANGE_BOUND_FADE'},
            {'id': 'TREND_CONTINUATION', 'direction': 'long', 'name': 'TREND_CONTINUATION'}
        ]

    async def fetch_data(self):
        """Загрузка исторических данных"""
        print(f"\n📥 Fetching {self.period_days} days of {self.symbol}...")

        since = self.exchange.parse8601(
            (datetime.now() - timedelta(days=self.period_days)).isoformat()
        )

        all_candles = []
        while True:
            candles = await self.exchange.fetch_ohlcv(
                self.symbol,
                self.timeframe,
                since=since,
                limit=1000
            )

            if not candles:
                break

            all_candles.extend(candles)
            since = candles[-1][0] + 1

            if len(candles) < 1000:
                break

        df = pd.DataFrame(
            all_candles,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        print(f"✅ Loaded {len(df)} candles")
        return df

    def calculate_indicators(self, df, idx):
        """Расчёт индикаторов для текущей свечи"""
        lookback = min(100, idx)
        data = df.iloc[max(0, idx-lookback):idx+1]

        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50

        # Volume
        avg_volume = data['volume'].rolling(window=20).mean().iloc[-1]
        current_volume = data['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # Trend (простой EMA)
        ema_20 = data['close'].ewm(span=20).mean().iloc[-1]
        current_price = data['close'].iloc[-1]
        trend = "BULLISH" if current_price > ema_20 else "BEARISH"

        return {
            'rsi': current_rsi,
            'volume_ratio': volume_ratio,
            'trend': trend,
            'price': current_price
        }

    def generate_signal(self, indicators, scenario):
        """Генерация сигнала на основе сценария"""
        rsi = indicators['rsi']
        vol_ratio = indicators['volume_ratio']
        trend = indicators['trend']

        scenario_id = scenario['id'] if isinstance(scenario, dict) else scenario
        scenario_direction = scenario.get('direction', 'long') if isinstance(scenario, dict) else 'long'

        # Простая логика на основе direction из JSON
        confidence = 50
        signal_type = None

        # Для long сценариев
        if scenario_direction == 'long':
            if rsi < 40 and trend == "BULLISH" and vol_ratio > 1.2:
                confidence = 70
                signal_type = "LONG"
            elif rsi < 35:
                confidence = 65
                signal_type = "LONG"

        # Для short сценариев
        elif scenario_direction == 'short':
            if rsi > 60 and trend == "BEARISH" and vol_ratio > 1.2:
                confidence = 70
                signal_type = "SHORT"
            elif rsi > 65:
                confidence = 65
                signal_type = "SHORT"

        # BREAKOUT по названию
        if "BREAKOUT" in scenario_id.upper():
            if vol_ratio > 1.5:
                confidence = 68
                signal_type = "LONG" if trend == "BULLISH" else "SHORT"

        # REVERSAL по названию
        if "REVERSAL" in scenario_id.upper():
            if rsi > 70:
                confidence = 65
                signal_type = "SHORT"
            elif rsi < 30:
                confidence = 65
                signal_type = "LONG"

        if confidence >= 60 and signal_type:
            return {
                'type': signal_type,
                'confidence': confidence,
                'scenario': scenario_id
            }

        return None

    def execute_trade(self, signal, price, timestamp):
        """Выполнение сделки"""
        # Закрываем существующую позицию если противоположный сигнал
        if self.open_position:
            if self.open_position['type'] != signal['type']:
                self.close_position(price, timestamp, 'SIGNAL_EXIT')

        # Открываем новую позицию
        if not self.open_position:
            position_value = self.current_capital * self.position_size
            size = position_value / price

            self.open_position = {
                'type': signal['type'],
                'scenario': signal['scenario'],
                'entry_price': price,
                'size': size,
                'entry_time': timestamp,
                'confidence': signal['confidence'],
                'stop_loss': price * 0.97 if signal['type'] == 'LONG' else price * 1.03,
                'take_profit': price * 1.05 if signal['type'] == 'LONG' else price * 0.95
            }

    def close_position(self, price, timestamp, reason):
        """Закрытие позиции"""
        if not self.open_position:
            return

        pos = self.open_position

        # Расчёт PnL
        if pos['type'] == 'LONG':
            pnl = (price - pos['entry_price']) * pos['size']
        else:
            pnl = (pos['entry_price'] - price) * pos['size']

        self.current_capital += pnl

        pnl_pct = (pnl / (pos['entry_price'] * pos['size'])) * 100

        # Сохраняем сделку
        self.trades.append({
            'scenario': pos['scenario'],
            'type': pos['type'],
            'entry_time': pos['entry_time'],
            'exit_time': timestamp,
            'entry_price': pos['entry_price'],
            'exit_price': price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'confidence': pos['confidence'],
            'exit_reason': reason
        })

        self.open_position = None

    def check_stop_take(self, price, timestamp):
        """Проверка SL/TP"""
        if not self.open_position:
            return

        pos = self.open_position

        if pos['type'] == 'LONG':
            if price <= pos['stop_loss']:
                self.close_position(pos['stop_loss'], timestamp, 'STOP_LOSS')
            elif price >= pos['take_profit']:
                self.close_position(pos['take_profit'], timestamp, 'TAKE_PROFIT')
        else:
            if price >= pos['stop_loss']:
                self.close_position(pos['stop_loss'], timestamp, 'STOP_LOSS')
            elif price <= pos['take_profit']:
                self.close_position(pos['take_profit'], timestamp, 'TAKE_PROFIT')

    async def run(self):
        """Основной цикл"""
        print("\n🚀 Starting backtest...\n")

        # Загрузка данных
        df = await self.fetch_data()

        # Прогрев индикаторов
        warmup = 100
        print(f"🔥 Warming up ({warmup} candles)...")
        print(f"📊 Testing on {len(df) - warmup} candles...\n")

        # Основной цикл
        for i in range(warmup, len(df)):
            current_candle = df.iloc[i]
            price = current_candle['close']
            timestamp = current_candle['timestamp']

            # Проверка SL/TP
            self.check_stop_take(price, timestamp)

            # Индикаторы
            indicators = self.calculate_indicators(df, i)

            # Генерация сигналов по всем сценариям
            for scenario in self.scenarios:
                signal = self.generate_signal(indicators, scenario)
                if signal:
                    self.execute_trade(signal, price, timestamp)
                    break  # Один сигнал за свечу

            # Прогресс
            if i % 100 == 0:
                progress = ((i - warmup) / (len(df) - warmup)) * 100
                print(f"⏳ {progress:.1f}% | Trades: {len(self.trades)} | Capital: ${self.current_capital:,.0f}")

        # Закрываем открытую позицию
        if self.open_position:
            final_price = df.iloc[-1]['close']
            final_time = df.iloc[-1]['timestamp']
            self.close_position(final_price, final_time, 'BACKTEST_END')

        print("\n✅ Backtest completed!\n")

        # Анализ
        self.print_results()
        self.save_results()

    def print_results(self):
        """Вывод результатов"""
        if not self.trades:
            print("❌ No trades executed")
            return

        df_trades = pd.DataFrame(self.trades)

        # Метрики
        total_trades = len(df_trades)
        wins = df_trades[df_trades['pnl'] > 0]
        losses = df_trades[df_trades['pnl'] <= 0]

        win_rate = len(wins) / total_trades * 100
        total_pnl = df_trades['pnl'].sum()
        roi = (self.current_capital - self.initial_capital) / self.initial_capital * 100

        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses['pnl'].mean()) if len(losses) > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

        # По сценариям
        by_scenario = df_trades.groupby('scenario').agg({
            'pnl': ['count', 'sum', lambda x: (x > 0).sum()]
        })
        by_scenario.columns = ['trades', 'pnl', 'wins']
        by_scenario['win_rate'] = (by_scenario['wins'] / by_scenario['trades'] * 100).round(1)
        by_scenario = by_scenario.sort_values('win_rate', ascending=False)

        # Печать
        print("="*70)
        print(f"  🎯 BACKTEST RESULTS - {len(self.scenarios)} SCENARIOS")
        print("="*70)
        print(f"\n📊 OVERALL:")
        print(f"├─ Trades: {total_trades} ({len(wins)} wins, {len(losses)} losses)")
        print(f"├─ Win Rate: {win_rate:.1f}% {'✅' if win_rate >= 55 else '❌'}")
        print(f"├─ Total PnL: ${total_pnl:,.2f}")
        print(f"├─ ROI: {roi:.2f}%")
        print(f"├─ Avg Win: ${avg_win:,.2f}")
        print(f"├─ Avg Loss: ${avg_loss:,.2f}")
        print(f"└─ Profit Factor: {profit_factor:.2f} {'✅' if profit_factor >= 1.5 else '❌'}")

        print(f"\n📈 TOP 10 BEST:")
        for i, (sc, row) in enumerate(by_scenario.head(10).iterrows(), 1):
            status = "✅" if row['win_rate'] >= 55 else "⚠️"
            print(f"{i}. {status} {sc}: {int(row['wins'])}/{int(row['trades'])} ({row['win_rate']:.1f}%) | ${row['pnl']:,.0f}")

        print(f"\n📉 TOP 10 WORST:")
        for i, (sc, row) in enumerate(by_scenario.tail(10).iterrows(), 1):
            print(f"{i}. ❌ {sc}: {int(row['wins'])}/{int(row['trades'])} ({row['win_rate']:.1f}%) | ${row['pnl']:,.0f}")

        print("\n" + "="*70 + "\n")

    def save_results(self):
        """Сохранение результатов"""
        if not self.trades:
            return

        os.makedirs("tests/results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV со всеми сделками
        df_trades = pd.DataFrame(self.trades)
        csv_path = f"tests/results/backtest_all_scenarios_{timestamp}.csv"
        df_trades.to_csv(csv_path, index=False)

        # Сводка по сценариям
        by_scenario = df_trades.groupby('scenario').agg({
            'pnl': ['count', 'sum', lambda x: (x > 0).sum()]
        })
        by_scenario.columns = ['trades', 'total_pnl', 'wins']
        by_scenario['win_rate'] = (by_scenario['wins'] / by_scenario['trades'] * 100).round(1)
        by_scenario = by_scenario.sort_values('win_rate', ascending=False)

        scenario_csv = f"tests/results/scenarios_summary_{timestamp}.csv"
        by_scenario.to_csv(scenario_csv)

        print(f"💾 All trades: {csv_path}")
        print(f"💾 Scenario summary: {scenario_csv}")

    async def cleanup(self):
        """Закрытие соединений"""
        await self.exchange.close()


async def main():
    backtest = MinimalBacktest()
    try:
        await backtest.run()
    finally:
        await backtest.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
