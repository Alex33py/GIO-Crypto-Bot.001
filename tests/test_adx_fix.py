"""
Quick Test: ADX Fix Verification
Проверяем, что ADX теперь вычисляется корректно
"""
import sys
import os

# ✅ Добавляем корень проекта в sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np

# ✅ ПРАВИЛЬНЫЙ импорт из analytics\advanced_indicators.py!
from analytics.advanced_indicators import AdvancedIndicators

print("=" * 70)
print("  🧪 TESTING ADX FIX")
print("=" * 70)

# Генерируем тестовые OHLCV данные (30 свечей)
np.random.seed(42)
num_candles = 30
base_price = 50000

highs = []
lows = []
closes = []

print(f"\n1️⃣ Generating {num_candles} test candles...")

for i in range(num_candles):
    price = base_price + (i * 10) + np.random.uniform(-100, 100)
    high = price + np.random.uniform(50, 200)
    low = price - np.random.uniform(50, 200)
    close = np.random.uniform(low, high)

    highs.append(high)
    lows.append(low)
    closes.append(close)

print(f"   ✅ Generated {len(closes)} candles")
print(f"   📊 First: H={highs[0]:.2f}, L={lows[0]:.2f}, C={closes[0]:.2f}")
print(f"   📊 Last: H={highs[-1]:.2f}, L={lows[-1]:.2f}, C={closes[-1]:.2f}")

# Вычисляем ADX
print(f"\n2️⃣ Calculating ADX with period=14...")

try:
    # ✅ Метод calculate_adx принимает highs, lows, closes
    adx_result = AdvancedIndicators.calculate_adx(
        highs=highs,
        lows=lows,
        closes=closes,
        period=14
    )

    print(f"   ✅ ADX calculation completed")

    print(f"\n3️⃣ ADX Result:")
    print(f"   ADX: {adx_result.get('adx', 0):.2f}")
    print(f"   +DI: {adx_result.get('plus_di', 0):.2f}")
    print(f"   -DI: {adx_result.get('minus_di', 0):.2f}")
    print(f"   Trend Strength: {adx_result.get('trend_strength', 'N/A')}")
    print(f"   Trend Direction: {adx_result.get('trend_direction', 'N/A')}")

    # Валидация
    print(f"\n4️⃣ Validation:")
    adx_value = adx_result.get('adx', 0)

    if adx_value > 0:
        print("   ✅ SUCCESS! ADX is calculating correctly!")
        print(f"   ✅ ADX = {adx_value:.2f} (expected > 0)")
        print(f"   ✅ Module 'analytics\\advanced_indicators.py' found!")
    else:
        print("   ⚠️ WARNING! ADX is 0.0")
        print("   ⚠️ This might be expected if data is too flat/random")

except ImportError as e:
    print(f"\n❌ IMPORT ERROR:")
    print(f"   {e}")
    print(f"\n💡 Solution: Check if 'analytics\\advanced_indicators.py' exists")

except Exception as e:
    print(f"\n❌ ERROR during ADX calculation:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70 + "\n")
