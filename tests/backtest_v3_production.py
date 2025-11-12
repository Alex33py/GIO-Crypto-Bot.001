"""
🚀 BACKTEST v3 - PRODUCTION OPTIMIZED
TARGET: PF >= 2.0
KEY IMPROVEMENTS:
1. Strict MTF alignment (1h bullish + 4h bullish/neutral)
2. ADX > 30 filter (RAISED from 25 - strong trend only)
3. Volatility filter (ATR ratio >= 0.8)
4. Optimal TP/SL: 2:1 ratio (TP 2*ATR, SL 1*ATR)
5. NO RSI exit (only TP/SL)
6. Volume confirmation required
7. Clean, high-quality signals only
"""

import sys
import os
import pandas as pd
import numpy as np
import ta
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BacktestV3Production:
    """Production-ready backtest for PF >= 2.0"""

    def __init__(self):
        self.df_1h = None
        self.df_4h = None
        self.trades = []
        self.config = {
            'min_adx': 30,
            'tp_multiplier': 2.0,
            'sl_multiplier': 1.0,
            'volume_requirement': 1.0,
        }

    def load_data(self):
        """Загрузить исторические данные"""
        try:
            self.df_1h = pd.read_csv("data/historical/BTCUSDT_1h_90d.csv")
            self.df_1h['timestamp'] = pd.to_datetime(self.df_1h['timestamp'])

            self.df_4h = pd.read_csv("data/historical/BTCUSDT_4h_90d.csv")
            self.df_4h['timestamp'] = pd.to_datetime(self.df_4h['timestamp'])

            print(f"✅ Loaded: {len(self.df_1h)} 1h bars, {len(self.df_4h)} 4h bars")
            return True
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def calculate_features(self):
        """Рассчитать ВСЕ технические индикаторы"""
        for df in [self.df_1h, self.df_4h]:
            # RSI
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()

            # ADX - ГЛАВНЫЙ ИНДИКАТОР!
            adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            df['adx'] = adx_ind.adx()

            # EMA20 для определения позиции цены
            df['ema20'] = df['close'].rolling(20).mean()

            # Volume SMA
            df['volume_sma'] = df['volume'].rolling(20).mean()

            # ATR для TP/SL
            atr_ind = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'])
            df['atr'] = atr_ind.average_true_range()

            # ✅ НОВОЕ: ATR SMA для фильтра волатильности
            df['atr_sma_20'] = df['atr'].rolling(20).mean()

        print("✅ Features calculated")

    def determine_trend(self, row):
        """Определить тренд на основе ADX + Price position"""
        if pd.isna(row['adx']) or pd.isna(row['ema20']):
            return 'neutral'

        if row['adx'] < 20:
            return 'neutral'
        elif row['close'] > row['ema20']:
            return 'bullish'
        else:
            return 'bearish'

    def can_trade(self, row):
        """ЖЁСТКИЕ ФИЛЬТРЫ: можем ли торговать?"""
        if pd.isna(row['adx']) or pd.isna(row['volume_sma']):
            return False

        # Проверка волатильности
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
        """Основной цикл бектеста"""
        print("\n🎯 Генерация сигналов (v3 Production - ADX>=30 + Vol Filter)...\n")

        df = self.df_1h.copy()
        df_4h = self.df_4h.copy()

        position = None

        for i in range(50, len(df)):
            row = df.iloc[i]

            # Найти соответствующую 4h свечу
            df_4h_subset = df_4h[df_4h['timestamp'] <= row['timestamp']]
            if df_4h_subset.empty:
                continue

            row_4h = df_4h_subset.iloc[-1]

            # === ВХОД: Открыть позицию ===
            if position is None and self.can_trade(row):
                trend_1h = self.determine_trend(row)
                trend_4h = self.determine_trend(row_4h)

                can_long = (trend_1h == 'bullish' and
                           trend_4h in ['bullish', 'neutral'])
                can_short = (trend_1h == 'bearish' and
                            trend_4h in ['bearish', 'neutral'])


                if can_long and not pd.isna(row['atr']):
                    position = {
                        'direction': 'LONG',
                        'entry_price': row['close'],
                        'entry_time': row['timestamp'],
                        'atr': row['atr'],
                        'entry_adx': row['adx'],
                    }
                    print(f"✅ LONG @ {row['close']:.0f} | ADX={row['adx']:.0f} | {row['timestamp']}")

                elif can_short and not pd.isna(row['atr']):
                    position = {
                        'direction': 'SHORT',
                        'entry_price': row['close'],
                        'entry_time': row['timestamp'],
                        'atr': row['atr'],
                        'entry_adx': row['adx'],
                    }
                    print(f"✅ SHORT @ {row['close']:.0f} | ADX={row['adx']:.0f} | {row['timestamp']}")

            # === ВЫХОД: Закрыть позицию ===
            elif position is not None:
                atr = position['atr']
                entry = position['entry_price']
                direction = position['direction']

                # Вычислить TP/SL
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

                    status = '✅' if pnl > 0 else '❌'
                    print(f"{status} EXIT {direction:5s} @ {row['close']:.0f} | PnL: {pnl_pct:+.2f}% [{exit_reason}]")

                    position = None

    def analyze(self):
        """Анализ результатов"""
        if not self.trades:
            print("❌ Нет сделок!")
            return

        df = pd.DataFrame(self.trades)

        total = len(df)
        wins = len(df[df['pnl'] > 0])
        losses = len(df[df['pnl'] < 0])

        win_rate = (wins / total) * 100 if total > 0 else 0

        total_profit = df[df['pnl'] > 0]['pnl'].sum()
        total_loss = abs(df[df['pnl'] < 0]['pnl'].sum())

        pf = total_profit / total_loss if total_loss > 0 else 0
        total_pnl = df['pnl'].sum()

        avg_win = total_profit / wins if wins > 0 else 0
        avg_loss = total_loss / losses if losses > 0 else 0
        rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        # Print results
        print("\n" + "="*70)
        print("📊 РЕЗУЛЬТАТЫ БЕКТЕСТА v3 PRODUCTION (ADX>=30 + VOL FILTER)")
        print("="*70)
        print(f"\n📈 Trades: {total} | Wins: {wins} ({win_rate:.1f}%) | Losses: {losses}")
        print(f"\n💰 PROFIT FACTOR: {pf:.2f}  ← ГЛАВНОЕ ЧИСЛО!")
        print(f"   Total PnL: ${total_pnl:,.0f}")
        print(f"   Avg Win: ${avg_win:,.0f}")
        print(f"   Avg Loss: ${avg_loss:,.0f}")
        print(f"   Risk/Reward Ratio: 1:{rr_ratio:.2f}")
        print("\n" + "="*70)

        # Сохранить результаты
        os.makedirs("tests/results", exist_ok=True)
        csv_path = f"tests/results/backtest_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_path, index=False)
        print(f"💾 Saved to: {csv_path}")

        return df

    def run(self):
        """Запустить полный бектест"""
        print("🚀 BACKTEST v3 PRODUCTION - OPTIMIZED FOR PF >= 2.0 (ADX>=30 + VOL FILTER)")
        print("="*70)

        if self.load_data():
            self.calculate_features()
            self.backtest()
            self.analyze()
        else:
            print("❌ Failed to load data!")


if __name__ == "__main__":
    bt = BacktestV3Production()
    bt.run()
