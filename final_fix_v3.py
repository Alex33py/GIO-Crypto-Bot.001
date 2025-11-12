"""
ФИНАЛЬНЫЙ КОМПЛЕКСНЫЙ ФИКС v3
С правильной структурой JSON и путями к файлам
"""
import json
import re

print("="*60)
print("🔧 ФИНАЛЬНЫЙ КОМПЛЕКСНЫЙ ФИКС v3")
print("="*60)

# 1. MTF Requirements + ADX Thresholds в JSON
print("\n1️⃣ Модифицируем JSON сценариев...")
file_path = "data/scenarios/gio_scenarios_top5_core.json"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scenarios = data.get('scenarios', [])
    modified_count = 0
    
    for scenario in scenarios:
        scenario_id = scenario.get('id', 'unknown')
        
        # Модифицируем MTF alignment
        if 'if' in scenario and 'mtf_alignment' in scenario['if']:
            mtf_alignment = scenario['if']['mtf_alignment']
            
            for i, condition in enumerate(mtf_alignment):
                # Для LONG: разреши bearish на 1d
                if 'LONG' in scenario_id and 'trend_1d' in condition:
                    # Удалим строгие требования к 1d
                    mtf_alignment[i] = "trend_1d != None"  # Любой тренд
                    print(f"   ✅ {scenario_id}: 1d = любой тренд")
                    modified_count += 1
                
                # Для SHORT: разреши bullish на 1h/4h
                elif 'SHORT' in scenario_id:
                    if 'trend_1h' in condition or 'trend_4h' in condition:
                        mtf_alignment[i] = condition.replace("!= 'bullish'", "!= None")
                        print(f"   ✅ {scenario_id}: упрощено {condition}")
                        modified_count += 1
        
        # Снижаем ADX пороги в trend_strength
        if 'if' in scenario and 'trend_strength' in scenario['if']:
            trend_strength = scenario['if']['trend_strength']
            
            for i, condition in enumerate(trend_strength):
                # Заменяем adx > 30 на adx > 20
                if 'adx' in condition and '> 30' in condition:
                    trend_strength[i] = condition.replace('> 30', '> 20')
                    print(f"   ✅ {scenario_id}: ADX порог 30→20")
                    modified_count += 1
    
    # Сохраняем
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ JSON модифицирован! Изменений: {modified_count}")

except Exception as e:
    print(f"   ❌ Ошибка JSON: {e}")

# 2. ADX Threshold в Python коде
print("\n2️⃣ Снижаем ADX порог в unified_scenario_matcher.py...")
try:
    file_path = "systems/unified_scenario_matcher.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
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
            print(f"   ✅ {old} → {new}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"   ✅ Python код обновлён! Изменений: {changes}")

except Exception as e:
    print(f"   ❌ Ошибка Python: {e}")

print("\n" + "="*60)
print("✅ ФИНАЛЬНЫЙ ФИКС ЗАВЕРШЁН!")
print("="*60)
print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
print("   1. Ctrl+C - останови бота")
print("   2. python main.py --mode live --log-level INFO")
print("   3. Жди 10 минут")
print("   4. Проверь /signals в Telegram")
print("\n📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:")
print("   - ADX порог снижен с 30 на 20")
print("   - MTF требования смягчены (1d любой тренд для LONG)")
print("   - Confidence порог уже снижен (0.45)")
print("   - Должны появиться 1-5 сигналов в час")
