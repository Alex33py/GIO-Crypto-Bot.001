#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confidence Booster
Повышает точность confidence score через дополнительные проверки
"""

class ConfidenceBooster:
    """Улучшает confidence score через взвешенные факторы"""

    def __init__(self):
        self.weights = {
            'trend_strength': 0.25,
            'volume_confirmation': 0.20,
            'mtf_alignment': 0.20,
            'technical_confluence': 0.15,
            'sentiment': 0.10,
            'volatility': 0.10
        }

    def boost_confidence(self, base_confidence: float, market_data: dict, indicators: dict) -> float:
        """
        Повысить confidence через дополнительные проверки

        Args:
            base_confidence: Базовая confidence из сценария (0-100)
            market_data: Данные рынка
            indicators: Технические индикаторы

        Returns:
            Улучшенная confidence (0-100)
        """

        boosters = []

        # 1. Сила тренда (ADX + RSI)
        trend_boost = self._check_trend_strength(indicators)
        boosters.append(('trend_strength', trend_boost))

        # 2. Подтверждение объёмом
        volume_boost = self._check_volume_confirmation(indicators)
        boosters.append(('volume_confirmation', volume_boost))

        # 3. MTF выравнивание
        mtf_boost = self._check_mtf_alignment(market_data.get('mtf', {}))
        boosters.append(('mtf_alignment', mtf_boost))

        # 4. Техническое схождение (EMA, MACD)
        technical_boost = self._check_technical_confluence(indicators)
        boosters.append(('technical_confluence', technical_boost))

        # 5. Волатильность (ATR)
        volatility_boost = self._check_volatility(indicators)
        boosters.append(('volatility', volatility_boost))

        # Взвешенная сумма
        total_boost = sum(
            self.weights[name] * value
            for name, value in boosters
        )

        # Итоговая confidence
        final_confidence = min(100, base_confidence + (total_boost * 40))  # Бонус до +40%

        return round(final_confidence, 1)

    def _check_trend_strength(self, indicators: dict) -> float:
        """Проверить силу тренда (ADX + RSI)"""
        adx = indicators.get('adx', 0)
        rsi = indicators.get('rsi', 50)

        # ADX > 25 = сильный тренд
        adx_score = min(1.0, adx / 40) if adx > 25 else 0

        # RSI экстремум = сильный тренд
        rsi_score = 0
        if rsi > 60 or rsi < 40:
            rsi_score = min(1.0, abs(rsi - 50) / 30)

        return (adx_score + rsi_score) / 2

    def _check_volume_confirmation(self, indicators: dict) -> float:
        """Проверить подтверждение объёмом"""
        volume = indicators.get('volume', 0)
        volume_avg = indicators.get('volume_avg', 1)

        if volume_avg == 0:
            return 0

        volume_ratio = volume / volume_avg

        # Volume > 1.5x avg = сильное подтверждение
        if volume_ratio > 1.5:
            return 1.0
        elif volume_ratio > 1.2:
            return 0.7
        elif volume_ratio > 1.0:
            return 0.4
        else:
            return 0

    def _check_mtf_alignment(self, mtf_data: dict) -> float:
        """Проверить выравнивание MTF"""
        trends = []

        for tf in ['1h', '4h', '1d']:
            if tf in mtf_data:
                trend = mtf_data[tf].get('trend', 'neutral')
                trends.append(trend)

        if len(trends) == 0:
            return 0

        # Все тренды одинаковые = идеальное выравнивание
        if len(set(trends)) == 1 and trends[0] != 'neutral':
            return 1.0

        # 2 из 3 совпадают
        if trends.count('up') >= 2 or trends.count('down') >= 2:
            return 0.6

        return 0.3

    def _check_technical_confluence(self, indicators: dict) -> float:
        """Проверить техническое схождение"""
        score = 0

        # 1. Цена относительно EMA
        price = indicators.get('price', 0)
        ema_20 = indicators.get('ema_20', 0)
        ema_50 = indicators.get('ema_50', 0)

        if price > 0 and ema_20 > 0 and ema_50 > 0:
            # Цена выше обеих EMA = бычий сигнал
            if price > ema_20 and price > ema_50 and ema_20 > ema_50:
                score += 0.5
            # Цена ниже обеих EMA = медвежий сигнал
            elif price < ema_20 and price < ema_50 and ema_20 < ema_50:
                score += 0.5

        # 2. MACD гистограмма
        macd_hist = indicators.get('macd_hist', 0)
        if abs(macd_hist) > 0:
            score += 0.5

        return min(1.0, score)

    def _check_volatility(self, indicators: dict) -> float:
        """Проверить волатильность (ATR)"""
        atr_pct = indicators.get('atr_pct', 0)

        # Оптимальная волатильность 1-3%
        if 1.0 <= atr_pct <= 3.0:
            return 1.0
        elif 0.5 <= atr_pct < 1.0 or 3.0 < atr_pct <= 5.0:
            return 0.6
        else:
            return 0.3
