# -*- coding: utf-8 -*-
"""
Скачивание 5-minute данных для ML training
Период: 180 дней (6 месяцев)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
from pybit.unified_trading import HTTP
import time

class HighFreqDataDownloader:
    """Загрузка 5-minute данных для ML"""

    def __init__(self):
        self.session = HTTP(testnet=False)
        self.output_dir = "data/ml_training"
        os.makedirs(self.output_dir, exist_ok=True)

    def download_5min_klines(self, symbol, days=180):
        """
        Загрузить 5-minute свечи

        Args:
            symbol: "BTCUSDT"
            days: 180 (6 месяцев)
        """
        print(f"\n📥 Загрузка 5min данных {symbol} за {days} дней...")

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        all_klines = []
        current_start = start_time

        while current_start < end_time:
            try:
                start_ts = int(current_start.timestamp() * 1000)
                end_ts = int((current_start + timedelta(days=7)).timestamp() * 1000)

                response = self.session.get_kline(
                    category="linear",
                    symbol=symbol,
                    interval="5",  # 5 minutes
                    start=start_ts,
                    end=end_ts,
                    limit=1000
                )

                if response["retCode"] == 0 and response["result"]["list"]:
                    klines = response["result"]["list"]
                    all_klines.extend(klines)

                    current_start += timedelta(days=7)
                    print(f"  ✅ Загружено {len(all_klines)} свечей до {current_start.strftime('%Y-%m-%d')}")

                    time.sleep(0.5)  # Rate limiting
                else:
                    print(f"  ⚠️ No data for period")
                    break

            except Exception as e:
                print(f"  ❌ Error: {e}")
                time.sleep(5)
                continue

        # Convert to DataFrame
        df = pd.DataFrame(all_klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])

        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)

        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Save
        filename = f"{self.output_dir}/{symbol}_5min_{days}d.csv"
        df.to_csv(filename, index=False)

        print(f"\n✅ Сохранено: {filename}")
        print(f"   Свечей: {len(df)}")
        print(f"   Период: {df['timestamp'].min()} → {df['timestamp'].max()}")

        return df

    def download_all_assets(self, assets=['BTCUSDT', 'ETHUSDT'], days=180):
        """Загрузить несколько активов"""
        print("\n" + "="*80)
        print("📥 ЗАГРУЗКА 5-MINUTE ДАННЫХ ДЛЯ ML TRAINING")
        print("="*80)

        results = {}

        for symbol in assets:
            df = self.download_5min_klines(symbol, days=days)
            if df is not None:
                results[symbol] = df
                print(f"\n{symbol}: {len(df)} свечей")

        print("\n" + "="*80)
        print("✅ ЗАГРУЗКА ЗАВЕРШЕНА")
        print("="*80)

        return results

def main():
    downloader = HighFreqDataDownloader()

    # Загрузить BTC и ETH (для портфолио)
    downloader.download_all_assets(
        assets=['BTCUSDT', 'ETHUSDT'],
        days=180  # 6 месяцев
    )

if __name__ == "__main__":
    main()
