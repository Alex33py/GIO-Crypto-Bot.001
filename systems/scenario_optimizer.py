# -*- coding: utf-8 -*-
"""
TOP 10 Scenarios Optimizer
Поиск лучших комбинаций параметров
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import ta
from datetime import datetime

class ScenarioOptimizer:
    """Поиск TOP 10 оптимальных сценариев"""

    def __init__(self):
        self.results = []
        self.df = None

    def load_data(self):
        """Загрузить 5-minute данные"""
        self.df = pd.read_csv("data/ml_training/BTCUSDT_5min_180d.csv")
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.calculate_indicators()
        print(f"✅ Loaded {len(self.df)} bars")

    def calculate_indicators(self):
        """Рассчитать индикаторы"""
        # ATR
        atr_ind = ta.volatility.AverageTrueRange(
            self.df['high'], self.df['low'], self.df['close']
        )
        self.df['atr'] = atr_ind.average_true_range()

        # ADX
        adx_ind = ta.trend.ADXIndicator(
            self.df['high'], self.df['low'], self.df['close']
        )
        self.df['adx'] = adx_ind.adx()

        # EMA
        self.df['ema_20'] = self.df['close'].ewm(span=20).mean()
        self.df['volume_sma'] = self.df['volume'].rolling(20).mean()

    def backtest_scenario(self, min_adx, tp_mult, sl_mult):
        """
        Backtestить один сценарий

        Args:
            min_adx: минимальный ADX для входа
            tp_mult: множитель для Take Profit (ATR * tp_mult)
            sl_mult: множитель для Stop Loss (ATR * sl_mult)

        Returns:
            dict с метриками
        """
        trades = []
        position = None

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            # Вход
            if position is None:
                if (pd.notna(row['adx']) and row['adx'] > min_adx and
                    pd.notna(row['atr']) and row['volume'] > row['volume_sma']):

                    if row['close'] > row['ema_20']:  # Long
                        position = {
                            'direction': 'LONG',
                            'entry': row['close'],
                            'time': row['timestamp'],
                            'atr': row['atr'],
                        }

            # Выход
            elif position is not None:
                atr = position['atr']
                entry = position['entry']

                tp = entry + atr * tp_mult
                sl_price = entry - atr * sl_mult

                if row['close'] >= tp or row['close'] <= sl_price:
                    pnl = row['close'] - entry
                    pnl_pct = (pnl / entry) * 100

                    trades.append({
                        'entry': entry,
                        'exit': row['close'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'result': 'WIN' if pnl > 0 else 'LOSS',
                        'atr': atr,
                    })

                    position = None

        # Вычислить метрики
        if not trades:
            return None

        df_trades = pd.DataFrame(trades)

        total = len(df_trades)
        wins = len(df_trades[df_trades['pnl'] > 0])
        losses = len(df_trades[df_trades['pnl'] < 0])

        if losses == 0:
            return None

        win_rate = (wins / total) * 100 if total > 0 else 0
        total_profit = df_trades[df_trades['pnl'] > 0]['pnl'].sum()
        total_loss = abs(df_trades[df_trades['pnl'] < 0]['pnl'].sum())
        pf = total_profit / total_loss if total_loss > 0 else 0
        total_pnl = df_trades['pnl'].sum()

        return {
            'min_adx': min_adx,
            'tp_mult': tp_mult,
            'sl_mult': sl_mult,
            'trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'pf': pf,
            'total_pnl': total_pnl,
            'avg_win': total_profit / wins if wins > 0 else 0,
            'avg_loss': total_loss / losses if losses > 0 else 0,
        }

    def search_best_scenarios(self):
        """Поиск TOP 10 сценариев"""
        print("\n🔍 SEARCHING FOR BEST SCENARIOS...\n")

        # Параметры для оптимизации
        adx_range = [20, 22, 25, 28, 30]          # min ADX
        tp_mult_range = [1.5, 2.0, 2.5, 3.0]      # TP multiplier
        sl_mult_range = [0.8, 1.0, 1.2]           # SL multiplier

        count = 0
        for min_adx in adx_range:
            for tp_mult in tp_mult_range:
                for sl_mult in sl_mult_range:
                    result = self.backtest_scenario(min_adx, tp_mult, sl_mult)

                    if result is not None and result['pf'] > 1.0:  # Только profitable
                        self.results.append(result)
                        count += 1

                        if count % 10 == 0:
                            print(f"  ✅ {count} scenarios tested...")

        print(f"\n✅ Total scenarios: {len(self.results)}")

    def get_top_10(self):
        """Получить TOP 10 сценариев"""
        if not self.results:
            print("❌ No profitable scenarios found!")
            return None

        # Сортировать по Profit Factor
        df_results = pd.DataFrame(self.results)
        df_results = df_results[df_results['pf'] > 1.0]  # Только profitable
        df_results = df_results.sort_values('pf', ascending=False).head(10)

        return df_results

    def print_top_10(self, df_top10):
        """Вывести TOP 10"""
        print("\n" + "="*100)
        print("🏆 TOP 10 BEST SCENARIOS")
        print("="*100 + "\n")

        for idx, (_, row) in enumerate(df_top10.iterrows(), 1):
            print(f"{idx}. ADX={row['min_adx']:.0f} | TP={row['tp_mult']:.1f}*ATR | SL={row['sl_mult']:.1f}*ATR")
            print(f"   PF: {row['pf']:.2f} | WR: {row['win_rate']:.1f}% | Trades: {row['trades']:.0f}")
            print(f"   Avg Win: ${row['avg_win']:.2f} | Avg Loss: ${row['avg_loss']:.2f}")
            print(f"   Total PnL: ${row['total_pnl']:+,.0f}\n")

        print("="*100)

    def save_top_10(self, df_top10):
        """Сохранить TOP 10"""
        os.makedirs("data/optimization", exist_ok=True)
        csv_path = "data/optimization/top_10_scenarios.csv"
        df_top10.to_csv(csv_path, index=False)
        print(f"💾 Saved: {csv_path}")

    def run(self):
        """Запустить оптимизацию"""
        print("🚀 SCENARIO OPTIMIZER - TOP 10 SEARCH")
        print("="*100)

        self.load_data()
        self.search_best_scenarios()
        df_top10 = self.get_top_10()

        if df_top10 is not None:
            self.print_top_10(df_top10)
            self.save_top_10(df_top10)

if __name__ == "__main__":
    optimizer = ScenarioOptimizer()
    optimizer.run()
