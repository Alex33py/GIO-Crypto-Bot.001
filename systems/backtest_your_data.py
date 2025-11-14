# -*- coding: utf-8 -*-
"""
BACKTEST на РЕАЛЬНЫХ ДАННЫХ которые уже загружены
Используем BTCUSDT_1h_90d.csv
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import ta
from datetime import datetime
import json

class RealDataBacktester:
    """Backtest на реальных данных из CSV"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.trades = []

        # Оптимальная конфигурация из DAY 5
        self.config = {
            'sl_mult': 1.0,
            'tp_mult': 3.5,
            'min_adx': 20,
            'rsi_min': 35,
            'rsi_max': 65,
            'vol_mult': 0.8,
        }

    def load_data(self):
        """Загрузить CSV"""
        print(f"\n📥 Загрузка данных: {self.csv_path}")

        try:
            self.df = pd.read_csv(self.csv_path)

            # Проверить колонки
            required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if all(col in self.df.columns for col in required):
                print(f"✅ Загружено {len(self.df)} свечей")
                print(f"   Период: {self.df['timestamp'].min()} - {self.df['timestamp'].max()}")
                return True
            else:
                print(f"❌ Неправильные колонки. Нужны: {required}")
                print(f"   Имеются: {list(self.df.columns)}")
                return False

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False

    def calculate_indicators(self):
        """Расчёт индикаторов"""
        print("\n📊 Расчёт индикаторов...")

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
        self.df['ema_50'] = self.df['close'].ewm(span=50).mean()

        # Volume SMA
        self.df['volume_sma'] = self.df['volume'].rolling(20).mean()

        # RSI
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], 14).rsi()

        print("✅ Индикаторы рассчитаны!")

    def backtest(self):
        """Запуск backtest"""
        print("\n🎯 Запуск BACKTEST...")
        print(f"   Config: SL={self.config['sl_mult']}x, TP={self.config['tp_mult']}x")
        print(f"   ADX={self.config['min_adx']}, RSI={self.config['rsi_min']}-{self.config['rsi_max']}\n")

        sl_mult = self.config['sl_mult']
        tp_mult = self.config['tp_mult']
        min_adx = self.config['min_adx']
        rsi_min = self.config['rsi_min']
        rsi_max = self.config['rsi_max']
        vol_mult = self.config['vol_mult']

        position = None
        trades = []

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            # Вход
            if position is None:
                # Все фильтры
                try:
                    if not (pd.notna(row['adx']) and row['adx'] > min_adx):
                        continue
                    if not (pd.notna(row['rsi']) and rsi_min < row['rsi'] < rsi_max):
                        continue
                    if not (row['volume'] > row['volume_sma'] * vol_mult):
                        continue
                    if not (row['close'] > row['ema_20'] > row['ema_50']):
                        continue

                    # Открыть позицию
                    position = {
                        'entry': row['close'],
                        'atr': row['atr'],
                        'time': row['timestamp'],
                        'bar': i,
                    }
                except:
                    continue

            # Выход
            elif position is not None:
                try:
                    tp = position['entry'] + position['atr'] * tp_mult
                    sl_price = position['entry'] - position['atr'] * sl_mult

                    if row['close'] >= tp or row['close'] <= sl_price:
                        pnl = row['close'] - position['entry']
                        pnl_pct = (pnl / position['entry']) * 100
                        bars_held = i - position['bar']

                        trades.append({
                            'entry_time': position['time'],
                            'exit_time': row['timestamp'],
                            'entry': position['entry'],
                            'exit': row['close'],
                            'pnl': pnl,
                            'pnl_pct': pnl_pct,
                            'result': 'WIN' if pnl > 0 else 'LOSS',
                            'bars': bars_held,
                        })

                        position = None
                except:
                    continue

        self.trades = trades

    def print_results(self):
        """Вывести результаты"""
        if not self.trades:
            print("\n❌ NO TRADES!")
            return

        df_trades = pd.DataFrame(self.trades)

        total = len(df_trades)
        wins = (df_trades['result'] == 'WIN').sum()
        losses = total - wins

        win_rate = (wins / total) * 100 if total > 0 else 0

        df_wins = df_trades[df_trades['result'] == 'WIN']
        df_losses = df_trades[df_trades['result'] == 'LOSS']

        total_profit = df_wins['pnl'].sum() if len(df_wins) > 0 else 0
        total_loss = abs(df_losses['pnl'].sum()) if len(df_losses) > 0 else 0

        pf = total_profit / total_loss if total_loss > 0 else 0
        total_pnl = df_trades['pnl'].sum()

        # Sharpe
        returns = df_trades['pnl_pct']
        sharpe = (returns.mean() / returns.std()) if returns.std() > 0 else 0

        # Drawdown
        cum_returns = (1 + returns / 100).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_dd = drawdown.min()

        print("\n" + "="*100)
        print("📊 РЕЗУЛЬТАТЫ BACKTEST НА РЕАЛЬНЫХ ДАННЫХ")
        print("="*100 + "\n")

        print(f"📈 ОСНОВНЫЕ МЕТРИКИ:")
        print(f"   ├─ Total Trades: {total}")
        print(f"   ├─ Wins: {wins} ({win_rate:.1f}%)")
        print(f"   ├─ Losses: {losses}")
        print(f"   ├─ Win/Loss: {wins}/{losses}")
        print(f"   └─ Profit Factor: {pf:.2f} {'✅' if pf >= 1.5 else '⚠️'}\n")

        print(f"💰 PnL МЕТРИКИ:")
        print(f"   ├─ Total PnL: ${total_pnl:+,.2f}")
        print(f"   ├─ Avg PnL: ${total_pnl/total:+,.2f}")
        print(f"   ├─ Avg Win: ${total_profit/wins:+,.2f}" if wins > 0 else "   ├─ Avg Win: N/A")
        print(f"   ├─ Avg Loss: ${-total_loss/losses:+,.2f}" if losses > 0 else "   ├─ Avg Loss: N/A")
        print(f"   └─ Best Trade: ${df_trades['pnl'].max():+,.2f}\n")

        print(f"📉 РИСК МЕТРИКИ:")
        print(f"   ├─ Worst Trade: ${df_trades['pnl'].min():+,.2f}")
        print(f"   ├─ Max Drawdown: {max_dd*100:.2f}%")
        print(f"   ├─ Sharpe Ratio: {sharpe:.2f}")
        print(f"   └─ Avg Bars: {df_trades['bars'].mean():.0f}\n")

        print("="*100)

        # Сохранить
        self.save_trades(df_trades)

    def save_trades(self, df_trades):
        """Сохранить таблицу сделок"""
        os.makedirs('tests/results', exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"tests/results/backtest_real_data_{timestamp}.csv"

        df_trades.to_csv(path, index=False)
        print(f"💾 Сохранено: {path}\n")

    def run(self):
        """Запустить весь процесс"""
        print("\n" + "="*100)
        print("🚀 BACKTEST НА РЕАЛЬНЫХ ДАННЫХ")
        print("="*100)

        if not self.load_data():
            return

        self.calculate_indicators()
        self.backtest()
        self.print_results()

# Main
if __name__ == "__main__":
    # Используем 1h 90d данные
    tester = RealDataBacktester("data/historical/BTCUSDT_1h_90d.csv")
    tester.run()
