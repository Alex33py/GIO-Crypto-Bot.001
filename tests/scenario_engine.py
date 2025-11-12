"""
🎯 SCENARIO ENGINE v1.1 - GIO BOT
Парсит JSON с 24 сценариями и генерирует торговые сигналы
УЛУЧШЕНО: Понижены пороги, добавлена защита от NaN
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class ScenarioEngine:
    """Scenario Engine для оценки рыночных сигналов"""

    def __init__(self, scenarios_json_path: str):
        """Инициализировать engine с JSON файлом"""
        with open(scenarios_json_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.scenarios = self.config.get('scenarios', [])
        self.priority_system = self.config.get('priority_system', {})

        print(f"✅ Loaded {len(self.scenarios)} scenarios from {scenarios_json_path}")
        print(f"🎯 High confidence threshold: score >= 0.60")  # ← ИЗМЕНЕНО!

    def evaluate_scenario(self, scenario: dict, market_data: dict) -> dict:
        """Оценить один сценарий"""

        scenario_id = scenario.get('id')
        opinion = scenario.get('opinion')

        score = 0.0
        met_conditions = 0
        total_conditions = 0
        details = {}

        # Веса категорий
        weights = {
            'mtf_alignment': 0.12,
            'trend_strength': 0.08,
            'cvd_orderflow': 0.17,
            'volume_profile': 0.15,
            'cluster_analysis': 0.13,
            'funding_conditions': 0.07,
            'oi_analysis': 0.11,
            'positioning_metrics': 0.07,
            'additional_filters': 0.03
        }

        # Проверить каждую категорию
        for category, weight in weights.items():
            conditions = scenario.get('if', {}).get(category, [])

            if conditions:
                passed = sum(1 for c in conditions if self._eval_condition(c, market_data))
                cat_score = passed / len(conditions) if conditions else 0.5
                score += cat_score * weight
                met_conditions += passed
                total_conditions += len(conditions)
                details[category] = {
                    'score': cat_score,
                    'passed': passed,
                    'total': len(conditions)
                }
            else:
                details[category] = {'score': 0.5, 'passed': 0, 'total': 0}

        # ← ИЗМЕНЕНО ТУТ! ========================================
        # Проверить пороги
        min_metrics = 1  # ← Было: scenario.get('min_metrics', 3)
        status = scenario.get('status', '')
        is_valid = (met_conditions >= min_metrics)  # ← Убрали: and (status == 'deal')
        # ========================================================

        return {
            'scenario_id': scenario_id,
            'opinion': opinion,
            'score': score,
            'met_conditions': met_conditions,
            'total_conditions': total_conditions,
            'is_valid': is_valid,
            'details': details
        }


    def _eval_condition(self, condition: str, market_data: dict) -> bool:
        """Оценить одно условие"""
        try:
            eval_str = condition

            # Заменить все ключи из market_data
            for key in sorted(market_data.keys(), key=len, reverse=True):
                value = market_data[key]

                # ← ДОБАВЛЕНО: Защита от NaN/inf!
                if isinstance(value, (float, np.floating)):
                    if np.isnan(value) or np.isinf(value):
                        value = 0.0

                if isinstance(value, str):
                    eval_str = eval_str.replace(key, f"'{value}'")
                elif isinstance(value, bool):
                    eval_str = eval_str.replace(key, str(value))
                else:
                    eval_str = eval_str.replace(key, str(value))

            return eval(eval_str)
        except:
            return False

    def generate_signal(self, market_data: dict) -> Optional[dict]:
        """Генерировать сигнал с взвешенным выбором"""

        results = []

        # Оценить ВСЕ сценарии
        for scenario in self.scenarios:
            result = self.evaluate_scenario(scenario, market_data)
            if result['is_valid']:
                results.append(result)

        if not results:
            return None

        # Сортировать по score
        results = sorted(results, key=lambda x: x['score'], reverse=True)

        # ← ВЗВЕШЕННЫЙ ВЫБОР!
        import random
        import numpy as np

        high_threshold = 0.15
        medium_threshold = 0.12

        # Разделить по confidence
        high_conf = [r for r in results if r['score'] >= high_threshold]
        medium_conf = [r for r in results if high_threshold > r['score'] >= medium_threshold]
        low_conf = [r for r in results if r['score'] < medium_threshold]

        # ← ДОБАВЛЕНО: ПРОВЕРКА ПУСТОТЫ!
        if not high_conf and not medium_conf and not low_conf:
            return None  # Нет подходящих сценариев

        # Взвешенный выбор: HIGH (75%), MEDIUM (20%), LOW (5%)
        weights = []
        scenarios_pool = []

        for s in high_conf:
            scenarios_pool.append(s)
            weights.append(0.75 / max(len(high_conf), 1))

        for s in medium_conf[:2]:  # Max 2 MEDIUM
            scenarios_pool.append(s)
            weights.append(0.20 / max(len(medium_conf[:2]), 1))

        if low_conf and random.random() < 0.05:  # 5% шанс LOW
            scenarios_pool.append(low_conf[0])
            weights.append(0.05)

        # ← ДОБАВЛЕНО: ЕСЛИ scenarios_pool ПУСТОЙ, ВЕРНУТЬ None!
        if not scenarios_pool:
            return None

        # Нормализовать веса
        weights = np.array(weights)
        weights = weights / weights.sum()

        # Выбрать по вероятности
        best = np.random.choice(scenarios_pool, p=weights)

        if best['score'] >= high_threshold:
            confidence = 'HIGH'
        elif best['score'] >= medium_threshold:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        return {
            'confidence': confidence,
            'scenario_id': best['scenario_id'],
            'opinion': best['opinion'],
            'score': best['score'],
            'details': best['details'],
            'runners_up': [
                {
                    'scenario_id': r['scenario_id'],
                    'opinion': r['opinion'],
                    'score': r['score']
                }
                for r in results[1:min(3, len(results))]
            ]
        }
