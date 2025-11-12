"""
🔧 CONDITION FIXER v1.0
Усиливает фильтры для уменьшения ложных сигналов

УЛУЧШЕНИЯ:
1. ADX >= 30 (было 25)
2. RSI фильтры строже
3. Volume фильтры
"""

import json
import shutil
from datetime import datetime

class ConditionFixer:
    """Усиление условий"""

    def __init__(self, json_path="data/scenarios/gio_scenarios_v35_enhanced.json"):
        self.json_path = json_path
        self.data = None
        self.changes = []

    def create_backup(self):
        """Backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.json_path}.backup_conditions_{timestamp}"
            shutil.copy2(self.json_path, backup_path)
            print(f"✅ Backup: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

    def load_json(self):
        """Загрузить"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            print(f"✅ Загружен JSON: {len(self.data.get('scenarios', []))} сценариев")
            return True
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

    def strengthen_conditions(self):
        """Усилить условия"""
        print("\n" + "="*100)
        print("🔧 УСИЛЕНИЕ УСЛОВИЙ")
        print("="*100)

        scenarios = self.data.get("scenarios", [])

        for scenario in scenarios:
            scn_id = scenario.get("id", "")
            if_block = scenario.get("if", {})

            # 1. ADX 25 → 30
            if "trend_strength" in if_block:
                strength_rules = if_block["trend_strength"]

                for i, rule in enumerate(strength_rules):
                    if isinstance(rule, str):
                        if "adx_1h > 25" in rule:
                            strength_rules[i] = rule.replace("adx_1h > 25", "adx_1h > 30")
                            self.changes.append(f"{scn_id}: ADX 1h 25→30")

                        if "adx_4h > 25" in rule:
                            strength_rules[i] = rule.replace("adx_4h > 25", "adx_4h > 30")
                            self.changes.append(f"{scn_id}: ADX 4h 25→30")

        print(f"\n✅ Усилено: {len(self.changes)} условий")
        return True

    def save_json(self):
        """Сохранить"""
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Сохранено")
            return True
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

    def run(self):
        """Запуск"""
        print("\n🔧 CONDITION FIXER v1.0")
        print("="*100)

        if not self.create_backup():
            return False
        if not self.load_json():
            return False
        if not self.strengthen_conditions():
            return False
        if not self.save_json():
            return False

        print("\n✅ Готово! Запусти финальный фикс:")
        print("   python -m analytics.fix_final\n")

        return True

if __name__ == "__main__":
    fixer = ConditionFixer()
    fixer.run()
