"""
Исправляем импорт scenario_matcher на unified_scenario_matcher
"""

file_path = "core/bot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем импорт
old_import = 'from core.scenario_matcher import EnhancedScenarioMatcher'
new_import = 'from systems.unified_scenario_matcher import EnhancedScenarioMatcher'

if old_import in content:
    content = content.replace(old_import, new_import)
    print(f"✅ Импорт изменён:")
    print(f"   Было: {old_import}")
    print(f"   Стало: {new_import}")
else:
    print("⚠️ Старый импорт не найден!")
    print("Ищем другие варианты...")
    
    # Альтернативные варианты
    if 'from core.scenario_matcher' in content:
        content = content.replace(
            'from core.scenario_matcher',
            'from systems.unified_scenario_matcher'
        )
        print("✅ Импорт изменён (альтернативный вариант)")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Файл core/bot.py обновлён!")
print("🎯 ПЕРЕЗАПУСТИ БОТА!")
