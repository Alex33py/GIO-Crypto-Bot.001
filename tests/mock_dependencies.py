"""
Mock Dependencies для бектестинга
Заглушки для config.settings, config.constants, utils.*
"""

import os


# ==================== CONFIG.SETTINGS ====================
class MockLogger:
    """Mock logger для бектеста"""
    @staticmethod
    def info(msg):
        print(f"ℹ️  {msg}")

    @staticmethod
    def error(msg):
        print(f"❌ {msg}")

    @staticmethod
    def debug(msg):
        # Отключаем debug в бектесте
        pass

    @staticmethod
    def warning(msg):
        print(f"⚠️  {msg}")


# Mock settings
logger = MockLogger()
SCENARIOS_DIR = "data/scenarios"
DATA_DIR = "data"
VOLUME_PROFILE_LEVELS_COUNT = 50
INSTITUTIONAL_VOLUME_THRESHOLD = 1000000
ICEBERG_DETECTION_THRESHOLD = 5


# ==================== CONFIG.CONSTANTS ====================
class TrendDirectionEnum:
    """Mock trend direction enum"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class VetoReasonEnum:
    """Mock veto reason enum"""
    NONE = None
    HIGH_VOLATILITY = "high_volatility"
    LOW_LIQUIDITY = "low_liquidity"
    NEWS_IMPACT = "news_impact"


# ==================== UTILS.HELPERS ====================
def current_epoch_ms():
    """Текущее время в миллисекундах"""
    import time
    return int(time.time() * 1000)


def safe_float(value, default=0.0):
    """Безопасное преобразование в float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Безопасное преобразование в int"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


# ==================== UTILS.VALIDATORS ====================
def validate_trade_data(trade_data):
    """Валидация trade data (всегда True для бектеста)"""
    return True


def validate_orderbook_data(orderbook_data):
    """Валидация orderbook data (всегда True для бектеста)"""
    return True


# ==================== EXPORT ====================
__all__ = [
    'logger',
    'SCENARIOS_DIR',
    'DATA_DIR',
    'VOLUME_PROFILE_LEVELS_COUNT',
    'INSTITUTIONAL_VOLUME_THRESHOLD',
    'ICEBERG_DETECTION_THRESHOLD',
    'TrendDirectionEnum',
    'VetoReasonEnum',
    'current_epoch_ms',
    'safe_float',
    'safe_int',
    'validate_trade_data',
    'validate_orderbook_data'
]
