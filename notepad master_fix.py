"""
МАСТЕР-ФИКС: Все исправления одним скриптом
"""
import json

print("="*60)
print("🔧 МАСТЕР-ФИКС: Снижение требований для генерации сигналов")
print("="*60)

# 1. MTF Requirements
print("\n1️⃣ Модифицируем MTF требования...")
file_path = "data/scenarios/gio_scenarios_top5_core.json"

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for scenario in data.get('scenarios', []):
    if scenario['side'] == 'long':
        mtf = scenario.get('mtf', {})
        conditions = mtf.get('conditions', {})
        if '1D' in conditions:
            conditions['1D'] = ['bullish', 'neutral', 'bearish']
        mtf['required_alignment'] = 2
        print(f"   ✅ {scenario['id']}: 1D любой тренд, alignment=2")

    elif scenario['side'] == 'short':
        mtf = scenario.get('mtf', {})
        conditions = mtf.get('conditions', {})
        if '1H' in conditions:
            conditions['1H'] = ['bearish', 'neutral', 'bullish']
        if '4H' in conditions:
            conditions['4H'] = ['bearish', 'neutral', 'bullish']
        mtf['required_alignment'] = 2
        print(f"   ✅ {scenario['id']}: 1H/4H любой тренд, alignment=2")

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("   ✅ MTF требования снижены!")

# 2. ADX Threshold
print("\n2️⃣ Снижаем ADX порог с 30 на 20...")
file_path = "trading/unified_scenario_matcher.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('if adx < 25:', 'if adx < 20:')
content = content.replace('< 25, нет тренда', '< 20, нет тренда')
content = content.replace('min_adx=30,', 'min_adx=20,')
content = content.replace('if adx < 30:', 'if adx < 20:')
content = content.replace('"adx_filter": adx >= 30,', '"adx_filter": adx >= 20,')
content = content.replace('adx >= 40 and', 'adx >= 30 and')
content = content.replace('adx >= 30 and', 'adx >= 20 and')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("   ✅ ADX порог снижен до 20!")

# 3. Confidence Threshold
print("\n3️⃣ Снижаем confidence порог...")
file_path = "core/bot.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('min_confidence = 0.60', 'min_confidence = 0.45')
content = content.replace('MIN_CONFIDENCE = 0.60', 'MIN_CONFIDENCE = 0.45')
content = content.replace('confidence_score < 0.60:', 'confidence_score < 0.45:')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("   ✅ Confidence порог снижен до 0.45!")

print("\n" + "="*60)
print("✅ ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
print("="*60)
print("\n🎯 ПЕРЕЗАПУСТИ БОТА:")
print("   Ctrl+C")
print("   python main.py --mode live --log-level INFO")
print("\n⏱️ Жди 5-10 минут, затем проверь /signals")
