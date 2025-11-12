# -*- coding: utf-8 -*-
"""
Volume Profile - Упрощённая обёртка для бектеста
Использует только OHLCV свечи (без реального orderbook)
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


def calculate_candle_volume_profile(ohlcv_data, bins=50):
    """
    Простой расчёт Volume Profile из OHLCV свечей
    Для бектеста (без реального orderbook)

    Args:
        ohlcv_data: Список словарей с ключами: open, high, low, close, volume
        bins: Количество ценовых бинов

    Returns:
        Dict с POC, VAH, VAL
    """
    try:
        if not ohlcv_data or len(ohlcv_data) < 10:
            return _empty_vp()

        df = pd.DataFrame(ohlcv_data)
        price_min = df['low'].min()
        price_max = df['high'].max()

        if price_min == price_max:
            return _empty_vp()

        # Ценовые бины
        price_bins = np.linspace(price_min, price_max, bins + 1)
        volume_by_price = np.zeros(bins)

        # Распределяем объём по ценам
        for _, candle in df.iterrows():
            candle_low = candle['low']
            candle_high = candle['high']
            candle_volume = candle['volume']

            bin_indices = np.where(
                (price_bins[:-1] <= candle_high) &
                (price_bins[1:] >= candle_low)
            )[0]

            if len(bin_indices) > 0:
                volume_per_bin = candle_volume / len(bin_indices)
                volume_by_price[bin_indices] += volume_per_bin

        # POC
        poc_bin_idx = np.argmax(volume_by_price)
        poc_price = (price_bins[poc_bin_idx] + price_bins[poc_bin_idx + 1]) / 2

        # Value Area (70%)
        total_volume = volume_by_price.sum()
        target_volume = total_volume * 0.70

        value_area_indices = [poc_bin_idx]
        accumulated_volume = volume_by_price[poc_bin_idx]

        lower_idx = poc_bin_idx - 1
        upper_idx = poc_bin_idx + 1

        while accumulated_volume < target_volume:
            lower_vol = volume_by_price[lower_idx] if lower_idx >= 0 else 0
            upper_vol = volume_by_price[upper_idx] if upper_idx < bins else 0

            if lower_vol == 0 and upper_vol == 0:
                break

            if upper_vol >= lower_vol and upper_idx < bins:
                value_area_indices.append(upper_idx)
                accumulated_volume += upper_vol
                upper_idx += 1
            elif lower_idx >= 0:
                value_area_indices.append(lower_idx)
                accumulated_volume += lower_vol
                lower_idx -= 1
            else:
                break

        vah_idx = max(value_area_indices)
        val_idx = min(value_area_indices)

        vah_price = price_bins[vah_idx + 1]
        val_price = price_bins[val_idx]

        current_price = df.iloc[-1]['close']
        vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()

        distance_from_poc_pct = abs(current_price - poc_price) / poc_price * 100

        return {
            "poc": round(poc_price, 2),
            "vah": round(vah_price, 2),
            "val": round(val_price, 2),
            "vwap": round(vwap, 2),
            "current_price": round(current_price, 2),
            "distance_from_poc_pct": round(distance_from_poc_pct, 2),
            "confidence_modifier": 1.0
        }
    except Exception as e:
        print(f"⚠️ VP error: {e}")
        return _empty_vp()


def _empty_vp():
    """Возвращает пустой профиль при ошибке"""
    return {
        "poc": 0.0,
        "vah": 0.0,
        "val": 0.0,
        "vwap": 0.0,
        "current_price": 0.0,
        "distance_from_poc_pct": 0.0,
        "confidence_modifier": 1.0
    }


class EnhancedVolumeProfileCalculator:
    """Volume Profile Calculator для бота"""

    def __init__(self):
        pass

    async def calculate_profile(self, symbol: str, klines: list) -> dict:
        """Рассчитать Volume Profile"""
        return calculate_candle_volume_profile(klines)

    def get_trading_signals(self, profile: dict) -> dict:
        """Получить торговые сигналы"""
        return {"strength": 0.5, "direction": "neutral"}


# Экспорт

    async def calculate_from_orderbook(self, symbol: str, orderbook: dict, 
                                      timeframe: str = "1h") -> dict:
        """
        Рассчитать Volume Profile из orderbook данных
        
        Args:
            symbol: торговая пара
            orderbook: данные orderbook {'bids': [...], 'asks': [...]}
            timeframe: таймфрейм (по умолчанию 1h)
            
        Returns:
            dict с POC, VAH, VAL и другими метриками
        """
        try:
            # Извлекаем bids и asks
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                return self._default_vp_result()
            
            # Рассчитываем уровни цен и объёмы
            all_levels = []
            
            # Обрабатываем bids (покупки)
            for price, volume in bids:
                all_levels.append({
                    'price': float(price),
                    'volume': float(volume),
                    'side': 'buy'
                })
            
            # Обрабатываем asks (продажи)
            for price, volume in asks:
                all_levels.append({
                    'price': float(price),
                    'volume': float(volume),
                    'side': 'sell'
                })
            
            # Сортируем по цене
            all_levels.sort(key=lambda x: x['price'])
            
            if not all_levels:
                return self._default_vp_result()
            
            # Находим POC (точка с максимальным объёмом)
            max_volume = 0
            poc_price = all_levels[0]['price']
            
            for level in all_levels:
                if level['volume'] > max_volume:
                    max_volume = level['volume']
                    poc_price = level['price']
            
            # Рассчитываем общий объём
            total_volume = sum(l['volume'] for l in all_levels)
            
            # Находим 70% зону (Value Area)
            target_volume = total_volume * 0.7
            cumulative_volume = 0
            value_area = []
            
            # Начинаем от POC и расширяемся
            sorted_levels = sorted(all_levels, 
                                 key=lambda x: abs(x['price'] - poc_price))
            
            for level in sorted_levels:
                cumulative_volume += level['volume']
                value_area.append(level)
                if cumulative_volume >= target_volume:
                    break
            
            # VAH и VAL
            prices = [l['price'] for l in value_area]
            vah = max(prices) if prices else poc_price
            val = min(prices) if prices else poc_price
            
            return {
                'poc': poc_price,
                'vah': vah,
                'val': val,
                'total_volume': total_volume,
                'value_area_volume': cumulative_volume,
                'levels': len(all_levels),
                'timestamp': orderbook.get('timestamp', None)
            }
            
        except Exception as e:
            self.logger.error(f"❌ calculate_from_orderbook error: {e}")
            return self._default_vp_result()
    
    def _default_vp_result(self) -> dict:
        """Возвращает дефолтный результат Volume Profile"""
        return {
            'poc': 0.0,
            'vah': 0.0,
            'val': 0.0,
            'total_volume': 0.0,
            'value_area_volume': 0.0,
            'levels': 0,
            'timestamp': None
        }

__all__ = ["calculate_candle_volume_profile", "EnhancedVolumeProfileCalculator"]
