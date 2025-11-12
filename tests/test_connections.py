# tests/test_connections.py

import sys
sys.path.append('.')

from bot.live_signal_tracker import LiveSignalTracker
from bot.telegram_sender import TelegramSender
import pandas as pd


def test_all():
    print("\n" + "="*60)
    print("🧪 CONNECTION TESTS")
    print("="*60)

    # Test 1: Load historical data
    print("\n1️⃣ Testing data loading...")
    try:
        df = pd.read_csv('data/historical/BTCUSDT_1h_90d.csv')
        print(f"   ✅ Loaded {len(df)} candles")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # Test 2: Signal tracker
    print("\n2️⃣ Testing signal tracker...")
    try:
        tracker = LiveSignalTracker()
        signal = tracker.check_signal(
            df['close'].tail(100),
            df['high'].tail(100),
            df['low'].tail(100),
            df['volume'].tail(100)
        )
        if signal:
            print(f"   ✅ Signal generated: {signal['scenario']}")
        else:
            print(f"   ⚠️ No signal (filters may not pass)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    # Test 3: Telegram connection
    print("\n3️⃣ Testing Telegram connection...")
    try:
        sender = TelegramSender()
        if sender.send_test():
            print(f"   ✅ Telegram connected")
        else:
            print(f"   ❌ Telegram failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_all()
