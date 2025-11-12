#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 MERGE & FIX SCENARIOS - Объединение 100 + 12 сценариев в один готовый файл
Версия: 3.0 Production Ready
Автор: GIO Bot Team
Дата: 2025-10-31
"""

import json
from typing import Dict, List, Any
from pathlib import Path

class ScenariosUnitedMerger:
    """Объединение и исправление сценариев"""

    def __init__(self):
        self.base_path = Path('data/scenarios')
        self.v3_100_file = self.base_path / 'gio_scenarios_100_with_features_v3.json'
        self.v2_12_file = self.base_path / 'gio_scenarios_v2.json'
        self.output_file = self.base_path / 'gio_scenarios_112_final_v3.json'

    def load_json(self, filepath):
        """Загрузить JSON файл"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки {filepath}: {e}")
            return None

    def save_json(self, data, filepath):
        """Сохранить JSON файл"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Сохранено: {filepath}")
        except Exception as e:
            print(f"❌ Ошибка сохранения {filepath}: {e}")

    def fix_scenario_mtf_trends(self, scenario: Dict) -> Dict:
        """ФИКС #1: Добавить mtf_trends в conditions"""
        conditions = scenario.get('conditions', {})

        if 'mtf_trends' in conditions:
            return scenario

        opinion = scenario.get('opinion', 'bullish')
        side = scenario.get('side', 'long')
        required = 'bullish' if side == 'long' else 'bearish'

        mtf_trends = {
            'required': required,
            'mode': 'majority',
            'min_alignment': 2,
            '1h': required,
            '4h': required,
            '1d': required
        }

        conditions['mtf_trends'] = mtf_trends
        scenario['conditions'] = conditions
        return scenario

    def fix_scenario_adx(self, scenario: Dict) -> Dict:
        """ФИКС #2: Убедиться что ADX в metrics"""
        conditions = scenario.get('conditions', {})
        metrics = conditions.get('metrics', {})

        if 'adx' not in metrics:
            metrics['adx'] = {'operator': '>', 'value': 20}
            conditions['metrics'] = metrics
            scenario['conditions'] = conditions

        return scenario

    def convert_v2_to_v3_conditions(self, scenario: Dict) -> Dict:
        """Конвертировать v2.0 сценарий в v3.0 format"""
        conditions = {}

        if 'mtf' in scenario:
            mtf_v2 = scenario['mtf']
            mtf_trends = self._convert_mtf_v2_to_v3(mtf_v2)
            if mtf_trends:
                conditions['mtf_trends'] = mtf_trends

        if 'volume_profile' in scenario:
            conditions['volume_profile'] = scenario['volume_profile']

        if 'metrics' in scenario:
            conditions['metrics'] = scenario['metrics']

        if 'clusters' in scenario:
            conditions['clusters'] = scenario['clusters']

        if 'triggers' in scenario:
            conditions['triggers'] = scenario['triggers']

        if 'news' in scenario:
            conditions['news'] = scenario['news']

        scenario['conditions'] = conditions
        return scenario

    def _convert_mtf_v2_to_v3(self, mtf_v2: Dict) -> Dict:
        """Конвертировать MTF из v2.0 в v3.0"""
        if not mtf_v2:
            return {}

        mode = mtf_v2.get('mode', 'majority')
        conditions_dict = mtf_v2.get('conditions', {})

        required = 'bullish'
        if '1H' in conditions_dict:
            trends = conditions_dict['1H']
            if isinstance(trends, list):
                if 'bearish' in trends:
                    required = 'bearish'

        mtf_trends = {
            'required': required,
            'mode': mode,
            'min_alignment': mtf_v2.get('required_alignment', 2)
        }

        for tf, values in conditions_dict.items():
            if isinstance(values, list) and values:
                mtf_trends[tf] = values[0]

        return mtf_trends

    def merge_scenarios(self) -> List[Dict]:
        """Объединить все сценарии"""
        print("📥 Загрузка сценариев...")

        # Загрузить v3 (100 сценариев)
        print("📖 Загрузка v3 (100 сценариев)...")
        v3_data = self.load_json(self.v3_100_file)
        if not v3_data:
            print("❌ Не удалось загрузить v3 сценарии!")
            return []

        scenarios_v3 = v3_data.get('scenarios', [])
        print(f"✅ Загружено {len(scenarios_v3)} сценариев v3")

        # Загрузить v2 (12 сценариев)
        print("📖 Загрузка v2 (12 сценариев)...")
        v2_data = self.load_json(self.v2_12_file)
        if not v2_data:
            print("⚠️  Файл v2 не найден. Используем только v3")
            scenarios_v2 = []
        else:
            scenarios_v2 = v2_data.get('scenarios', [])
            print(f"✅ Загружено {len(scenarios_v2)} сценариев v2")

        # ИСПРАВЛЕНИЯ
        print("\n🔧 Применение фиксов...\n")

        # Фикс для v3 сценариев
        print("📝 Фиксирование v3 сценариев...")
        for scenario in scenarios_v3:
            scenario = self.fix_scenario_mtf_trends(scenario)
            scenario = self.fix_scenario_adx(scenario)
        print(f"✅ Исправлено {len(scenarios_v3)} сценариев v3")

        # Фикс для v2 сценариев
        print("📝 Конвертирование v2 сценариев...")
        for scenario in scenarios_v2:
            scenario = self.convert_v2_to_v3_conditions(scenario)
            scenario = self.fix_scenario_adx(scenario)
        print(f"✅ Конвертировано {len(scenarios_v2)} сценариев v2")

        # Объединить
        all_scenarios = scenarios_v3 + scenarios_v2

        # Убедиться что все ID уникальны
        print("\n✓ Проверка уникальности ID...")
        ids = [s.get('id') for s in all_scenarios]
        if len(ids) != len(set(ids)):
            print("⚠️  Найдены дублирующиеся ID! Переименовываю v2 сценарии...")
            for i, scenario in enumerate(scenarios_v2):
                old_id = scenario.get('id', f'SCN_{100+i+1}')
                new_id = f'{old_id}_V2'
                scenario['id'] = new_id

        all_scenarios = scenarios_v3 + scenarios_v2
        return all_scenarios

    def create_final_file(self):
        """Создать финальный файл"""
        print("\n" + "="*70)
        print("🚀 MERGE & FIX SCENARIOS")
        print("="*70)

        scenarios = self.merge_scenarios()

        if not scenarios:
            print("❌ Не удалось объединить сценарии!")
            return False

        # Создать финальный JSON
        final_data = {
            'version': '3.0',
            'status': 'production_ready',
            'count': len(scenarios),
            'created': '2025-10-31',
            'description': 'United GIO Bot Scenarios - 100 (v3) + 12 (v2 converted)',
            'metadata': {
                'total_scenarios': len(scenarios),
                'scenarios_v3': 100,
                'scenarios_v2_converted': len(scenarios) - 100,
                'all_fixed': True,
                'mtf_active': True,
                'adx_integrated': True
            },
            'scenarios': scenarios
        }

        # Сохранить
        self.save_json(final_data, self.output_file)

        print(f"\n✅ УСПЕШНО ОБЪЕДИНЕНО!")
        print(f"   📊 Всего сценариев: {len(scenarios)}")
        print(f"   ✓ MTF активирован: Да")
        print(f"   ✓ ADX интегрирован: Да")
        print(f"   ✓ Версия: 3.0 Production Ready")
        print(f"   📁 Файл: {self.output_file}")

        return True


def main():
    merger = ScenariosUnitedMerger()
    merger.create_final_file()


if __name__ == '__main__':
    main()
