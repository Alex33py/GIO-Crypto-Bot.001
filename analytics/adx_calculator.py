"""ADX Calculator - упрощённая версия для бектеста"""

def calculate_adx(high, low, close, period=14):
    """Простой расчёт ADX"""
    try:
        import pandas as pd

        high_series = pd.Series(high)
        low_series = pd.Series(low)
        close_series = pd.Series(close)

        # Упрощённый расчёт
        high_diff = high_series.diff()
        low_diff = -low_series.diff()

        plus_dm = high_diff.copy()
        plus_dm[(high_diff < 0) | (high_diff <= low_diff)] = 0

        minus_dm = low_diff.copy()
        minus_dm[(low_diff < 0) | (low_diff <= high_diff)] = 0

        tr1 = high_series - low_series
        tr2 = abs(high_series - close_series.shift())
        tr3 = abs(low_series - close_series.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        current_adx = adx.iloc[-1]
        return float(current_adx) if not pd.isna(current_adx) else 25.0
    except:
        return 25.0  # Значение по умолчанию
