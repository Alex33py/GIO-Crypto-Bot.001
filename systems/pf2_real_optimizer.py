# -*- coding: utf-8 -*-
"""
GRID SEARCH: PF 2.0+ на реальных данных
Стратегия: КАЧЕСТВО вместо КОЛИЧЕСТВА
"""

import pandas as pd
import numpy as np
import ta
from itertools import product

class PF2Optimizer:
    """Оптимизация для PF 2.0+"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.results = []

    def load_and_prep(self):
        """Загрузка + индикаторы"""
        self.df = pd.read_csv(self.csv_path)

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

        # НОВОЕ: Momentum strength
        self.df['price_momentum'] = self.df['close'].pct_change(5).rolling(5).mean()

        print("✅ Data prepared!")

    def backtest_selective(self, sl_mult, tp_mult, min_adx, min_rsi_strength,
                          max_deals_per_day=2):
        """
        Backtest СЕЛЕКТИВНЫЙ:
        - Только HIGH QUALITY сделки
        - Максимум 2 сделки в день
        - Требуется сильный импульс
        """
        trades = []
        position = None
        last_deal_bar = -999
        deals_today = 0
        current_date = None

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            # Reset counter each day
            if current_date != row['timestamp'][:10]:
                current_date = row['timestamp'][:10]
                deals_today = 0

            # Вход
            if position is None and deals_today < max_deals_per_day:
                try:
                    # БАЗОВЫЕ ФИЛЬТРЫ
                    if not (pd.notna(row['adx']) and row['adx'] > min_adx):
                        continue
                    if not (row['volume'] > row['volume_sma'] * 0.8):
                        continue
                    if not (row['close'] > row['ema_20'] > row['ema_50']):
                        continue

                    # НОВОЕ: Momentum strength filter
                    if row['price_momentum'] < min_rsi_strength:
                        continue

                    # НОВОЕ: Avoid consecutive deals
                    if i - last_deal_bar < 8:  # Min 8 bars between trades
                        continue

                    position = {
                        'entry': row['close'],
                        'atr': row['atr'],
                        'bar': i,
                    }
                    deals_today += 1
                    last_deal_bar = i

                except:
                    continue

            # Выход
            elif position is not None:
                try:
                    tp = position['entry'] + position['atr'] * tp_mult
                    sl = position['entry'] - position['atr'] * sl_mult

                    if row['close'] >= tp or row['close'] <= sl:
                        pnl = row['close'] - position['entry']
                        pnl_pct = (pnl / position['entry']) * 100

                        trades.append({
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'result': 'WIN' if pnl > 0 else 'LOSS'
                        })

                        position = None
                except:
                    continue

        # Анализ
        if len(trades) < 3:
            return None

        df_trades = pd.DataFrame(trades)
        wins = (df_trades['pnl'] > 0).sum()
        losses = len(df_trades) - wins

        if losses == 0:
            return None

        total_profit = df_trades[df_trades['pnl'] > 0]['pnl'].sum()
        total_loss = abs(df_trades[df_trades['pnl'] < 0]['pnl'].sum())
        pf = total_profit / total_loss

        win_rate = (wins / len(df_trades)) * 100

        return {
            'sl_mult': sl_mult,
            'tp_mult': tp_mult,
            'min_adx': min_adx,
            'min_momentum': min_rsi_strength,
            'trades': len(df_trades),
            'win_rate': win_rate,
            'pf': pf,
            'total_pnl': df_trades['pnl'].sum(),
        }

    def search_pf2(self):
        """Grid Search для PF 2.0+"""
        print("\n🔍 Searching for PF 2.0+ on REAL data...\n")

        # КЛЮЧЕВЫЕ ПАРАМЕТРЫ ДЛЯ PF 2.0:
        # 1. Узкий SL (1.0-1.2)
        # 2. Средний TP (2.0-2.5)
        # 3. Высокий ADX (25-30) - только сильные тренды
        # 4. Сильный импульс

        configs = list(product(
            [0.8, 1.0],         # SL (узкий!)
            [2.0, 2.2, 2.5],    # TP (средний)
            [25, 28, 30],       # ADX (ВЫСОКИЙ!)
            [0.005, 0.01, 0.015],  # Min momentum (СИЛЬНЫЙ)
        ))

        print(f"Testing {len(configs)} configs for PF 2.0+\n")

        for sl, tp, adx, momentum in configs:
            result = self.backtest_selective(sl, tp, adx, momentum)

            if result and result['pf'] >= 1.8:
                self.results.append(result)

                if result['pf'] >= 2.0:
                    print(f"🎉 FOUND PF 2.0+!")
                    print(f"   SL={sl}x TP={tp}x ADX={adx} Momentum={momentum:.3f}")
                    print(f"   WR={result['win_rate']:.1f}% PF={result['pf']:.2f} Trades={result['trades']}\n")
                else:
                    print(f"✅ Good: SL={sl} TP={tp} ADX={adx} → PF={result['pf']:.2f}")

    def print_top(self):
        """TOP результаты"""
        if not self.results:
            print("\n❌ No PF 2.0 found! Try different params.")
            return

        df = pd.DataFrame(self.results)
        df = df.nlargest(10, 'pf')

        print("\n" + "="*100)
        print("🏆 TOP 10 FOR PF 2.0+ (REAL DATA)")
        print("="*100 + "\n")

        for idx, (_, row) in enumerate(df.iterrows(), 1):
            print(f"{idx}. SL={row['sl_mult']}x TP={row['tp_mult']}x ADX={row['min_adx']} "
                  f"Momentum={row['min_momentum']:.3f}")
            print(f"   WR={row['win_rate']:.1f}% PF={row['pf']:.2f} Trades={row['trades']:.0f}\n")

    def run(self):
        """Execute"""
        print("\n" + "="*100)
        print("🚀 OPTIMIZATION: PF 2.0+ ON REAL DATA")
        print("="*100)

        self.load_and_prep()
        self.search_pf2()
        self.print_top()

if __name__ == "__main__":
    optimizer = PF2Optimizer("data/historical/BTCUSDT_1h_90d.csv")
    optimizer.run()



# python systems/grid_search_real_data.py
