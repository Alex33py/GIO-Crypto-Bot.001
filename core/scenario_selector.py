"""
Multi-Criteria Scenario Selection Engine
Профессиональный выбор сценариев с рейтингованием и diversity
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from config.settings import logger


@dataclass
class ScoredScenario:
    """Сценарий с полным профилем оценки"""

    scenario: Dict
    match_score: float  # Точность совпадения (0-1)
    confidence_level: str  # deal | risky_entry | observation
    relevance_score: float  # Релевантность к текущему тренду (0-1)
    stability_score: float  # Стабильность сценария (0-1)
    diversity_rank: float  # Diversity score (0-1)
    composite_score: float  # Финальный score


class ScenarioSelector:
    """Выбор сценариев на основе множества критериев"""

    def __init__(self, top_k: int = 3, diversity_weight: float = 0.2):
        """
        Args:
            top_k: Количество top сценариев для selection
            diversity_weight: Вес diversity при расчёте composite score
        """
        self.top_k = top_k
        self.diversity_weight = diversity_weight
        self.selected_scenarios_history = []

    def evaluate_all_scenarios(
        self,
        scenarios: List[Dict],
        match_scores: Dict[str, float],
        mtf_trends: Dict,
        current_regime: str = "neutral",
    ) -> List[ScoredScenario]:
        """Полная оценка всех сценариев по множеству критериев"""
        evaluated = []

        for scenario in scenarios:
            scenario_id = scenario.get("id")
            score_value = match_scores.get(scenario_id, 0.0)

            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Извлекаем float из tuple ЗДЕСЬ!
            if isinstance(score_value, tuple):
                match_score = float(score_value[0]) if score_value else 0.0
            elif isinstance(score_value, (int, float)):
                match_score = float(score_value)
            else:
                logger.warning(f"⚠️ Некорректный тип match_score для {scenario_id}: {type(score_value)}")
                match_score = 0.0

            # 1. RELEVANCE: насколько сценарий релевантен текущему тренду
            relevance = self._calculate_relevance(scenario, mtf_trends)

            # 2. STABILITY: стабильность (сценарии, которые часто работают)
            stability = self._calculate_stability(scenario, current_regime)

            # 3. DIVERSITY: отличие от уже выбранных
            diversity = self._calculate_diversity(scenario)

            # 4. Confidence level (теперь передаётся match_score как float)
            confidence_level = self._determine_confidence(match_score)

            # 5. COMPOSITE SCORE (взвешенная комбинация)
            composite = self._calculate_composite_score(
                match_score=match_score,  # ✅ Теперь это float!
                relevance=relevance,
                stability=stability,
                diversity=diversity,
                confidence_level=confidence_level,
            )

            scored = ScoredScenario(
                scenario=scenario,
                match_score=match_score,  # ✅ Сохраняем как float
                confidence_level=confidence_level,
                relevance_score=relevance,
                stability_score=stability,
                diversity_rank=diversity,
                composite_score=composite,
            )
            evaluated.append(scored)

        return evaluated


    def select_best_scenario(
        self,
        evaluated_scenarios: List[ScoredScenario],
    ) -> Tuple[Optional[ScoredScenario], Dict]:
        """Выбор ЛУЧШЕГО сценария с деталями решения"""
        if not evaluated_scenarios:
            return None, {"reason": "No scenarios evaluated"}

        # Сортируем по composite_score
        sorted_scenarios = sorted(
            evaluated_scenarios,
            key=lambda x: x.composite_score,
            reverse=True,
        )

        best = sorted_scenarios[0]

        # Логика выбора
        reason = self._determine_selection_reason(
            best,
            sorted_scenarios[:3] if len(sorted_scenarios) >= 3 else sorted_scenarios,
        )

        # Сохраняем в историю для diversity
        self.selected_scenarios_history.append(best.scenario.get("id"))
        if len(self.selected_scenarios_history) > 50:
            self.selected_scenarios_history.pop(0)

        return best, reason

    def _calculate_relevance(self, scenario: Dict, mtf_trends: Dict) -> float:
        """Релевантность к текущему тренду"""
        direction = scenario.get("direction", "LONG")
        dominant_trend = mtf_trends.get("dominant", "neutral")

        relevance = 0.0

        if direction.upper() == "LONG":
            if dominant_trend in ["bullish", "strong_bullish"]:
                relevance = 1.0
            elif dominant_trend == "neutral":
                relevance = 0.5
            else:
                relevance = 0.2
        else:  # SHORT
            if dominant_trend in ["bearish", "strong_bearish"]:
                relevance = 1.0
            elif dominant_trend == "neutral":
                relevance = 0.5
            else:
                relevance = 0.2

        return relevance

    def _calculate_stability(self, scenario: Dict, current_regime: str) -> float:
        """Стабильность сценария"""
        # В реальной системе: историческая win_rate
        base_stability = 0.7

        # Modifier по типу
        scenario_type = scenario.get("type", "standard")
        if scenario_type == "advanced":
            base_stability += 0.1

        return min(base_stability, 1.0)

    def _calculate_diversity(self, scenario: Dict) -> float:
        """Diversity: насколько этот сценарий отличается от уже выбранных"""
        scenario_id = scenario.get("id")

        # Если часто выбирали - давать меньше diversity
        selection_count = self.selected_scenarios_history.count(scenario_id)
        diversity = max(0.0, 1.0 - (selection_count / 10.0))

        return diversity

    def _determine_confidence(self, match_score) -> str:
        """Определить уровень confidence"""
        # ✅ Если match_score - tuple, берём первый элемент
        if isinstance(match_score, tuple):
            score_value = match_score[0]
        else:
            score_value = match_score

        # Проверяем корректность типа
        if not isinstance(score_value, (int, float)):
            logger.warning(f"⚠️ match_score некорректного типа: {type(score_value)}, значение: {score_value}")
            return "observation"

        # Определяем confidence
        if score_value >= 0.15:
            return "deal"
        elif score_value >= 0.10:
            return "risky_entry"
        else:
            return "observation"


    def _calculate_composite_score(
        self,
        match_score: float,
        relevance: float,
        stability: float,
        diversity: float,
        confidence_level: str,
    ) -> float:
        """Composite score с взвешиванием критериев"""
        # Веса для каждого критерия
        weights = {
            "match": 0.40,  # Точность совпадения с условиями
            "relevance": 0.25,  # Релевантность к тренду
            "stability": 0.15,  # Историческая стабильность
            "diversity": self.diversity_weight,  # Diversity
        }

        composite = (
            weights["match"] * match_score
            + weights["relevance"] * relevance
            + weights["stability"] * stability
            + weights["diversity"] * diversity
        )

        # Boost для deal-уровня
        if confidence_level == "deal":
            composite *= 1.2

        return min(composite, 1.0)

    def _determine_selection_reason(
        self,
        best: ScoredScenario,
        top_candidates: List[ScoredScenario],
    ) -> Dict:
        """Детальное объяснение выбора"""
        reason = {
            "selected_scenario": best.scenario.get("id"),
            "composite_score": round(best.composite_score, 3),
            "confidence": best.confidence_level,
            "match_score": round(best.match_score, 3),
            "relevance": round(best.relevance_score, 3),
            "stability": round(best.stability_score, 3),
            "diversity": round(best.diversity_rank, 3),
            "selection_reason": self._explain_selection(best, top_candidates),
            "alternatives": [
                {
                    "scenario_id": s.scenario.get("id"),
                    "score": round(s.composite_score, 3),
                }
                for s in top_candidates[1:3]
            ],
        }
        return reason

    def _explain_selection(
        self,
        best: ScoredScenario,
        candidates: List[ScoredScenario],
    ) -> str:
        """Текстовое объяснение выбора"""
        if best.match_score >= 0.35:
            return "High match score + Good relevance to current trend"
        elif best.relevance_score >= 0.8:
            return "Excellent relevance to current market regime"
        elif best.diversity_rank > 0.8:
            return "Fresh scenario for portfolio diversity"
        else:
            return "Balanced scenario meeting multiple criteria"
