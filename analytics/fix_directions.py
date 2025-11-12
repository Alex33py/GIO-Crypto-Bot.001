"""
🔧 DIRECTION FIXER v1.0
Исправляет направления SHORT сценариев (SCN_013-024)

ПРОБЛЕМА: Все SHORT сценарии генерируют LONG сигналы!
РЕШЕНИЕ: Исправить "opinion" на "bearish" для SCN_013-024
"""

import json
import shutil
from datetime import datetime

class DirectionFixer:
    """Исправление направлений сценариев"""

    def __init__(self, json_path="data/scenarios/gio_scenarios_v35_enhanced.json"):
        self.json_path = json_path
        self.data = None
        self.changes = []

    def create_backup(self):
        """Создать резервную копию"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.json_path}.backup_directions_{timestamp}"
            shutil.copy2(self.json_path, backup_path)
            print(f"✅ Backup: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Ошибка backup: {e}")
            return False

    def load_json(self):
        """Загрузить JSON"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            print(f"✅ JSON загружен: {len(self.data.get('scenarios', []))} сценариев")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False

    def fix_directions(self):
        """Исправить направления"""
        print("\n" + "="*100)
        print("🔧 ИСПРАВЛЕНИЕ НАПРАВЛЕНИЙ")
        print("="*100)

        scenarios = self.data.get("scenarios", [])

        # SHORT сценарии (должны быть bearish)
        short_ids = [
            "SCN_013_SHORT_MOMENTUM_CORE",
            "SCN_014_SHORT_MOMENTUM_HIGH_VOL",
            "SCN_015_SHORT_MOMENTUM_CLUSTER",
            "SCN_016_SHORT_PULLBACK_CORE",
            "SCN_017_SHORT_PULLBACK_LOW_VOLUME",
            "SCN_018_SHORT_BREAKOUT_CORE",
            "SCN_019_SHORT_BREAKOUT_NEWS",
            "SCN_020_SHORT_DISTRIBUTION_EXHAUST",
            "SCN_021_SHORT_MEANREV_BALANCE",
            "SCN_022_SHORT_MOMENTUM_VAH_REJECT",
            "SCN_023_SHORT_BREAKDOWN_VAL",
            "SCN_024_SHORT_DISTRIBUTION_POC_FAIL"
        ]

        for scenario in scenarios:
            scn_id = scenario.get("id", "")

            if scn_id in short_ids:
                # Проверяем текущее значение
                current_opinion = scenario.get("opinion", "")

                if current_opinion != "bearish":
                    scenario["opinion"] = "bearish"
                    self.changes.append(f"{scn_id}: {current_opinion} → bearish")
                    print(f"   ✅ {scn_id}: {current_opinion} → bearish")

        print(f"\n✅ Исправлено: {len(self.changes)} сценариев")
        return True

    def save_json(self):
        """Сохранить JSON"""
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Сохранено: {self.json_path}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False

    def print_report(self):
        """Отчёт"""
        print("\n" + "="*100)
        print("📊 ОТЧЁТ")
        print("="*100)
        print(f"\n✅ Всего изменений: {len(self.changes)}\n")
        for change in self.changes:
            print(f"   • {change}")
        print("\n" + "="*100)

    def run(self):
        """Запустить"""
        print("\n🔧 DIRECTION FIXER v1.0")
        print("="*100)

        if not self.create_backup():
            return False
        if not self.load_json():
            return False
        if not self.fix_directions():
            return False
        if not self.save_json():
            return False

        self.print_report()

        print("\n✅ Готово! Запусти следующий фикс:")
        print("   python -m analytics.fix_conditions\n")

        return True

if __name__ == "__main__":
    fixer = DirectionFixer()
    fixer.run()
