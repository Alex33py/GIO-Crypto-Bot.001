# -*- coding: utf-8 -*-
"""
MTF (Multi-Timeframe) Alignment Scorer
Гибкая система оценки тренда
"""

class MTFScorer:
    """Flexible MTF alignment scoring"""

    def __init__(self):
        pass

    def calculate_mtf_score(self, close, ema_20, ema_50, ema_200=None):
        """
        Calculate MTF alignment score (0-3)

        Returns:
            score: 0-3 (higher = stronger trend)
            strength: 'WEAK', 'MEDIUM', 'STRONG'
        """
        score = 0

        # Level 1: Price above EMA20 (short-term)
        if close > ema_20:
            score += 1

        # Level 2: EMA20 above EMA50 (medium-term)
        if ema_20 > ema_50:
            score += 1

        # Level 3: EMA50 above EMA200 (long-term, if available)
        if ema_200 is not None and ema_50 > ema_200:
            score += 1

        # Strength classification
        if score == 0:
            strength = 'BEARISH'
        elif score == 1:
            strength = 'WEAK'
        elif score == 2:
            strength = 'MEDIUM'
        else:
            strength = 'STRONG'

        return score, strength

    def should_allow_entry(self, score, min_score=2):
        """
        Check if MTF score allows entry

        Args:
            score: MTF score (0-3)
            min_score: Minimum required score (default 2)

        Returns:
            bool: True if entry allowed
        """
        return score >= min_score


# EXAMPLE USAGE
if __name__ == "__main__":
    scorer = MTFScorer()

    # Test case 1: STRONG uptrend
    score, strength = scorer.calculate_mtf_score(
        close=50000,
        ema_20=49500,
        ema_50=49000,
        ema_200=48000
    )
    print(f"Case 1: Score={score}, Strength={strength}")  # 3, STRONG

    # Test case 2: MEDIUM uptrend
    score, strength = scorer.calculate_mtf_score(
        close=50000,
        ema_20=49500,
        ema_50=48000  # EMA20 > close, but not > EMA50
    )
    print(f"Case 2: Score={score}, Strength={strength}")  # 1-2, MEDIUM

    # Test case 3: WEAK (allow if min_score=1)
    score, strength = scorer.calculate_mtf_score(
        close=50000,
        ema_20=49000,  # close > ema_20 only
        ema_50=51000
    )
    print(f"Case 3: Score={score}, Strength={strength}, Allow={scorer.should_allow_entry(score, min_score=1)}")
