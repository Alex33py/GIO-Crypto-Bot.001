# -*- coding: utf-8 -*-
"""
GRID SEARCH на РЕАЛЬНЫХ данных
Найдём параметры которые действительно работают!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import ta
from itertools import product
from datetime import datetime

class GridSearchRealData:
    """Grid Search на реальных данных"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.results = []

    def load_data(self):
        """Загрузить CSV"""
        print(f"\n📥 Загрузка: {self.csv_path}")

        self.df = pd.read_csv(self.csv_path)
        print(f"✅ Загружено {len(self.df)} свечей\n")

    def calculate_indicators(self):
        """Индикаторы"""
        atr_ind = ta.volatility.AverageTrueRange(
            self.df['high'], self.df['low'], self.df['close']
        )
        self.df['atr'] = atr_ind.average_true_range()

        adx_ind = ta.trend.ADXIndicator(
            self.df['high'], self.df['low'], self.df['close']
        )
        self.df['adx'] = adx_ind.adx()

        self.df['ema_20'] = self.df['close'].ewm(span=20).mean()
        self.df['ema_50'] = self.df['close'].ewm(span=50).mean()
        self.df['volume_sma'] = self.df['volume'].rolling(20).mean()
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], 14).rsi()

        print("✅ Индикаторы рассчитаны!")

    def backtest(self, sl_mult, tp_mult, min_adx, rsi_min, rsi_max, vol_mult):
        """Backtest"""
        trades = []
        position = None

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            if position is None:
                try:
                    if not (pd.notna(row['adx']) and row['adx'] > min_adx):
                        continue
                    if not (pd.notna(row['rsi']) and rsi_min < row['rsi'] < rsi_max):
                        continue
                    if not (row['volume'] > row['volume_sma'] * vol_mult):
                        continue
                    if not (row['close'] > row['ema_20'] > row['ema_50']):
                        continue

                    position = {'entry': row['close'], 'atr': row['atr'], 'bar': i}
                except:
                    continue

            elif position is not None:
                try:
                    tp = position['entry'] + position['atr'] * tp_mult
                    sl_price = position['entry'] - position['atr'] * sl_mult

                    if row['close'] >= tp or row['close'] <= sl_price:
                        pnl = row['close'] - position['entry']
                        trades.append({'pnl': pnl, 'pnl_pct': (pnl/position['entry'])*100})
                        position = None
                except:
                    continue

        if len(trades) < 5:
            return None

        df_trades = pd.DataFrame(trades)
        wins = (df_trades['pnl'] > 0).sum()
        losses = len(df_trades) - wins

        if losses == 0:
            return None

        win_rate = (wins / len(df_trades)) * 100
        total_profit = df_trades[df_trades['pnl'] > 0]['pnl'].sum()
        total_loss = abs(df_trades[df_trades['pnl'] < 0]['pnl'].sum())
        pf = total_profit / total_loss

        returns = df_trades['pnl_pct']
        sharpe = (returns.mean() / returns.std()) if returns.std() > 0 else 0

        return {
            'sl_mult': sl_mult,
            'tp_mult': tp_mult,
            'min_adx': min_adx,
            'rsi_min': rsi_min,
            'rsi_max': rsi_max,
            'vol_mult': vol_mult,
            'trades': len(df_trades),
            'win_rate': win_rate,
            'pf': pf,
            'sharpe': sharpe,
            'total_pnl': df_trades['pnl'].sum(),
        }

    def search(self):
        """Grid Search"""
        print("\n🔍 GRID SEARCH на РЕАЛЬНЫХ данных...\n")

        # ОСЛАБЛЕННЫЕ параметры (больше сделок)
        configs = list(product(
            [0.8, 1.0, 1.2],      # SL
            [2.0, 2.5, 3.0],      # TP
            [15, 20, 25],         # ADX (ниже!)
            [30, 35, 40],         # RSI min
            [60, 65, 70],         # RSI max
            [0.6, 0.8, 1.0],      # Volume (мягче!)
        ))

        print(f"Total configs: {len(configs)}\n")

        for i, (sl_price, tp, adx, rsi_min, rsi_max, vol) in enumerate(configs, 1):
            if rsi_min >= rsi_max:
                continue

            result = self.backtest(sl_price, tp, adx, rsi_min, rsi_max, vol)

            if result and result['pf'] >= 1.0:
                self.results.append(result)

                if result['pf'] > 1.3:
                    print(f"[{i}] ✅ SL={sl_price} TP={tp} ADX={adx} RSI={rsi_min}-{rsi_max} Vol={vol}")
                    print(f"    WR={result['win_rate']:.1f}% PF={result['pf']:.2f} Trades={result['trades']}\n")

    def print_top(self):
        """TOP 10"""
        if not self.results:
            print("\n❌ No profitable configs found!")
            return

        df = pd.DataFrame(self.results)
        df['score'] = df['win_rate']*0.4/50 + df['pf']*0.4/1.5 + df['sharpe']*0.2/1.5
        df = df.nlargest(10, 'score')

        print("\n" + "="*100)
        print("🏆 TOP 10 REAL DATA CONFIGS")
        print("="*100 + "\n")

        for idx, (_, row) in enumerate(df.iterrows(), 1):
            print(f"{idx}. SL={row['sl_mult']}x TP={row['tp_mult']}x ADX={row['min_adx']} RSI={row['rsi_min']}-{row['rsi_max']} Vol={row['vol_mult']}x")
            print(f"   WR={row['win_rate']:.1f}% PF={row['pf']:.2f} Trades={row['trades']:.0f} Score={row['score']:.2f}\n")

        print("="*100)

    def run(self):
        """Запустить"""
        print("\n" + "="*100)
        print("🚀 GRID SEARCH НА РЕАЛЬНЫХ ДАННЫХ")
        print("="*100)

        self.load_data()
        self.calculate_indicators()
        self.search()
        self.print_top()

if __name__ == "__main__":
    optimizer = GridSearchRealData("data/historical/BTCUSDT_1h_90d.csv")
    optimizer.run()
