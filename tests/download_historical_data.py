"""
📥 HISTORICAL DATA DOWNLOADER v2.0
Загрузка реальных данных напрямую с Bybit API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
from pybit.unified_trading import HTTP

class HistoricalDataDownloader:
    """Загрузка исторических данных"""

    def __init__(self):
        self.session = HTTP(testnet=False)
        self.symbol = "BTCUSDT"
        self.output_dir = "data/historical"

        # Создать папку
        os.makedirs(self.output_dir, exist_ok=True)

    def download_klines(self, timeframe, days=30):
        """
        Загрузить свечи

        Args:
            timeframe: "60" (1h), "240" (4h)
            days: Количество дней назад
        """
        print(f"\n📥 Загрузка {timeframe}min данных за {days} дней...")

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # Конвертация в timestamp (milliseconds)
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)

        try:
            # Загрузить данные
            response = self.session.get_kline(
                category="linear",
                symbol=self.symbol,
                interval=timeframe,
                start=start_ts,
                end=end_ts,
                limit=1000
            )

            if response["retCode"] != 0:
                print(f"❌ API Error: {response['retMsg']}")
                return None

            klines = response["result"]["list"]

            if not klines:
                print(f"❌ Нет данных для {timeframe}min")
                return None

            # Конвертировать в DataFrame
            # Bybit возвращает: [timestamp, open, high, low, close, volume, turnover]
            df = pd.DataFrame(klines, columns=[
                "timestamp", "open", "high", "low", "close", "volume", "turnover"
            ])

            # Типы
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")
            df["open"] = df["open"].astype(float)
            df["high"] = df["high"].astype(float)
            df["low"] = df["low"].astype(float)
            df["close"] = df["close"].astype(float)
            df["volume"] = df["volume"].astype(float)

            # Убрать turnover (не нужен)
            df = df[["timestamp", "open", "high", "low", "close", "volume"]]

            # Сортировка по времени (Bybit возвращает в обратном порядке)
            df = df.sort_values("timestamp").reset_index(drop=True)

            # Сохранить
            tf_name = "1h" if timeframe == "60" else "4h"
            filename = f"{self.output_dir}/BTCUSDT_{tf_name}_{days}d.csv"
            df.to_csv(filename, index=False)

            print(f"✅ Сохранено: {filename}")
            print(f"   Свечей: {len(df)}")
            print(f"   Период: {df['timestamp'].min()} → {df['timestamp'].max()}")

            return df

        except Exception as e:
            print(f"❌ Ошибка загрузки {timeframe}min: {e}")
            return None

    def download_all(self, days=30):
        """Загрузить все таймфреймы"""
        print("\n" + "="*80)
        print("📥 ЗАГРУЗКА ИСТОРИЧЕСКИХ ДАННЫХ")
        print("="*80)

        # timeframe в минутах для Bybit
        timeframes = {
            "60": "1h",   # 1 час
            "240": "4h"   # 4 часа
        }

        results = {}

        for tf_mins, tf_name in timeframes.items():
            df = self.download_klines(tf_mins, days=days)
            if df is not None:
                results[tf_name] = df

        print("\n" + "="*80)
        print("✅ ЗАГРУЗКА ЗАВЕРШЕНА")
        print("="*80)

        for tf, df in results.items():
            print(f"\n{tf}: {len(df)} свечей")

        return results

def main():
    """Главная функция"""
    downloader = HistoricalDataDownloader()

    # Загрузить 90 дней данных
    downloader.download_all(days=90)  # ← ИЗМЕНИТЬ С 30 НА 90


if __name__ == "__main__":
    main()
