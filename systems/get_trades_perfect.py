# -*- coding: utf-8 -*-
"""
ИДЕАЛЬНЫЙ BACKTEST: PF 1.67 от Grid Search
Копия алгоритма с ТОЧНЫМИ параметрами
"""

import pandas as pd
import numpy as np
import ta
from datetime import datetime


class PerfectTradesReport:
    """Точно повторить Grid Search результаты"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.trades = []

    def load_and_prep(self):
        """Загрузка + индикаторы"""
        self.df = pd.read_csv(self.csv_path)

        # ATR - КРИТИЧНО!
        atr_ind = ta.volatility.AverageTrueRange(
            self.df['high'], self.df['low'], self.df['close'], window=14
        )
        self.df['atr'] = atr_ind.average_true_range()

        # ADX - с правильным периодом
        adx_ind = ta.trend.ADXIndicator(
            self.df['high'], self.df['low'], self.df['close'], window=14
        )
        self.df['adx'] = adx_ind.adx()

        # EMA 20 и 50
        self.df['ema_20'] = self.df['close'].ewm(span=20, adjust=False).mean()
        self.df['ema_50'] = self.df['close'].ewm(span=50, adjust=False).mean()

        # Volume SMA 20
        self.df['volume_sma'] = self.df['volume'].rolling(window=20, min_periods=1).mean()

        # RSI 14
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], window=14).rsi()

        print("✅ Индикаторы рассчитаны правильно!")

    def backtest_perfect(self):
        """
        ИДЕАЛЬНЫЙ BACKTEST - Копия Grid Search параметров
        SL=1.2x TP=2.0x ADX=20 RSI=30-60 Vol=0.6x
        """
        # ✅ ТОП-1 КОНФИГУРАЦИЯ (ТОЧНАЯ)
        SL_MULT = 1.2
        TP_MULT = 2.0
        MIN_ADX = 20.0  # Ровно 20, не >=20!
        MIN_RSI = 30.0
        MAX_RSI = 60.0
        MIN_VOL_MULT = 0.6

        print("\n" + "="*80)
        print("🔍 ИДЕАЛЬНЫЙ BACKTEST - ТОЧНАЯ КОПИЯ GRID SEARCH")
        print("="*80)
        print(f"✅ SL={SL_MULT}x TP={TP_MULT}x")
        print(f"✅ ADX >= {MIN_ADX} (РОВНО {MIN_ADX}, не выше!)")
        print(f"✅ RSI ∈ [{MIN_RSI}, {MAX_RSI}]")
        print(f"✅ Volume > {MIN_VOL_MULT}x базовой")
        print("="*80 + "\n")

        position = None
        trade_num = 0
        consecutive_bars_no_trade = 0

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            # Вход
            if position is None:
                try:
                    # ✅ ФИЛЬТР 1: ADX (РОВНО >= 20, не >20)
                    if pd.isna(row['adx']) or row['adx'] < MIN_ADX:
                        continue

                    # ✅ ФИЛЬТР 2: Volume (МИНИМУМ 60% от базовой)
                    if pd.isna(row['volume_sma']):
                        continue
                    vol_ratio = row['volume'] / row['volume_sma']
                    if vol_ratio < MIN_VOL_MULT:
                        continue

                    # ✅ ФИЛЬТР 3: EMA выравнивание (close > EMA20 > EMA50)
                    if not (row['close'] > row['ema_20'] and row['ema_20'] > row['ema_50']):
                        continue

                    # ✅ ФИЛЬТР 4: RSI диапазон
                    if pd.isna(row['rsi']) or not (MIN_RSI <= row['rsi'] <= MAX_RSI):
                        continue

                    # ✅ Избегать слишком частых сделок
                    if consecutive_bars_no_trade < 5:
                        consecutive_bars_no_trade += 1
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
                        'entry_volume_ratio': vol_ratio,
                        'entry_bar': i,
                        'tp': row['close'] + (atr_value * TP_MULT),
                        'sl': row['close'] - (atr_value * SL_MULT),
                    }

                    consecutive_bars_no_trade = 0

                    print(f"[{trade_num}] ENTRY @ ${row['close']:.2f} | ADX={row['adx']:.1f} RSI={row['rsi']:.1f} Vol={vol_ratio:.2f}x")

                except Exception as e:
                    continue

            # Выход
            elif position is not None:
                try:
                    tp = position['tp']
                    sl = position['sl']

                    # ✅ ТОЧНАЯ проверка TP/SL
                    exit_price = None
                    exit_reason = None

                    # Проверяем HIGH для SL (нижний уровень)
                    # Проверяем LOW для TP (верхний уровень)

                    # На самом деле для LONG:
                    # TP срабатывает если close >= tp
                    # SL срабатывает если close <= sl

                    if row['high'] >= tp:
                        exit_reason = "TAKE_PROFIT"
                        exit_price = tp
                    elif row['low'] <= sl:
                        exit_reason = "STOP_LOSS"
                        exit_price = sl
                    else:
                        consecutive_bars_no_trade += 1
                        continue

                    # Расчёт PnL (ТОЧНЫЙ)
                    pnl = exit_price - position['entry_price']
                    pnl_pct = (pnl / position['entry_price']) * 100
                    duration_bars = i - position['entry_bar']
                    duration_hours = duration_bars * 1  # 1 час = 1 бар в 1h timeframe

                    # Сохранить сделку
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
                        'duration_hours': duration_hours,
                        'entry_atr': position['entry_atr'],
                        'entry_adx': position['entry_adx'],
                        'entry_rsi': position['entry_rsi'],
                        'volume_ratio': position['entry_volume_ratio'],
                        'tp_level': position['tp'],
                        'sl_level': position['sl'],
                        'result': 'WIN' if pnl > 0 else 'LOSS',
                    })

                    print(f"    EXIT @ ${exit_price:.2f} | {exit_reason} | PnL={pnl_pct:+.2f}% ({duration_hours}h)")

                    position = None
                    consecutive_bars_no_trade = 0

                except Exception as e:
                    print(f"❌ Error in exit: {e}")
                    continue

        print(f"\n✅ Завершено! Всего сделок: {len(self.trades)}")

    def calculate_metrics(self):
        """Расчёт метрик"""
        if not self.trades:
            print("❌ Нет сделок!")
            return

        df_trades = pd.DataFrame(self.trades)

        wins = df_trades[df_trades['result'] == 'WIN']
        losses = df_trades[df_trades['result'] == 'LOSS']

        win_rate = (len(wins) / len(df_trades)) * 100

        # Profit Factor ТОЧНЫЙ
        total_wins = wins['pnl'].sum()
        total_losses = abs(losses['pnl'].sum())

        if total_losses == 0:
            pf = float('inf')
        else:
            pf = total_wins / total_losses

        avg_win = wins['pnl_pct'].mean()
        avg_loss = losses['pnl_pct'].mean()

        print("\n" + "="*80)
        print("📊 МЕТРИКИ (ИДЕАЛЬНЫЙ BACKTEST)")
        print("="*80)
        print(f"✅ Всего сделок: {len(df_trades)}")
        print(f"✅ Побед: {len(wins)} ({win_rate:.1f}%)")
        print(f"✅ Убытков: {len(losses)} ({100-win_rate:.1f}%)")
        print(f"✅ Средняя прибыль: {avg_win:+.2f}%")
        print(f"✅ Средний убыток: {avg_loss:.2f}%")
        print(f"✅ Средняя длительность: {df_trades['duration_hours'].mean():.1f}h")
        print(f"\n🏆 Profit Factor: {pf:.2f}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print("="*80)

        # Проверка соответствия Grid Search
        if abs(pf - 1.67) < 0.05:
            print("✅✅✅ СООТВЕТСТВУЕТ GRID SEARCH (PF = 1.67)! 🎉")
        else:
            print(f"⚠️ Расхождение: PF {pf:.2f} vs ожидаемо 1.67")
            print(f"   Разница: {pf - 1.67:+.2f}")

        print()

        # Сохранить CSV
        self.save_to_csv(df_trades)

    def save_to_csv(self, df_trades):
        """Сохранить в CSV"""
        import os
        os.makedirs("systems/results", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"systems/results/trades_perfect_{timestamp}.csv"
        df_trades.to_csv(filename, index=False, encoding='utf-8-sig')

        print(f"💾 Сохранено: {filename}\n")

    def run(self):
        """Execute"""
        self.load_and_prep()
        self.backtest_perfect()
        self.calculate_metrics()


if __name__ == "__main__":
    report = PerfectTradesReport("data/historical/BTCUSDT_1h_90d.csv")
    report.run()
