# -*- coding: utf-8 -*-
"""
Детектор рыночного режима
Предотвращает curve fitting через адаптивные параметры
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import ta

class MarketRegimeDetector:
    """Определение рыночного режима (High Vol, Ranging, Strong Trend, Choppy)"""

    def __init__(self):
        self.regime_history = []

    def calculate_features(self, df):
        """Вычислить features для определения режима"""

        # ATR percentage (волатильность)
        atr_ind = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'])
        df['atr'] = atr_ind.average_true_range()
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        df['atr_pct_ma_20'] = df['atr_pct'].rolling(20).mean()

        # ADX (тренд)
        adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
        df['adx'] = adx_ind.adx()
        df['adx_ma_20'] = df['adx'].rolling(20).mean()

        # EMA для определения направления
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()

        # RSI для определения перекупленности/перепроданности
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()

        return df

    def detect_regime(self, df):
        """
        Определить текущий рыночный режим
        ОБНОВЛЕНО: смягчённые пороги для реального рынка
        """

        if len(df) < 20:
            return 'UNKNOWN'

        row = df.iloc[-1]

        atr_pct = row['atr_pct_ma_20']
        adx_ma = row['adx_ma_20']
        current_adx = row['adx']

        # LOGIC
        if pd.isna(atr_pct) or pd.isna(adx_ma):
            return 'UNKNOWN'

        # HIGH VOLATILITY (опасно)
        if atr_pct > 2.5:  # Было 2.0, стало 2.5 (меньше исключений)
            return 'HIGH_VOL'

        # RANGING (скучно)
        if atr_pct < 0.5 and adx_ma < 18:  # Было < 20, стало < 18
            return 'RANGING'

        # STRONG TREND (идеально!) - СМЯГЧЕНО ⭐
        if adx_ma > 22 and current_adx > 20:
            return 'STRONG_TREND'

        # MEDIUM TREND (новый режим!) ⭐
        if adx_ma > 18 and current_adx > 16:
            return 'MEDIUM_TREND'

        # CHOPPY (неопределённо)
        return 'CHOPPY'

    def detect(self, metrics: dict) -> str:
        """
        Wrapper для совместимости с unified_scenario_matcher
        Принимает dict metrics вместо DataFrame

        Args:
            metrics: Словарь с рыночными данными

        Returns:
            Строка с режимом рынка (STRONG_TREND, RANGING, и т.д.)
        """
        try:
            from config.settings import logger

            # Проверяем наличие необходимых данных
            if 'candles' not in metrics or len(metrics.get('candles', [])) < 20:
                logger.warning(f"⚠️ Недостаточно данных для detect_regime: {len(metrics.get('candles', []))} свечей")
                return 'UNKNOWN'

            # Создаём DataFrame из свечей
            candles_data = metrics['candles']
            df = pd.DataFrame(candles_data)

            # Убеждаемся что есть нужные колонки
            required_cols = ['high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"⚠️ Отсутствуют необходимые колонки: {required_cols}")
                return 'UNKNOWN'

            # Рассчитываем features
            df = self.calculate_features(df)

            # Определяем режим
            regime = self.detect_regime(df)

            logger.debug(f"🔍 Режим рынка определён: {regime}")
            return regime

        except Exception as e:
            from config.settings import logger
            logger.error(f"❌ Ошибка detect(): {e}", exc_info=True)
            return 'UNKNOWN'


    def get_adaptive_config(self, regime):
        """
        Получить адаптивный конфиг в зависимости от режима
        """

        configs = {
            'STRONG_TREND': {
                'min_adx': 22,
                'tp_multiplier': 2.5,
                'sl_multiplier': 1.0,
                'volume_requirement': 0.8,
                'trade': True,
                'description': '✅ STRONG TREND - идеально для торговли'
            },

            'MEDIUM_TREND': {
                'min_adx': 18,
                'tp_multiplier': 2.0,
                'sl_multiplier': 1.0,
                'volume_requirement': 0.9,
                'trade': True,
                'description': '✅ MEDIUM TREND - торгуем осторожно'
            },

            'HIGH_VOL': {
                'min_adx': 40,              # Жестче - нужен очень сильный сигнал
                'tp_multiplier': 1.2,       # Меньше - быстро выходим
                'sl_multiplier': 1.5,       # Шире - больше места
                'volume_requirement': 1.2,
                'trade': True,
                'description': '⚠️ HIGH VOL - торгуем осторожно'
            },

            'RANGING': {
                'min_adx': 100,             # Невозможно - не торгуем
                'tp_multiplier': 1.0,
                'sl_multiplier': 1.0,
                'volume_requirement': 100,
                'trade': False,
                'description': '❌ RANGING - избегаем'
            },

            'CHOPPY': {
                'min_adx': 100,             # Невозможно - не торгуем
                'tp_multiplier': 1.0,
                'sl_multiplier': 1.0,
                'volume_requirement': 100,
                'trade': False,
                'description': '❌ CHOPPY - избегаем'
            },

            'UNKNOWN': {
                'min_adx': 100,
                'tp_multiplier': 1.0,
                'sl_multiplier': 1.0,
                'volume_requirement': 100,
                'trade': False,
                'description': '❓ UNKNOWN - избегаем'
            }
        }

        return configs.get(regime, configs['UNKNOWN'])

    def get_regime_stats(self, regimes_history):
        """Статистика по режимам за последнее время"""

        if not regimes_history:
            return {}

        df = pd.DataFrame(regimes_history)
        return df['regime'].value_counts().to_dict()

def main():
    """Test"""
    df = pd.read_csv("data/ml_training/BTCUSDT_5min_180d.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    detector = MarketRegimeDetector()
    df = detector.calculate_features(df)

    # Последние 100 свечей
    for i in range(-100, 0):
        regime = detector.detect_regime(df.iloc[:len(df)+i])
        config = detector.get_adaptive_config(regime)

        if i % 20 == 0:
            print(f"{df.iloc[len(df)+i]['timestamp']}: {regime} - {config['description']}")

if __name__ == "__main__":
    main()
