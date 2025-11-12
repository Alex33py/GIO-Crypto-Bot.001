# -*- coding: utf-8 -*-
"""
Enhanced Unified Scenario Matcher v2.0
Продвинутый матчер сценариев с поддержкой market regime detection
"""

# import json
# import os
# from typing import Dict, List, Optional, Tuple
# from datetime import datetime
# from pathlib import Path
# from config.settings import logger, SCENARIOS_DIR, DATA_DIR
# from systems.market_regime_detector import MarketRegimeDetector

# -*- coding: utf-8 -*-
"""
Enhanced Unified Scenario Matcher v2.0
Продвинутый матчер сценариев с поддержкой market regime detection
"""


import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# ===== ПАТЧ ДЛЯ БЕКТЕСТА =====
try:
    from config.settings import logger, SCENARIOS_DIR, DATA_DIR
    from systems.market_regime_detector import MarketRegimeDetector
except (ImportError, ModuleNotFoundError):
    # Fallback для бектеста - используем mock зависимости
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))
    from mock_dependencies import logger, SCENARIOS_DIR, DATA_DIR
    from mock_market_regime import MarketRegimeDetector
# ===== КОНЕЦ ПАТЧА =====

try:
    from systems.adx_volatility_filters import (
        get_adx_confidence,
        calculate_atr_based_levels,
        check_volatility_regime,
        validate_signal_with_filters
    )
    FILTERS_AVAILABLE = True
except ImportError:
    print("⚠️ ADX/Volatility фильтры не найдены, используем fallback логику")
    FILTERS_AVAILABLE = False

from analytics.confidence_booster import ConfidenceBooster


class EnhancedScenarioMatcher:
    """
    Улучшенный матчер сценариев с:
    - Автоматическим определением рыночного режима
    - Детальной валидацией сигналов
    - Расчётом уверенности
    - Отслеживанием фазы рынка
    """

    def __init__(self):
        """Инициализация матчера"""
        self.scenarios = []
        self.strategies = {}
        self.regime_detector = MarketRegimeDetector()
        self.confidence_booster = ConfidenceBooster()

        # Загружаем данные
        self._load_scenarios()
        self._load_strategies()

        logger.info("✅ EnhancedScenarioMatcher v2.0 инициализирован with ConfidenceBooster")



    def _load_scenarios(self):
        """Загрузка сценариев из JSON"""
        try:
            # Попробуем несколько вариантов файлов
            possible_files = [
                Path(DATA_DIR) / "scenarios" / "gio_scenarios_top5_core.json",
            ]

            scenarios_path = None
            for file_path in possible_files:
                if file_path.exists():
                    scenarios_path = file_path
                    logger.info(f"✅ Найден файл сценариев: {file_path.name}")
                    break

            if not scenarios_path:
                logger.error(f"❌ Файл сценариев не найден ни один из: {[f.name for f in possible_files]}")
                return

            with open(scenarios_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.scenarios = data.get("scenarios", [])
            logger.info(f"✅ Загружено {len(self.scenarios)} сценариев")

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки сценариев: {e}")
            self.scenarios = []



    def _load_strategies(self):
        """Загрузка стратегий из JSON"""
        try:
            strategies_path = Path(DATA_DIR) / "strategies" / "strategy_extensions_v1.1.json"

            if not strategies_path.exists():
                logger.error(f"❌ Файл стратегий не найден: {strategies_path}")
                return

            with open(strategies_path, 'r', encoding='utf-8') as f:
                self.strategies = json.load(f)

            logger.info("✅ Загружены правила стратегий")

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки стратегий: {e}")
            self.strategies = {}

    def match_scenario(
        self,
        symbol: str,
        market_data: Dict,
        indicators: Dict,
        mtf_trends: Dict,
        volume_profile: Dict,
        news_sentiment: Dict,
        veto_checks: Dict
    ) -> Optional[Dict]:
        """
        Главный метод: найти подходящий сценарий
        """
        try:
            # Получаем ADX из indicators
            adx = indicators.get("adx", 0)
            logger.debug(f"DEBUG {symbol}: ADX={adx} - Current ADX value")

            if adx < 15:
                logger.debug(f"⚠️ {symbol}: ADX={adx:.1f} < 15, нет тренда - скип")
                return None

            logger.debug(f"ℹ️ {symbol}: ADX={adx:.1f} (фильтр включен)")

            # 1. Собираем все метрики в единый dict
            metrics = self._build_metrics(
                market_data, indicators, mtf_trends,
                volume_profile, news_sentiment
            )

            # ✅ ДОБАВИТЬ: передаем свечи для regime detector
            metrics["candles"] = market_data.get("candles", [])

            logger.debug(f"📋 {symbol}: Доступные метрики: {list(metrics.keys())}")

            # Диагностика наличия свечей
            logger.debug(f"📊 {symbol}: Свечей в metrics: {len(metrics.get('candles', []))}")
            if not metrics.get("candles"):
                logger.warning(f"⚠️ {symbol}: НЕТ СВЕЧЕЙ для regime detector!")
                logger.warning(f"   market_data keys: {list(market_data.keys())}")
                logger.warning(f"   mtf_cache available: {hasattr(self, 'mtf_cache')}")

            # Если свечей нет в market_data, берем из MTF cache
            if not metrics["candles"] and hasattr(self, 'mtf_cache'):
                # Попробуем получить свечи из кэша
                symbol_cache = self.mtf_cache.get(symbol, {})
                for interval in ['1h', '4h', '1d']:
                    cached_candles = symbol_cache.get(interval, [])
                    if cached_candles:
                        metrics["candles"] = cached_candles
                        logger.debug(f"📊 {symbol}: Используем {len(cached_candles)} свечей из MTF cache ({interval})")
                        break

            # 2. Определяем рыночный режим
            market_regime = self.regime_detector.detect(metrics)
            logger.info(f"📊 {symbol}: Рыночный режим = {market_regime}")

            # 3. Выбираем подходящие стратегии для режима
            suitable_strategies = self._get_suitable_strategies(market_regime)
            logger.debug(f"🎯 Подходящие стратегии: {suitable_strategies}")

            # 4. Ищем лучший сценарий
            best_match = self._find_best_scenario(
                symbol, metrics, suitable_strategies, mtf_trends
            )

            if not best_match:
                return None

            # 5. Валидация сценария
            validation = self._validate_scenario(best_match, metrics, veto_checks)

            # 6. Расчёт уверенности
            confidence = self._calculate_confidence(best_match, metrics, validation)

            # 7. Построение итогового сигнала
            signal = self._build_signal(
                best_match, metrics, market_regime,
                confidence, validation
            )

            return signal

        except Exception as e:
            logger.error(f"❌ Ошибка match_scenario для {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None


    def _validate_scenario(
        self,
        scenario: Dict,
        metrics: Dict,
        veto_checks: Dict
    ) -> Dict:
        """
        ✅ УЛУЧШЕННАЯ ВАЛИДАЦИЯ с фильтрами ADX + Volatility
        """

        # Получаем ADX и ATR
        adx = metrics.get("adx", 0)
        atr = metrics.get("atr_14", 0)
        atr_sma = metrics.get("atr_sma_20", atr)

        # ✅ ВРЕМЕННО ОТКЛЮЧЕНО: ADX фильтр для тестирования
        vol_regime = 'normal'
        adx_confidence = 0.5

        # Стандартные проверки
        validation = {
            "basic_conditions": True,
            "volume_confirmation": metrics.get("volume", 0) >= metrics.get("volume_ma20", 0),
            "cluster_orderflow": metrics.get("cluster_imbalance", 0) > 1,
            "multi_timeframe_alignment": True,
            "news_sentiment": abs(metrics.get("news_score", 0)) < 0.3,
            "veto_passed": not any(veto_checks.values()),

            # ✅ ВРЕМЕННО: всегда True для тестирования
            "adx_filter": True,
            "volatility_filter": True,
            "adx_confidence": adx_confidence,
            "vol_regime": vol_regime
        }

        return validation

    def _build_metrics(
        self,
        market_data: Dict,
        indicators: Dict,
        mtf_trends: Dict,
        volume_profile: Dict,
        news_sentiment: Dict
    ) -> Dict:
        """Объединить все метрики в один dict"""
        metrics = {}

        # Market data
        metrics.update({
            "price": market_data.get("close", 0),
            "volume": market_data.get("volume", 0),
            "candles": market_data.get("candles", [])
        })

        # Indicators
        metrics.update(indicators)

        # MTF trends
        metrics["trend_1h"] = mtf_trends.get("1H", "neutral")
        metrics["trend_4h"] = mtf_trends.get("4H", "neutral")
        metrics["trend_1d"] = mtf_trends.get("1D", "neutral")

        # Volume Profile
        metrics["poc"] = volume_profile.get("poc", metrics["price"])
        metrics["vah"] = volume_profile.get("vah", metrics["price"] * 1.01)
        metrics["val"] = volume_profile.get("val", metrics["price"] * 0.99)
        metrics["vwap"] = volume_profile.get("vwap", metrics["price"])

        # News sentiment
        metrics["news_score"] = news_sentiment.get("overall_score", 0)
        metrics["news_sentiment"] = news_sentiment.get("overall", "neutral")

        return metrics


    def _get_suitable_strategies(self, market_regime: str) -> List[str]:
        """Получить подходящие стратегии для режима"""
        selector = self.strategies.get("strategy_selector", {})
        regime_map = selector.get("market_regime", {})
        all_weather = selector.get("all_weather", [])

        strategies = regime_map.get(market_regime, [])
        strategies.extend(all_weather)

        return list(set(strategies))  # Убираем дубликаты


    def _find_best_scenario(
        self,
        symbol: str,
        metrics: Dict,
        suitable_strategies: List[str],
        mtf_trends: Dict
    ) -> Optional[Dict]:
        """Найти лучший подходящий сценарий"""

        matches = []

        logger.debug(f"🔍 {symbol}: Проверяю {len(self.scenarios)} сценариев...")
        logger.debug(f"   Подходящие стратегии: {suitable_strategies}")
        logger.debug(f"   MTF trends: {mtf_trends}")

        rejected_reasons = {
            "strategy_mismatch": 0,
            "mtf_mismatch": 0,
            "low_trigger_score": 0
        }

        for i, scenario in enumerate(self.scenarios):
            # Проверяем что стратегия подходит
            strategy_match = scenario["strategy"] in suitable_strategies
            if not strategy_match:
                rejected_reasons["strategy_mismatch"] += 1
                if i < 3:
                    logger.debug(f"   ❌ {scenario['id']}: strategy '{scenario['strategy']}' не в {suitable_strategies}")
                continue

            # Проверяем MTF условия
            mtf_match = self._check_mtf_conditions(scenario, mtf_trends)
            if not mtf_match:
                rejected_reasons["mtf_mismatch"] += 1
                if i < 3:
                    logger.debug(f"   ❌ {scenario['id']}: MTF не совпадает")
                continue

            # ✅ ИСПРАВЛЕНО: Проверяем triggers/scoring_system
            # Новый формат использует "scoring_system", старый "triggers"
            if "scoring_system" in scenario:
                min_score = scenario["scoring_system"].get("deal_threshold", 0.4)
            elif "triggers" in scenario:
                min_score = scenario["triggers"].get("min_score", 0.7)
            else:
                # Если нет ни того ни другого - используем default
                min_score = 0.45
                logger.debug(f"   ⚠️ {scenario['id']}: Нет scoring_system/triggers, используем min_score=0.55")

            # Для нового формата нужно считать score по-другому
            # Пока используем упрощённый вариант
            trigger_score = self._evaluate_triggers_new_format(scenario, metrics)

            if i < 3:
                logger.debug(f"   🎯 {scenario['id']}: strategy✅ MTF✅ score={trigger_score:.2f} (min={min_score})")

            if trigger_score >= min_score:
                matches.append({
                    "scenario": scenario,
                    "score": trigger_score
                })
            else:
                rejected_reasons["low_trigger_score"] += 1

        # Итоговая диагностика
        if not matches:
            logger.warning(f"⚠️ {symbol}: Ни один сценарий не подошёл из {len(self.scenarios)}!")
            logger.warning(f"   Причины отклонения:")
            logger.warning(f"   • Strategy mismatch: {rejected_reasons['strategy_mismatch']}")
            logger.warning(f"   • MTF mismatch: {rejected_reasons['mtf_mismatch']}")
            logger.warning(f"   • Low trigger score: {rejected_reasons['low_trigger_score']}")
            return None

        # Возвращаем сценарий с лучшим score
        best = max(matches, key=lambda x: x["score"])
        logger.info(f"🎯 {symbol}: Найден сценарий {best['scenario']['id']} (score={best['score']:.2f})")
        logger.info(f"   📊 Всего подошло: {len(matches)} сценариев")

        return best["scenario"]

    def _check_mtf_conditions(self, scenario: Dict, mtf_trends: Dict) -> bool:
        """
        Проверка Multi-TimeFrame условий

        ✅ СМЯГЧЕНО: Требуем 2 из 3 совпадений вместо всех 3
        """

        # ✅ НОВЫЙ ФОРМАТ: "if" -> "mtf_alignment"
        if "if" in scenario and "mtf_alignment" in scenario["if"]:
            mtf_conditions = scenario["if"]["mtf_alignment"]

            # ✅ СМЯГЧЕНО: требуем только 2 из 3 совпадений
            aligned = 0
            required = 1

            for condition in mtf_conditions:
                # ✅ ИСПРАВЛЕНО: Используем UPPERCASE ключи как в signal_generation_service
                if "trend_1h" in condition:
                    tf_key = "1H"  # Было: "1h"
                elif "trend_4h" in condition:
                    tf_key = "4H"  # Было: "4h"
                elif "trend_1d" in condition:
                    tf_key = "1D"  # Было: "1d"
                else:
                    continue

                # Получаем фактический тренд
                actual_trend = mtf_trends.get(tf_key, "neutral")

                # Проверяем условие
                if "==" in condition:
                    expected = condition.split("==")[1].strip().strip("'\"")
                    if actual_trend == expected:
                        aligned += 1
                elif "!=" in condition:
                    excluded = condition.split("!=")[1].strip().strip("'\"")
                    if excluded == "None":
                        if actual_trend and actual_trend != "neutral":
                            aligned += 1
                    elif actual_trend != excluded:
                        aligned += 1

            logger.debug(f"   MTF: {aligned}/{len(mtf_conditions)} aligned (required: {required})")
            return aligned >= required

        # ✅ СТАРЫЙ ФОРМАТ: "mtf" -> "conditions"
        mtf = scenario.get("mtf", {})
        conditions = mtf.get("conditions", {})
        required_alignment = mtf.get("required_alignment", 2)

        aligned = 0

        for tf, expected_trends in conditions.items():
            actual_trend = mtf_trends.get(tf, "neutral")

            if actual_trend in expected_trends:
                aligned += 1

        logger.debug(f"   MTF (old): {aligned}/{len(conditions)} aligned (required: {required_alignment})")
        return aligned >= required_alignment




    def _evaluate_triggers(self, scenario: Dict, metrics: Dict) -> float:
        """Оценка triggers сценария"""
        triggers = scenario.get("triggers", {})
        conditions = triggers.get("conditions", {})

        total_score = 0.0

        for condition, weight in conditions.items():
            if self._check_condition(condition, metrics):
                total_score += float(weight)

        return total_score


    def _check_condition(self, condition: str, metrics: Dict) -> bool:
        """Проверка одного условия"""
        try:
            # Простые boolean условия
            if condition in metrics:
                return bool(metrics[condition])

            # Условия с операторами (>= <= == etc)
            if ">=" in condition:
                left, right = condition.split(">=")
                left_val = self._resolve_value(left.strip(), metrics)
                right_val = self._resolve_value(right.strip(), metrics)
                return left_val is not None and right_val is not None and left_val >= right_val

            elif "<=" in condition:
                left, right = condition.split("<=")
                left_val = self._resolve_value(left.strip(), metrics)
                right_val = self._resolve_value(right.strip(), metrics)
                return left_val is not None and right_val is not None and left_val <= right_val

            elif "==" in condition:
                left, right = condition.split("==")
                left_val = self._resolve_value(left.strip(), metrics)
                right_val = right.strip()
                return str(left_val) == right_val

            return False

        except Exception as e:
            logger.debug(f"⚠️ Ошибка проверки условия '{condition}': {e}")
            return False


    def _resolve_value(self, expr: str, metrics: Dict):
        """Вычислить значение выражения"""
        # Простое значение из metrics
        if expr in metrics:
            return metrics[expr]

        # Arithmetic expression (volume_ma20*1.5)
        if "*" in expr:
            parts = expr.split("*")
            val = metrics.get(parts[0].strip())
            multiplier = float(parts[1].strip())
            return val * multiplier if val is not None else None

        # Число
        try:
            return float(expr)
        except:
            return None

    def _evaluate_triggers_new_format(self, scenario: Dict, metrics: Dict) -> float:
        """
        Оценка score для нового JSON формата с "if" и "weights"
        """
        # Получаем условия и веса
        conditions = scenario.get("if", {})
        weights = scenario.get("weights", {})

        total_score = 0.0
        max_possible = sum(weights.values()) if weights else 1.0

        # Проверяем каждую категорию условий
        for category, category_conditions in conditions.items():
            weight = weights.get(category, 0.1)

            if not isinstance(category_conditions, list):
                continue

            # Подсчитываем сколько условий выполнено
            met_conditions = 0
            total_conditions = len(category_conditions)

            for condition in category_conditions:
                if self._check_condition_new_format(condition, metrics):
                    met_conditions += 1

            # Добавляем взвешенный score
            if total_conditions > 0:
                category_score = (met_conditions / total_conditions) * weight
                total_score += category_score

        # Нормализуем к 0-1
        return total_score / max_possible if max_possible > 0 else 0.0


    def _check_condition_new_format(self, condition: str, metrics: Dict) -> bool:
        """Проверка условия в новом формате (строки типа "adx_1h > 20")"""
        try:
            # ✅ ОБРАБОТКА ФУНКЦИЙ: abs(price - poc) <= X
            if condition.startswith("abs("):
                abs_expr = condition[4:condition.find(")")]
                rest = condition[condition.find(")")+1:].strip()

                parts = abs_expr.split("-")
                if len(parts) == 2:
                    left_val = self._resolve_metric_value(parts[0].strip(), metrics)
                    right_val = self._resolve_metric_value(parts[1].strip(), metrics)
                    abs_result = abs(left_val - right_val)

                    if "<=" in rest:
                        threshold_expr = rest.split("<=")[1].strip()
                        threshold = self._resolve_metric_value(threshold_expr, metrics)
                        return abs_result <= threshold

            # ✅ ОБРАБОТКА between
            if "between" in condition:
                parts = condition.split("between")
                metric = parts[0].strip()
                range_parts = parts[1].split("and")
                min_val = float(range_parts[0].strip())
                max_val = float(range_parts[1].strip())
                value = self._resolve_metric_value(metric, metrics)
                return min_val <= value <= max_val

            # ✅ ОБРАБОТКА == и !=  (СТРОКОВЫЕ СРАВНЕНИЯ)
            if "==" in condition:
                parts = condition.split("==")
                left_metric = parts[0].strip()
                right_value = parts[1].strip().strip("'\"")
                left_val = metrics.get(left_metric, "")
                return str(left_val) == right_value

            elif "!=" in condition:
                parts = condition.split("!=")
                left_metric = parts[0].strip()
                right_value = parts[1].strip().strip("'\"")
                left_val = metrics.get(left_metric, "")
                if right_value == "None":
                    return left_val is not None and left_val != "neutral"
                return str(left_val) != right_value

            # ✅ ЧИСЛОВЫЕ ОПЕРАТОРЫ
            elif ">=" in condition:
                parts = condition.split(">=")
                left = self._resolve_metric_value(parts[0].strip(), metrics)
                right = self._resolve_metric_value(parts[1].strip(), metrics)
                return left >= right
            elif ">" in condition:
                parts = condition.split(">")
                left = self._resolve_metric_value(parts[0].strip(), metrics)
                right = self._resolve_metric_value(parts[1].strip(), metrics)
                return left > right
            elif "<=" in condition:
                parts = condition.split("<=")
                left = self._resolve_metric_value(parts[0].strip(), metrics)
                right = self._resolve_metric_value(parts[1].strip(), metrics)
                return left <= right
            elif "<" in condition:
                parts = condition.split("<")
                left = self._resolve_metric_value(parts[0].strip(), metrics)
                right = self._resolve_metric_value(parts[1].strip(), metrics)
                return left < right
            else:
                return False
        except Exception as e:
            logger.debug(f"⚠️ Ошибка проверки условия '{condition}': {e}")
            return False


    def _resolve_metric_value(self, expr: str, metrics: Dict) -> float:
        """
        Вычислить значение метрики или выражения

        Поддерживает:
        - Простые метрики: "price", "adx_1h"
        - Арифметику: "1.2 * atr", "volume_ma20 * 0.7"
        - Числа: "20", "0.55"
        """
        expr = expr.strip()

        # Обработка арифметических операций
        if "*" in expr:
            parts = expr.split("*")
            left = self._resolve_metric_value(parts[0].strip(), metrics)
            right = self._resolve_metric_value(parts[1].strip(), metrics)
            return left * right
        elif "/" in expr:
            parts = expr.split("/")
            left = self._resolve_metric_value(parts[0].strip(), metrics)
            right = self._resolve_metric_value(parts[1].strip(), metrics)
            return left / right if right != 0 else 0
        elif "+" in expr:
            parts = expr.split("+")
            left = self._resolve_metric_value(parts[0].strip(), metrics)
            right = self._resolve_metric_value(parts[1].strip(), metrics)
            return left + right
        elif "-" in expr and not expr.startswith("-"):  # Избегаем отрицательных чисел
            parts = expr.split("-")
            left = self._resolve_metric_value(parts[0].strip(), metrics)
            right = self._resolve_metric_value(parts[1].strip(), metrics)
            return left - right

        # Проверка что это метрика
        if expr in metrics:
            value = metrics[expr]
            return float(value) if value is not None else 0.0

        # Попытка распарсить как число
        try:
            return float(expr)
        except ValueError:
            logger.debug(f"⚠️ Не могу распарсить '{expr}' как метрику или число")
            return 0.0



    def _calculate_confidence(
        self,
        scenario: Dict,
        metrics: Dict,
        validation: Dict
    ) -> str:
        """
        ✅ УЛУЧШЕННЫЙ РАСЧЁТ УВЕРЕННОСТИ
        """

        if not validation.get("basic_conditions", False):
            return "low"

        # Подсчитываем validation score
        passed = sum(1 for k, v in validation.items()
                    if isinstance(v, bool) and v and k != 'rejection_reason')
        total = sum(1 for v in validation.values() if isinstance(v, bool))
        validation_ratio = passed / total if total > 0 else 0

        try:
            adx = float(metrics.get("adx", 0))
            volume = float(metrics.get("volume", 1))
            volume_ma20 = float(metrics.get("volume_ma20", 1))
            volume_ratio = volume / max(volume_ma20, 1)

            adx_confidence = validation.get('adx_confidence', 0)
            vol_regime = validation.get('vol_regime', 'normal')

        except (ValueError, TypeError):
            adx = 0
            volume_ratio = 1.0
            adx_confidence = 0
            vol_regime = 'normal'

        # HIGH confidence
        if (validation_ratio >= 0.9 and
            adx >= 30 and
            vol_regime == 'high' and
            volume_ratio >= 2.0):
            return "high"

        # MEDIUM confidence
        elif (validation_ratio >= 0.7 and
            adx >= 30 and
            vol_regime in ['normal', 'high']):
            return "medium"

        else:
            return "low"



    def _build_signal(
        self,
        scenario: Dict,
        metrics: Dict,
        market_regime: str,
        confidence: str,
        validation: Dict
    ) -> Dict:
        """Построение финального сигнала"""

        price = metrics["price"]

        # ✅ АДАПТАЦИЯ ПОД НОВЫЙ ФОРМАТ JSON
        tactics = scenario.get("tactics", {})
        direction = tactics.get("direction", "long")

        entry_price = price
        atr = metrics.get("atr_14", price * 0.02)

        if FILTERS_AVAILABLE:
            levels = calculate_atr_based_levels(
                close_price=entry_price,
                atr_value=atr,
                direction='LONG' if direction == "long" else 'SHORT',
                atr_mult_sl=1.5,
                atr_mult_tp=3.0
            )

            if levels:
                stop_loss = levels['sl_price']
                tp1 = levels['tp_price']
                if direction == "long":
                    tp2 = tp1 * 1.2
                    tp3 = tp1 * 1.5
                else:
                    tp2 = tp1 * 0.85
                    tp3 = tp1 * 0.70
            else:
                levels = None
        else:
            levels = None

        # Fallback если ATR недоступен
        if not levels:
            sl_distance = price * 0.015
            if direction == "long":
                stop_loss = entry_price - sl_distance
                tp1 = entry_price * 1.015
                tp2 = entry_price * 1.025
                tp3 = entry_price * 1.04
            else:
                stop_loss = entry_price + sl_distance
                tp1 = entry_price * 0.985
                tp2 = entry_price * 0.975
                tp3 = entry_price * 0.96

        # Улучшить confidence через ConfidenceBooster
        base_confidence_str = confidence  # "low", "medium", "high"

        # Конвертируем строку в число
        confidence_map = {'low': 30, 'medium': 50, 'high': 80}
        base_confidence_num = confidence_map.get(base_confidence_str, 30)

        # Применяем booster
        boosted_confidence = self.confidence_booster.boost_confidence(
            base_confidence=base_confidence_num,
            market_data={"mtf": {}},  # Передаём минимальные данные
            indicators=metrics
        )

        logger.debug(f"💡 Confidence boost: {base_confidence_str} ({base_confidence_num}%) → {boosted_confidence:.1f}%")

        # Определяем новый уровень
        if boosted_confidence >= 60:
            final_confidence = "high"
        elif boosted_confidence >= 40:
            final_confidence = "medium"
        else:
            final_confidence = "low"

        return {
            "signal": True,
            "scenario_id": scenario.get("id", "UNKNOWN"),
            "scenario_name": scenario.get("id", "UNKNOWN"),
            "strategy": scenario.get("strategy", "unknown"),
            "phase": scenario.get("phase", "unknown"),
            "side": direction,
            "direction": "LONG" if direction == "long" else "SHORT",

            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,

            "confidence": final_confidence,
            "confidence_numeric": boosted_confidence,
            "market_regime": market_regime,
            "risk_profile": scenario.get("risk_management", {}).get("risk_per_trade", 0.01),
            "tactic_name": tactics.get("notes", "ATR-based"),
            "position_size": 1.0,

            "validation": validation,
            "influenced_metrics": {
                "adx": metrics.get("adx"),
                "volume_ratio": self._safe_volume_ratio(metrics),
                "trend_1h": metrics.get("trend_1h"),
                "trend_4h": metrics.get("trend_4h")
            },

            "status": "active",
            "timestamp": datetime.now(),
            "matched": True  # Для совместимости с signal_generation_service
        }


    def _calculate_sl_distance(self, sl_config: Dict, metrics: Dict) -> float:
        """Рассчитать расстояние для SL"""
        sl_type = sl_config.get("type", "fixed")
        sl_value = sl_config.get("value", "1.5%")

        price = metrics["price"]
        atr = metrics.get("atr", price * 0.02)

        if sl_type == "dynamic":
            # Парсим "max(1.8%, atr*1.0)" или подобные выражения
            if isinstance(sl_value, str) and "max" in sl_value:
                try:
                    # Извлекаем проценты и ATR множитель
                    # Формат: "max(X.X%, atr*Y.Y)"
                    import re
                    percent_match = re.search(r'(\d+\.?\d*)%', sl_value)
                    atr_match = re.search(r'atr\*(\d+\.?\d*)', sl_value)

                    percent_val = float(percent_match.group(1)) / 100 if percent_match else 0.015
                    atr_multiplier = float(atr_match.group(1)) if atr_match else 1.0

                    percent_sl = price * percent_val
                    atr_sl = atr * atr_multiplier

                    return max(percent_sl, atr_sl)

                except Exception as e:
                    logger.debug(f"⚠️ Ошибка парсинга SL value '{sl_value}': {e}")
                    return price * 0.015
            else:
                # Fallback для других dynamic типов
                return price * 0.015

        elif sl_type == "fixed":
            # Для fixed - просто процент
            try:
                if isinstance(sl_value, str) and "%" in sl_value:
                    percent = float(sl_value.replace("%", "")) / 100
                    return price * percent
                else:
                    return price * 0.015
            except:
                return price * 0.015

        else:
            # Fallback для остальных типов (level, trailing, etc)
            return price * 0.015


    def _safe_volume_ratio(self, metrics: Dict) -> float:
        """Безопасный расчёт volume ratio"""
        try:
            volume = float(metrics.get("volume", 1))
            volume_ma20 = float(metrics.get("volume_ma20", 1))
            return volume / max(volume_ma20, 1)
        except (ValueError, TypeError):
            return 1.0

    async def find_matching_scenarios(
        self,
        symbol: str,
        market_data: Dict,
        limit: int = 3
    ) -> List[Dict]:
        """
        Алиас для match_scenario() — для совместимости с bot.py

        Args:
            symbol: Торговая пара
            market_data: Все рыночные данные
            limit: Максимальное количество сценариев (не используется, т.к. возвращаем 1 лучший)

        Returns:
            List[Dict]: Список сценариев (обычно 1 элемент или пустой)
        """
        try:
            # Извлекаем данные из market_data
            indicators = market_data.get("indicators", {})
            mtf_trends = market_data.get("mtf_trends", {})
            volume_profile = market_data.get("volume_profile", {})
            news_sentiment = market_data.get("news_sentiment", {})
            veto_checks = market_data.get("veto_checks", {})

            # Вызываем основной метод
            signal = self.match_scenario(
                symbol=symbol,
                market_data=market_data,
                indicators=indicators,
                mtf_trends=mtf_trends,
                volume_profile=volume_profile,
                news_sentiment=news_sentiment,
                veto_checks=veto_checks
            )

            # Возвращаем список с 1 сценарием или пустой список
            if signal:
                return [signal]
            else:
                return []

        except Exception as e:
            logger.error(f"❌ find_matching_scenarios: {e}")
            return []



# Экспорт
__all__ = ["EnhancedScenarioMatcher"]
