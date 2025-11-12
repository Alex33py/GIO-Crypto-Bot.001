"""
🔍 SCENARIO DIAGNOSTICS v1.0
Проверка целостности сценариев и их активности

Использование:
    python -m analytics.check_scenarios
"""

import json
import os
from pathlib import Path

class ScenarioDiagnostics:
    """Диагностика сценариев в JSON и бектесте"""

    def __init__(self):
        self.json_path = "data/scenarios/gio_scenarios_v35_enhanced.json"
        self.scenarios_from_json = []
        self.scenarios_from_backtest = set()

    def load_json_scenarios(self):
        """Загрузить сценарии из JSON"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.scenarios_from_json = data.get("scenarios", [])
            print(f"✅ JSON загружен: {self.json_path}")
            print(f"   Всего сценариев: {len(self.scenarios_from_json)}")
            return True

        except FileNotFoundError:
            print(f"❌ Файл не найден: {self.json_path}")
            return False
        except Exception as e:
            print(f"❌ Ошибка загрузки JSON: {e}")
            return False

    def load_backtest_scenarios(self):
        """Загрузить сценарии из последнего бектеста"""
        try:
            import pandas as pd

            csv_files = list(Path("tests/results").glob("backtest_full_sim_*.csv"))
            if not csv_files:
                print("❌ CSV не найдены!")
                return False

            latest_csv = max(csv_files, key=os.path.getctime)
            df = pd.read_csv(latest_csv)

            self.scenarios_from_backtest = set(df["scenario"].unique())
            print(f"✅ Бектест загружен: {latest_csv.name}")
            print(f"   Сценариев с сделками: {len(self.scenarios_from_backtest)}")
            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки бектеста: {e}")
            return False

    def check_json_integrity(self):
        """Проверить целостность JSON"""
        print("\n" + "=" * 100)
        print("🔍 ПРОВЕРКА JSON ФАЙЛА")
        print("=" * 100)

        scenario_ids = {s.get("id") for s in self.scenarios_from_json}

        # Ожидаемые ID
        expected = {f"SCN_{i:03d}_" for i in range(1, 25)}

        # Проверка
        print(f"\n📋 Найдено сценариев: {len(scenario_ids)}")
        print(f"📊 Ожидалось: 24 (SCN_001 - SCN_024)")

        # Список всех ID
        print("\n📝 Сценарии в JSON:")
        for s in sorted(self.scenarios_from_json, key=lambda x: x.get("id", "")):
            sid = s.get("id", "???")
            status = s.get("status", "???")
            direction = s.get("direction", "???")
            print(f"   {sid:<40} | {direction:<5} | {status}")

        # Проверка на дубликаты
        if len(scenario_ids) != len(self.scenarios_from_json):
            print("\n⚠️ ВНИМАНИЕ: Есть дубликаты ID!")
        else:
            print("\n✅ Дубликатов нет")

        return len(scenario_ids) == 24

    def check_backtest_activity(self):
        """Проверить активность сценариев"""
        print("\n" + "=" * 100)
        print("🎯 ПРОВЕРКА АКТИВНОСТИ В БЕКТЕСТЕ")
        print("=" * 100)

        json_ids = {s.get("id") for s in self.scenarios_from_json}
        active_ids = self.scenarios_from_backtest

        # Сценарии с сделками
        print(f"\n✅ Сценарии с сделками ({len(active_ids)}):")
        for sid in sorted(active_ids):
            print(f"   {sid}")

        # Сценарии БЕЗ сделок
        inactive_ids = json_ids - active_ids
        if inactive_ids:
            print(f"\n❌ Сценарии БЕЗ сделок ({len(inactive_ids)}):")
            for sid in sorted(inactive_ids):
                print(f"   {sid}")
        else:
            print("\n✅ Все сценарии активны!")

        # Статистика
        print(f"\n📊 Статистика:")
        print(f"   Всего в JSON: {len(json_ids)}")
        print(f"   Активных: {len(active_ids)} ({len(active_ids)/len(json_ids)*100:.1f}%)")
        print(f"   Неактивных: {len(inactive_ids)} ({len(inactive_ids)/len(json_ids)*100:.1f}%)")

    def analyze_inactive(self):
        """Анализ неактивных сценариев"""
        print("\n" + "=" * 100)
        print("🔬 АНАЛИЗ НЕАКТИВНЫХ СЦЕНАРИЕВ")
        print("=" * 100)

        json_ids = {s.get("id"): s for s in self.scenarios_from_json}
        active_ids = self.scenarios_from_backtest
        inactive_ids = set(json_ids.keys()) - active_ids

        if not inactive_ids:
            print("\n✅ Нет неактивных сценариев!")
            return

        print(f"\n📋 Детальная информация о неактивных:")
        for sid in sorted(inactive_ids):
            scenario = json_ids.get(sid, {})
            direction = scenario.get("direction", "???")
            status = scenario.get("status", "???")

            print(f"\n{sid}:")
            print(f"   Direction: {direction}")
            print(f"   Status: {status}")
            print(f"   Проблема: Сценарий не генерирует сигналы")

            # Причины
            if_conditions = scenario.get("if", {})
            print(f"   Условий: {len(if_conditions)}")

    def run(self):
        """Запустить диагностику"""
        print("\n🔍 SCENARIO DIAGNOSTICS v1.0")
        print("=" * 100)

        # Загрузка
        if not self.load_json_scenarios():
            return False
        if not self.load_backtest_scenarios():
            return False

        # Проверки
        self.check_json_integrity()
        self.check_backtest_activity()
        self.analyze_inactive()

        print("\n✅ Диагностика завершена!\n")
        return True

if __name__ == "__main__":
    diagnostics = ScenarioDiagnostics()
    diagnostics.run()
