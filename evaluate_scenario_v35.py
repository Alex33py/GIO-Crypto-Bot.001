"""
evaluate_scenario_v35.py
Адаптер для сценариев v3.5 с hardcoded данными
"""

def evaluate_v35_conditions(conditions_dict, row):
    """
    Оценивает условия v3.5, учитывая hardcoded значения

    Args:
        conditions_dict: dict с условиями из JSON
        row: Series с реальными данными

    Returns:
        tuple: (passed, total)
    """
    passed = 0
    total = 0

    for category, conditions in conditions_dict.items():
        for condition_str in conditions:
            total += 1

            # Реальные условия (используем данные)
            if 'trend_' in condition_str and ('==' in condition_str or '!=' in condition_str):
                passed += evaluate_trend_condition(condition_str, row)
            elif 'adx_' in condition_str:
                passed += evaluate_adx_condition(condition_str, row)
            elif 'volume' in condition_str and ('>' in condition_str or '<' in condition_str):
                passed += evaluate_volume_condition(condition_str, row)
            elif 'rsi' in condition_str:
                passed += evaluate_rsi_condition(condition_str, row)
            elif 'macd' in condition_str:
                passed += evaluate_macd_condition(condition_str, row)
            elif 'price' in condition_str:
                passed += evaluate_price_condition(condition_str, row)
            elif 'ema' in condition_str:
                passed += evaluate_ema_condition(condition_str, row)

            # Hardcoded условия (всегда neutral/пропуск)
            elif any(x in condition_str for x in [
                'funding_rate', 'long_short_ratio', 'crowding_index',
                'open_interest', 'oi_', 'cvd_slope', 'cvd_confirms',
                'delta_5m_avg', 'cvd_microtrend', 'cluster.',
                'news_score', 'major_news', 'atr_pct', 'volatility_regime',
                'breakout_hh_or_ll', 'lsr_trend', 'funding_trend'
            ]):
                # Для hardcoded условий возвращаем 50% вероятность
                # (нейтральное значение, не влияет сильно на score)
                passed += 0.5

    return passed, total


def evaluate_trend_condition(condition_str, row):
    """Оценивает условия типа trend_1h == 'bullish'"""
    try:
        if "trend_1h == 'bullish'" in condition_str:
            return 1.0 if row.get('trend_1h') == 'bullish' else 0.0
        elif "trend_1h == 'bearish'" in condition_str:
            return 1.0 if row.get('trend_1h') == 'bearish' else 0.0
        elif "trend_1h != 'bearish'" in condition_str:
            return 1.0 if row.get('trend_1h') != 'bearish' else 0.0
        elif "trend_1h != 'bullish'" in condition_str:
            return 1.0 if row.get('trend_1h') != 'bullish' else 0.0

        # 4h тренды
        elif "trend_4h == 'bullish'" in condition_str:
            return 1.0 if row.get('trend_4h') == 'bullish' else 0.0
        elif "trend_4h == 'bearish'" in condition_str:
            return 1.0 if row.get('trend_4h') == 'bearish' else 0.0
        elif "trend_4h != 'bearish'" in condition_str:
            return 1.0 if row.get('trend_4h') != 'bearish' else 0.0
        elif "trend_4h != 'bullish'" in condition_str:
            return 1.0 if row.get('trend_4h') != 'bullish' else 0.0

        # 1d тренды (упрощенно, всегда true для нейтральности)
        elif 'trend_1d' in condition_str:
            return 0.7  # Нейтральное значение
    except:
        return 0.0

    return 0.0


def evaluate_adx_condition(condition_str, row):
    """Оценивает ADX условия"""
    try:
        adx_value = None
        threshold = None

        if 'adx_1h' in condition_str:
            adx_value = row.get('adx_1h', 0)
            # Extract threshold: "adx_1h > 20" -> 20
            if '>' in condition_str:
                threshold = float(condition_str.split('>')[1].strip())
                return 1.0 if adx_value > threshold else 0.0
            elif '<' in condition_str:
                threshold = float(condition_str.split('<')[1].strip())
                return 1.0 if adx_value < threshold else 0.0

        elif 'adx_4h' in condition_str:
            adx_value = row.get('adx_4h', 0)
            if '>' in condition_str:
                threshold = float(condition_str.split('>')[1].strip())
                return 1.0 if adx_value > threshold else 0.0
            elif '<' in condition_str:
                threshold = float(condition_str.split('<')[1].strip())
                return 1.0 if adx_value < threshold else 0.0

        elif 'adx_slope' in condition_str:
            # Для adx_slope возвращаем нейтральное значение
            return 0.5
    except:
        return 0.0

    return 0.0


def evaluate_volume_condition(condition_str, row):
    """Оценивает Volume условия"""
    try:
        volume = row.get('volume', 0)
        volume_sma = row.get('volume_sma', volume)

        if 'volume > volume_ma20' in condition_str or 'volume > volume_sma' in condition_str:
            # Extract multiplier if present
            if '*' in condition_str:
                multiplier = float(condition_str.split('*')[1].strip())
                return 1.0 if volume > volume_sma * multiplier else 0.0
            else:
                return 1.0 if volume > volume_sma else 0.0

        elif 'volume < volume_ma20' in condition_str or 'volume < volume_sma' in condition_str:
            return 1.0 if volume < volume_sma else 0.0

        elif 'volume_delta_1h >' in condition_str:
            # Для volume_delta возвращаем нейтральное значение
            return 0.5
        elif 'volume_delta_1h <' in condition_str:
            return 0.5
    except:
        return 0.0

    return 0.0


def evaluate_rsi_condition(condition_str, row):
    """Оценивает RSI условия"""
    try:
        rsi = row.get('rsi', 50)

        if 'between' in condition_str:
            # "rsi_1h between 40 and 70"
            parts = condition_str.split('between')[1].split('and')
            lower = float(parts[0].strip())
            upper = float(parts[1].strip())
            return 1.0 if lower <= rsi <= upper else 0.0
        elif '>' in condition_str:
            threshold = float(condition_str.split('>')[1].strip())
            return 1.0 if rsi > threshold else 0.0
        elif '<' in condition_str:
            threshold = float(condition_str.split('<')[1].strip())
            return 1.0 if rsi < threshold else 0.0
    except:
        return 0.0

    return 0.0


def evaluate_macd_condition(condition_str, row):
    """Оценивает MACD условия"""
    try:
        macd_hist = row.get('macd_hist', 0)

        if 'macd_hist_1h > 0' in condition_str:
            return 1.0 if macd_hist > 0 else 0.0
        elif 'macd_hist_1h < 0' in condition_str:
            return 1.0 if macd_hist < 0 else 0.0
    except:
        return 0.0

    return 0.0


def evaluate_price_condition(condition_str, row):
    """Оценивает Price условия"""
    try:
        price = row.get('close', 0)

        if 'price > ema_20_1h' in condition_str:
            ema20 = row.get('ema_20', price)
            return 1.0 if price > ema20 else 0.0
        elif 'price < ema_20_1h' in condition_str:
            ema20 = row.get('ema_20', price)
            return 1.0 if price < ema20 else 0.0
        elif 'abs(price - poc)' in condition_str:
            # Упрощенно возвращаем нейтральное значение
            return 0.7
    except:
        return 0.0

    return 0.0


def evaluate_ema_condition(condition_str, row):
    """Оценивает EMA условия"""
    # В текущих данных нет прямого EMA, возвращаем нейтральное значение
    return 0.5
