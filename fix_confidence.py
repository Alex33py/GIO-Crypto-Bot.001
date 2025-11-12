import json

# Открой файл
with open('data/scenarios/gio_scenarios_top5_core.json', 'r') as f:
    data = json.load(f)

# Изменить глобальные пороги
for scenario in data.get('scenarios', []):
    # 1. Измени confidence_threshold
    if 'if' in scenario and 'confidence_threshold' in scenario['if']:
        scenario['if']['confidence_threshold'] = ["score >= 0.60"]

    # 2. Измени scoring_system
    if 'scoring_system' in scenario:
        scenario['scoring_system']['deal_threshold'] = 0.55
        scenario['scoring_system']['high_confidence_threshold'] = 0.70
        scenario['scoring_system']['min_metrics_required'] = 2

# Сохрани
with open('data/scenarios/gio_scenarios_top5_core.json', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ Confidence порог снижен с 0.75 на 0.60!")
print("✅ Deal threshold: 0.65 → 0.55")
print("✅ Min metrics required: 4 → 2")
