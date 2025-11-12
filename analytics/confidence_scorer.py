# -*- coding: utf-8 -*-
"""
Advanced Confidence Scoring System
"""

class ConfidenceScorer:
    """Calculate confidence level 0.0-1.0"""

    def __init__(self):
        pass

    def calculate_score(self, mtf_score, adx, rsi, volume_ratio,
                       funding_rate=0, ls_ratio=1.0, cvd_ratio=0):
        """
        Calculate final confidence score (0.0 - 1.0)

        Args:
            mtf_score: 0-3 (from MTFScorer)
            adx: 0-100 (trend strength)
            rsi: 0-100 (momentum)
            volume_ratio: 1.0-5.0+ (volume confirmation)
            funding_rate: -0.1 to 0.1 (market bias)
            ls_ratio: long/short ratio (market crowding)
            cvd_ratio: -1.0 to 1.0 (buying pressure)

        Returns:
            confidence: 0.0-1.0
            level: 'LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH'
        """

        # Base score from MTF (most important)
        confidence = (mtf_score / 3.0) * 0.4  # 40% weight

        # ADX strength (trend confirmation)
        if adx > 40:
            confidence += 0.2  # +20%
        elif adx > 30:
            confidence += 0.1

        # RSI position (momentum)
        if 45 <= rsi <= 65:
            confidence += 0.15  # +15%

        # Volume confirmation
        if volume_ratio > 1.5:
            confidence += 0.15  # +15%
        elif volume_ratio > 1.0:
            confidence += 0.1

        # CVD (buy/sell pressure)
        if cvd_ratio > 0.3:
            confidence += 0.1  # +10%

        # Market metrics (reduce if crowded)
        if abs(funding_rate) > 0.01:
            confidence *= 0.9  # -10%

        if ls_ratio > 2.5 or ls_ratio < 0.4:
            confidence *= 0.85  # -15%

        # Normalize to 0.0-1.0
        confidence = max(0.0, min(1.0, confidence))

        # Classify level
        if confidence > 0.8:
            level = 'VERY_HIGH'
        elif confidence > 0.6:
            level = 'HIGH'
        elif confidence > 0.4:
            level = 'MEDIUM'
        else:
            level = 'LOW'

        return confidence, level


# TEST
if __name__ == "__main__":
    scorer = ConfidenceScorer()

    # Perfect signal
    conf, level = scorer.calculate_score(
        mtf_score=3, adx=50, rsi=55, volume_ratio=2.0,
        cvd_ratio=0.5, ls_ratio=1.5, funding_rate=0.001
    )
    print(f"Perfect signal: {conf:.2f} ({level})")  # ~0.85 VERY_HIGH

    # Weak signal
    conf, level = scorer.calculate_score(
        mtf_score=1, adx=20, rsi=35, volume_ratio=0.8,
        cvd_ratio=-0.3, ls_ratio=2.8, funding_rate=0.015
    )
    print(f"Weak signal: {conf:.2f} ({level})")  # ~0.15 LOW
