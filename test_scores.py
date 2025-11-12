import json
from tests.market_data_simulator import MarketDataSimulator
from core.scenario_matcher import UnifiedScenarioMatcher
import pandas as pd

# Создаём тестовые данные
simulator = MarketDataSimulator()
matcher = UnifiedScenarioMatcher()

# Загружаем сценарии
data = json.load(open("data/scenarios/gio_scenarios_100_with_features_v3.json"))
scenarios = data["scenarios"]

# Создаём тестовый DataFrame
test_data = pd.DataFrame(
    {
        "timestamp": pd.date_range("2024-01-01", periods=200, freq="1H"),
        "open": [100] * 200,
        "high": [101] * 200,
        "low": [99] * 200,
        "close": [100.5] * 200,
        "volume": [1000] * 200,
    }
)

# Генерируем market_data
market_data = simulator.generate_full_market_data(
    test_data, 150, {"rsi": 50, "adx": 25, "volume_ratio": 1.0, "momentum": 0}
)
indicators = market_data["indicators"]

print("Проверка scores для первых 20 сценариев:")
print()
for s in scenarios[:20]:
    score = matcher._calculate_scenario_score(
        s,
        market_data,
        indicators,
        market_data["mtf_trends"],
        market_data["volume_profile"],
        market_data["news_sentiment"],
        market_data.get("cvd"),
    )
    print(f"{s['id']:10} | score={score:.2%}")
