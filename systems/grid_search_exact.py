# -*- coding: utf-8 -*-
"""
ТОЧНЫЙ GRID SEARCH BACKTEST - БЕЗ ЛИШНИХ ФИЛЬТРОВ
Только 2 фильтра:
1. ADX >= 20
2. Volume >= 0.6x
"""

import pandas as pd
import numpy as np
import ta
from datetime import datetime


class GridSearchExactCopy:
    """Точная копия Grid Search алгоритма"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.trades = []

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

        # Volume SMA
        self.df['volume_sma'] = self.df['volume'].rolling(window=20, min_periods=1).mean()

        # RSI (для информации)
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], window=14).rsi()

        print("✅ Индикаторы рассчитаны!")

    def backtest_grid_search_exact(self):
        """
        ТОЧНО КОПИРУЕМ Grid Search логику
        МИНИМУМ фильтров = максимум сделок
        """
        # ТОП-1 КОНФИГУРАЦИЯ
        SL_MULT = 1.2
        TP_MULT = 2.0
        MIN_ADX = 20.0
        MIN_VOL_MULT = 0.6

        print("\n" + "="*80)
        print("🎯 ТОЧНАЯ КОПИЯ GRID SEARCH")
        print("="*80)
        print(f"✅ МИНИМУМ фильтров:")
        print(f"   1. ADX >= {MIN_ADX}")
        print(f"   2. Volume >= {MIN_VOL_MULT}x")
        print(f"✅ SL={SL_MULT}x TP={TP_MULT}x")
        print("="*80 + "\n")

        position = None
        trade_num = 0

        for i in range(100, len(self.df)):  # Минимум warmup 100 баров
            row = self.df.iloc[i]

            # ВХОД
            if position is None:
                try:
                    # ✅ ФИЛЬТР 1: ADX >= 20 (РОВНО)
                    if pd.isna(row['adx']) or row['adx'] < MIN_ADX:
                        continue

                    # ✅ ФИЛЬТР 2: Volume >= 0.6x (РОВНО)
                    if pd.isna(row['volume_sma']) or row['volume_sma'] == 0:
                        continue
                    vol_ratio = row['volume'] / row['volume_sma']
                    if vol_ratio < MIN_VOL_MULT:
                        continue

                    # ✅ ВСЁ! Других фильтров нет!

                    trade_num += 1

                    atr_value = row['atr']

                    position = {
                        'trade_num': trade_num,
                        'entry_time': row['timestamp'],
                        'entry_price': row['close'],
                        'entry_atr': atr_value,
                        'entry_adx': row['adx'],
                        'entry_rsi': row['rsi'],
                        'entry_volume_ratio': vol_ratio,
                        'entry_bar': i,
                        'tp': row['close'] + (atr_value * TP_MULT),
                        'sl_price': row['close'] - (atr_value * SL_MULT),
                    }

                    print(f"[{trade_num:2d}] ENTRY @ ${row['close']:>10.2f} | ADX={row['adx']:>5.1f} Vol={vol_ratio:>4.2f}x")

                except Exception as e:
                    continue

            # ВЫХОД
            elif position is not None:
                try:
                    tp = position['tp']
                    sl_price = position['sl_price']

                    exit_price = None
                    exit_reason = None

                    # Проверка TP/SL
                    if row['high'] >= tp:
                        exit_reason = "TP"
                        exit_price = tp
                    elif row['low'] <= sl_price:
                        exit_reason = "SL"
                        exit_price = sl_price
                    else:
                        continue

                    # Расчёт PnL
                    pnl = exit_price - position['entry_price']
                    pnl_pct = (pnl / position['entry_price']) * 100
                    duration_bars = i - position['entry_bar']

                    # Сохранить
                    self.trades.append({
                        'trade_num': position['trade_num'],
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry_price'],
                        'exit_time': row['timestamp'],
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'duration_bars': duration_bars,
                        'entry_adx': position['entry_adx'],
                        'volume_ratio': position['entry_volume_ratio'],
                        'tp_level': position['tp'],
                        'sl_level': position['sl_price'],
                        'result': 'WIN' if pnl > 0 else 'LOSS',
                    })

                    status = "✅" if pnl > 0 else "❌"
                    print(f"        EXIT @ ${exit_price:>10.2f} | {exit_reason} | {status} {pnl_pct:+6.2f}% ({duration_bars}h)")

                    position = None

                except Exception as e:
                    continue

        print(f"\n✅ Завершено! Всего сделок: {len(self.trades)}")

    def print_metrics(self):
        """Вывод метрик"""
        if not self.trades:
            print("❌ Нет сделок!")
            return

        df_trades = pd.DataFrame(self.trades)

        wins = df_trades[df_trades['result'] == 'WIN']
        losses = df_trades[df_trades['result'] == 'LOSS']

        win_rate = (len(wins) / len(df_trades)) * 100

        # Profit Factor
        total_wins = wins['pnl'].sum()
        total_losses = abs(losses['pnl'].sum()) if len(losses) > 0 else 1
        pf = total_wins / total_losses if total_losses > 0 else 0

        avg_win = wins['pnl_pct'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_pct'].mean() if len(losses) > 0 else 0

        print("\n" + "="*80)
        print("📊 ФИНАЛЬНЫЕ МЕТРИКИ")
        print("="*80)
        print(f"📈 Всего сделок: {len(df_trades)}")
        print(f"✅ Побед: {len(wins)} ({win_rate:.1f}%)")
        print(f"❌ Убытков: {len(losses)} ({100-win_rate:.1f}%)")
        print(f"💰 Avg Win: {avg_win:+.2f}%")
        print(f"💸 Avg Loss: {avg_loss:.2f}%")
        print(f"⏱️ Avg Duration: {df_trades['duration_bars'].mean():.1f}h")
        print(f"\n🏆 Profit Factor: {pf:.2f}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print("="*80)

        # Проверка
        if abs(pf - 1.67) < 0.05:
            print("✅ СОВПАДАЕТ С GRID SEARCH! 🎉")
        elif pf > 1.5:
            print(f"✅ ХОРОШИЙ РЕЗУЛЬТАТ (PF = {pf:.2f})")
        else:
            print(f"⚠️ НИЗКИЙ РЕЗУЛЬТАТ (PF = {pf:.2f})")

        print()

        # Сохранить CSV
        import os
        os.makedirs("systems/results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"systems/results/trades_grid_exact_{timestamp}.csv"
        df_trades.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Сохранено: {filename}\n")

    def run(self):
        """Execute"""
        self.load_and_prep()
        self.backtest_grid_search_exact()
        self.print_metrics()


if __name__ == "__main__":
    backtest = GridSearchExactCopy("data/historical/BTCUSDT_1h_90d.csv")
    backtest.run()
