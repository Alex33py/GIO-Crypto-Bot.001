# -*- coding: utf-8 -*-
"""
Adaptive Backtest - защита от curve fitting
Использует MarketRegimeDetector для адаптивных параметров
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import ta
from datetime import datetime
from systems.market_regime_detector import MarketRegimeDetector

class AdaptiveBacktest:
    """Backtest с адаптивными параметрами"""

    def __init__(self):
        self.df = None
        self.trades = []
        self.regime_detector = MarketRegimeDetector()
        self.recent_trades_tracker = []  # Для macro stop-loss

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
        """Рассчитать индикаторы + regime features"""
        print("🔧 Calculating indicators...")

        # Используем regime detector для вычисления features
        self.df = self.regime_detector.calculate_features(self.df)

        # Volume
        self.df['volume_sma'] = self.df['volume'].rolling(20).mean()

        print("✅ Indicators calculated")

    def determine_trend(self, row):
        """Определить тренд"""
        if pd.isna(row.get('ema_20')):
            return 'neutral'

        if row['close'] > row['ema_20']:
            return 'bullish'
        else:
            return 'bearish'

    def check_macro_stop_loss(self):
        """
        Macro stop-loss: если последние 20 сделок имеют loss rate > 70%
        → PAUSE trading
        """
        if len(self.recent_trades_tracker) < 20:
            return False  # Not enough data

        recent_20 = self.recent_trades_tracker[-20:]
        loss_count = sum(1 for t in recent_20 if t['result'] == 'LOSS')
        loss_rate = loss_count / 20

        if loss_rate > 0.70:
            return True  # PAUSE

        return False

    def can_trade(self, row, config):
        """Фильтры + macro stop-loss"""

        # Macro stop-loss
        if self.check_macro_stop_loss():
            return False

        # Базовые фильтры
        if pd.isna(row.get('adx')) or pd.isna(row.get('volume_sma')):
            return False

        checks = {
            'adx_strong': row['adx'] > config['min_adx'],
            'volume_ok': row['volume'] > config['volume_requirement'] * row['volume_sma'],
        }

        return all(checks.values())

    def backtest(self):
        """Основной цикл с адаптивными параметрами"""
        print("\n🎯 Running ADAPTIVE backtest...\n")

        df = self.df
        position = None
        current_regime = 'UNKNOWN'
        regime_changes = 0

        for i in range(200, len(df)):
            row = df.iloc[i]

            # Определить CURRENT regime
            df_window = df.iloc[:i+1]
            new_regime = self.regime_detector.detect_regime(df_window)

            if new_regime != current_regime:
                regime_changes += 1
                config = self.regime_detector.get_adaptive_config(new_regime)
                print(f"📊 {row['timestamp']}: Regime changed to {new_regime} - {config['description']}")
                current_regime = new_regime

            # Получить current config
            config = self.regime_detector.get_adaptive_config(current_regime)

            # Вход
            if position is None and config['trade'] and self.can_trade(row, config):
                trend = self.determine_trend(row)

                if trend == 'bullish' and not pd.isna(row['atr']):
                    position = {
                        'direction': 'LONG',
                        'entry_price': row['close'],
                        'entry_time': row['timestamp'],
                        'atr': row['atr'],
                        'config': config.copy(),
                        'regime': current_regime,
                    }

                elif trend == 'bearish' and not pd.isna(row['atr']):
                    position = {
                        'direction': 'SHORT',
                        'entry_price': row['close'],
                        'entry_time': row['timestamp'],
                        'atr': row['atr'],
                        'config': config.copy(),
                        'regime': current_regime,
                    }

            # Выход
            elif position is not None:
                atr = position['atr']
                entry = position['entry_price']
                direction = position['direction']
                cfg = position['config']

                if direction == 'LONG':
                    tp = entry + atr * cfg['tp_multiplier']
                    sl = entry - atr * cfg['sl_multiplier']
                    should_close = row['close'] >= tp or row['close'] <= sl
                    exit_reason = 'TP' if row['close'] >= tp else 'SL'

                else:  # SHORT
                    tp = entry - atr * cfg['tp_multiplier']
                    sl = entry + atr * cfg['sl_multiplier']
                    should_close = row['close'] <= tp or row['close'] >= sl
                    exit_reason = 'TP' if row['close'] <= tp else 'SL'

                if should_close:
                    pnl = row['close'] - entry if direction == 'LONG' else entry - row['close']
                    pnl_pct = (pnl / entry) * 100
                    result = 'WIN' if pnl > 0 else 'LOSS'

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
                        'regime': position['regime'],
                        'result': result,
                    })

                    # Track для macro stop-loss
                    self.recent_trades_tracker.append({'result': result})

                    position = None

        print(f"\n✅ Backtest complete! Regime changes: {regime_changes}")

    def analyze(self):
        """Анализ результатов"""
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

        avg_win = total_profit / wins if wins > 0 else 0
        avg_loss = total_loss / losses if losses > 0 else 0

        print("\n" + "="*70)
        print("📊 ADAPTIVE BACKTEST RESULTS")
        print("="*70)
        print(f"\n📈 Trades: {total} | Wins: {wins} ({win_rate:.1f}%) | Losses: {losses}")
        print(f"\n💰 PROFIT FACTOR: {pf:.2f}  ← ADAPTIVE!")
        print(f"   Total PnL: ${total_pnl:,.0f}")
        print(f"   Avg Win: ${avg_win:.2f}")
        print(f"   Avg Loss: ${avg_loss:.2f}")

        # По режимам
        print("\n📊 TRADES BY REGIME:")
        regime_stats = df.groupby('regime').agg({
            'pnl': ['count', 'sum'],
            'result': lambda x: (x == 'WIN').sum()
        })

        for regime in regime_stats.index:
            count = regime_stats.loc[regime, ('pnl', 'count')]
            pnl = regime_stats.loc[regime, ('pnl', 'sum')]
            wins_r = regime_stats.loc[regime, ('result', '<lambda>')]
            wr = (wins_r / count * 100) if count > 0 else 0
            print(f"   {regime:15s}: {count:3d} trades, {wr:5.1f}% WR, ${pnl:+,.0f}")

        print("\n" + "="*70)

        # Save
        os.makedirs("tests/results", exist_ok=True)
        csv_path = f"tests/results/backtest_adaptive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_path, index=False)
        print(f"💾 Saved: {csv_path}")

        return df

    def run(self):
        """Запустить adaptive backtest"""
        print("🚀 ADAPTIVE BACKTEST - ANTI CURVE FITTING")
        print("="*70)

        if self.load_data():
            self.calculate_features()
            self.backtest()
            self.analyze()

if __name__ == "__main__":
    bt = AdaptiveBacktest()
    bt.run()
