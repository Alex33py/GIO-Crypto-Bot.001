"""Test Day 5: Optimized Parameters"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scenario_matcher import UnifiedScenarioMatcher as ScenarioMatcher

print("=" * 70)
print("  🧪 TESTING DAY 5 PARAMETERS")
print("=" * 70)

matcher = ScenarioMatcher()

print(f"\n1️⃣ Current Thresholds:")
print(f"   DEAL: {matcher.deal_threshold * 100:.0f}%")
print(f"   RISKY: {matcher.risky_threshold * 100:.0f}%")
print(f"   OBSERVATION: {matcher.observation_threshold * 100:.0f}%")

print(f"\n2️⃣ Expected (Day 5):")
print(f"   DEAL: 70%")
print(f"   RISKY: 55%")
print(f"   OBSERVATION: 35%")

print(f"\n3️⃣ Validation:")
if matcher.deal_threshold == 0.70:
    print(f"   ✅ DEAL: 70% (correct)")
else:
    print(f"   ❌ DEAL: {matcher.deal_threshold * 100:.0f}% (expected 70%)")

if matcher.risky_threshold == 0.55:
    print(f"   ✅ RISKY: 55% (correct)")
else:
    print(f"   ❌ RISKY: {matcher.risky_threshold * 100:.0f}% (expected 55%)")

if matcher.observation_threshold == 0.35:
    print(f"   ✅ OBSERVATION: 35% (correct)")
else:
    print(f"   ❌ OBSERVATION: {matcher.observation_threshold * 100:.0f}% (expected 35%)")

# Тест категоризации
test_scores = [0.75, 0.60, 0.40, 0.30]
print(f"\n4️⃣ Signal Categorization:")
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
print(f"   75% → DEAL ✅")
print(f"   60% → RISKY ✅")
print(f"   40% → OBSERVATION ✅")
print(f"   30% → SKIP ✅")

print("\n" + "=" * 70 + "\n")
