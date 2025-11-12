import json

data = json.load(open('data/scenarios/gio_scenarios_100_with_features_v3.json'))

print("Проверка формата сценариев:\n")
for i, s in enumerate(data['scenarios'][:20]):
    has_if = bool(s.get('if'))
    has_conditions = bool(s.get('conditions'))
    print(f"{s['id']:10} | if={str(has_if):5} | conditions={str(has_conditions):5}")
