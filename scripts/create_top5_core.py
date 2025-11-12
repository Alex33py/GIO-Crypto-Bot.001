"""
Создать JSON с топ-5 CORE сценариями (обсуждённые ранее)
"""
import json

# Топ-5 ID сценариев (обсуждённые с пользователем)
TOP_5_CORE_IDS = [
    "SCN_001_LONG_MOMENTUM_CORE",       # Импульс LONG
    "SCN_002_LONG_MOMENTUM_HIGH_VOL",   # Импульс + объем LONG
    "SCN_004_LONG_PULLBACK_CORE",       # Откат LONG
    "SCN_013_SHORT_MOMENTUM_CORE",      # Импульс SHORT
    "SCN_016_SHORT_PULLBACK_CORE"       # Откат SHORT
]

def create_top5_core():
    """Создать топ-5 CORE сценариев"""

    # Загрузить полный JSON
    with open('data/scenarios/gio_scenarios_v35_enhanced.json', 'r', encoding='utf-8') as f:
        full_data = json.load(f)

    # Фильтровать только ТОП-5 CORE
    top5_scenarios = [
        s for s in full_data['scenarios']
        if s['id'] in TOP_5_CORE_IDS
    ]

    print(f"✅ Найдено {len(top5_scenarios)} из 5 сценариев")

    found_ids = [s['id'] for s in top5_scenarios]
    missing_ids = [id for id in TOP_5_CORE_IDS if id not in found_ids]

    if missing_ids:
        print(f"⚠️ Отсутствуют сценарии: {missing_ids}")
        print(f"   Возможно, они есть в полном файле")

    # Создать новый JSON
    output = {
        "meta": {
            "version": "3.5-top5-core",
            "description": "Top 5 CORE scenarios discussed with user",
            "date": "2025-11-05",
            "source": "gio_scenarios_v35_enhanced.json",
            "scenarios_found": len(top5_scenarios),
            "expected": 5,
            "changes": [
                "ADX trend strength filter",
                "CVD+Volume bonus confidence",
                "Improved MTF flexibility",
                "Priority system / RR rules"
            ]
        },
        "core_scenarios": {
            "long": {
                "momentum": ["SCN_001", "SCN_002"],
                "pullback": ["SCN_004"]
            },
            "short": {
                "momentum": ["SCN_013"],
                "pullback": ["SCN_016"]
            }
        },
        "scenarios": top5_scenarios
    }

    # Сохранить
    with open('data/scenarios/gio_scenarios_top5_core.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Создан файл: data/scenarios/gio_scenarios_top5_core.json")
    print(f"   Сценарии: {len(top5_scenarios)}")
    print(f"   Найдены:")
    for s in top5_scenarios:
        print(f"     - {s['id']}")

    if missing_ids:
        print(f"\n⚠️ ВНИМАНИЕ: {len(missing_ids)} сценарий отсутствует!")
        print(f"   Проверьте полный файл gio_scenarios_v35_enhanced.json")

    return len(top5_scenarios) == 5

if __name__ == "__main__":
    success = create_top5_core()

    if success:
        print(f"\n🎉 УСПЕШНО! Все 5 сценариев найдены и сохранены!")
    else:
        print(f"\n⚠️ ВНИМАНИЕ! Не все сценарии найдены. Проверьте файл.")
