"""
Flexible Multi-Timeframe Alignment Scorer
Заменяет жёсткую проверку "все TF bullish" на взвешенную оценку
"""

class FlexibleMTFScorer:
    """
    Гибкая оценка согласованности трендов по таймфреймам

    Веса:
    - 4H (долгосрочный): 50% - главный тренд
    - 1H (среднесрочный): 30% - подтверждение
    - 15M (краткосрочный): 20% - точка входа
    """

    def __init__(self):
        # Веса по важности таймфрейма
        self.weights = {
            "4h": 0.50,   # Долгосрочный тренд - самый важный
            "1h": 0.30,   # Среднесрочный - подтверждение
            "15m": 0.20   # Краткосрочный - точка входа (больше шума)
        }

        # Пороги согласованности
        self.thresholds = {
            "STRONG": 0.80,    # >= 80%: Все TF согласны (напр. 4H+1H+15M = 100%)
            "MODERATE": 0.60,  # >= 60%: Большинство согласны (напр. 4H+1H = 80%)
            "WEAK": 0.40,      # >= 40%: Минимальное согласие (напр. 4H+15M = 70%)
        }

    def calculate_alignment(self, trends: dict, required_direction: str) -> dict:
        """
        Вычисление согласованности трендов

        Args:
            trends: {"4h": "BULLISH", "1h": "BULLISH", "15m": "BEARISH"}
            required_direction: "BULLISH" или "BEARISH"

        Returns:
            {
                "score": 0.80,      # 4H(0.50) + 1H(0.30) = 0.80
                "strength": "STRONG",
                "direction": "BULLISH",
                "aligned_tfs": ["4h", "1h"],
                "misaligned_tfs": ["15m"]
            }
        """
        required_direction = required_direction.upper()

        # Считаем взвешенный score
        score = 0.0
        aligned_tfs = []
        misaligned_tfs = []

        for tf, weight in self.weights.items():
            trend = trends.get(tf, "NEUTRAL").upper()

            if trend == required_direction:
                score += weight
                aligned_tfs.append(tf)
            else:
                misaligned_tfs.append(tf)

        # Определяем силу alignment
        if score >= self.thresholds["STRONG"]:
            strength = "STRONG"
        elif score >= self.thresholds["MODERATE"]:
            strength = "MODERATE"
        elif score >= self.thresholds["WEAK"]:
            strength = "WEAK"
        else:
            strength = "NONE"

        # Определяем направление
        if score >= 0.40:  # Минимум 40% согласны
            direction = required_direction
        else:
            direction = "NEUTRAL"

        return {
            "score": round(score, 2),
            "strength": strength,
            "direction": direction,
            "aligned_tfs": aligned_tfs,
            "misaligned_tfs": misaligned_tfs
        }

    def adjust_confidence(self, base_confidence: float, mtf_result: dict) -> float:
        """
        Корректировка базового confidence на основе MTF alignment

        Args:
            base_confidence: Исходный confidence (0-100)
            mtf_result: Результат calculate_alignment()

        Returns:
            Скорректированный confidence (0-100)

        Multipliers:
        - STRONG: x1.20 (+20% если все TF согласны)
        - MODERATE: x1.00 (без изменений)
        - WEAK: x0.80 (-20% если слабое согласие)
        - NONE: x0.50 (-50% если нет согласия)
        """
        multipliers = {
            "STRONG": 1.20,    # Усилить на 20%
            "MODERATE": 1.00,  # Без изменений
            "WEAK": 0.80,      # Ослабить на 20%
            "NONE": 0.50       # Ослабить на 50%
        }

        multiplier = multipliers[mtf_result["strength"]]
        adjusted = base_confidence * multiplier

        # Ограничиваем в пределах 0-100
        return min(max(adjusted, 0.0), 100.0)

    def get_explanation(self, mtf_result: dict) -> str:
        """
        Текстовое пояснение MTF alignment

        Returns:
            "STRONG BULLISH alignment (80%): 4h✓ 1h✓ 15m✗"
        """
        aligned = " ".join([f"{tf}✓" for tf in mtf_result["aligned_tfs"]])
        misaligned = " ".join([f"{tf}✗" for tf in mtf_result["misaligned_tfs"]])

        return f"{mtf_result['strength']} {mtf_result['direction']} alignment ({int(mtf_result['score']*100)}%): {aligned} {misaligned}"


# ============================================
# ТЕСТИРОВАНИЕ (можно запустить отдельно)
# ============================================

if __name__ == "__main__":
    scorer = FlexibleMTFScorer()

    # Тест 1: ВСЕ bullish (было 37.5%, станет STRONG)
    test1 = {"4h": "BULLISH", "1h": "BULLISH", "15m": "BULLISH"}
    result1 = scorer.calculate_alignment(test1, "BULLISH")
    print(f"\n✅ TEST 1 (All Bullish):")
    print(f"   {scorer.get_explanation(result1)}")
    print(f"   Confidence adjustment: 50 → {scorer.adjust_confidence(50, result1)}")

    # Тест 2: 4H+1H bullish, 15M bearish (было 0%, станет MODERATE)
    test2 = {"4h": "BULLISH", "1h": "BULLISH", "15m": "BEARISH"}
    result2 = scorer.calculate_alignment(test2, "BULLISH")
    print(f"\n✅ TEST 2 (4H+1H Bullish, 15M Bearish):")
    print(f"   {scorer.get_explanation(result2)}")
    print(f"   Confidence adjustment: 50 → {scorer.adjust_confidence(50, result2)}")

    # Тест 3: Только 4H bullish (было 0%, станет WEAK)
    test3 = {"4h": "BULLISH", "1h": "BEARISH", "15m": "BEARISH"}
    result3 = scorer.calculate_alignment(test3, "BULLISH")
    print(f"\n✅ TEST 3 (Only 4H Bullish):")
    print(f"   {scorer.get_explanation(result3)}")
    print(f"   Confidence adjustment: 50 → {scorer.adjust_confidence(50, result3)}")

    # Тест 4: Все bearish (было 0%, станет NONE)
    test4 = {"4h": "BEARISH", "1h": "BEARISH", "15m": "BEARISH"}
    result4 = scorer.calculate_alignment(test4, "BULLISH")
    print(f"\n✅ TEST 4 (All Bearish vs BULLISH requirement):")
    print(f"   {scorer.get_explanation(result4)}")
    print(f"   Confidence adjustment: 50 → {scorer.adjust_confidence(50, result4)}")
