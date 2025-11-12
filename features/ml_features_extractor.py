# -*- coding: utf-8 -*-
"""
ML Features Extractor для GIO Bot
Использует существующие данные из вашего проекта
"""

import sys
import os
import pandas as pd
import numpy as np
import ta

class MLFeaturesExtractor:
    """Извлечение ML features из market data"""

    def __init__(self):
        self.feature_names = []

    def calculate_all_features(self, df):
        """
        Вычислить все ML features на историческом датасете

        Args:
            df: DataFrame с колонками [timestamp, open, high, low, close, volume]

        Returns:
            DataFrame с features
        """
        print("🔧 Вычисление ML features...")

        # 1. Technical Indicators (ваши существующие)
        df = self._add_technical_features(df)

        # 2. Volume Features
        df = self._add_volume_features(df)

        # 3. Volatility Features
        df = self._add_volatility_features(df)

        # 4. Price Action Features
        df = self._add_price_action_features(df)

        # 5. Temporal Features
        df = self._add_temporal_features(df)

        print(f"✅ Вычислено {len(self.feature_names)} features")

        return df

    def _add_technical_features(self, df):
        """Технические индикаторы"""
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)

        # ADX - ваш основной индикатор!
        adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
        df['adx'] = adx_ind.adx()
        df['adx_strong_trend'] = (df['adx'] > 30).astype(int)

        # MACD
        macd_ind = ta.trend.MACD(df['close'])
        df['macd'] = macd_ind.macd()
        df['macd_signal'] = macd_ind.macd_signal()
        df['macd_diff'] = macd_ind.macd_diff()
        df['macd_bullish'] = (df['macd_diff'] > 0).astype(int)

        # EMA
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        df['ema_200'] = df['close'].ewm(span=200).mean()
        df['price_above_ema20'] = (df['close'] > df['ema_20']).astype(int)
        df['price_above_ema50'] = (df['close'] > df['ema_50']).astype(int)

        # Bollinger Bands
        bb_ind = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb_ind.bollinger_hband()
        df['bb_lower'] = bb_ind.bollinger_lband()
        df['bb_middle'] = bb_ind.bollinger_mavg()
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        self.feature_names.extend([
            'rsi', 'rsi_overbought', 'rsi_oversold',
            'adx', 'adx_strong_trend',
            'macd', 'macd_signal', 'macd_diff', 'macd_bullish',
            'price_above_ema20', 'price_above_ema50',
            'bb_position'
        ])

        return df

    def _add_volume_features(self, df):
        """Volume features - ваш CVD концепт"""
        # Volume SMA
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['volume_above_avg'] = (df['volume_ratio'] > 1.2).astype(int)

        # Buy/Sell pressure (approximation)
        df['buy_pressure'] = ((df['close'] - df['low']) / (df['high'] - df['low'])).fillna(0.5)
        df['sell_pressure'] = 1 - df['buy_pressure']

        # CVD approximation (ваша идея!)
        df['cvd_approx'] = (df['buy_pressure'] * df['volume']).cumsum()
        df['cvd_ma_20'] = df['cvd_approx'].rolling(20).mean()
        df['cvd_direction'] = (df['cvd_approx'] > df['cvd_ma_20']).astype(int)

        self.feature_names.extend([
            'volume_ratio', 'volume_above_avg',
            'buy_pressure', 'sell_pressure',
            'cvd_direction'
        ])

        return df

    def _add_volatility_features(self, df):
        """Volatility features - ваш Vol Filter!"""
        # ATR
        atr_ind = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'])
        df['atr'] = atr_ind.average_true_range()
        df['atr_sma_20'] = df['atr'].rolling(20).mean()
        df['atr_ratio'] = df['atr'] / df['atr_sma_20']
        df['high_volatility'] = (df['atr_ratio'] > 1.2).astype(int)
        df['low_volatility'] = (df['atr_ratio'] < 0.8).astype(int)

        # ATR percentage
        df['atr_pct'] = (df['atr'] / df['close']) * 100

        self.feature_names.extend([
            'atr_ratio', 'high_volatility', 'low_volatility', 'atr_pct'
        ])

        return df

    def _add_price_action_features(self, df):
        """Price action patterns"""
        # Returns
        df['return_1'] = df['close'].pct_change(1)
        df['return_5'] = df['close'].pct_change(5)
        df['return_20'] = df['close'].pct_change(20)

        # Price position in range
        df['high_20'] = df['high'].rolling(20).max()
        df['low_20'] = df['low'].rolling(20).min()
        df['price_position'] = (df['close'] - df['low_20']) / (df['high_20'] - df['low_20'])

        # Candle patterns
        df['candle_body'] = abs(df['close'] - df['open'])
        df['candle_upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['candle_lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        df['bullish_candle'] = (df['close'] > df['open']).astype(int)

        self.feature_names.extend([
            'return_1', 'return_5', 'return_20',
            'price_position',
            'bullish_candle'
        ])

        return df

    def _add_temporal_features(self, df):
        """Time-based features"""
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

        # Trading sessions
        df['session_ny'] = ((df['hour'] >= 14) & (df['hour'] < 21)).astype(int)
        df['session_london'] = ((df['hour'] >= 8) & (df['hour'] < 16)).astype(int)
        df['session_tokyo'] = ((df['hour'] >= 0) & (df['hour'] < 9)).astype(int)

        self.feature_names.extend([
            'hour', 'day_of_week', 'is_weekend',
            'session_ny', 'session_london', 'session_tokyo'
        ])

        return df

    def get_feature_names(self):
        """Список всех feature names"""
        return self.feature_names

def main():
    """Test feature extraction"""
    # Загрузить данные
    df = pd.read_csv("data/ml_training/BTCUSDT_5min_180d.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Extract features
    extractor = MLFeaturesExtractor()
    df_features = extractor.calculate_all_features(df)

    # Save
    os.makedirs("data/ml_training/features", exist_ok=True)
    df_features.to_csv("data/ml_training/features/BTCUSDT_features.csv", index=False)

    print(f"\n✅ Features saved: {len(df_features)} rows, {len(extractor.get_feature_names())} features")
    print(f"\nFeature names: {extractor.get_feature_names()[:10]}...")

if __name__ == "__main__":
    main()
