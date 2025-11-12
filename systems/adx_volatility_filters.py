# analytics/adx_volatility_filters.py

"""
Фильтры для улучшения качества сигналов:
1. ADX фильтр - отсеивает шумовые тренды
2. ATR динамический SL/TP - адаптируется к волатильности
3. Volatility фильтр - ловит только когда рынок движется
"""

import numpy as np


def get_adx_confidence(adx_value):
    """
    Преобразовать ADX в коэффициент уверенности (0.0 - 1.2)

    ADX интерпретация:
    - 0-25: Нет тренда (ШУМОВАЯ ЗОНА)
    - 25-40: Умеренный тренд (OK)
    - 40-50: Сильный тренд (GOOD)
    - 50+: Очень сильный тренд (BEST)
    """
    if adx_value < 25:
        return 0.0  # Нет тренда - нет сделок
    elif adx_value < 30:
        return 0.5  # Слабый тренд - маленький коэффициент
    elif adx_value < 40:
        return 0.8  # Хороший тренд
    elif adx_value < 50:
        return 1.0  # Сильный тренд
    else:
        return 1.2  # Очень сильный - бонус +20%


def calculate_atr_based_levels(close_price, atr_value, direction='LONG',
                               atr_mult_sl=1.5, atr_mult_tp=3.0):
    """
    Рассчитать Stop Loss и Take Profit на основе ATR

    Это НАМНОГО лучше чем просто процент!

    Args:
        close_price: текущая цена
        atr_value: Average True Range (14 периодов)
        direction: 'LONG' или 'SHORT'
        atr_mult_sl: множитель для SL (1.5 = 1.5 * ATR)
        atr_mult_tp: множитель для TP (3.0 = 3.0 * ATR)

    Returns:
        dict с ценами SL/TP и процентами
    """

    if atr_value == 0 or atr_value is None:
        return None

    if direction == 'LONG':
        # Покупаем выше, стоп ниже
        sl_price = close_price - (atr_value * atr_mult_sl)
        tp_price = close_price + (atr_value * atr_mult_tp)

    elif direction == 'SHORT':
        # Продаем ниже, стоп выше
        sl_price = close_price + (atr_value * atr_mult_sl)
        tp_price = close_price - (atr_value * atr_mult_tp)

    else:
        return None

    # Считаем проценты для логирования
    sl_percent = abs((close_price - sl_price) / close_price) * 100
    tp_percent = abs((tp_price - close_price) / close_price) * 100

    risk_reward = tp_percent / sl_percent if sl_percent > 0 else 0

    return {
        'sl_price': round(sl_price, 2),
        'tp_price': round(tp_price, 2),
        'sl_percent': round(sl_percent, 2),
        'tp_percent': round(tp_percent, 2),
        'risk_reward_ratio': round(risk_reward, 2)
    }


def check_volatility_regime(atr_current, atr_sma_20):
    """
    Проверить режим волатильности

    Сравнивает текущий ATR со средним ATR за 20 свечей

    Returns:
        tuple: (regime_type, ratio)
        - 'low': Волатильность низкая - ИЗБЕГАТЬ сделок
        - 'normal': Волатильность нормальная - OK
        - 'high': Волатильность высокая - ЛУЧШЕ всего
    """

    if atr_sma_20 == 0 or atr_sma_20 is None:
        return 'normal', 1.0

    ratio = atr_current / atr_sma_20

    if ratio < 0.8:
        return 'low', ratio
    elif ratio > 1.2:
        return 'high', ratio
    else:
        return 'normal', ratio


def validate_signal_with_filters(market_data, scenario_score,
                                 min_adx=30, min_scenario=0.55):
    """
    Полная валидация сигнала со всеми фильтрами

    Args:
        market_data: dict с OHLCV + индикаторами
        scenario_score: скор сценария (0.0-1.0)
        min_adx: минимальный ADX для входа (по умолчанию 30)
        min_scenario: минимальный скор сценария (по умолчанию 0.55)

    Returns:
        dict с результатом валидации или None
    """

    # Проверка 1: ADX
    adx = market_data.get('adx_14', 0)
    if adx < min_adx:
        return {
            'valid': False,
            'reason': f'ADX too weak: {adx:.1f} < {min_adx}'
        }

    # Проверка 2: Сценарий
    if scenario_score < min_scenario:
        return {
            'valid': False,
            'reason': f'Scenario score too low: {scenario_score:.2f} < {min_scenario}'
        }

    # Проверка 3: Волатильность
    atr = market_data.get('atr_14', 0)
    atr_sma = market_data.get('atr_sma_20', atr)

    vol_regime, vol_ratio = check_volatility_regime(atr, atr_sma)

    if vol_regime == 'low':
        return {
            'valid': False,
            'reason': f'Volatility too low: {vol_ratio:.2f} < 0.8'
        }

    # ВСЕ ФИЛЬТРЫ ПРОЙДЕНЫ! ✅
    adx_confidence = get_adx_confidence(adx)
    final_confidence = scenario_score * (0.5 + adx_confidence * 0.5)

    return {
        'valid': True,
        'confidence': final_confidence,
        'adx_confidence': adx_confidence,
        'vol_regime': vol_regime,
        'vol_ratio': vol_ratio,
        'atr': atr,
        'adx': adx
    }


# Пример использования:
if __name__ == "__main__":
    # Тестовые данные
    test_data = {
        'close': 104701,
        'atr_14': 1200,
        'atr_sma_20': 1100,
        'adx_14': 36
    }

    # Проверить LONG сигнал
    levels = calculate_atr_based_levels(
        close_price=test_data['close'],
        atr_value=test_data['atr_14'],
        direction='LONG'
    )

    print("SL/TP уровни для LONG:")
    print(f"  SL: {levels['sl_price']} ({levels['sl_percent']}%)")
    print(f"  TP: {levels['tp_price']} ({levels['tp_percent']}%)")
    print(f"  R/R: 1:{levels['risk_reward_ratio']}")

    # Проверить волатильность
    vol_regime, vol_ratio = check_volatility_regime(
        test_data['atr_14'],
        test_data['atr_sma_20']
    )
    print(f"\nВолатильность: {vol_regime} (ratio={vol_ratio:.2f})")

    # Полная валидация
    validation = validate_signal_with_filters(
        test_data,
        scenario_score=0.65
    )
    print(f"\nВалидация: {validation}")
