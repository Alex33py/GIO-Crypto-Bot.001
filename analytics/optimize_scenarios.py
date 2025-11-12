"""
🔧 SCENARIO OPTIMIZER v1.0
Автоматическое исправление неактивных и убыточных сценариев

Использование:
    python -m analytics.optimize_scenarios

Что делает:
    1. Создаёт backup JSON
    2. Исправляет ADX фильтры (20 → 25)
    3. Расширяет SL (0.3 → 0.5 ATR)
    4. Сохраняет оптимизированный JSON
"""

import json
import os
import shutil
from datetime import datetime

class ScenarioOptimizer:
    """Автоматическая оптимизация сценариев"""

    def __init__(self, json_path="data/scenarios/gio_scenarios_v35_enhanced.json"):
        self.json_path = json_path
        self.data = None
        self.changes_made = []

    def create_backup(self):
        """Создать резервную копию"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.json_path}.backup_{timestamp}"
            shutil.copy2(self.json_path, backup_path)
            print(f"✅ Backup создан: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания backup: {e}")
            return False

    def load_json(self):
        """Загрузить JSON"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            print(f"✅ JSON загружен: {len(self.data.get('scenarios', []))} сценариев")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки JSON: {e}")
            return False

    def optimize_scenarios(self):
        """Оптимизировать сценарии"""
        if not self.data:
            return False

        print("\n" + "=" * 100)
        print("🔧 НАЧИНАЕМ ОПТИМИЗАЦИЮ")
        print("=" * 100)

        scenarios = self.data.get("scenarios", [])

        # Неактивные сценарии (нужно снизить строгость)
        inactive = [
            "SCN_005_LONG_PULLBACK_LOW_VOLUME",
            "SCN_008_LONG_TRAP_RECLAIM_CORE",
            "SCN_010_LONG_MOMENTUM_VAL_RETEST",
            "SCN_013_SHORT_MOMENTUM_CORE",
            "SCN_014_SHORT_MOMENTUM_HIGH_VOL",
            "SCN_019_SHORT_BREAKOUT_NEWS",
            "SCN_022_SHORT_MOMENTUM_VAH_REJECT"
        ]

        # Убыточные сценарии (нужны строже фильтры)
        lossy = [
            "SCN_003_LONG_MOMENTUM_CLUSTER",
            "SCN_004_LONG_PULLBACK_CORE",
            "SCN_009_LONG_MEANREV_BALANCE",
            "SCN_018_SHORT_BREAKOUT_CORE",
            "SCN_020_SHORT_DISTRIBUTION_EXHAUST",
            "SCN_021_SHORT_MEANREV_BALANCE",
            "SCN_023_SHORT_BREAKDOWN_VAL",
            "SCN_024_SHORT_DISTRIBUTION_POC_FAIL"
        ]

        # Нейтральный
        neutral = ["SCN_001_LONG_MOMENTUM_CORE"]

        for scenario in scenarios:
            scn_id = scenario.get("id", "")

            # 1. ИСПРАВИТЬ ADX ФИЛЬТРЫ (для ВСЕХ)
            if self._fix_adx_filters(scenario, scn_id):
                self.changes_made.append(f"{scn_id}: ADX 20→25")

            # 2. РАСШИРИТЬ SL (для убыточных)
            if scn_id in lossy:
                if self._fix_stop_loss(scenario, scn_id):
                    self.changes_made.append(f"{scn_id}: SL 0.3→0.5 ATR")

        print(f"\n✅ Оптимизация завершена! Изменений: {len(self.changes_made)}")
        return True

    def _fix_adx_filters(self, scenario, scn_id):
        """Исправить ADX фильтры: 20 → 25"""
        changed = False

        if_block = scenario.get("if", {})

        # Проверяем trend_strength
        if "trend_strength" in if_block:
            strength_rules = if_block["trend_strength"]

            for i, rule in enumerate(strength_rules):
                if isinstance(rule, str):
                    # Замена adx > 20 на adx > 25
                    if "adx_1h > 20" in rule:
                        strength_rules[i] = rule.replace("adx_1h > 20", "adx_1h > 25")
                        changed = True

                    if "adx_4h > 20" in rule:
                        strength_rules[i] = rule.replace("adx_4h > 20", "adx_4h > 25")
                        changed = True

        return changed

    def _fix_stop_loss(self, scenario, scn_id):
        """Расширить SL: 0.3 → 0.5 ATR"""
        changed = False

        tactics = scenario.get("tactics", {})

        if "sl_rules" in tactics:
            sl_rules = tactics["sl_rules"]

            for i, rule in enumerate(sl_rules):
                if isinstance(rule, str):
                    # LONG: val - 0.3*atr → val - 0.5*atr
                    if "val - 0.3*atr" in rule:
                        sl_rules[i] = rule.replace("val - 0.3*atr", "val - 0.5*atr")
                        changed = True

                    # SHORT: vah + 0.3*atr → vah + 0.5*atr
                    if "vah + 0.3*atr" in rule:
                        sl_rules[i] = rule.replace("vah + 0.3*atr", "vah + 0.5*atr")
                        changed = True

        return changed

    def save_json(self):
        """Сохранить оптимизированный JSON"""
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 JSON сохранен: {self.json_path}")
            return True

        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False

    def print_report(self):
        """Отчёт о изменениях"""
        print("\n" + "=" * 100)
        print("📊 ОТЧЁТ О ИЗМЕНЕНИЯХ")
        print("=" * 100)

        if not self.changes_made:
            print("\n⚠️ Изменений не было!")
            return

        print(f"\n✅ Всего изменений: {len(self.changes_made)}\n")

        for change in self.changes_made:
            print(f"   • {change}")

        print("\n" + "=" * 100)

    def run(self):
        """Запустить оптимизацию"""
        print("\n🔧 SCENARIO OPTIMIZER v1.0")
        print("=" * 100)

        # Шаг 1: Backup
        if not self.create_backup():
            return False

        # Шаг 2: Загрузка
        if not self.load_json():
            return False

        # Шаг 3: Оптимизация
        if not self.optimize_scenarios():
            return False

        # Шаг 4: Сохранение
        if not self.save_json():
            return False

        # Шаг 5: Отчёт
        self.print_report()

        print("\n✅ Готово! Теперь запусти новый бектест:")
        print("   python tests/backtest_full_sim.py\n")

        return True

if __name__ == "__main__":
    optimizer = ScenarioOptimizer()
    optimizer.run()
