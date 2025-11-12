import json

# Загрузить финальный JSON
with open('data/scenarios/gio_scenarios_112_final_v3.json', 'r') as f:
    data = json.load(f)

# Проверить первый сценарий
scenario = data['scenarios'][0]

print("🔍 СТРУКТУРА ПЕРВОГО СЦЕНАРИЯ:")
print(f"ID: {scenario.get('id')}")
print(f"Keys: {list(scenario.keys())}")
print(f"\nConditions: {scenario.get('conditions', {})}")
print(f"\nmtf_trends: {scenario.get('conditions', {}).get('mtf_trends', 'NOT FOUND')}")

# Проверить статистику
mtf_count = 0
for s in data['scenarios'][:20]:
    if 'mtf_trends' in s.get('conditions', {}):
        mtf_count += 1

print(f"\n📊 MTF in first 20 scenarios: {mtf_count}/20")

# Детальная проверка первых 3
print("\n🔎 ДЕТАЛЬНАЯ ПРОВЕРКА ПЕРВЫХ 3:")
for i in range(min(3, len(data['scenarios']))):
    s = data['scenarios'][i]
    conditions = s.get('conditions', {})
    mtf = conditions.get('mtf_trends', {})
    print(f"\n{s.get('id')}:")
    print(f"  conditions keys: {list(conditions.keys())}")
    print(f"  mtf_trends: {mtf}")
    if mtf:
        print(f"  required: {mtf.get('required', 'NOT SET')}")
