# Файл: tests/test_parser.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scenario_matcher import UnifiedScenarioMatcher
import json

# Загружаем первый сценарий
with open('data/scenarios/gio_scenarios_100_with_features_v3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

scenario = data['scenarios'][0]  # SCN_001

print(f"Тестируем сценарий: {scenario['id']}")
print(f"\nif блок:")
print(json.dumps(scenario.get('if', {}), indent=2))

# Создаём тестовые данные
market_data = {
    'price': 100.0,
    'poc': 100.0,
    'vah': 101.0,
    'val': 99.0,
    'mtf_trends': {
        '1H': 'bullish',
        '4H': 'bullish',
        '1D': 'bullish',
    },
    'cvd': {
        'cvd_confirms': True,
        'cvd_value': 5000,
    },
    'clusters': {
        'stacked_imbalance_up': 5,
        'stacked_imbalance_down': 0,
        'poc_shift_up': True,
        'poc_shift_down': False,
    },
    'news_sentiment': {
        'overall_score': 0.1,
    },
}

indicators = {'atr': 1.2}

# Создаём matcher и тестируем
matcher = UnifiedScenarioMatcher()
score = matcher._evaluate_if_conditions(scenario, market_data, indicators)

print(f"\n✅ Результат: score = {score:.2%}")
