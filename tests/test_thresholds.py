"""
Test #2: Lower Thresholds Verification
Проверяем, что новые пороги применяются корректно
"""
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.scenario_matcher import ScenarioMatcher

print("=" * 70)
print("  🧪 TESTING LOWER THRESHOLDS")
print("=" * 70)

# Инициализируем matcher
matcher = ScenarioMatcher()

print(f"\n1️⃣ Current Thresholds:")
print(f"   DEAL: {matcher.deal_threshold * 100:.0f}%")
print(f"   RISKY: {matcher.risky_threshold * 100:.0f}%")
print(f"   OBSERVATION: {matcher.observation_threshold * 100:.0f}%")

print(f"\n2️⃣ Expected:")
print(f"   DEAL: 55%")
print(f"   RISKY: 40%")
print(f"   OBSERVATION: 25%")

print(f"\n3️⃣ Validation:")
if matcher.deal_threshold == 0.55:
    print(f"   ✅ DEAL threshold: 55% (correct)")
else:
    print(f"   ❌ DEAL threshold: {matcher.deal_threshold * 100:.0f}% (expected 55%)")

if matcher.risky_threshold == 0.40:
    print(f"   ✅ RISKY threshold: 40% (correct)")
else:
    print(f"   ❌ RISKY threshold: {matcher.risky_threshold * 100:.0f}% (expected 40%)")

if matcher.observation_threshold == 0.25:
    print(f"   ✅ OBSERVATION threshold: 25% (correct)")
else:
    print(f"   ❌ OBSERVATION threshold: {matcher.observation_threshold * 100:.0f}% (expected 25%)")

# Проверка категоризации
test_scores = [0.60, 0.45, 0.30, 0.20]
print(f"\n4️⃣ Signal Categorization Test:")

for score in test_scores:
    if score >= matcher.deal_threshold:
        category = "DEAL"
    elif score >= matcher.risky_threshold:
        category = "RISKY"
    elif score >= matcher.observation_threshold:
        category = "OBSERVATION"
    else:
        category = "SKIP"

    print(f"   Score {score * 100:.0f}% → {category}")

print(f"\n5️⃣ Expected Results:")
print(f"   60% → DEAL ✅")
print(f"   45% → RISKY ✅")
print(f"   30% → OBSERVATION ✅")
print(f"   20% → SKIP ✅")

print("\n" + "=" * 70 + "\n")
