"""
🎯 CVD CALCULATOR MODULE - GIO BOT
Cumulative Volume Delta из OHLCV данных
"""

import pandas as pd
import numpy as np
from typing import Dict


class CVDCalculator:
    """Рассчитывает CVD и связанные метрики"""

    def __init__(self, window: int = 20):
        """
        Args:
            window: окно для расчёта SMA трендов CVD
        """
        self.window = window

    def calculate_cvd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать CVD для всего DataFrame

        Args:
            df: DataFrame с колонками [open, high, low, close, volume]

        Returns:
            df с добавленными колонками [volume_delta, cvd, cvd_trend, cvd_slope]
        """
        df = df.copy()

        df['direction'] = np.where(df['close'] > df['open'], 1, -1)

        df['range'] = df['high'] - df['low']
        df['range'] = np.where(df['range'] == 0, 1, df['range'])

        df['buy_vol'] = df['volume'] * (df['close'] - df['low']) / df['range']
        df['sell_vol'] = df['volume'] - df['buy_vol']

        df['volume_delta'] = df['buy_vol'] - df['sell_vol']
        df['cvd'] = df['volume_delta'].cumsum()

        df['cvd_sma'] = df['cvd'].rolling(window=self.window, min_periods=1).mean()
        df['cvd_slope'] = df['cvd'].diff().fillna(0)
        df['cvd_trend'] = np.where(df['cvd'] > df['cvd_sma'], 'bullish', 'bearish')

        cvd_max = df['cvd'].rolling(window=50, min_periods=1).max()
        cvd_min = df['cvd'].rolling(window=50, min_periods=1).min()
        cvd_range = cvd_max - cvd_min
        cvd_range = np.where(cvd_range == 0, 1, cvd_range)
        df['cvd_normalized'] = (df['cvd'] - cvd_min) / cvd_range

        df['price_direction'] = np.where(df['close'] > df['close'].shift(1), 1, -1)
        df['cvd_confirms'] = (df['price_direction'] == np.sign(df['cvd_slope'])).astype(int)

        df = df.drop(columns=['direction', 'range', 'buy_vol', 'sell_vol', 'price_direction', 'cvd_sma'])

        return df

    def get_cvd_metrics(self, df: pd.DataFrame, idx: int) -> Dict:
        """
        Получить CVD метрики для конкретной строки

        Args:
            df: DataFrame с CVD колонками
            idx: индекс строки

        Returns:
            Dict с метриками: cvd_value, cvd_trend, cvd_slope, cvd_confirms
        """
        if idx < 0 or idx >= len(df):
            return {
                'cvd_value': 0.0,
                'cvd_trend': 'neutral',
                'cvd_slope': 0.0,
                'cvd_confirms': False,
                'cvd_normalized': 0.5
            }

        row = df.iloc[idx]

        return {
            'cvd_value': float(row['cvd']) if pd.notna(row['cvd']) else 0.0,
            'cvd_trend': str(row['cvd_trend']) if pd.notna(row['cvd_trend']) else 'neutral',
            'cvd_slope': float(row['cvd_slope']) if pd.notna(row['cvd_slope']) else 0.0,
            'cvd_confirms': bool(row['cvd_confirms']) if pd.notna(row['cvd_confirms']) else False,
            'cvd_normalized': float(row['cvd_normalized']) if pd.notna(row['cvd_normalized']) else 0.5
        }
