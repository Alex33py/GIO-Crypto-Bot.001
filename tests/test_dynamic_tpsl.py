"""
Test #3: Dynamic TP/SL with ATR
Проверяем адаптивные TP/SL на основе ATR
"""
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np
from analytics.advanced_indicators import AdvancedIndicators

print("=" * 70)
print("  🧪 TESTING DYNAMIC TP/SL WITH ATR")
print("=" * 70)

# Генерируем тестовые данные
np.random.seed(42)
num_candles = 30
base_price = 50000

highs = []
lows = []
closes = []

for i in range(num_candles):
    price = base_price + (i * 10) + np.random.uniform(-100, 100)
    high = price + np.random.uniform(50, 200)
    low = price - np.random.uniform(50, 200)
    close = np.random.uniform(low, high)

    highs.append(high)
    lows.append(low)
    closes.append(close)

print(f"\n1️⃣ Calculating ATR...")

# Вычисляем ATR
atr_result = AdvancedIndicators.calculate_atr(
    highs=highs,
    lows=lows,
    closes=closes,
    period=14
)

atr = atr_result.get('atr', 0)  # ✅ Извлекаем значение из Dict

current_price = closes[-1]
print(f"   Current Price: {current_price:.2f}")
print(f"   ATR (14): {atr:.2f}")


# Вычисляем динамические TP/SL
atr_percent = (atr / current_price) * 100

sl_percent = atr_percent * 1.5
tp1_percent = atr_percent * 2.0
tp2_percent = atr_percent * 3.0
tp3_percent = atr_percent * 4.0

print(f"\n2️⃣ ATR-based Percentages:")
print(f"   ATR%: {atr_percent:.2f}%")
print(f"   SL%: {sl_percent:.2f}% (1.5x ATR)")
print(f"   TP1%: {tp1_percent:.2f}% (2x ATR)")
print(f"   TP2%: {tp2_percent:.2f}% (3x ATR)")
print(f"   TP3%: {tp3_percent:.2f}% (4x ATR)")

# Long позиция
print(f"\n3️⃣ LONG Position Prices:")
stop_loss = current_price * (1 - sl_percent / 100)
tp1 = current_price * (1 + tp1_percent / 100)
tp2 = current_price * (1 + tp2_percent / 100)
tp3 = current_price * (1 + tp3_percent / 100)

print(f"   Entry: {current_price:.2f}")
print(f"   SL: {stop_loss:.2f} ({-sl_percent:.2f}%)")
print(f"   TP1: {tp1:.2f} (+{tp1_percent:.2f}%)")
print(f"   TP2: {tp2:.2f} (+{tp2_percent:.2f}%)")
print(f"   TP3: {tp3:.2f} (+{tp3_percent:.2f}%)")

# Risk:Reward Ratio
rr_ratio = tp1_percent / sl_percent
print(f"\n4️⃣ Risk:Reward Ratio:")
print(f"   TP1:SL = {rr_ratio:.2f}:1")
print(f"   Expected: ~1.33:1 (2.0/1.5)")

print(f"\n5️⃣ Validation:")
if atr > 0:
    print(f"   ✅ ATR calculated: {atr:.2f}")
else:
    print(f"   ❌ ATR is 0")

if 1.2 <= rr_ratio <= 1.5:
    print(f"   ✅ Risk:Reward ratio looks good: {rr_ratio:.2f}:1")
else:
    print(f"   ⚠️ Risk:Reward ratio unusual: {rr_ratio:.2f}:1")

print("\n" + "=" * 70 + "\n")
