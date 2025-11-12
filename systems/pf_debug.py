# -*- coding: utf-8 -*-
"""
Debug PF Optimizer - проверка что происходит
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import ta

class PFDebug:
    """Debug optimizer"""

    def __init__(self):
        self.df = None

    def load_data(self):
        """Загрузить данные"""
        self.df = pd.read_csv("data/ml_training/BTCUSDT_5min_180d.csv")
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

        # Индикаторы
        atr_ind = ta.volatility.AverageTrueRange(
            self.df['high'], self.df['low'], self.df['close']
        )
        self.df['atr'] = atr_ind.average_true_range()
        self.df['atr_sma_20'] = self.df['atr'].rolling(20).mean()

        adx_ind = ta.trend.ADXIndicator(
            self.df['high'], self.df['low'], self.df['close']
        )
        self.df['adx'] = adx_ind.adx()

        self.df['ema_20'] = self.df['close'].ewm(span=20).mean()
        self.df['ema_50'] = self.df['close'].ewm(span=50).mean()
        self.df['volume_sma'] = self.df['volume'].rolling(20).mean()
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], 14).rsi()

        print(f"✅ Loaded {len(self.df)} bars\n")

    def test_simple(self):
        """Тест простой стратегии БЕЗ фильтров"""
        print("🧪 TEST 1: SIMPLE STRATEGY (ADX=28, TP=3.0, SL=0.8)")
        print("="*70)

        trades = []
        position = None

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            # Вход
            if position is None:
                if (pd.notna(row['adx']) and row['adx'] > 28 and
                    pd.notna(row['atr']) and
                    row['volume'] > row['volume_sma'] and
                    row['close'] > row['ema_20']):

                    position = {
                        'entry': row['close'],
                        'atr': row['atr'],
                    }

            # Выход
            elif position is not None:
                tp = position['entry'] + position['atr'] * 3.0
                sl = position['entry'] - position['atr'] * 0.8

                if row['close'] >= tp or row['close'] <= sl:
                    pnl = row['close'] - position['entry']
                    trades.append({'pnl': pnl, 'result': 'WIN' if pnl > 0 else 'LOSS'})
                    position = None

        self.print_stats(trades, "SIMPLE STRATEGY")

    def test_with_vol_filter(self):
        """Тест с vol filter"""
        print("\n🧪 TEST 2: WITH VOL FILTER")
        print("="*70)

        trades = []
        position = None
        skipped = 0

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            # Вход
            if position is None:
                if not (pd.notna(row['adx']) and row['adx'] > 28 and
                       pd.notna(row['atr']) and
                       row['volume'] > row['volume_sma'] and
                       row['close'] > row['ema_20']):
                    continue

                # VOL FILTER
                atr_pct = (row['atr'] / row['atr_sma_20']) if row['atr_sma_20'] > 0 else 1
                if atr_pct < 0.9 or atr_pct > 1.3:
                    skipped += 1
                    continue

                position = {
                    'entry': row['close'],
                    'atr': row['atr'],
                }

            # Выход
            elif position is not None:
                tp = position['entry'] + position['atr'] * 3.0
                sl = position['entry'] - position['atr'] * 0.8

                if row['close'] >= tp or row['close'] <= sl:
                    pnl = row['close'] - position['entry']
                    trades.append({'pnl': pnl, 'result': 'WIN' if pnl > 0 else 'LOSS'})
                    position = None

        print(f"Skipped by vol filter: {skipped}")
        self.print_stats(trades, "WITH VOL FILTER")

    def test_with_all_filters(self):
        """Тест со всеми фильтрами"""
        print("\n🧪 TEST 3: WITH ALL FILTERS (Vol + RSI + Trend + RR)")
        print("="*70)

        trades = []
        position = None
        skipped_vol = 0
        skipped_rsi = 0
        skipped_trend = 0
        skipped_rr = 0

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            # Вход
            if position is None:
                if not (pd.notna(row['adx']) and row['adx'] > 28 and
                       pd.notna(row['atr']) and
                       row['volume'] > row['volume_sma'] and
                       row['close'] > row['ema_20']):
                    continue

                # VOL FILTER
                atr_pct = (row['atr'] / row['atr_sma_20']) if row['atr_sma_20'] > 0 else 1
                if atr_pct < 0.9 or atr_pct > 1.3:
                    skipped_vol += 1
                    continue

                # RSI FILTER
                if row['rsi'] > 70 or row['rsi'] < 30:
                    skipped_rsi += 1
                    continue

                # TREND FILTER
                if not (row['close'] > row['ema_20'] > row['ema_50']):
                    skipped_trend += 1
                    continue

                # RR FILTER
                tp = row['close'] + row['atr'] * 3.0
                sl = row['close'] - row['atr'] * 0.5
                reward = tp - row['close']
                risk = row['close'] - sl
                rr = reward / risk if risk > 0 else 0

                if rr < 3.5:
                    skipped_rr += 1
                    continue

                position = {
                    'entry': row['close'],
                    'atr': row['atr'],
                }

            # Выход
            elif position is not None:
                tp = position['entry'] + position['atr'] * 3.0
                sl = position['entry'] - position['atr'] * 0.5

                if row['close'] >= tp or row['close'] <= sl:
                    pnl = row['close'] - position['entry']
                    trades.append({'pnl': pnl, 'result': 'WIN' if pnl > 0 else 'LOSS'})
                    position = None

        print(f"Skipped by vol: {skipped_vol}")
        print(f"Skipped by RSI: {skipped_rsi}")
        print(f"Skipped by trend: {skipped_trend}")
        print(f"Skipped by RR: {skipped_rr}")
        self.print_stats(trades, "WITH ALL FILTERS")

    def print_stats(self, trades, name):
        """Вывести статистику"""
        if not trades:
            print(f"\n❌ {name}: NO TRADES!\n")
            return

        df_trades = pd.DataFrame(trades)

        total = len(df_trades)
        wins = len(df_trades[df_trades['pnl'] > 0])
        losses = total - wins
        win_rate = (wins / total) * 100 if total > 0 else 0

        total_profit = df_trades[df_trades['pnl'] > 0]['pnl'].sum() if wins > 0 else 0
        total_loss = abs(df_trades[df_trades['pnl'] < 0]['pnl'].sum()) if losses > 0 else 0
        pf = total_profit / total_loss if total_loss > 0 else 0
        total_pnl = df_trades['pnl'].sum()

        print(f"\n📊 {name} RESULTS:")
        print(f"   Trades: {total}")
        print(f"   Wins: {wins} ({win_rate:.1f}%)")
        print(f"   PF: {pf:.2f}")
        print(f"   Total PnL: ${total_pnl:+,.0f}\n")

    def run(self):
        """Запустить debug"""
        print("🔍 PF OPTIMIZER DEBUG")
        print("="*70 + "\n")

        self.load_data()
        self.test_simple()
        self.test_with_vol_filter()
        self.test_with_all_filters()

if __name__ == "__main__":
    debug = PFDebug()
    debug.run()
