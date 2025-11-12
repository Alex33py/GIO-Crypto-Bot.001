# -*- coding: utf-8 -*-
"""
Детальный отчёт по сделкам для ТОП-1 конфигурации
SL=1.2x TP=2.0x ADX=20 RSI=30-60 Vol=0.6x
"""

import pandas as pd
import numpy as np
import ta
from datetime import datetime


class TradesDetailReport:
    """Получить детальный отчёт по всем сделкам"""

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None
        self.trades = []

    def load_and_prep(self):
        """Загрузка + индикаторы"""
        self.df = pd.read_csv(self.csv_path)

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

        # Volume
        self.df['volume_sma'] = self.df['volume'].rolling(20).mean()

        # RSI
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], 14).rsi()

        # Momentum
        self.df['price_momentum'] = self.df['close'].pct_change(5).rolling(5).mean()

        print("✅ Индикаторы рассчитаны!")

    def backtest_with_details(self):
        """
        Backtest с ТОП-1 параметрами + детали каждой сделки
        """
        # ✅ ТОП-1 КОНФИГУРАЦИЯ
        SL_MULT = 1.2
        TP_MULT = 2.0
        MIN_ADX = 20
        MIN_RSI = 30
        MAX_RSI = 60
        MIN_VOL_MULT = 0.6

        print("\n🚀 Запуск backtest с ТОП-1 параметрами...")
        print(f"   SL={SL_MULT}x TP={TP_MULT}x ADX>={MIN_ADX} RSI={MIN_RSI}-{MAX_RSI} Vol>{MIN_VOL_MULT}x\n")

        position = None
        trade_num = 0

        for i in range(200, len(self.df)):
            row = self.df.iloc[i]

            # Вход
            if position is None:
                try:
                    # ФИЛЬТРЫ
                    if not (pd.notna(row['adx']) and row['adx'] >= MIN_ADX):
                        continue

                    if not (row['volume'] > row['volume_sma'] * MIN_VOL_MULT):
                        continue

                    if not (row['close'] > row['ema_20'] > row['ema_50']):
                        continue

                    if not (MIN_RSI <= row['rsi'] <= MAX_RSI):
                        continue

                    # ВХОД
                    trade_num += 1

                    position = {
                        'trade_num': trade_num,
                        'entry_time': row['timestamp'],
                        'entry_price': row['close'],
                        'entry_atr': row['atr'],
                        'entry_adx': row['adx'],
                        'entry_rsi': row['rsi'],
                        'entry_volume': row['volume'],
                        'entry_bar': i,
                        'tp': row['close'] + (row['atr'] * TP_MULT),
                        'sl': row['close'] - (row['atr'] * SL_MULT),
                    }

                    print(f"[{trade_num}] ENTRY @ {row['close']:.2f} | ADX={row['adx']:.1f} RSI={row['rsi']:.1f}")

                except Exception as e:
                    continue

            # Выход
            elif position is not None:
                try:
                    tp = position['tp']
                    sl = position['sl']

                    # Проверка TP/SL
                    if row['close'] >= tp:
                        exit_reason = "TAKE_PROFIT"
                        exit_price = tp
                    elif row['close'] <= sl:
                        exit_reason = "STOP_LOSS"
                        exit_price = sl
                    else:
                        continue

                    # Расчёт PnL
                    pnl = exit_price - position['entry_price']
                    pnl_pct = (pnl / position['entry_price']) * 100
                    duration_bars = i - position['entry_bar']

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
                        'entry_atr': position['entry_atr'],
                        'entry_adx': position['entry_adx'],
                        'entry_rsi': position['entry_rsi'],
                        'tp_level': position['tp'],
                        'sl_level': position['sl'],
                        'result': 'WIN' if pnl > 0 else 'LOSS',
                    })

                    print(f"    EXIT @ {exit_price:.2f} | {exit_reason} | PnL={pnl_pct:+.2f}% | Duration={duration_bars}h")

                    position = None

                except Exception as e:
                    continue

        print(f"\n✅ Завершено! Всего сделок: {len(self.trades)}")

    def save_to_csv(self):
        """Сохранить в CSV"""
        if not self.trades:
            print("❌ Нет сделок для сохранения!")
            return

        df_trades = pd.DataFrame(self.trades)

        # Сортировка по номеру сделки
        df_trades = df_trades.sort_values('trade_num')

        # Создать папку results
        import os
        os.makedirs("systems/results", exist_ok=True)

        # Сохранить CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"systems/results/trades_details_{timestamp}.csv"
        df_trades.to_csv(filename, index=False, encoding='utf-8-sig')

        print(f"\n💾 Сохранено: {filename}")

        # Вывод статистики
        wins = df_trades[df_trades['result'] == 'WIN']
        losses = df_trades[df_trades['result'] == 'LOSS']

        print("\n" + "="*80)
        print("📊 СТАТИСТИКА ПО СДЕЛКАМ")
        print("="*80)
        print(f"Всего сделок: {len(df_trades)}")
        print(f"Побед: {len(wins)} ({len(wins)/len(df_trades)*100:.1f}%)")
        print(f"Убытков: {len(losses)} ({len(losses)/len(df_trades)*100:.1f}%)")
        print(f"Средняя прибыль: {wins['pnl_pct'].mean():.2f}%")
        print(f"Средний убыток: {losses['pnl_pct'].mean():.2f}%")
        print(f"Средняя длительность: {df_trades['duration_bars'].mean():.1f} часов")
        print(f"Profit Factor: {wins['pnl'].sum() / abs(losses['pnl'].sum()):.2f}")
        print("="*80)

        # Топ-5 лучших и худших сделок
        print("\n🏆 ТОП-5 ЛУЧШИХ СДЕЛОК:")
        top5 = df_trades.nlargest(5, 'pnl_pct')[['trade_num', 'entry_time', 'pnl_pct', 'duration_bars']]
        for idx, row in top5.iterrows():
            print(f"  #{row['trade_num']}: {row['entry_time']} → +{row['pnl_pct']:.2f}% ({row['duration_bars']}h)")

        print("\n📉 ТОП-5 ХУДШИХ СДЕЛОК:")
        worst5 = df_trades.nsmallest(5, 'pnl_pct')[['trade_num', 'entry_time', 'pnl_pct', 'duration_bars']]
        for idx, row in worst5.iterrows():
            print(f"  #{row['trade_num']}: {row['entry_time']} → {row['pnl_pct']:.2f}% ({row['duration_bars']}h)")

        print("\n")

    def run(self):
        """Execute"""
        print("\n" + "="*80)
        print("🔍 ДЕТАЛЬНЫЙ ОТЧЁТ: ТОП-1 КОНФИГУРАЦИЯ")
        print("="*80)

        self.load_and_prep()
        self.backtest_with_details()
        self.save_to_csv()


if __name__ == "__main__":
    report = TradesDetailReport("data/historical/BTCUSDT_1h_90d.csv")
    report.run()
