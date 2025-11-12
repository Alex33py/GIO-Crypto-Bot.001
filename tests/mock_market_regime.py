"""
Mock MarketRegimeDetector для бектестинга
Упрощённый детектор рыночного режима на основе RSI + Trend + Volume
"""


class MarketRegimeDetector:
    """Mock market regime detector"""

    def __init__(self):
        pass

    def detect(self, metrics: dict) -> str:
        """
        Определение рыночного режима на основе метрик

        Args:
            metrics: Dict с рыночными метриками (RSI, trend, volume, etc.)

        Returns:
            Режим рынка: "trending", "ranging", "volatile", "quiet"
        """
        try:
            rsi = metrics.get('rsi', 50)
            volume_ratio = metrics.get('volume_ratio', 1.0)
            trend_1h = metrics.get('trend_1h', 'neutral')
            trend_4h = metrics.get('trend_4h', 'neutral')
            adx = metrics.get('adx', 25)

            # TRENDING: сильный тренд + высокий ADX
            if adx > 30 and (trend_1h == trend_4h != 'neutral'):
                return "trending"

            # RANGING: RSI в середине + низкий ADX
            if 40 <= rsi <= 60 and adx < 20:
                return "ranging"

            # VOLATILE: высокий volume + широкий диапазон RSI
            if volume_ratio > 1.5:
                return "volatile"

            # QUIET: низкий volume + стабильный RSI
            if volume_ratio < 0.8:
                return "quiet"

            # Default: ranging
            return "ranging"

        except Exception as e:
            print(f"⚠️ Market regime detection error: {e}")
            return "ranging"


__all__ = ['MarketRegimeDetector']
