# -*- coding: utf-8 -*-
"""
Backtest на 5-minute data для ML training
Генерирует МНОГО сделок для обучения модели
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import ta
from datetime import datetime

class Backtest5MinML:
    """Backtest на 5-minute data"""

    def __init__(self):
        self.df = None
        self.trades = []
        self.config = {
            'min_adx': 30,
            'tp_multiplier': 2.0,
            'sl_multiplier': 1.0,
            'volume_requirement': 1.0,
        }

    def load_data(self):
        """Загрузить 5-minute данные"""
        try:
            self.df = pd.read_csv("data/ml_training/BTCUSDT_5min_180d.csv")
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            print(f"✅ Loaded: {len(self.df)} 5-minute bars")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def calculate_features(self):
        """Рассчитать индикаторы"""
        print("🔧 Calculating indicators...")

        df = self.df

        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()

        # ADX
        adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
        df['adx'] = adx_ind.adx()

        # EMA
        df['ema_20'] = df['close'].rolling(20).mean()

        # Volume
        df['volume_sma'] = df['volume'].rolling(20).mean()

        # ATR
        atr_ind = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'])
        df['atr'] = atr_ind.average_true_range()
        df['atr_sma_20'] = df['atr'].rolling(20).mean()

        print("✅ Indicators calculated")

    def determine_trend(self, row):
        """Определить тренд"""
        if pd.isna(row['adx']) or pd.isna(row['ema_20']):
            return 'neutral'

        if row['adx'] < 20:
            return 'neutral'
        elif row['close'] > row['ema_20']:
            return 'bullish'
        else:
            return 'bearish'

    def can_trade(self, row):
        """Фильтры"""
        if pd.isna(row['adx']) or pd.isna(row['volume_sma']):
            return False

        # Volatility filter
        if not pd.isna(row.get('atr', 0)) and not pd.isna(row.get('atr_sma_20', 0)):
            atr = row['atr']
            atr_sma = row['atr_sma_20']
            if atr_sma > 0:
                vol_ratio = atr / atr_sma
                if vol_ratio < 0.8:
                    return False

        checks = {
            'adx_strong': row['adx'] > self.config['min_adx'],
            'volume_ok': row['volume'] > self.config['volume_requirement'] * row['volume_sma'],
        }

        return all(checks.values())

    def backtest(self):
        """Основной цикл"""
        print("\n🎯 Running backtest on 5-minute data...\n")

        df = self.df
        position = None

        for i in range(200, len(df)):  # Начать с 200 для indicators
            row = df.iloc[i]

            # Вход
            if position is None and self.can_trade(row):
                trend = self.determine_trend(row)

                if trend == 'bullish' and not pd.isna(row['atr']):
                    position = {
                        'direction': 'LONG',
                        'entry_price': row['close'],
                        'entry_time': row['timestamp'],
                        'entry_idx': i,
                        'atr': row['atr'],
                    }

                elif trend == 'bearish' and not pd.isna(row['atr']):
                    position = {
                        'direction': 'SHORT',
                        'entry_price': row['close'],
                        'entry_time': row['timestamp'],
                        'entry_idx': i,
                        'atr': row['atr'],
                    }

            # Выход
            elif position is not None:
                atr = position['atr']
                entry = position['entry_price']
                direction = position['direction']

                if direction == 'LONG':
                    tp = entry + atr * self.config['tp_multiplier']
                    sl = entry - atr * self.config['sl_multiplier']
                    should_close = row['close'] >= tp or row['close'] <= sl
                    exit_reason = 'TP' if row['close'] >= tp else 'SL'

                else:  # SHORT
                    tp = entry - atr * self.config['tp_multiplier']
                    sl = entry + atr * self.config['sl_multiplier']
                    should_close = row['close'] <= tp or row['close'] >= sl
                    exit_reason = 'TP' if row['close'] <= tp else 'SL'

                if should_close:
                    pnl = row['close'] - entry if direction == 'LONG' else entry - row['close']
                    pnl_pct = (pnl / entry) * 100

                    self.trades.append({
                        'entry': entry,
                        'exit': row['close'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'direction': direction,
                        'exit_reason': exit_reason,
                        'atr': atr,
                        'entry_time': position['entry_time'],
                        'exit_time': row['timestamp'],
                    })

                    position = None

    def analyze(self):
        """Анализ"""
        if not self.trades:
            print("❌ No trades!")
            return

        df = pd.DataFrame(self.trades)

        total = len(df)
        wins = len(df[df['pnl'] > 0])
        losses = len(df[df['pnl'] < 0])
        win_rate = (wins / total) * 100

        total_profit = df[df['pnl'] > 0]['pnl'].sum()
        total_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
        pf = total_profit / total_loss if total_loss > 0 else 0
        total_pnl = df['pnl'].sum()

        print("\n" + "="*70)
        print("📊 BACKTEST RESULTS (5-MINUTE DATA)")
        print("="*70)
        print(f"\n📈 Trades: {total} | Wins: {wins} ({win_rate:.1f}%) | Losses: {losses}")
        print(f"\n💰 PROFIT FACTOR: {pf:.2f}")
        print(f"   Total PnL: ${total_pnl:,.0f}")
        print("\n" + "="*70)

        # Save
        os.makedirs("tests/results", exist_ok=True)
        csv_path = f"tests/results/backtest_5min_ml_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_path, index=False)
        print(f"💾 Saved: {csv_path}")

        return df

    def run(self):
        """Запустить"""
        print("🚀 BACKTEST 5-MIN DATA FOR ML TRAINING")
        print("="*70)

        if self.load_data():
            self.calculate_features()
            self.backtest()
            self.analyze()

if __name__ == "__main__":
    bt = Backtest5MinML()
    bt.run()
