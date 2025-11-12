#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Technical Indicators
Продвинутые технические индикаторы для трейдинга
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from config.settings import logger


class AdvancedIndicators:
    """Продвинутые технические индикаторы"""

    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict:
        """
        MACD - Moving Average Convergence Divergence

        Args:
            prices: Список цен закрытия
            fast_period: Быстрая EMA (default: 12)
            slow_period: Медленная EMA (default: 26)
            signal_period: Сигнальная линия (default: 9)

        Returns:
            Dict с MACD, Signal, Histogram
        """
        try:
            if len(prices) < slow_period:
                return {"macd": 0, "signal": 0, "histogram": 0}

            # Преобразуем в numpy
            prices_arr = np.array(prices, dtype=float)

            # EMA helper
            def ema(data, period):
                multiplier = 2 / (period + 1)
                ema_values = [data[0]]
                for price in data[1:]:
                    ema_values.append(
                        (price - ema_values[-1]) * multiplier + ema_values[-1]
                    )
                return ema_values

            # Вычисляем MACD
            fast_ema = ema(prices_arr, fast_period)
            slow_ema = ema(prices_arr, slow_period)

            macd_line = np.array(fast_ema) - np.array(slow_ema)
            signal_line = ema(macd_line, signal_period)
            histogram = macd_line - np.array(signal_line)

            return {
                "macd": round(float(macd_line[-1]), 4),
                "signal": round(float(signal_line[-1]), 4),
                "histogram": round(float(histogram[-1]), 4),
                "trend": "bullish" if histogram[-1] > 0 else "bearish",
            }

        except Exception as e:
            logger.error(f"❌ Ошибка расчёта MACD: {e}")
            return {"macd": 0, "signal": 0, "histogram": 0}

    @staticmethod
    def calculate_stoch_rsi(
        prices: List[float], period: int = 14, smooth_k: int = 3, smooth_d: int = 3
    ) -> Dict:
        """
        Stochastic RSI - более чувствительная версия RSI

        Args:
            prices: Список цен
            period: Период RSI
            smooth_k: Период сглаживания %K
            smooth_d: Период сглаживания %D

        Returns:
            Dict с StochRSI K и D линиями
        """
        try:
            if len(prices) < period + smooth_k + smooth_d:
                return {"k": 50, "d": 50, "signal": "neutral"}

            # Вычисляем RSI
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            avg_gain = np.mean(gains[:period])
            avg_loss = np.mean(losses[:period])

            rsi_values = []
            for i in range(period, len(prices)):
                if avg_loss == 0:
                    rsi = 100
                else:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)

                if i < len(prices) - 1:
                    avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                    avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            # Stochastic of RSI
            if len(rsi_values) < period:
                return {"k": 50, "d": 50, "signal": "neutral"}

            stoch_rsi = []
            for i in range(period, len(rsi_values) + 1):
                rsi_slice = rsi_values[i - period : i]
                min_rsi = min(rsi_slice)
                max_rsi = max(rsi_slice)

                if max_rsi - min_rsi == 0:
                    stoch = 50
                else:
                    stoch = ((rsi_values[i - 1] - min_rsi) / (max_rsi - min_rsi)) * 100
                stoch_rsi.append(stoch)

            # Сглаживание %K
            k_values = []
            for i in range(smooth_k, len(stoch_rsi) + 1):
                k_values.append(np.mean(stoch_rsi[i - smooth_k : i]))

            # Сглаживание %D
            d_values = []
            for i in range(smooth_d, len(k_values) + 1):
                d_values.append(np.mean(k_values[i - smooth_d : i]))

            k = k_values[-1] if k_values else 50
            d = d_values[-1] if d_values else 50

            # Определяем сигнал
            if k > 80:
                signal = "overbought"
            elif k < 20:
                signal = "oversold"
            else:
                signal = "neutral"

            return {"k": round(float(k), 2), "d": round(float(d), 2), "signal": signal}

        except Exception as e:
            logger.error(f"❌ Ошибка расчёта Stochastic RSI: {e}")
            return {"k": 50, "d": 50, "signal": "neutral"}

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float], period: int = 20, std_dev: float = 2.0
    ) -> Dict:
        """
        Bollinger Bands - полосы Боллинджера

        Args:
            prices: Список цен
            period: Период SMA
            std_dev: Количество стандартных отклонений

        Returns:
            Dict с upper, middle, lower bands и width
        """
        try:
            if len(prices) < period:
                return {"upper": 0, "middle": 0, "lower": 0, "width": 0}

            prices_arr = np.array(prices[-period:], dtype=float)

            # Средняя линия (SMA)
            middle = np.mean(prices_arr)

            # Стандартное отклонение
            std = np.std(prices_arr)

            # Верхняя и нижняя полосы
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)

            # Ширина полос (в %)
            width = ((upper - lower) / middle) * 100 if middle > 0 else 0

            # Позиция цены относительно полос
            current_price = prices[-1]
            position = (
                ((current_price - lower) / (upper - lower)) * 100
                if (upper - lower) > 0
                else 50
            )

            return {
                "upper": round(float(upper), 2),
                "middle": round(float(middle), 2),
                "lower": round(float(lower), 2),
                "width": round(float(width), 4),
                "position": round(float(position), 2),
                "squeeze": width < 10,  # Сжатие полос
            }

        except Exception as e:
            logger.error(f"❌ Ошибка расчёта Bollinger Bands: {e}")
            return {"upper": 0, "middle": 0, "lower": 0, "width": 0}

    @staticmethod
    def calculate_atr(
        highs: List[float], lows: List[float], closes: List[float], period: int = 14
    ) -> Dict:
        """
        ATR - Average True Range (волатильность)

        Args:
            highs: Список максимумов
            lows: Список минимумов
            closes: Список цен закрытия
            period: Период расчёта

        Returns:
            Dict с ATR и уровнем волатильности
        """
        try:
            if len(closes) < period + 1:
                return {"atr": 0, "volatility": "low"}

            # True Range
            tr_list = []
            for i in range(1, len(closes)):
                high_low = highs[i] - lows[i]
                high_close = abs(highs[i] - closes[i - 1])
                low_close = abs(lows[i] - closes[i - 1])

                tr = max(high_low, high_close, low_close)
                tr_list.append(tr)

            # ATR (сглаженное среднее TR)
            atr = np.mean(tr_list[-period:])

            # Определяем уровень волатильности
            current_price = closes[-1]
            atr_percentage = (atr / current_price) * 100 if current_price > 0 else 0

            if atr_percentage > 3:
                volatility = "high"
            elif atr_percentage > 1.5:
                volatility = "medium"
            else:
                volatility = "low"

            return {
                "atr": round(float(atr), 2),
                "atr_percentage": round(float(atr_percentage), 2),
                "volatility": volatility,
            }

        except Exception as e:
            logger.error(f"❌ Ошибка расчёта ATR: {e}")
            return {"atr": 0, "volatility": "low"}

    @staticmethod
    def calculate_adx(
        highs: List[float], lows: List[float], closes: List[float], period: int = 14
    ) -> Dict:
        """
        ADX - Average Directional Index (сила тренда)

        ✨ ОБНОВЛЁННАЯ ВЕРСИЯ для Backtest Integration

        Args:
            highs: Список максимумов
            lows: Список минимумов
            closes: Список цен закрытия
            period: Период расчёта

        Returns:
            Dict с ADX, +DI, -DI и силой тренда

        Интерпретация ADX:
        - ADX > 25: Сильный тренд (трендовые сценарии работают)
        - ADX 20-25: Умеренный тренд
        - ADX < 20: Флет/Ranging (Mean Reversion работает)

        Интерпретация DI:
        - +DI > -DI: Бычий тренд
        - -DI > +DI: Медвежий тренд
        """
        try:
            # Проверка минимальной длины данных
            if len(closes) < period + 1:
                return {
                    "adx": 0,
                    "plus_di": 0,
                    "minus_di": 0,
                    "trend_strength": "weak",
                    "trend_direction": "neutral",
                }

            # Преобразуем в numpy arrays
            highs_arr = np.array(highs, dtype=float)
            lows_arr = np.array(lows, dtype=float)
            closes_arr = np.array(closes, dtype=float)

            # ============================================
            # 1. Вычисляем True Range (TR)
            # ============================================
            tr_list = []
            for i in range(1, len(closes_arr)):
                high_low = highs_arr[i] - lows_arr[i]
                high_close = abs(highs_arr[i] - closes_arr[i - 1])
                low_close = abs(lows_arr[i] - closes_arr[i - 1])

                tr = max(high_low, high_close, low_close)
                tr_list.append(tr)

            # ============================================
            # 2. Вычисляем Directional Movement (+DM, -DM)
            # ============================================
            plus_dm_list = []
            minus_dm_list = []

            for i in range(1, len(highs_arr)):
                high_diff = highs_arr[i] - highs_arr[i - 1]
                low_diff = lows_arr[i - 1] - lows_arr[i]

                # +DM: Движение вверх
                if high_diff > low_diff and high_diff > 0:
                    plus_dm = high_diff
                else:
                    plus_dm = 0

                # -DM: Движение вниз
                if low_diff > high_diff and low_diff > 0:
                    minus_dm = low_diff
                else:
                    minus_dm = 0

                plus_dm_list.append(plus_dm)
                minus_dm_list.append(minus_dm)

            # ============================================
            # 3. Сглаживание (smoothed averages)
            # ============================================
            def smooth(data, period):
                """Wilder's smoothing (как в оригинальном ADX)"""
                if len(data) < period:
                    return [0] * len(data)

                smoothed = [sum(data[:period])]  # Первое значение - сумма

                for i in range(period, len(data)):
                    # Wilder's smoothing: (prev * (period-1) + current) / period
                    smoothed.append((smoothed[-1] * (period - 1) + data[i]) / period)

                return smoothed

            smoothed_tr = smooth(tr_list, period)
            smoothed_plus_dm = smooth(plus_dm_list, period)
            smoothed_minus_dm = smooth(minus_dm_list, period)

            # ============================================
            # 4. Вычисляем +DI и -DI
            # ============================================
            plus_di_list = []
            minus_di_list = []

            for i in range(len(smoothed_tr)):
                if smoothed_tr[i] > 0:
                    plus_di = (smoothed_plus_dm[i] / smoothed_tr[i]) * 100
                    minus_di = (smoothed_minus_dm[i] / smoothed_tr[i]) * 100
                else:
                    plus_di = 0
                    minus_di = 0

                plus_di_list.append(plus_di)
                minus_di_list.append(minus_di)

            # ============================================
            # 5. Вычисляем DX (Directional Index)
            # ============================================
            dx_list = []

            for i in range(len(plus_di_list)):
                di_sum = plus_di_list[i] + minus_di_list[i]
                di_diff = abs(plus_di_list[i] - minus_di_list[i])

                if di_sum > 0:
                    dx = (di_diff / di_sum) * 100
                else:
                    dx = 0

                dx_list.append(dx)

            # ============================================
            # 6. Вычисляем ADX (сглаженный DX)
            # ============================================
            if len(dx_list) < period:
                adx_value = 0
            else:
                # Первое значение ADX - среднее первых period значений DX
                adx_list = [np.mean(dx_list[:period])]

                # Последующие значения - Wilder's smoothing
                for i in range(period, len(dx_list)):
                    adx = ((adx_list[-1] * (period - 1)) + dx_list[i]) / period
                    adx_list.append(adx)

                adx_value = adx_list[-1] if adx_list else 0

            # ============================================
            # 7. Последние значения +DI и -DI
            # ============================================
            plus_di_value = plus_di_list[-1] if plus_di_list else 0
            minus_di_value = minus_di_list[-1] if minus_di_list else 0

            # ============================================
            # 8. Определяем силу и направление тренда
            # ============================================
            if adx_value > 25:
                trend_strength = "strong"
            elif adx_value > 20:
                trend_strength = "moderate"
            else:
                trend_strength = "weak"

            # Направление по DI
            if plus_di_value > minus_di_value:
                trend_direction = "bullish"
            elif minus_di_value > plus_di_value:
                trend_direction = "bearish"
            else:
                trend_direction = "neutral"

            return {
                "adx": round(float(adx_value), 2),
                "plus_di": round(float(plus_di_value), 2),
                "minus_di": round(float(minus_di_value), 2),
                "trend_strength": trend_strength,
                "trend_direction": trend_direction,
            }

        except Exception as e:
            logger.error(f"❌ Ошибка расчёта ADX: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "adx": 0,
                "plus_di": 0,
                "minus_di": 0,
                "trend_strength": "weak",
                "trend_direction": "neutral",
            }

    @staticmethod
    def apply_adx_filter(
        confidence: float, scenario_type: str, adx_data: Dict
    ) -> float:
        """
        Корректировка confidence на основе ADX

        ✨ НОВАЯ ФУНКЦИЯ для Backtest Integration

        Args:
            confidence: Базовый confidence (0-100)
            scenario_type: Тип сценария (BREAKOUT, MEAN_REVERSION и т.д.)
            adx_data: Результат calculate_adx()

        Returns:
            Скорректированный confidence

        Логика:
        1. Трендовые сценарии (BREAKOUT, TREND_CONTINUATION):
        - Нужен СИЛЬНЫЙ тренд (ADX > 25) → усилить +15%
        - Флет (ADX < 20) → ослабить -40%

        2. Флетовые сценарии (MEAN_REVERSION, RANGE_BOUND):
        - Нужен ФЛЕТ (ADX < 20) → усилить +10%
        - Сильный тренд (ADX > 30) → ослабить -30%

        Примеры:
            >>> apply_adx_filter(50, 'BREAKOUT', {'adx': 30})  # Сильный тренд
            57.5  # 50 * 1.15

            >>> apply_adx_filter(50, 'BREAKOUT', {'adx': 15})  # Флет
            30.0  # 50 * 0.60

            >>> apply_adx_filter(50, 'MEAN_REVERSION', {'adx': 15})  # Флет
            55.0  # 50 * 1.10
        """
        try:
            adx_value = adx_data.get("adx", 0)

            # ============================================
            # 1. ТРЕНДОВЫЕ СЦЕНАРИИ
            # ============================================
            # Эти сценарии работают НА ТРЕНДЕ
            trending_scenarios = [
                "BREAKOUT",
                "TREND_CONTINUATION",
                "WYCKOFF_MARKUP",
                "WYCKOFF_MARKDOWN",
                "MOMENTUM",
                "TREND_REVERSAL",  # Может быть у вас
            ]

            if scenario_type.upper() in trending_scenarios:
                if adx_value > 25:
                    # Сильный тренд → УСИЛИТЬ
                    confidence *= 1.15
                    logger.debug(
                        f"   📈 ADX {adx_value:.1f} > 25 → {scenario_type} усилен на 15%"
                    )

                elif adx_value < 20:
                    # Флет → ОСЛАБИТЬ (трендовые стратегии не работают)
                    confidence *= 0.60
                    logger.debug(
                        f"   📉 ADX {adx_value:.1f} < 20 → {scenario_type} ослаблен на 40%"
                    )

            # ============================================
            # 2. ФЛЕТОВЫЕ СЦЕНАРИИ
            # ============================================
            # Эти сценарии работают НА ФЛЕТЕ
            ranging_scenarios = [
                "MEAN_REVERSION",
                "RANGE_BOUND",
                "WYCKOFF_ACCUMULATION",
                "WYCKOFF_DISTRIBUTION",
                "CONSOLIDATION",
                "SIDEWAYS",  # Может быть у вас
            ]

            if scenario_type.upper() in ranging_scenarios:
                if adx_value < 20:
                    # Флет → УСИЛИТЬ
                    confidence *= 1.10
                    logger.debug(
                        f"   📊 ADX {adx_value:.1f} < 20 → {scenario_type} усилен на 10%"
                    )

                elif adx_value > 30:
                    # Сильный тренд → ОСЛАБИТЬ (mean reversion не работает)
                    confidence *= 0.70
                    logger.debug(
                        f"   📉 ADX {adx_value:.1f} > 30 → {scenario_type} ослаблен на 30%"
                    )

            # ============================================
            # 3. ОГРАНИЧИВАЕМ В ПРЕДЕЛАХ 0-100
            # ============================================
            confidence = min(max(confidence, 0.0), 100.0)

            return confidence

        except Exception as e:
            logger.error(f"❌ Ошибка применения ADX фильтра: {e}")
            return confidence  # Возвращаем без изменений при ошибке

    @staticmethod
    def get_ai_interpretation(
        macd: Dict, stoch_rsi: Dict, bollinger: Dict, atr: Dict, adx: Dict
    ) -> str:
        """
        AI интерпретация технических индикаторов

        Args:
            macd: MACD данные
            stoch_rsi: Stochastic RSI данные
            bollinger: Bollinger Bands данные
            atr: ATR данные
            adx: ADX данные

        Returns:
            Строка с AI интерпретацией
        """
        try:
            interpretation = []

            # 1. MACD
            macd_trend = macd.get("trend", "neutral")
            macd_histogram = macd.get("histogram", 0)

            if macd_trend == "bullish":
                if abs(macd_histogram) > 100:
                    interpretation.append(
                        "🟢 **MACD** показывает **сильный бычий тренд** — импульс вверх набирает силу."
                    )
                else:
                    interpretation.append(
                        "🟢 **MACD** в бычьей зоне, но импульс слабый — подтверждения недостаточно."
                    )
            elif macd_trend == "bearish":
                if abs(macd_histogram) > 100:
                    interpretation.append(
                        "🔴 **MACD** показывает **сильный медвежий тренд** — давление продавцов высокое."
                    )
                else:
                    interpretation.append(
                        "🔴 **MACD** в медвежьей зоне, но импульс слабый — возможна стабилизация."
                    )
            else:
                interpretation.append(
                    "⚪ **MACD** нейтрален — рынок в балансе, нет чёткого направления."
                )

            # 2. Stochastic RSI
            stoch_k = stoch_rsi.get("k", 50)

            if stoch_k > 80:
                interpretation.append(
                    f"🔴 **Stoch RSI** перекуплен (%K {stoch_k:.1f}) — риск коррекции вниз."
                )
            elif stoch_k < 20:
                interpretation.append(
                    f"🟢 **Stoch RSI** перепродан (%K {stoch_k:.1f}) — потенциал отскока вверх."
                )
            else:
                interpretation.append(
                    f"⚪ **Stoch RSI** нейтрален (%K {stoch_k:.1f}) — нет экстремальных значений."
                )

            # 3. Bollinger Bands
            bb_squeeze = bollinger.get("squeeze", False)
            bb_width = bollinger.get("width", 0)

            if bb_squeeze:
                interpretation.append(
                    f"⚡ **Bollinger Bands** сжимаются (width {bb_width:.1f}%) — готовится **сильное движение**!"
                )
            elif bb_width > 5:
                interpretation.append(
                    f"📊 **Bollinger Bands** расширены (width {bb_width:.1f}%) — **высокая волатильность**."
                )
            else:
                interpretation.append(
                    f"⚪ **Bollinger Bands** в нейтральной зоне (width {bb_width:.1f}%) — умеренная волатильность."
                )

            # 4. ADX (Сила тренда)
            adx_value = adx.get("adx", 0)

            if adx_value > 25:
                interpretation.append(
                    f"🔥 **ADX {adx_value:.1f}** — **сильный тренд**! Следуй за трендом."
                )
            elif adx_value > 15:
                interpretation.append(
                    f"📊 **ADX {adx_value:.1f}** — умеренный тренд, возможно боковое движение."
                )
            else:
                interpretation.append(
                    f"⚪ **ADX {adx_value:.1f}** — слабый тренд, рынок в боковике."
                )

            # 5. ATR (Волатильность)
            atr_volatility = atr.get("volatility", "medium")
            atr_percentage = atr.get("atr_percentage", 0)

            if atr_volatility == "high":
                interpretation.append(
                    f"⚡ **ATR {atr_percentage:.2f}%** — **высокая волатильность**, увеличь стоп-лоссы!"
                )
            elif atr_volatility == "low":
                interpretation.append(
                    f"😴 **ATR {atr_percentage:.2f}%** — низкая волатильность, спокойный рынок."
                )
            else:
                interpretation.append(
                    f"📊 **ATR {atr_percentage:.2f}%** — умеренная волатильность."
                )

            # 6. Рекомендация
            bullish_signals = sum(
                [macd_trend == "bullish", stoch_k < 20, adx_value > 20]
            )

            bearish_signals = sum(
                [macd_trend == "bearish", stoch_k > 80, adx_value > 20]
            )

            if bullish_signals >= 2:
                interpretation.append(
                    "\n💡 **РЕКОМЕНДАЦИЯ:** 🚀 Рассмотри **LONG** при подтверждении."
                )
            elif bearish_signals >= 2:
                interpretation.append(
                    "\n💡 **РЕКОМЕНДАЦИЯ:** 🔻 Рассмотри **SHORT** при подтверждении."
                )
            elif bb_squeeze:
                interpretation.append(
                    "\n💡 **РЕКОМЕНДАЦИЯ:** ⏸️ Жди пробоя Bollinger Bands — готовится сильное движение!"
                )
            else:
                interpretation.append(
                    "\n💡 **РЕКОМЕНДАЦИЯ:** ⏸️ Ожидание подтверждения перед открытием позиций."
                )

            return " ".join(interpretation)

        except Exception as e:
            logger.error(f"❌ Ошибка AI интерпретации индикаторов: {e}")
            return "⚠️ Ошибка генерации AI интерпретации."


# Экспорт
__all__ = ["AdvancedIndicators"]
