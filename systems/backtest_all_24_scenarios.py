# -*- coding: utf-8 -*-
"""
ФИНАЛЬНЫЙ BACKTEST: 24 СЦЕНАРИЯ + TOP-1 ПАРАМЕТРЫ
Использует gio_scenarios_top24_core.json
"""

import pandas as pd
import numpy as np
import ta
import json
from datetime import datetime
import os


class Backtest24Scenarios:
    """Backtest с TOP-1 параметрами и всеми 24 сценариями"""

    def __init__(self, csv_path, scenarios_json_path):
        self.csv_path = csv_path
        self.scenarios_json_path = scenarios_json_path
        self.df = None
        self.scenarios = []
        self.trades = []

    def load_scenarios(self):
        """Загрузить 24 сценария"""
        try:
            with open(self.scenarios_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.scenarios = data.get('scenarios', [])

            print(f"✅ Загружено {len(self.scenarios)} сценариев из {self.scenarios_json_path}")

            # Показать загруженные сценарии
            for scenario in self.scenarios:
                scenario_id = scenario.get('id', 'UNKNOWN')
                print(f"   - {scenario_id}")

        except Exception as e:
            print(f"❌ Ошибка загрузки сценариев: {e}")
            return False

        return True

    def load_and_prep(self):
        """Загрузка + индикаторы"""
        self.df = pd.read_csv(self.csv_path)

        # ATR
        atr_ind = ta.volatility.AverageTrueRange(
            self.df['high'], self.df['low'], self.df['close'], window=14
        )
        self.df['atr'] = atr_ind.average_true_range()

        # ADX
        adx_ind = ta.trend.ADXIndicator(
            self.df['high'], self.df['low'], self.df['close'], window=14
        )
        self.df['adx'] = adx_ind.adx()

        # Volume
        self.df['volume_sma'] = self.df['volume'].rolling(window=20, min_periods=1).mean()

        # RSI
        self.df['rsi'] = ta.momentum.RSIIndicator(self.df['close'], window=14).rsi()

        # EMA
        self.df['ema_20'] = self.df['close'].ewm(span=20, adjust=False).mean()
        self.df['ema_50'] = self.df['close'].ewm(span=50, adjust=False).mean()

        print("✅ Индикаторы рассчитаны!")

    def backtest_with_all_scenarios(self):
        """Backtest с TOP-1 параметрами и 24 сценариями"""

        # TOP-1 конфигурация
        SL_MULT = 1.2
        TP_MULT = 3.0
        MIN_ADX = 20
        MAX_ADX = 70
        MIN_RSI = 40
        MAX_RSI = 70
        MIN_VOL_MULT = 1.0
        USE_EMA = True

        print("\n" + "="*100)
        print("🏆 ФИНАЛЬНЫЙ BACKTEST: TOP-1 КОНФИГУРАЦИЯ + 24 СЦЕНАРИЯ")
        print("="*100)
        print(f"✅ TOP-1 параметры: SL={SL_MULT}x TP={TP_MULT}x ADX={MIN_ADX}-{MAX_ADX} RSI={MIN_RSI}-{MAX_RSI}")
        print(f"✅ Количество сценариев: {len(self.scenarios)}")
        print("="*100 + "\n")

        position = None
        trade_num = 0
        scenario_idx = 0

        for i in range(100, len(self.df)):
            row = self.df.iloc[i]

            # ВХОД
            if position is None:
                try:
                    # TOP-1 ФИЛЬТРЫ
                    if pd.isna(row['adx']) or not (MIN_ADX <= row['adx'] <= MAX_ADX):
                        continue

                    if pd.isna(row['volume_sma']) or row['volume_sma'] == 0:
                        continue
                    vol_ratio = row['volume'] / row['volume_sma']
                    if vol_ratio < MIN_VOL_MULT:
                        continue

                    if pd.isna(row['rsi']) or not (MIN_RSI <= row['rsi'] <= MAX_RSI):
                        continue

                    if USE_EMA:
                        if not (row['close'] > row['ema_20'] > row['ema_50']):
                            continue

                    # ВХОД - используем 24 сценария по ротации
                    trade_num += 1
                    scenario = self.scenarios[scenario_idx % len(self.scenarios)]
                    scenario_id = scenario.get('id', f'SCN_{scenario_idx:03d}')

                    atr_value = row['atr']

                    position = {
                        'trade_num': trade_num,
                        'entry_time': row['timestamp'],
                        'entry_price': row['close'],
                        'entry_atr': atr_value,
                        'entry_adx': row['adx'],
                        'entry_rsi': row['rsi'],
                        'entry_bar': i,
                        'tp': row['close'] + (atr_value * TP_MULT),
                        'sl_price': row['close'] - (atr_value * SL_MULT),
                        'scenario_id': scenario_id,
                    }

                    scenario_idx += 1

                    if trade_num % 10 == 0 or trade_num <= 20:
                        print(f"[{trade_num:3d}] ENTRY @ ${row['close']:>10.2f} | {scenario_id} | ADX={row['adx']:>5.1f} RSI={row['rsi']:>5.1f}")

                except Exception as e:
                    continue

            # ВЫХОД
            elif position is not None:
                try:
                    tp = position['tp']
                    sl_price = position['sl_price']

                    if row['high'] >= tp:
                        exit_price = tp
                        exit_reason = "TP"
                    elif row['low'] <= sl_price:
                        exit_price = sl_price
                        exit_reason = "SL"
                    else:
                        continue

                    pnl = exit_price - position['entry_price']
                    pnl_pct = (pnl / position['entry_price']) * 100
                    duration_bars = i - position['entry_bar']

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
                        'scenario_id': position['scenario_id'],
                        'tp_level': position['tp'],
                        'sl_level': position['sl_price'],
                        'result': 'WIN' if pnl > 0 else 'LOSS',
                    })

                    status = "✅" if pnl > 0 else "❌"
                    if position['trade_num'] % 10 == 0 or position['trade_num'] <= 20:
                        print(f"    EXIT @ ${exit_price:>10.2f} | {exit_reason} | {status} {pnl_pct:+6.2f}%")

                    position = None

                except:
                    continue

        print(f"\n✅ Завершено! Всего сделок: {len(self.trades)}")

    def analyze_and_save(self):
        """Анализ и сохранение результатов"""
        if not self.trades:
            print("❌ Нет сделок!")
            return

        df_trades = pd.DataFrame(self.trades)

        wins = df_trades[df_trades['result'] == 'WIN']
        losses = df_trades[df_trades['result'] == 'LOSS']

        win_rate = (len(wins) / len(df_trades)) * 100
        total_wins = wins['pnl'].sum()
        total_losses = abs(losses['pnl'].sum()) if len(losses) > 0 else 1
        pf = total_wins / total_losses if total_losses > 0 else 0

        avg_win = wins['pnl_pct'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_pct'].mean() if len(losses) > 0 else 0

        print("\n" + "="*100)
        print("📊 ФИНАЛЬНАЯ СТАТИСТИКА")
        print("="*100)
        print(f"📈 Trades: {len(df_trades)}")
        print(f"✅ Wins: {len(wins)} ({win_rate:.1f}%)")
        print(f"❌ Losses: {len(losses)} ({100-win_rate:.1f}%)")
        print(f"💰 Avg Win: {avg_win:+.2f}%")
        print(f"💸 Avg Loss: {avg_loss:.2f}%")
        print(f"⏱️ Avg Duration: {df_trades['duration_bars'].mean():.1f}h")
        print(f"\n🏆 Profit Factor: {pf:.2f}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print("="*100)

        # Анализ по сценариям
        print("\n📊 СТАТИСТИКА ПО СЦЕНАРИЯМ:")
        print("="*100)
        scenario_stats = []

        for scenario_id in df_trades['scenario_id'].unique():
            scenario_trades = df_trades[df_trades['scenario_id'] == scenario_id]
            scenario_wins = scenario_trades[scenario_trades['result'] == 'WIN']
            scenario_losses = scenario_trades[scenario_trades['result'] == 'LOSS']

            scenario_win_rate = (len(scenario_wins) / len(scenario_trades)) * 100 if len(scenario_trades) > 0 else 0

            scenario_total_wins = scenario_wins['pnl'].sum() if len(scenario_wins) > 0 else 0
            scenario_total_losses = abs(scenario_losses['pnl'].sum()) if len(scenario_losses) > 0 else 1
            scenario_pf = scenario_total_wins / scenario_total_losses if scenario_total_losses > 0 else 0

            scenario_stats.append({
                'scenario_id': scenario_id,
                'trades': len(scenario_trades),
                'wins': len(scenario_wins),
                'losses': len(scenario_losses),
                'win_rate': scenario_win_rate,
                'pf': scenario_pf,
            })

        df_scenario_stats = pd.DataFrame(scenario_stats)
        df_scenario_stats = df_scenario_stats.sort_values('pf', ascending=False)

        print(df_scenario_stats.to_string(index=False))
        print("="*100)

        # Сохранить
        os.makedirs("systems/results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Сохранить все сделки
        filename_trades = f"systems/results/backtest_24scenarios_{timestamp}.csv"
        df_trades.to_csv(filename_trades, index=False, encoding='utf-8-sig')
        print(f"\n💾 Сохранено (сделки): {filename_trades}")

        # Сохранить статистику по сценариям
        filename_stats = f"systems/results/backtest_24scenarios_stats_{timestamp}.csv"
        df_scenario_stats.to_csv(filename_stats, index=False, encoding='utf-8-sig')
        print(f"💾 Сохранено (статистика): {filename_stats}\n")

    def run(self):
        if not self.load_scenarios():
            return
        self.load_and_prep()
        self.backtest_with_all_scenarios()
        self.analyze_and_save()


if __name__ == "__main__":
    backtest = Backtest24Scenarios(
        "data/historical/BTCUSDT_1h_90d.csv",
        "data/scenarios/gio_scenarios_v35_enhanced.json"  # ← 24 СЦЕНАРИЯ
    )
    backtest.run()
