"""
МАСТЕР-ФИКС v2: Исправленная версия с проверкой структуры
"""
import json

print("="*60)
print("🔧 МАСТЕР-ФИКС v2: Снижение требований для генерации сигналов")
print("="*60)

# 1. MTF Requirements
print("\n1️⃣ Модифицируем MTF требования...")
file_path = "data/scenarios/gio_scenarios_top5_core.json"

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Проверяем структуру файла
    if 'scenarios' in data:
        scenarios = data['scenarios']
    elif isinstance(data, list):
        scenarios = data
    else:
        print("   ❌ Неизвестная структура JSON!")
        scenarios = []
    
    modified_count = 0
    
    for scenario in scenarios:
        # Безопасная проверка наличия ключей
        side = scenario.get('side', scenario.get('direction', '')).lower()
        
        if 'long' in side:
            mtf = scenario.get('mtf', {})
            conditions = mtf.get('conditions', {})
            
            # Разреши любой тренд на 1D для LONG
            for tf in ['1D', '1d', 'D', 'd']:
                if tf in conditions:
                    old_val = conditions[tf]
                    conditions[tf] = ['bullish', 'neutral', 'bearish']
                    print(f"   ✅ {scenario.get('id', 'unknown')}: {tf} = любой тренд (было: {old_val})")
                    modified_count += 1
                    break
            
            # Снижаем required_alignment
            if 'required_alignment' in mtf:
                if mtf['required_alignment'] >= 3:
                    mtf['required_alignment'] = 2
                    print(f"   ✅ {scenario.get('id', 'unknown')}: required_alignment = 2")
        
        elif 'short' in side:
            mtf = scenario.get('mtf', {})
            conditions = mtf.get('conditions', {})
            
            # Разреши любой тренд на 1H и 4H для SHORT
            for tf in ['1H', '1h', 'H', 'h']:
                if tf in conditions:
                    conditions[tf] = ['bearish', 'neutral', 'bullish']
                    print(f"   ✅ {scenario.get('id', 'unknown')}: {tf} = любой тренд")
                    modified_count += 1
            
            for tf in ['4H', '4h']:
                if tf in conditions:
                    conditions[tf] = ['bearish', 'neutral', 'bullish']
                    print(f"   ✅ {scenario.get('id', 'unknown')}: {tf} = любой тренд")
            
            # Снижаем required_alignment
            if 'required_alignment' in mtf:
                if mtf['required_alignment'] >= 3:
                    mtf['required_alignment'] = 2
    
    # Сохраняем обратно
    if 'scenarios' in data:
        data['scenarios'] = scenarios
        save_data = data
    else:
        save_data = scenarios
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ MTF требования снижены! Модифицировано: {modified_count}")

except FileNotFoundError:
    print(f"   ❌ Файл не найден: {file_path}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 2. ADX Threshold
print("\n2️⃣ Снижаем ADX порог с 30 на 20...")
try:
    file_path = "trading/unified_scenario_matcher.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем все вхождения ADX порогов
    replacements = {
        'if adx < 25:': 'if adx < 20:',
        'ADX={adx:.1f} < 25': 'ADX={adx:.1f} < 20',
        'min_adx=30': 'min_adx=20',
        'if adx < 30:': 'if adx < 20:',
        'adx >= 30,': 'adx >= 20,',
        'adx >= 40': 'adx >= 30',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("   ✅ ADX порог снижен до 20!")

except FileNotFoundError:
    print(f"   ❌ Файл не найден: {file_path}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

# 3. Confidence Threshold
print("\n3️⃣ Снижаем confidence порог...")
try:
    file_path = "core/bot.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    replacements = {
        'min_confidence = 0.60': 'min_confidence = 0.45',
        'MIN_CONFIDENCE = 0.60': 'MIN_CONFIDENCE = 0.45',
        'confidence_score < 0.60': 'confidence_score < 0.45',
        'confidence >= 0.60': 'confidence >= 0.45',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("   ✅ Confidence порог снижен до 0.45!")

except FileNotFoundError:
    print(f"   ❌ Файл не найден: {file_path}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

print("\n" + "="*60)
print("✅ МАСТЕР-ФИКС ЗАВЕРШЁН!")
print("="*60)
print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
print("   1. Ctrl+C - останови бота")
print("   2. python main.py --mode live --log-level INFO")
print("   3. Жди 5-10 минут")
print("   4. Проверь /signals в Telegram")
