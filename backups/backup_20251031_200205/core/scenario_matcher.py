#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Scenario Matcher - Объединённая версия с полной функциональностью
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from config.settings import logger, DATA_DIR
from core.scenario_selector import ScenarioSelector


class SignalStatus(Enum):
    """Статусы торговых сигналов"""

    DEAL = "deal"
    RISKY_ENTRY = "risky_entry"
    OBSERVATION = "observation"


@dataclass
class ScenarioMatch:
    """Результат сопоставления сценария"""

    scenario_id: int
    scenario_name: str
    score: float
    status: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: str
    veto_warnings: List[str]


class UnifiedScenarioMatcher:
    """
    Объединённый Scenario Matcher с полной функциональностью:
    - Загрузка JSON сценариев
    - Проверка MTF, ExoCharts, News, CVD, Clusters, Triggers
    - Расчёт weighted score
    - Классификация: deal / risky_entry / observation
    """

    def __init__(
        self,
        scenarios_path: str = None,
        deal_threshold: float = 0.15,
        risky_threshold: float = 0.10,
        observation_threshold: float = 0.05,
    ):
        """
        Args:
            scenarios_path: Путь к JSON-файлу со сценариями (опционально)
            deal_threshold: Порог для статуса DEAL (50%)
            risky_threshold: Порог для статуса RISKY_ENTRY (40%)
            observation_threshold: Порог для статуса OBSERVATION (30%)
        """

        # === ЗАГРУЗКА ОБОИХ ФАЙЛОВ СЦЕНАРИЕВ ===
        self.scenarios = []

        # Пути к файлам - используем ОБЪЕДИНЁННЫЙ файл!
        combined_path = os.path.join(
            DATA_DIR, "scenarios", "gio_scenarios_112_final_v3.json"
        )
        v3_path = combined_path
        v2_path = None


        # Счётчики
        v3_count = 0
        v2_count = 0

        # 1. ЗАГРУЖАЕМ V3 (100 сценариев)
        try:
            if os.path.exists(v3_path):
                logger.info(f"📂 Загрузка v3 сценариев из: {v3_path}")
                with open(v3_path, "r", encoding="utf-8") as f:
                    v3_data = json.load(f)

                # Извлекаем сценарии
                if isinstance(v3_data, dict) and "scenarios" in v3_data:
                    v3_scenarios = v3_data["scenarios"]
                elif isinstance(v3_data, list):
                    v3_scenarios = v3_data
                else:
                    v3_scenarios = []

                # Добавляем к общему списку
                self.scenarios.extend(v3_scenarios)
                v3_count = len(v3_scenarios)
                logger.info(f"✅ Загружено {v3_count} сценариев из v3")
            else:
                logger.warning(f"⚠️ Файл v3 не найден: {v3_path}")

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки v3 сценариев: {e}")

        # 2. ЗАГРУЖАЕМ V2 (12 сценариев)
        try:
            if os.path.exists(v2_path):
                logger.info(f"📂 Загрузка v2 сценариев из: {v2_path}")
                with open(v2_path, "r", encoding="utf-8") as f:
                    v2_data = json.load(f)

                # Извлекаем сценарии
                if isinstance(v2_data, dict) and "scenarios" in v2_data:
                    v2_scenarios = v2_data["scenarios"]
                elif isinstance(v2_data, list):
                    v2_scenarios = v2_data
                else:
                    v2_scenarios = []

                # ВАЖНО: Изменяем ID сценариев v2, чтобы избежать конфликтов
                # SCN_001 → SCN_101, SCN_002 → SCN_102, и т.д.
                for scenario in v2_scenarios:
                    original_id = scenario.get("id", "")

                    # Парсим номер из ID (например, "SCN_001" → 1)
                    if original_id.startswith("SCN_"):
                        try:
                            scenario_num = int(original_id.split("_")[1])
                            # Добавляем 100 к номеру
                            new_id = f"SCN_{scenario_num + 100:03d}"
                            scenario["id"] = new_id

                            # Добавляем метку источника
                            scenario["source"] = "v2_detailed"

                        except (ValueError, IndexError):
                            # Если не удалось распарсить, оставляем как есть
                            scenario["source"] = "v2_detailed"

                # Добавляем к общему списку
                self.scenarios.extend(v2_scenarios)
                v2_count = len(v2_scenarios)
                logger.info(
                    f"✅ Загружено {v2_count} сценариев из v2 (ID: SCN_101-SCN_112)"
                )
            else:
                logger.warning(f"⚠️ Файл v2 не найден: {v2_path}")

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки v2 сценариев: {e}")

        # 3. ИТОГОВАЯ СТАТИСТИКА
        total_count = len(self.scenarios)

        if total_count == 0:
            logger.error("❌ НЕ ЗАГРУЖЕНО НИ ОДНОГО СЦЕНАРИЯ!")
        else:
            logger.info(
                f"✅ UnifiedScenarioMatcher инициализирован "
                f"({total_count} сценариев: {v3_count} v3 + {v2_count} v2, "
                f"пороги: deal={deal_threshold:.0%}, risky={risky_threshold:.0%})"
            )

        # Пороги классификации
        self.deal_threshold = deal_threshold
        self.risky_threshold = risky_threshold
        self.observation_threshold = observation_threshold

        # Сохраняем путь (для совместимости)
        self.scenarios_path = v3_path if v3_count > 0 else v2_path
        # === ИНИЦИАЛИЗИРУЕМ SCENARIO SELECTOR ===
        self.scenario_selector = ScenarioSelector(top_k=3, diversity_weight=0.2)

    def load_scenarios(self, scenarios: Optional[List[Dict]] = None):
        """
        Загрузка сценариев из JSON или приём готового списка

        Args:
            scenarios: Готовый список сценариев (опционально)
        """
        try:
            # Если переданы готовые сценарии - используем их
            if scenarios is not None and isinstance(scenarios, list):
                self.scenarios = scenarios
                logger.info(f"✅ Получено {len(scenarios)} сценариев извне")
                return

            # Иначе - загружаем из JSON
            logger.info(f"🔍 Попытка загрузки сценариев из: {self.scenarios_path}")

            if not os.path.exists(self.scenarios_path):
                logger.error(f"❌ Файл сценариев не найден: {self.scenarios_path}")
                self.scenarios = []
                return

            with open(self.scenarios_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Проверка структуры JSON
            if isinstance(data, list):
                # JSON - это список сценариев
                self.scenarios = data
                logger.info(
                    f"✅ Загружено {len(self.scenarios)} сценариев из JSON (list)"
                )
            elif isinstance(data, dict) and "scenarios" in data:
                # JSON - это объект с ключом "scenarios"
                self.scenarios = data["scenarios"]
                logger.info(
                    f"✅ Загружено {len(self.scenarios)} сценариев из JSON (dict.scenarios)"
                )
            else:
                # Неизвестная структура
                logger.error(
                    f"❌ Неизвестная структура JSON. "
                    f"Тип: {type(data)}, "
                    f"Ключи: {list(data.keys()) if isinstance(data, dict) else 'N/A'}"
                )
                self.scenarios = []

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки сценариев: {e}", exc_info=True)
            self.scenarios = []

    def match_scenario(
        self,
        symbol: str,
        market_data: Dict,
        indicators: Dict,
        mtf_trends: Dict,
        volume_profile: Dict,
        news_sentiment: Dict,
        veto_checks: Dict,
        cvd_data: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """
        ОБНОВЛЁННАЯ ВЕРСИЯ (31 октября 2025)

        Изменения:
        1. ✨ Flexible MTF Alignment (вместо жёсткой проверки)
        2. ✨ ADX фильтрация по типу сценария
        3. 📉 Снижены веса Volume Profile (0.10) и Clusters (0.05)
        """
        try:
            # ============================================
            # ИМПОРТЫ С ОБРАБОТКОЙ ОШИБОК
            # ============================================
            try:
                from analytics.mtf_flexible_scorer import FlexibleMTFScorer
            except ImportError as e:
                logger.error(f"❌ FlexibleMTFScorer import failed: {e}")

                # Fallback: без MTF scorer
                class FlexibleMTFScorer:
                    def calculate_alignment(self, trends, direction):
                        return {
                            "score": 0.5,
                            "strength": "MODERATE",
                            "direction": direction,
                        }

                    def adjust_confidence(self, conf, result):
                        return conf

            try:
                # Импортируем через полный путь модуля
                import sys
                import os

                analytics_path = os.path.join(
                    os.path.dirname(__file__), "..", "analytics"
                )
                if analytics_path not in sys.path:
                    sys.path.insert(0, analytics_path)

                from indicators import AdvancedIndicators
            except ImportError:
                try:
                    # Альтернативный способ
                    from analytics.advanced_indicators import AdvancedIndicators
                except ImportError as e:
                    logger.error(f"❌ AdvancedIndicators import failed: {e}")

                    # Fallback: без ADX
                    class AdvancedIndicators:
                        @staticmethod
                        def calculate_adx(highs, lows, closes, period=14):
                            return {
                                "adx": 0,
                                "plus_di": 0,
                                "minus_di": 0,
                                "trend_strength": "weak",
                                "trend_direction": "neutral",
                            }

                        @staticmethod
                        def apply_adx_filter(confidence, scenario_type, adx_data):
                            return confidence

            logger.debug(f"🔍 Matching scenarios for {symbol}...")

            # ============================================
            # 1. ПОДГОТОВКА ДАННЫХ
            # ============================================

            unified_data = {
                "market_data": market_data,
                "price": market_data.get("price", market_data.get("close", 0)),
                "volume": market_data.get("volume", 0),
                "cvd": cvd_data if cvd_data else market_data.get("cvd", {}),
                "clusters": market_data.get("clusters", {}),
                "indicators": indicators,
                "mtf_trends": mtf_trends,
                "volume_profile": volume_profile,
                "news_sentiment": news_sentiment,
                "veto_checks": veto_checks,
            }

            # Нормализация MTF trends
            normalized_mtf = unified_data.get("mtf_trends", {})

            if isinstance(normalized_mtf, str):
                logger.warning(f"⚠️ MTF trends для {symbol} - строка: {normalized_mtf}")
                normalized_mtf = {
                    "1H": normalized_mtf,
                    "4H": normalized_mtf,
                    "1D": normalized_mtf,
                    "dominant": normalized_mtf,
                    "agreement": 100,
                    "strength": 0.5,
                }
            elif not isinstance(normalized_mtf, dict):
                logger.error(f"❌ MTF trends неправильный тип: {type(normalized_mtf)}")
                normalized_mtf = {
                    "1H": "neutral",
                    "4H": "neutral",
                    "1D": "neutral",
                    "dominant": "neutral",
                    "agreement": 0,
                    "strength": 0.0,
                }

            # VETO check
            if veto_checks.get("has_veto", False):
                logger.warning(
                    f"⛔ VETO активен для {symbol}: {veto_checks.get('veto_reasons', [])}"
                )
                return None

            # Вычисляем ADX
            ohlcv = market_data.get("ohlcv", [])

            if len(ohlcv) >= 14:
                recent_ohlcv = ohlcv[-30:]
                highs = [c["high"] for c in recent_ohlcv]
                lows = [c["low"] for c in recent_ohlcv]
                closes = [c["close"] for c in recent_ohlcv]

                adx_data = AdvancedIndicators.calculate_adx(
                    highs, lows, closes, period=14
                )
            else:
                adx_data = {
                    "adx": 0,
                    "plus_di": 0,
                    "minus_di": 0,
                    "trend_strength": "weak",
                    "trend_direction": "neutral",
                }
                logger.debug(f"⚠️ Недостаточно OHLCV данных для ADX ({len(ohlcv)} < 14)")

            # Инициализируем MTF scorer
            mtf_scorer = FlexibleMTFScorer()

            # ============================================
            # 2. ОЦЕНКА ВСЕХ СЦЕНАРИЕВ
            # ============================================

            best_match = None
            best_score = 0.0
            matched_features = []

            if not hasattr(self, "debug_counter"):
                self.debug_counter = 0
            self.debug_counter += 1

            debug_this_call = self.debug_counter <= 2

            if debug_this_call:
                print(f"\n🔍 DEBUG match_scenario call #{self.debug_counter}")

            scenario_scores = {}

            # =====================================================
            # DEBUG: Диагностика для Milestone #2
            # =====================================================
            if debug_this_call:
                logger.debug(f"🔍 ДИАГНОСТИКА match_scenario:")
                logger.debug(f"   market_data keys: {list(market_data.keys())}")
                logger.debug(f"   'ohlcv' в market_data: {'ohlcv' in market_data}")
                logger.debug(f"   len(ohlcv): {len(market_data.get('ohlcv', []))}")
                logger.debug(f"   mtf_trends type: {type(mtf_trends)}")
                logger.debug(
                    f"   mtf_trends keys: {list(mtf_trends.keys()) if isinstance(mtf_trends, dict) else 'NOT DICT'}"
                )

                # Проверка первого сценария
                if self.scenarios:
                    first_scenario = self.scenarios[0]
                    logger.debug(f"   Первый сценарий ID: {first_scenario.get('id')}")
                    logger.debug(f"   'conditions' keys: {list(first_scenario.get('conditions', {}).keys())}")
                    logger.debug(f"   'mtf_trends' в conditions: {'mtf_trends' in first_scenario.get('conditions', {})}")

                logger.debug(f"=" * 70)

            for scenario in self.scenarios:
                try:
                    scenario_id = scenario.get("id", "UNKNOWN")
                    scenario_type = scenario.get("type", "UNKNOWN")

                    # Вычисляем базовый score
                    score = self._calculate_scenario_score(  # ← Добавлен underscore!
                        scenario=scenario,
                        market_data=unified_data["market_data"],
                        indicators=indicators,
                        mtf_trends=normalized_mtf,
                        volume_profile=volume_profile,
                        news_sentiment=news_sentiment,
                        cvd_data=unified_data["cvd"],
                    )

                    # ✨ Flexible MTF Adjustment
                    conditions = scenario.get("conditions", {})
                    mtf_conditions = conditions.get("mtf_trends", {})

                    # 🔧 НОРМАЛИЗАЦИЯ: Преобразовать ключи normalized_mtf в lowercase
                    normalized_mtf_lowercase = {
                        k.lower(): v for k, v in normalized_mtf.items()
                    }

                    mtf_result = None
                    if mtf_conditions:
                        required_direction = mtf_conditions.get("required", "bullish")

                        mtf_result = mtf_scorer.calculate_alignment(
                            normalized_mtf_lowercase,  # ← ИСПОЛЬЗУЕМ LOWERCASE!
                            required_direction
                        )


                        # 🔍 DEBUG: Проверка результата
                        if debug_this_call and scenario.get('id') in ['SCN_001', 'SCN_002', 'SCN_003']:
                            print(f"   mtf_result: {mtf_result}")
                            print(f"   strength: {mtf_result.get('strength', 'N/A')}")

                        score = mtf_scorer.adjust_confidence(
                            score, mtf_result
                        )  # ← score УЖЕ 0-100

                        # 🔍 DEBUG: Проверка итогового score
                        if debug_this_call and scenario.get('id') in ['SCN_001', 'SCN_002', 'SCN_003']:
                            print(f"   score AFTER MTF: {score}")


                    adjusted_score = AdvancedIndicators.apply_adx_filter(
                        score, scenario_type, adx_data
                    )  # ← score УЖЕ 0-100


                    scenario_scores[scenario.get("id")] = adjusted_score


                    if debug_this_call and len(scenario_scores) <= 25:
                        # 🔍 ИСПРАВЛЕНИЕ: Проверка наличия mtf_result
                        if mtf_result and isinstance(mtf_result, dict):
                            mtf_str = mtf_result.get('strength', 'UNKNOWN')
                        else:
                            mtf_str = "N/A"
                        adx_str = f"{adx_data['adx']:.1f}"
                        print(
                            f"   {scenario_id}: score={adjusted_score*100:.2f}%  MTF={mtf_str}  ADX={adx_str}"
                        )


                except Exception as e:
                    logger.error(f"❌ Ошибка оценки сценария {scenario.get('id')}: {e}")
                    continue

            # ============================================
            # 3. ВЫБОР ЛУЧШЕГО СЦЕНАРИЯ
            # ============================================

            evaluated = self.scenario_selector.evaluate_all_scenarios(
                scenarios=self.scenarios,
                match_scores=scenario_scores,
                mtf_trends=normalized_mtf,
                current_regime=self._detect_market_regime(unified_data["market_data"]),
            )

            scored_scenario, selection_details = (
                self.scenario_selector.select_best_scenario(evaluated)
            )

            if scored_scenario is None:
                return None

            best_match = scored_scenario.scenario
            best_score = scored_scenario.match_score
            matched_features = self._get_matched_features(
                best_match, best_score
            )  # ← Добавлен underscore!

            # ============================================
            # 4. FALLBACK СЦЕНАРИИ
            # ============================================

            if best_score < self.observation_threshold:
                logger.debug(
                    f"⚠️ {symbol}: Best scenario score {best_score:.1f} < threshold. Fallback..."
                )

                cvd = unified_data.get("cvd", 0)
                ls_ratio = unified_data["market_data"].get("long_short_ratio", 1.0)
                funding = unified_data["market_data"].get("funding_rate", 0)
                rsi = indicators.get("rsi", 50)
                volume_ratio = unified_data["market_data"].get("volume_ratio", 1.0)

                # FALLBACK логика (LONG/SHORT/RANGE)
                if cvd > 2 and ls_ratio > 1.2 and rsi < 50:
                    best_match = {
                        "id": "FALLBACK_LONG",
                        "name": "Accumulation (Basic)",
                        "direction": "LONG",
                        "description": "Positive CVD + High LS Ratio",
                        "tp1_percent": 1.5,
                        "tp2_percent": 3.0,
                        "tp3_percent": 5.0,
                        "sl_percent": 1.0,
                        "conditions": {},
                        "timeframe": "1H",
                    }
                    best_score = 0.25
                    matched_features = ["positive_cvd", "high_ls_ratio", "oversold_rsi"]
                    logger.info(
                        f"🟢 FALLBACK LONG {symbol}! CVD={cvd:.1f}, LS={ls_ratio:.2f}"
                    )

                elif cvd < -2 and ls_ratio < 0.9 and rsi > 50:
                    best_match = {
                        "id": "FALLBACK_SHORT",
                        "name": "Distribution (Basic)",
                        "direction": "SHORT",
                        "description": "Negative CVD + Low LS Ratio",
                        "tp1_percent": 1.5,
                        "tp2_percent": 3.0,
                        "tp3_percent": 5.0,
                        "sl_percent": 1.0,
                        "conditions": {},
                        "timeframe": "1H",
                    }
                    best_score = 0.25
                    matched_features = [
                        "negative_cvd",
                        "low_ls_ratio",
                        "overbought_rsi",
                    ]
                    logger.info(
                        f"🔴 FALLBACK SHORT {symbol}! CVD={cvd:.1f}, LS={ls_ratio:.2f}"
                    )

                elif abs(cvd) < 2 and 0.9 <= ls_ratio <= 1.1 and volume_ratio > 1.2:
                    best_match = {
                        "id": "FALLBACK_RANGE",
                        "name": "Consolidation",
                        "direction": "LONG",
                        "description": "Neutral market",
                        "tp1_percent": 1.0,
                        "tp2_percent": 2.0,
                        "tp3_percent": 3.0,
                        "sl_percent": 0.8,
                        "conditions": {},
                        "timeframe": "1H",
                    }
                    best_score = 0.22
                    matched_features = ["neutral_cvd", "balanced_ls", "high_volume"]
                    logger.info(f"⚪ FALLBACK RANGE {symbol}: Neutral market")

                else:
                    return None

            # ============================================
            # 5. ФОРМИРОВАНИЕ РЕЗУЛЬТАТА
            # ============================================

            status = self._determine_status(best_score)  # ← Добавлен underscore!

            current_price = unified_data.get("price", 0)

            if current_price <= 0:
                logger.error(f"❌ Неправильная цена для {symbol}: {current_price}")
                return None

            direction = best_match.get("direction", "LONG")

            tp1_percent = best_match.get("tp1_percent", 2.0)
            tp2_percent = best_match.get("tp2_percent", 4.0)
            tp3_percent = best_match.get("tp3_percent", 6.0)
            sl_percent = best_match.get("sl_percent", 1.5)

            if direction.upper() == "LONG":
                tp1 = round(current_price * (1 + tp1_percent / 100), 2)
                tp2 = round(current_price * (1 + tp2_percent / 100), 2)
                tp3 = round(current_price * (1 + tp3_percent / 100), 2)
                stop_loss = round(current_price * (1 - sl_percent / 100), 2)
            else:
                tp1 = round(current_price * (1 - tp1_percent / 100), 2)
                tp2 = round(current_price * (1 - tp2_percent / 100), 2)
                tp3 = round(current_price * (1 - tp3_percent / 100), 2)
                stop_loss = round(current_price * (1 + sl_percent / 100), 2)

            result = {
                "scenario_id": best_match.get("id", "unknown"),
                "scenario_name": (
                    best_match.get("name")
                    or f"{best_match.get('strategy', 'Unknown').title()} - {best_match.get('phase', 'Setup').title()}"
                ),
                "symbol": symbol,
                "status": status,
                "score": round(best_score * 100, 2),
                "direction": direction,
                "entry_price": current_price,
                "timestamp": datetime.now().isoformat(),
                "matched_features": matched_features,
                "conditions": best_match.get("conditions", {}),
                "description": best_match.get("description", ""),
                "timeframe": best_match.get("timeframe", "1H"),
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3,
                "stop_loss": stop_loss,
                "adx": adx_data,
                "mtf_alignment": mtf_result,
            }

            # Логирование
            if status == "deal":
                logger.info(
                    f"🎯 DEAL для {symbol}! Score: {result['score']:.1f}%, {result['scenario_name']}"
                )
            elif status == "risky_entry":
                logger.info(
                    f"⚠️ RISKY ENTRY для {symbol}! Score: {result['score']:.1f}%, {result['scenario_name']}"
                )
            else:
                logger.debug(
                    f"📊 {symbol}: Score: {result['score']:.1f}%, {result['scenario_name']}"
                )

            if self.debug_counter <= 5:
                print(
                    f"\n✅ FINAL result: score={best_score:.2f}, status={status}, id={result.get('scenario_id')}"
                )

            return result

        except Exception as e:
            logger.error(f"❌ match_scenario для {symbol}: {e}", exc_info=True)
            return None

    def _calculate_scenario_score(
        self,
        scenario: Dict,
        market_data: Dict,
        indicators: Dict,
        mtf_trends: Dict,
        volume_profile: Dict,
        news_sentiment: Dict,
        cvd_data: Optional[Dict],
    ) -> float:
        """Расчёт weighted score сценария с ПОЛНЫМ DEBUG"""
        try:
            scenario_id = scenario.get("id", "UNKNOWN")

            # Получаем 'if' блок
            if_block = scenario.get("if")

            logger.info(f"🔍 _calculate_scenario_score для {scenario_id}")
            logger.info(f"   if_block exists: {bool(if_block)}")
            logger.info(f"   if_block type: {type(if_block)}")

            # === ЕСЛИ ЕСТЬ 'if' БЛОК - ИСПОЛЬЗУЕМ ПАРСЕР ===
            if if_block:
                logger.info(f"✅ ИСПОЛЬЗУЕМ ПАРСЕР для {scenario_id}")
                if_score = self._evaluate_if_conditions(
                    scenario, market_data, indicators
                )
                logger.info(f"   if_score = {if_score:.2%}")

                # Парсер имеет приоритет 60%
                score = if_score
                logger.info(f"   score after if: {score:.2%}")
                return score
            else:
                logger.info(
                    f"⚠️ БЕЗ if блока - используем старый метод для {scenario_id}"
                )
                return 0.20

        except Exception as e:
            logger.error(f"❌ Ошибка в _calculate_scenario_score: {e}", exc_info=True)
            return 0.0

    def _check_mtf_policy(
        self, scenario: Dict, indicators: Dict, mtf_trends: Dict
    ) -> float:
        """Проверка MTF условий с поддержкой v2 и v3 форматов"""
        try:
            # === ОПРЕДЕЛЯЕМ ФОРМАТ СЦЕНАРИЯ ===
            source = scenario.get("source", "v3")

            # === ПОДДЕРЖКА v2 ФОРМАТА (детальный) ===
            if (
                source == "v2_detailed"
                and "mtf" in scenario
                and isinstance(scenario["mtf"], dict)
            ):
                mtf_config = scenario["mtf"]
                mode = mtf_config.get("mode", "majority")
                required_alignment = mtf_config.get("required_alignment", 2)
                conditions = mtf_config.get("conditions", {})

                # Получаем тренды через универсальный геттер
                trend_1d = self._get_trend(mtf_trends, indicators, "1D")
                trend_4h = self._get_trend(mtf_trends, indicators, "4H")
                trend_1h = self._get_trend(mtf_trends, indicators, "1H")

                # Проверяем соответствие условиям
                aligned_count = 0

                # 1D
                if "1D" in conditions:
                    allowed_trends = conditions["1D"]
                    if trend_1d in allowed_trends:
                        aligned_count += 1

                # 4H
                if "4H" in conditions:
                    allowed_trends = conditions["4H"]
                    if trend_4h in allowed_trends:
                        aligned_count += 1

                # 1H
                if "1H" in conditions:
                    allowed_trends = conditions["1H"]
                    if trend_1h in allowed_trends:
                        aligned_count += 1

                # Оценка на основе mode
                if mode == "majority":
                    if aligned_count >= required_alignment:
                        return 0.9  # ✅ Достаточно выравнивания
                    elif aligned_count == required_alignment - 1:
                        return 0.6  # ⚠️ Почти достаточно
                    else:
                        return 0.3  # ❌ Недостаточно

                elif mode == "counter_trend":
                    # Для контр-трендовых: разные направления ОК
                    if aligned_count >= 1:
                        return 0.7
                    else:
                        return 0.4

                elif mode == "correction_in_range":
                    # Для коррекций в рендже
                    if aligned_count >= 1:
                        return 0.8
                    else:
                        return 0.5

                elif mode == "breakout_retest":
                    # Для breakout retest
                    if aligned_count >= required_alignment:
                        return 0.9
                    else:
                        return 0.5

            # === ПОДДЕРЖКА v3 ФОРМАТА (упрощённый) ===
            else:
                required_opinion = scenario.get("opinion", "bullish")

                if required_opinion == "bullish":
                    required_trend = "uptrend"
                elif required_opinion == "bearish":
                    required_trend = "downtrend"
                else:
                    required_trend = required_opinion

                # Получаем тренды через универсальный геттер
                trend_1h = self._get_trend(mtf_trends, indicators, "1H")
                trend_4h = self._get_trend(mtf_trends, indicators, "4H")
                trend_1d = self._get_trend(mtf_trends, indicators, "1D")

                # Считаем совпадения
                aligned_count = 0
                if trend_1h.lower() == required_trend.lower():
                    aligned_count += 1
                if trend_4h.lower() == required_trend.lower():
                    aligned_count += 1
                if trend_1d.lower() == required_trend.lower():
                    aligned_count += 1

                # Оценка
                if aligned_count == 3:
                    return 1.0
                elif aligned_count == 2:
                    return 0.7
                elif aligned_count == 1:
                    return 0.5
                else:
                    return 0.3

        except Exception as e:
            logger.error(f"❌ Ошибка проверки MTF: {e}")
            return 0.5

    def _check_exocharts(
        self, scenario: Dict, market_data: Dict, volume_profile: Dict
    ) -> float:
        """Проверка ExoCharts / Volume Profile"""
        try:
            current_price = market_data.get("price", 0)
            poc = volume_profile.get("poc", 0) or market_data.get("poc", 0)
            vah = volume_profile.get("vah", 0) or market_data.get("vah", 0)
            val = volume_profile.get("val", 0) or market_data.get("val", 0)

            if not all([current_price, poc, vah, val]):
                return 0.3  # нет данных Volume Profile

            direction = scenario.get("direction", "long")

            if direction == "long":
                # Для лонга хорошо: цена около VAL или чуть выше POC
                if val > 0 and abs(current_price - val) / val < 0.01:  # ±1% от VAL
                    return 0.9
                elif poc > 0 and current_price > poc and current_price < vah:
                    return 0.8
                elif current_price > vah:
                    return 0.6  # цена высоко, риск коррекции

            elif direction == "short":
                # Для шорта хорошо: цена около VAH или чуть ниже POC
                if vah > 0 and abs(current_price - vah) / vah < 0.01:  # ±1% от VAH
                    return 0.9
                elif poc > 0 and current_price < poc and current_price > val:
                    return 0.8
                elif current_price < val:
                    return 0.6  # цена низко, риск отскока

            return 0.5

        except Exception as e:
            logger.error(f"❌ Ошибка проверки ExoCharts: {e}")
            return 0.5

    def _check_indicator_conditions(self, conditions: Dict, indicators: Dict) -> float:
        """Проверка индикаторов (RSI, MACD, ATR)"""
        try:
            score = 0.0
            checks = 0

            # RSI
            if "rsi" in conditions:
                rsi_cond = conditions["rsi"]
                rsi_value = indicators.get("rsi", 50)

                if "min" in rsi_cond and "max" in rsi_cond:
                    if rsi_cond["min"] <= rsi_value <= rsi_cond["max"]:
                        score += 1
                checks += 1

            # MACD
            if "macd" in conditions:
                macd_cond = conditions["macd"]
                macd_histogram = indicators.get("macd_histogram", 0)

                if macd_cond.get("signal") == "bullish" and macd_histogram > 0:
                    score += 1
                elif macd_cond.get("signal") == "bearish" and macd_histogram < 0:
                    score += 1
                checks += 1

            # ATR
            if "atr" in conditions:
                atr_cond = conditions["atr"]
                atr_value = indicators.get("atr", 0)
                atr_threshold = atr_cond.get("min", 0)

                if atr_value >= atr_threshold:
                    score += 1
                checks += 1

            return score / checks if checks > 0 else 0.8  # По умолчанию OK

        except Exception as e:
            logger.error(f"❌ Ошибка проверки индикаторов: {e}")
            return 0.5

    def _check_news_policy(self, scenario: Dict, news_sentiment: Dict) -> float:
        """Проверка новостного sentiment"""
        try:
            sentiment = news_sentiment.get("sentiment", "neutral")
            sentiment_score = news_sentiment.get("score", 0)  # от -10 до +10
            direction = scenario.get("direction", "long")

            if direction == "long" and sentiment in ["bullish", "positive"]:
                return 0.8 + min(0.2, abs(sentiment_score) / 50)
            elif direction == "short" and sentiment in ["bearish", "negative"]:
                return 0.8 + min(0.2, abs(sentiment_score) / 50)
            elif sentiment == "neutral":
                return 0.5
            else:
                return 0.3  # sentiment против направления

        except Exception as e:
            logger.error(f"❌ Ошибка проверки news: {e}")
            return 0.5

    def _check_cvd(self, scenario: Dict, cvd_data: Dict) -> float:
        """Проверка CVD"""
        try:
            cvd = cvd_data.get("cvd", 0)
            direction = scenario.get("direction", "long")

            if direction == "long" and cvd > 0:
                return min(0.7 + (cvd / 1000000) * 0.3, 1.0)
            elif direction == "short" and cvd < 0:
                return min(0.7 + (abs(cvd) / 1000000) * 0.3, 1.0)
            else:
                return 0.4

        except Exception as e:
            logger.error(f"❌ Ошибка проверки CVD: {e}")
            return 0.5

    def _check_triggers(
        self, scenario: Dict, indicators: Dict, market_data: Dict
    ) -> float:
        """Проверка триггеров (T1/T2/T3) с поддержкой V2 и V3 форматов"""
        try:
            # Получаем направление сделки
            direction = scenario.get("direction", "long")
            if isinstance(direction, dict):
                direction = direction.get("direction", "long")

            # Получаем tactics из сценария V3
            tactics = scenario.get("tactics", {})
            if isinstance(tactics, dict):
                direction = tactics.get("direction", direction)

            score = 0.0
            triggers_fired = 0
            max_triggers = 3

            # T1: Технический триггер (RSI)
            rsi = indicators.get("rsi_1h", indicators.get("rsi", 50))
            if isinstance(rsi, (int, float)):
                if direction == "long" and 30 < rsi < 50:
                    triggers_fired += 1
                elif direction == "short" and 50 < rsi < 70:
                    triggers_fired += 1

            # T2: Объёмный триггер
            volume_ratio = market_data.get("volume_ratio", 1.0)
            if isinstance(volume_ratio, (int, float)) and volume_ratio > 1.3:
                triggers_fired += 1

            # T3: CVD подтверждение
            cvd_value = market_data.get("cvd", 0)

            # Безопасная проверка CVD
            if isinstance(cvd_value, (int, float)):
                if direction == "long" and cvd_value > 0:
                    triggers_fired += 1
                elif direction == "short" and cvd_value < 0:
                    triggers_fired += 1

            score = triggers_fired / max_triggers
            return score

        except Exception as e:
            logger.error(f"❌ Ошибка проверки triggers: {e}")
            return 0.5

    def _determine_status(self, score: float) -> str:
        """Определение статуса на основе score"""
        if score >= self.deal_threshold:
            return "deal"
        elif score >= self.risky_threshold:
            return "risky_entry"
        else:
            return "observation"

    def _get_trend(self, mtf_trends: Dict, indicators: Dict, tf_key: str) -> str:
        """Универсальный геттер для тренда с поддержкой разных форматов"""
        # Попробуем разные варианты ключей (1H, 1h, 1D, 1d)
        tf_variants = [tf_key, tf_key.lower(), tf_key.upper()]

        for variant in tf_variants:
            # Пробуем получить из mtf_trends
            if isinstance(mtf_trends, dict) and variant in mtf_trends:
                trend_data = mtf_trends[variant]

                # Если значение - словарь с ключом "trend"
                if isinstance(trend_data, dict):
                    return trend_data.get("trend", "neutral")
                # Если значение - строка напрямую
                elif trend_data:
                    return trend_data

            # Fallback: пробуем получить из indicators
            ind_key = f"trend_{variant.lower()}"
            if ind_key in indicators:
                return indicators[ind_key]

        # Если ничего не нашли - возвращаем neutral
        return "neutral"

    def _get_matched_features(self, scenario: Dict, score: float) -> List[str]:
        """Получение списка matched features для сценария"""
        features = []

        if score >= 0.7:
            features.append("mtf_aligned")
        if score >= 0.6:
            features.append("volume_profile_confirmed")
        if score >= 0.5:
            features.append("positive_news")

        return features

    def _parse_condition_string(
        self, condition: str, market_data: Dict, indicators: Dict
    ) -> bool:
        """
        Парсит строковые условия из JSON сценариев V3

        Примеры:
        - "trend_1d=='bullish'"
        - "abs(price-poc)<=1.0*atr"
        - "cluster.stacked_imbalance_up>=3"
        - "cvd_confirms==true"
        - "triggers.all==true"
        """
        try:
            # Подготавливаем данные для eval
            context = {
                "price": market_data.get("price", 0),
                "poc": market_data.get(
                    "poc", market_data.get("volume_profile", {}).get("poc", 0)
                ),
                "vah": market_data.get(
                    "vah", market_data.get("volume_profile", {}).get("vah", 0)
                ),
                "val": market_data.get(
                    "val", market_data.get("volume_profile", {}).get("val", 0)
                ),
                "atr": indicators.get("atr", market_data.get("price", 0) * 0.02),
                "volume": market_data.get("volume", 0),
                "volume_ma20": market_data.get(
                    "volume_ma20", market_data.get("volume", 0)
                ),
                "abs": abs,
                "min": min,
                "max": max,
            }

            # Добавляем тренды
            mtf_trends = market_data.get("mtf_trends", {})
            context["trend_1h"] = mtf_trends.get("1H", "neutral")
            context["trend_4h"] = mtf_trends.get("4H", "neutral")
            context["trend_1d"] = mtf_trends.get("1D", "neutral")

            # Добавляем CVD
            cvd_data = market_data.get("cvd", {})
            context["cvd_confirms"] = cvd_data.get("cvd_confirms", False)
            context["cvd_value"] = cvd_data.get("cvd_value", 0)

            # Добавляем clusters
            clusters = market_data.get("clusters", {})
            context["cluster"] = type(
                "obj",
                (object,),
                {
                    "stacked_imbalance_up": clusters.get("stacked_imbalance_up", 0),
                    "stacked_imbalance_down": clusters.get("stacked_imbalance_down", 0),
                    "poc_shift_up": clusters.get("poc_shift_up", False),
                    "poc_shift_down": clusters.get("poc_shift_down", False),
                    "absorption_high": clusters.get("absorption_high", False),
                    "absorption_low": clusters.get("absorption_low", False),
                },
            )()

            # Добавляем triggers
            context["triggers"] = type(
                "obj",
                (object,),
                {
                    "all": True,  # Для совместимости с "triggers.all==true"
                    "partial": False,
                },
            )()

            # Добавляем pullback_to_poc
            poc_value = context["poc"]
            price_value = context["price"]
            atr_value = context["atr"]
            if poc_value > 0 and atr_value > 0:
                context["pullback_to_poc"] = (
                    abs(price_value - poc_value) <= 1.0 * atr_value
                )
            else:
                context["pullback_to_poc"] = False

            # Добавляем news
            news = market_data.get("news_sentiment", {})
            context["news_score"] = news.get("overall_score", 0)

            # Парсим условие с защитой от опасного кода
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)

        except Exception as e:
            logger.debug(f"⚠️ Ошибка парсинга условия '{condition}': {e}")
            return False

    def _detect_market_regime(self, market_data: Dict) -> str:
        """Определить текущий режим рынка"""
        mtf_trends = market_data.get("mtf_trends", {})
        dominant = mtf_trends.get("dominant", "neutral")

        if dominant in ["strong_bullish", "bullish"]:
            return "uptrend"
        elif dominant in ["strong_bearish", "bearish"]:
            return "downtrend"
        else:
            return "neutral"

    def _evaluate_if_conditions(
        self, scenario: Dict, market_data: Dict, indicators: Dict
    ) -> float:
        """
        Оценка всех условий из блока 'if' в сценарии V3
        Поддерживает парсинг строковых условий
        """
        try:
            if_block = scenario.get("if", {})
            if not if_block:
                return 0.8  # Если нет условий - даём хороший score

            score = 0.0
            total_sections = 0

            # === MTF CONDITIONS ===
            if "mtf" in if_block:
                mtf_conditions = if_block["mtf"]
                if isinstance(mtf_conditions, list) and mtf_conditions:
                    mtf_passed = sum(
                        1
                        for cond in mtf_conditions
                        if self._parse_condition_string(cond, market_data, indicators)
                    )
                    mtf_score = mtf_passed / len(mtf_conditions)
                    score += mtf_score * 0.30  # MTF вес 30%
                    total_sections += 0.30

            # === EXOCHARTS CONDITIONS ===
            if "exocharts" in if_block:
                exo_conditions = if_block["exocharts"]
                if isinstance(exo_conditions, list) and exo_conditions:
                    exo_passed = sum(
                        1
                        for cond in exo_conditions
                        if self._parse_condition_string(cond, market_data, indicators)
                    )
                    exo_score = exo_passed / len(exo_conditions)
                    score += exo_score * 0.25  # ExoCharts вес 25%
                    total_sections += 0.25

            # === CVD CONDITIONS ===
            if "cvd" in if_block:
                cvd_conditions = if_block["cvd"]
                if isinstance(cvd_conditions, list) and cvd_conditions:
                    cvd_passed = sum(
                        1
                        for cond in cvd_conditions
                        if self._parse_condition_string(cond, market_data, indicators)
                    )
                    cvd_score = cvd_passed / len(cvd_conditions)
                    score += cvd_score * 0.15  # CVD вес 15%
                    total_sections += 0.15

            # === CLUSTERS CONDITIONS (OR groups) ===
            if "clusters" in if_block:
                clusters_conditions = if_block["clusters"]
                if isinstance(clusters_conditions, list) and clusters_conditions:
                    cluster_passed = 0
                    for cluster_group in clusters_conditions:
                        if isinstance(cluster_group, list) and cluster_group:
                            # Проверяем хотя бы одно условие в группе
                            if any(
                                self._parse_condition_string(
                                    cond, market_data, indicators
                                )
                                for cond in cluster_group
                            ):
                                cluster_passed += 1

                    cluster_score = cluster_passed / len(clusters_conditions)
                    score += cluster_score * 0.15  # Clusters вес 15%
                    total_sections += 0.15

            # === NEWS CONDITIONS (OR groups) ===
            if "news" in if_block:
                news_conditions = if_block["news"]
                if isinstance(news_conditions, list) and news_conditions:
                    news_passed = 0
                    for news_group in news_conditions:
                        if isinstance(news_group, list) and news_group:
                            # Проверяем хотя бы одно условие в группе
                            if any(
                                self._parse_condition_string(
                                    cond, market_data, indicators
                                )
                                for cond in news_group
                            ):
                                news_passed += 1

                    news_score = news_passed / len(news_conditions)
                    score += news_score * 0.10  # News вес 10%
                    total_sections += 0.10

            # === TRIGGERS CONDITIONS ===
            if "triggers" in if_block:
                triggers_conditions = if_block["triggers"]
                if isinstance(triggers_conditions, list) and triggers_conditions:
                    triggers_passed = 0
                    for trigger_group in triggers_conditions:
                        if isinstance(trigger_group, list) and trigger_group:
                            # Проверяем хотя бы одно условие в группе
                            if any(
                                self._parse_condition_string(
                                    cond, market_data, indicators
                                )
                                for cond in trigger_group
                            ):
                                triggers_passed += 1

                    trigger_score = triggers_passed / len(triggers_conditions)
                    score += trigger_score * 0.05  # Triggers вес 5%
                    total_sections += 0.05

            # Нормализуем score
            final_score = score / total_sections if total_sections > 0 else 0.5
            return max(0.0, min(1.0, final_score))

        except Exception as e:
            logger.error(f"❌ Ошибка оценки условий 'if': {e}")
            return 0.5


# Алиас для совместимости
ScenarioMatcher = UnifiedScenarioMatcher
EnhancedScenarioMatcher = UnifiedScenarioMatcher
