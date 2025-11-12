# -*- coding: utf-8 -*-
"""
ФИНАЛЬНЫЙ BACKTEST: ТОП-1 конфигурация
SL=1.2x TP=3.0x ADX=20-70 RSI=40-70 Vol=1.0x EMA=True
"""

import pandas as pd
import numpy as np
import ta
from datetime import datetime
import os


class FinalBacktest:
    """Финальный backtest с ТОП-1 параметрами"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.trades = []

    def load_and_prep(self):
        """Загрузка + индикаторы"""
        self.df = pd.read_csv(self.csv_path)

        atr_ind = ta.volatility.AverageTrueRange(
            self.df['high'], self.df['low'], self.df['close'], window=14
        )
        self.df['atr'] = atr_ind.average_true_range()

        adx_ind = ta.trend.ADXIndicator(
            self.df['high'], self.df['low'], self.df['close'], window=14
        )
        self.df['adx'] = adx_ind.adx()

        self.df['volume_sma'] = self.df['volume'].rolling(window=20, min_periods=1).mean()
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], window=14).rsi()
        self.df['ema_20'] = self.df['close'].ewm(span=20, adjust=False).mean()
        self.df['ema_50'] = self.df['close'].ewm(span=50, adjust=False).mean()

        print("✅ Индикаторы рассчитаны!")

    def backtest_top1(self):
        """ФИНАЛЬНЫЙ BACKTEST с ТОП-1 параметрами"""

        # ТОП-1 конфигурация
        SL_MULT = 1.2
        TP_MULT = 3.0
        MIN_ADX = 20
        MAX_ADX = 70
        MIN_RSI = 40
        MAX_RSI = 70
        MIN_VOL_MULT = 1.0
        USE_EMA = True

        print("\n" + "="*80)
        print("🏆 ФИНАЛЬНЫЙ BACKTEST: ТОП-1 КОНФИГУРАЦИЯ")
        print("="*80)
        print(f"✅ SL={SL_MULT}x TP={TP_MULT}x")
        print(f"✅ ADX: {MIN_ADX}-{MAX_ADX} RSI: {MIN_RSI}-{MAX_RSI} Vol: {MIN_VOL_MULT}x")
        print(f"✅ EMA Filter: {USE_EMA}")
        print("="*80 + "\n")

        position = None
        trade_num = 0

        for i in range(100, len(self.df)):
            row = self.df.iloc[i]

            # ВХОД
            if position is None:
                try:
                    # Фильтры
                    if pd.isna(row['adx']) or not (MIN_ADX <= row['adx'] <= MAX_ADX):
                        continue

                    if pd.isna(row['volume_sma']) or row['volume_sma'] == 0:
                        continue
                    vol_ratio = row['volume'] / row['volume_sma']
                    if vol_ratio < MIN_VOL_MULT:
                        continue

                    if pd.isna(row['rsi']) or not (MIN_RSI <= row['rsi'] <= MAX_RSI):
                        continue

                    if USE_EMA:
                        if not (row['close'] > row['ema_20'] > row['ema_50']):
                            continue

                    # ВХОД
                    trade_num += 1
                    atr_value = row['atr']

                    position = {
                        'trade_num': trade_num,
                        'entry_time': row['timestamp'],
                        'entry_price': row['close'],
                        'entry_atr': atr_value,
                        'entry_adx': row['adx'],
                        'entry_rsi': row['rsi'],
                        'entry_bar': i,
                        'tp': row['close'] + (atr_value * TP_MULT),
                        'sl': row['close'] - (atr_value * SL_MULT),
                    }

                    print(f"[{trade_num:2d}] ENTRY @ ${row['close']:>10.2f} | ADX={row['adx']:>5.1f} RSI={row['rsi']:>5.1f} Vol={vol_ratio:>4.2f}x")

                except:
                    continue

            # ВЫХОД
            elif position is not None:
                try:
                    tp = position['tp']
                    sl = position['sl']

                    if row['high'] >= tp:
                        exit_price = tp
                        exit_reason = "TP"
                    elif row['low'] <= sl:
                        exit_price = sl
                        exit_reason = "SL"
                    else:
                        continue

                    pnl = exit_price - position['entry_price']
                    pnl_pct = (pnl / position['entry_price']) * 100
                    duration_bars = i - position['entry_bar']

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
                        'tp_level': position['tp'],
                        'sl_level': position['sl'],
                        'result': 'WIN' if pnl > 0 else 'LOSS',
                    })

                    status = "✅" if pnl > 0 else "❌"
                    print(f"    EXIT @ ${exit_price:>10.2f} | {exit_reason} | {status} {pnl_pct:+6.2f}% ({duration_bars}h)")

                    position = None

                except:
                    continue

        print(f"\n✅ Завершено! Всего сделок: {len(self.trades)}")

    def print_metrics(self):
        """Метрики"""
        if not self.trades:
            print("❌ Нет сделок!")
            return

        df_trades = pd.DataFrame(self.trades)

        wins = df_trades[df_trades['result'] == 'WIN']
        losses = df_trades[df_trades['result'] == 'LOSS']

        win_rate = (len(wins) / len(df_trades)) * 100
        total_wins = wins['pnl'].sum()
        total_losses = abs(losses['pnl'].sum()) if len(losses) > 0 else 1
        pf = total_wins / total_losses if total_losses > 0 else 0

        avg_win = wins['pnl_pct'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_pct'].mean() if len(losses) > 0 else 0

        print("\n" + "="*80)
        print("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        print("="*80)
        print(f"📈 Trades: {len(df_trades)}")
        print(f"✅ Wins: {len(wins)} ({win_rate:.1f}%)")
        print(f"❌ Losses: {len(losses)} ({100-win_rate:.1f}%)")
        print(f"💰 Avg Win: {avg_win:+.2f}%")
        print(f"💸 Avg Loss: {avg_loss:.2f}%")
        print(f"⏱️ Avg Duration: {df_trades['duration_bars'].mean():.1f}h")
        print(f"\n🏆 Profit Factor: {pf:.2f}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print("="*80)

        # Сохранить
        os.makedirs("systems/results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"systems/results/backtest_final_{timestamp}.csv"
        df_trades.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 Сохранено: {filename}\n")

    def run(self):
        self.load_and_prep()
        self.backtest_top1()
        self.print_metrics()


if __name__ == "__main__":
    backtest = FinalBacktest("data/historical/BTCUSDT_1h_90d.csv")
    backtest.run()
