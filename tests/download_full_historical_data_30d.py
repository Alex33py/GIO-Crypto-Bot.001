"""
📥 FULL HISTORICAL DATA DOWNLOADER - 30 DAYS
Загружает 30 дней данных с Bybit API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pybit.unified_trading import HTTP
import pandas as pd
from datetime import datetime, timedelta
import time

class FullDataDownloader:
    """Загрузчик ВСЕХ данных для полного бектеста"""

    def __init__(self):
        self.session = HTTP(testnet=False)
        self.symbol = "BTCUSDT"

    def download_klines(self, interval, days):
        """Загрузить свечи"""
        print(f"\n📥 Загрузка {interval} данных за {days} дней...")

        end_time = int(datetime.now().timestamp() * 1000)

        # Интервалы в миллисекундах
        intervals_ms = {
            "60": 60 * 60 * 1000,      # 1h
            "240": 4 * 60 * 60 * 1000  # 4h
        }

        interval_ms = intervals_ms.get(interval, 60 * 60 * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)

        all_data = []
        current_start = start_time

        while current_start < end_time:
            try:
                response = self.session.get_kline(
                    category="linear",
                    symbol=self.symbol,
                    interval=interval,
                    start=current_start,
                    end=min(current_start + (200 * interval_ms), end_time),
                    limit=200
                )

                if response["retCode"] == 0:
                    data = response["result"]["list"]

                    if not data:
                        break

                    all_data.extend(data)

                    # Следующий батч
                    last_timestamp = int(data[-1][0])
                    current_start = last_timestamp + interval_ms

                    print(f"   Загружено: {len(all_data)} свечей...", end='\r')
                    time.sleep(0.3)  # Rate limiting
                else:
                    print(f"\n❌ Ошибка API: {response['retMsg']}")
                    break

            except Exception as e:
                print(f"\n⚠️ Ошибка: {e}")
                print("   Повтор через 2 секунды...")
                time.sleep(2)
                continue

        if not all_data:
            print(f"\n❌ Нет данных для {interval}")
            return pd.DataFrame()

        # Конвертация в DataFrame
        df = pd.DataFrame(all_data, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])

        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")

        for col in ["open", "high", "low", "close", "volume", "turnover"]:
            df[col] = df[col].astype(float)

        df = df.sort_values("timestamp").reset_index(drop=True)

        # Удалить дубликаты
        df = df.drop_duplicates(subset=['timestamp'], keep='first')

        print(f"\n✅ Загружено: {len(df)} свечей                    ")

        return df

    def download_funding_rate(self, days):
        """Загрузить Funding Rate"""
        print(f"\n📥 Загрузка Funding Rate за {days} дней...")

        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        try:
            response = self.session.get_funding_rate_history(
                category="linear",
                symbol=self.symbol,
                startTime=start_time,
                endTime=end_time,
                limit=200
            )

            if response["retCode"] == 0:
                data = response["result"]["list"]

                df = pd.DataFrame(data)
                if not df.empty:
                    df["fundingRateTimestamp"] = pd.to_datetime(
                        df["fundingRateTimestamp"].astype(int), unit="ms"
                    )
                    df["fundingRate"] = df["fundingRate"].astype(float)

                print(f"✅ Загружено: {len(df)} записей")
                return df

        except Exception as e:
            print(f"⚠️ Funding Rate недоступен: {e}")
            return pd.DataFrame()

    def download_open_interest(self, interval, days):
        """Загрузить Open Interest"""
        print(f"\n📥 Загрузка Open Interest ({interval}) за {days} дней...")

        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        try:
            response = self.session.get_open_interest(
                category="linear",
                symbol=self.symbol,
                intervalTime=interval,
                startTime=start_time,
                endTime=end_time,
                limit=200
            )

            if response["retCode"] == 0:
                data = response["result"]["list"]

                df = pd.DataFrame(data)
                if not df.empty:
                    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")
                    df["openInterest"] = df["openInterest"].astype(float)

                print(f"✅ Загружено: {len(df)} записей")
                return df

        except Exception as e:
            print(f"⚠️ Open Interest недоступен: {e}")
            return pd.DataFrame()

    def download_tickers(self):
        """Загрузить текущий Ticker (для CVD)"""
        print(f"\n📥 Загрузка Ticker данных...")

        try:
            response = self.session.get_tickers(
                category="linear",
                symbol=self.symbol
            )

            if response["retCode"] == 0:
                print(f"✅ Ticker данные получены")
                return response["result"]["list"][0]

        except Exception as e:
            print(f"⚠️ Ticker недоступен: {e}")
            return {}

    def save_all_data(self):
        """Сохранить все данные"""
        print("\n" + "="*80)
        print("📥 ЗАГРУЗКА ПОЛНЫХ ИСТОРИЧЕСКИХ ДАННЫХ - 30 ДНЕЙ")
        print("="*80)

        # Создать папки
        os.makedirs("data/historical", exist_ok=True)

        # 1. Klines (свечи) - 30 ДНЕЙ!
        df_1h = self.download_klines("60", 30)
        df_4h = self.download_klines("240", 30)

        if not df_1h.empty:
            df_1h.to_csv("data/historical/BTCUSDT_1h_30d.csv", index=False)
            print(f"\n💾 Сохранено: data/historical/BTCUSDT_1h_30d.csv ({len(df_1h)} свечей)")

        if not df_4h.empty:
            df_4h.to_csv("data/historical/BTCUSDT_4h_30d.csv", index=False)
            print(f"💾 Сохранено: data/historical/BTCUSDT_4h_30d.csv ({len(df_4h)} свечей)")

        # 2. Funding Rate
        df_funding = self.download_funding_rate(30)
        if not df_funding.empty:
            df_funding.to_csv("data/historical/BTCUSDT_funding_30d.csv", index=False)
            print(f"💾 Сохранено: data/historical/BTCUSDT_funding_30d.csv ({len(df_funding)} записей)")

        # 3. Open Interest
        df_oi = self.download_open_interest("1h", 30)
        if not df_oi.empty:
            df_oi.to_csv("data/historical/BTCUSDT_oi_30d.csv", index=False)
            print(f"💾 Сохранено: data/historical/BTCUSDT_oi_30d.csv ({len(df_oi)} записей)")

        # 4. Ticker snapshot
        ticker = self.download_tickers()
        if ticker:
            pd.DataFrame([ticker]).to_csv("data/historical/BTCUSDT_ticker_snapshot.csv", index=False)
            print(f"💾 Сохранено: data/historical/BTCUSDT_ticker_snapshot.csv")

        print("\n" + "="*80)
        print("✅ ЗАГРУЗКА ЗАВЕРШЕНА")
        print("="*80)
        print(f"\n📊 Ожидаемые данные:")
        print(f"   1h: ~720 свечей (30 дней × 24 часа)")
        print(f"   4h: ~180 свечей (30 дней × 6 свечей)")
        print(f"   Funding: ~90 записей (каждые 8 часов)")
        print(f"   OI: ~200 записей (каждый час, макс limit)")

if __name__ == "__main__":
    downloader = FullDataDownloader()
    downloader.save_all_data()
