# -*- coding: utf-8 -*-
"""
ПРОДВИНУТАЯ ОПТИМИЗАЦИЯ
Найти РЕАЛЬНЫЕ рабочие параметры на полной выборке (90 дней)
"""

import pandas as pd
import numpy as np
import ta
from itertools import product
from datetime import datetime


class AdvancedOptimizer:
    """Продвинутая оптимизация параметров"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.results = []

    def load_and_prep(self):
        """Загрузка + индикаторы"""
        self.df = pd.read_csv(self.csv_path)

        # ATR
        atr_ind = ta.volatility.AverageTrueRange(
            self.df['high'], self.df['low'], self.df['close'], window=14
        )
        self.df['atr'] = atr_ind.average_true_range()

        # ADX
        adx_ind = ta.trend.ADXIndicator(
            self.df['high'], self.df['low'], self.df['close'], window=14
        )
        self.df['adx'] = adx_ind.adx()

        # Volume
        self.df['volume_sma'] = self.df['volume'].rolling(window=20, min_periods=1).mean()

        # RSI
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], window=14).rsi()

        # EMA
        self.df['ema_20'] = self.df['close'].ewm(span=20, adjust=False).mean()
        self.df['ema_50'] = self.df['close'].ewm(span=50, adjust=False).mean()

        print("✅ Индикаторы рассчитаны!")

    def backtest_config(self, sl_mult, tp_mult, min_adx, max_adx,
                       min_rsi, max_rsi, min_vol_mult, use_ema):
        """
        Backtest одной конфигурации

        Args:
            sl_mult: множитель SL от ATR
            tp_mult: множитель TP от ATR
            min_adx: минимальный ADX
            max_adx: максимальный ADX
            min_rsi: минимальный RSI
            max_rsi: максимальный RSI
            min_vol_mult: минимальный объём
            use_ema: использовать EMA фильтр
        """
        trades = []
        position = None

        for i in range(100, len(self.df)):
            row = self.df.iloc[i]

            # ВХОД
            if position is None:
                try:
                    # Фильтр ADX (диапазон!)
                    if pd.isna(row['adx']) or not (min_adx <= row['adx'] <= max_adx):
                        continue

                    # Фильтр Volume
                    if pd.isna(row['volume_sma']) or row['volume_sma'] == 0:
                        continue
                    vol_ratio = row['volume'] / row['volume_sma']
                    if vol_ratio < min_vol_mult:
                        continue

                    # Фильтр RSI
                    if pd.isna(row['rsi']) or not (min_rsi <= row['rsi'] <= max_rsi):
                        continue

                    # Фильтр EMA (опционально)
                    if use_ema:
                        if not (row['close'] > row['ema_20'] > row['ema_50']):
                            continue

                    # ВХОД
                    atr_value = row['atr']

                    position = {
                        'entry_price': row['close'],
                        'entry_bar': i,
                        'tp': row['close'] + (atr_value * tp_mult),
                        'sl': row['close'] - (atr_value * sl_mult),
                    }

                except:
                    continue

            # ВЫХОД
            elif position is not None:
                try:
                    tp = position['tp']
                    sl = position['sl']

                    # Проверка TP/SL
                    if row['high'] >= tp:
                        exit_price = tp
                    elif row['low'] <= sl:
                        exit_price = sl
                    else:
                        continue

                    # PnL
                    pnl = exit_price - position['entry_price']

                    trades.append({
                        'pnl': pnl,
                        'result': 'WIN' if pnl > 0 else 'LOSS',
                    })

                    position = None

                except:
                    continue

        # Анализ
        if len(trades) < 10:  # Минимум 10 сделок
            return None

        df_trades = pd.DataFrame(trades)

        wins = len(df_trades[df_trades['result'] == 'WIN'])
        losses = len(trades) - wins

        if losses == 0:
            return None

        win_rate = (wins / len(trades)) * 100

        # Profit Factor
        total_wins = df_trades[df_trades['result'] == 'WIN']['pnl'].sum()
        total_losses = abs(df_trades[df_trades['result'] == 'LOSS']['pnl'].sum())

        if total_losses == 0:
            pf = 0
        else:
            pf = total_wins / total_losses

        # Sharpe Ratio (упрощённый)
        sharpe = (df_trades['pnl'].mean() / df_trades['pnl'].std()) if df_trades['pnl'].std() > 0 else 0

        return {
            'sl_mult': sl_mult,
            'tp_mult': tp_mult,
            'min_adx': min_adx,
            'max_adx': max_adx,
            'min_rsi': min_rsi,
            'max_rsi': max_rsi,
            'min_vol_mult': min_vol_mult,
            'use_ema': use_ema,
            'trades': len(trades),
            'win_rate': win_rate,
            'pf': pf,
            'sharpe': sharpe,
            'score': (pf * 0.5) + (win_rate/100 * 0.3) + (sharpe * 0.2),  # Взвешенный score
        }

    def optimize_full(self):
        """Полная оптимизация"""
        print("\n" + "="*80)
        print("🔍 ПРОДВИНУТАЯ ОПТИМИЗАЦИЯ")
        print("="*80)
        print("Этап 1: Тестируем различные комбинации параметров...")
        print()

        # РАСШИРЕННЫЙ GRID SEARCH
        configs = list(product(
            [0.8, 1.0, 1.2, 1.5],      # SL multiplier
            [1.5, 2.0, 2.5, 3.0],      # TP multiplier
            [20, 25, 30],              # Min ADX
            [50, 60, 70],              # Max ADX (диапазон!)
            [30, 35, 40],              # Min RSI
            [60, 65, 70],              # Max RSI
            [0.6, 0.8, 1.0],           # Min Volume
            [False, True],             # Use EMA filter
        ))

        print(f"Всего конфигураций: {len(configs)}")
        print()

        tested = 0
        for sl, tp, min_adx, max_adx, min_rsi, max_rsi, vol, ema in configs:
            tested += 1

            result = self.backtest_config(
                sl, tp, min_adx, max_adx,
                min_rsi, max_rsi, vol, ema
            )

            if result and result['pf'] >= 1.3:  # Минимум PF 1.3
                self.results.append(result)

                if result['pf'] >= 1.5:  # Показать только лучшие
                    print(f"[{tested:4d}] ✅ PF={result['pf']:.2f} WR={result['win_rate']:.1f}% "
                          f"SL={sl}x TP={tp}x ADX={min_adx}-{max_adx} "
                          f"RSI={min_rsi}-{max_rsi} Vol={vol}x EMA={ema}")

            if tested % 100 == 0:
                print(f"   Progress: {tested}/{len(configs)} ({tested/len(configs)*100:.1f}%)")

        print(f"\n✅ Тестирование завершено! Найдено {len(self.results)} хороших конфигураций")

    def print_top_results(self):
        """Вывод топ-10 результатов"""
        if not self.results:
            print("\n❌ Не найдено хороших конфигураций!")
            return

        # Сортировка по score
        df = pd.DataFrame(self.results)
        df = df.sort_values('score', ascending=False)

        print("\n" + "="*80)
        print("🏆 ТОП-10 ЛУЧШИХ КОНФИГУРАЦИЙ")
        print("="*80)

        for i, (idx, row) in enumerate(df.head(10).iterrows(), 1):
            print(f"\n{i}. Score: {row['score']:.3f}")
            print(f"   SL={row['sl_mult']:.1f}x TP={row['tp_mult']:.1f}x")
            print(f"   ADX: {row['min_adx']:.0f}-{row['max_adx']:.0f}")
            print(f"   RSI: {row['min_rsi']:.0f}-{row['max_rsi']:.0f}")
            print(f"   Volume: {row['min_vol_mult']:.1f}x")
            print(f"   EMA Filter: {row['use_ema']}")
            print(f"   → WR={row['win_rate']:.1f}% PF={row['pf']:.2f} Trades={row['trades']:.0f}")

        print("\n" + "="*80)

        # Сохранить результаты
        import os
        os.makedirs("systems/results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"systems/results/optimizer_results_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Сохранено: {filename}\n")

    def run(self):
        """Execute"""
        self.load_and_prep()
        self.optimize_full()
        self.print_top_results()


if __name__ == "__main__":
    optimizer = AdvancedOptimizer("data/historical/BTCUSDT_1h_90d.csv")
    optimizer.run()
