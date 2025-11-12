import sys
import asyncio
sys.path.append(r"D:\GIO.BOT.002")

from analytics.signal_generation_service import SignalGenerationService


class MockBot:
    mtf_cache = {
        symbol: {
            "1h": {
                "adx": 25,
                "rsi": 55,
                "ema_20": 30000,
                "volume": 1000,
                "trend": "up",
                "candles": [
                    {"open": 29900, "high": 30100, "low": 29800, "close": 30000, "volume": 1000, "timestamp": "2025-11-12T10:00:00Z"},
                    {"open": 30000, "high": 30200, "low": 29950, "close": 30150, "volume": 1100, "timestamp": "2025-11-12T11:00:00Z"},
                ]
            },
            "4h": {
                "adx": 30,
                "rsi": 60,
                "ema_20": 29500,
                "volume": 1500,
                "trend": "up",
                "candles": [
                    {"open": 29200, "high": 30000, "low": 29100, "close": 29800, "volume": 4000, "timestamp": "2025-11-12T08:00:00Z"},
                ]
            },
            "1d": {
                "adx": 20,
                "rsi": 65,
                "ema_20": 29000,
                "volume": 2000,
                "trend": "up",
                "candles": [
                    {"open": 28000, "high": 30000, "low": 27000, "close": 29500, "volume": 15000, "timestamp": "2025-11-11T00:00:00Z"},
                ]
            }
        }
        for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT"]
    }


class MockScenarioMatcher:
    def match_scenario(self, **kwargs):
        return {
            "matched": True,
            "direction": "LONG",
            "stop_loss": 29000,
            "tp1": 31000,
            "tp2": 32000,
            "tp3": 33000,
            "scenario_id": "TEST001",
            "confidence": "high"
        }

class MockSignalRecorder:
    def recordsignal(self, direction, entryprice, sl, tp1, tp2, tp3, scenarioid, status, qualityscore, riskreward):
        print(f"Recorded signal: {direction=}, {entryprice=}, {sl=}, {tp1=}, {tp2=}, {tp3=}, {scenarioid=}, {status=}, {qualityscore=}, {riskreward=}")

async def run_test():
    mock_bot = MockBot()
    mock_scenario_matcher = MockScenarioMatcher()
    mock_signal_recorder = MockSignalRecorder()

    svc = SignalGenerationService(mock_bot, mock_scenario_matcher, None, None, None, mock_signal_recorder)

    # Переопределяем метод получения цены, чтобы всегда возвращать фиктивное значение
    async def mock_get_current_price(symbol, max_cache_age_seconds=60):
        return 30000.0
    svc._get_current_price = mock_get_current_price

    results = await svc.generate_signals_for_all_symbols(manual_trigger=True)
    print("Test results:", results)

asyncio.run(run_test())
