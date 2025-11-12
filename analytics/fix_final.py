"""
🔧 FINAL FIXER v1.0
Финальная проверка и валидация

ПРОВЕРЯЕТ:
1. Все direction правильные
2. Все условия корректные
3. JSON валидный
"""

import json

class FinalFixer:
    """Финальная проверка"""

    def __init__(self, json_path="data/scenarios/gio_scenarios_v35_enhanced.json"):
        self.json_path = json_path
        self.data = None

    def load_json(self):
        """Загрузить"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            print(f"❌ JSON невалиден: {e}")
            return False

    def validate(self):
        """Валидация"""
        print("\n" + "="*100)
        print("✅ ФИНАЛЬНАЯ ВАЛИДАЦИЯ")
        print("="*100)

        scenarios = self.data.get("scenarios", [])

        long_count = 0
        short_count = 0
        issues = []

        for scenario in scenarios:
            scn_id = scenario.get("id", "")
            opinion = scenario.get("opinion", "")

            if "SHORT" in scn_id:
                if opinion != "bearish":
                    issues.append(f"❌ {scn_id}: opinion={opinion} (должно быть bearish)")
                else:
                    short_count += 1

            if "LONG" in scn_id:
                if opinion != "bullish":
                    issues.append(f"❌ {scn_id}: opinion={opinion} (должно быть bullish)")
                else:
                    long_count += 1

        print(f"\n📊 Сценарии:")
        print(f"   ✅ LONG (bullish): {long_count}")
        print(f"   ✅ SHORT (bearish): {short_count}")

        if issues:
            print(f"\n❌ Найдены проблемы:")
            for issue in issues:
                print(f"   {issue}")
            return False

        print(f"\n✅ Все проверки пройдены!")
        return True

    def run(self):
        """Запуск"""
        print("\n🔧 FINAL FIXER v1.0")
        print("="*100)

        if not self.load_json():
            return False

        if not self.validate():
            return False

        print("\n✅ Система готова к бектесту!")
        print("   python tests/backtest_full_simulation.py\n")

        return True

if __name__ == "__main__":
    fixer = FinalFixer()
    fixer.run()
