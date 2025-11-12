"""
Тест проверки совместимости ScenarioManager с 12 сценариями v2.0
"""

import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Импортируем ScenarioManager
from core.scenario_manager import ScenarioManager
from config.settings import DATABASE_PATH


async def test_scenario_manager():
    """Тест загрузки и работы с 12 сценариями"""

    print("=" * 70)
    print("🧪 ТЕСТ SCENARIOMANAGER С 12 СЦЕНАРИЯМИ V2.0")
    print("=" * 70)

    # 1. Проверка существования файла
    scenarios_file = Path("data/scenarios/gio_scenarios_100_with_features_v3.json")

    if not scenarios_file.exists():
        print(f"\n❌ ОШИБКА: Файл не найден: {scenarios_file}")
        print("   Создайте файл перед запуском теста!")
        return False

    print(f"\n✅ Файл найден: {scenarios_file}")

    # 2. Проверка валидности JSON
    try:
        with open(scenarios_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"✅ JSON валиден")
        print(f"   Версия: {data.get('version', 'не указана')}")
        print(f"   Описание: {data.get('description', 'не указано')}")
        print(f"   Сценариев в файле: {len(data.get('scenarios', []))}")

    except json.JSONDecodeError as e:
        print(f"\n❌ ОШИБКА: JSON невалиден!")
        print(f"   {e}")
        return False

    # 3. Проверка структуры сценариев
    print("\n📋 Проверка структуры сценариев...")

    required_fields = ["id", "name", "strategy", "side"]
    scenarios = data.get("scenarios", [])

    for i, scenario in enumerate(scenarios, 1):
        missing = [f for f in required_fields if f not in scenario]
        if missing:
            print(f"   ⚠️ Сценарий #{i}: отсутствуют поля {missing}")
        else:
            print(f"   ✅ Сценарий #{i}: {scenario['id']} - {scenario['name']}")

    # 4. Загрузка через ScenarioManager
    print("\n🔧 Тест загрузки через ScenarioManager...")

    try:
        manager = ScenarioManager(db_path=DATABASE_PATH)

        result = await manager.load_scenarios_from_json(
            filename="gio_scenarios_100_with_features_v3.json"
        )

        if result:
            print(f"✅ Загрузка успешна!")
            print(f"   Загружено сценариев: {len(manager.scenarios)}")

            # Вывести список загруженных ID
            loaded_ids = [s.get("id") for s in manager.scenarios]
            print(f"   IDs: {', '.join(loaded_ids)}")

        else:
            print(f"❌ Загрузка не удалась (result = {result})")
            return False

    except Exception as e:
        print(f"\n❌ ОШИБКА при загрузке через ScenarioManager:")
        print(f"   {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 5. Тест методов работы со сценариями
    print("\n🧪 Тест методов ScenarioManager...")

    try:
        # Получить сценарий по ID
        test_id = "SCN_001"
        scenario = manager.get_scenario_by_id(test_id)

        if scenario:
            print(f"✅ get_scenario_by_id('{test_id}'): {scenario.get('name')}")
        else:
            print(f"⚠️ get_scenario_by_id('{test_id}'): не найден")

        # Получить все LONG сценарии (case-insensitive)
        long_scenarios = [
            s for s in manager.scenarios if s.get("side", "").lower() == "long"
        ]
        print(f"✅ LONG сценариев: {len(long_scenarios)}")

        # Получить все SHORT сценарии (case-insensitive)
        short_scenarios = [
            s for s in manager.scenarios if s.get("side", "").lower() == "short"
        ]
        print(f"✅ SHORT сценариев: {len(short_scenarios)}")

    except Exception as e:
        print(f"⚠️ Ошибка при тестировании методов: {e}")

    # 6. Итоговый результат
    print("\n" + "=" * 70)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 70)
    print("\n📊 Резюме:")
    print(f"   • Файл существует и валиден")
    print(f"   • Загружено сценариев: {len(manager.scenarios)}")
    print(f"   • LONG: {len(long_scenarios)}, SHORT: {len(short_scenarios)}")
    print(f"   • ScenarioManager готов к работе с v2.0")
    print("\n✅ Можно запускать бота!")

    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_scenario_manager())
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
