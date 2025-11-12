"""
Фикс ADX порога в правильном файле
"""

file_path = "systems/unified_scenario_matcher.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем все вхождения ADX порогов
replacements = {
    'if adx < 25:': 'if adx < 20:',
    'ADX={adx:.1f} < 25': 'ADX={adx:.1f} < 20',
    'min_adx=30': 'min_adx=20',
    'if adx < 30:': 'if adx < 20:',
    'adx >= 30,': 'adx >= 20,',
    'adx >= 40 and': 'adx >= 30 and',
}

changes = 0
for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        changes += 1
        print(f"✅ Заменено: {old} → {new}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ ADX пороги обновлены! Изменений: {changes}")
print("🎯 ПЕРЕЗАПУСТИ БОТА!")
