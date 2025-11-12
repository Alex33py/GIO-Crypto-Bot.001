"""
Market Data Simulator for Backtest
Симулятор полных рыночных данных для точного тестирования всех сценариев
Генерирует: Orderbook, CVD, Clusters, News, Volume Profile
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class MarketDataSimulator:
    """Симулятор полных рыночных данных"""

    def __init__(self, seed: int = 42):
        """
        Инициализация симулятора
        Args:
            seed: Seed для воспроизводимости
        """
        np.random.seed(seed)
        self.seed = seed

    def generate_orderbook(self, price: float, volatility: float = 0.02) -> Dict:
        """
        Генерирование симулированного L2 orderbook

        Args:
            price: Текущая цена
            volatility: Волатильность (для depth распределения)

        Returns:
            Dict с bid/ask стеками
        """
        # Bid стек (под ценой)
        bid_levels = 20
        bids = []
        for i in range(bid_levels):
            bid_price = price * (1 - 0.001 * (i + 1))
            bid_volume = np.random.exponential(scale=10) * (bid_levels - i)
            bids.append([bid_price, bid_volume])

        # Ask стек (над ценой)
        ask_levels = 20
        asks = []
        for i in range(ask_levels):
            ask_price = price * (1 + 0.001 * (i + 1))
            ask_volume = np.random.exponential(scale=10) * (ask_levels - i)
            asks.append([ask_price, ask_volume])

        # Bid/Ask ratio (для анализа давления)
        total_bid_vol = sum(b[1] for b in bids)
        total_ask_vol = sum(a[1] for a in asks)
        bid_ask_ratio = total_bid_vol / max(total_ask_vol, 1)

        return {
            "bids": bids,
            "asks": asks,
            "bid_volume": total_bid_vol,
            "ask_volume": total_ask_vol,
            "bid_ask_ratio": bid_ask_ratio,
            "spread": asks[0][0] - bids[0][0]
        }

    def generate_cvd(self, df: pd.DataFrame, current_idx: int, lookback: int = 24) -> Dict:
        """
        Генерирование CVD (Cumulative Volume Delta)

        Args:
            df: DataFrame с OHLCV данными
            current_idx: Текущий индекс свечи
            lookback: Количество свечей для расчёта

        Returns:
            Dict с CVD метриками
        """
        start_idx = max(0, current_idx - lookback)
        candles = df.iloc[start_idx:current_idx + 1]

        # Определяем buy/sell volume (упрощённо на основе close vs open)
        buy_volume = 0
        sell_volume = 0

        for _, candle in candles.iterrows():
            volume = candle['volume']
            if candle['close'] >= candle['open']:
                buy_volume += volume * 0.6  # Предполагаем 60% объёма - покупки
            else:
                sell_volume += volume * 0.6

        # CVD = совокупный delta
        cvd = buy_volume - sell_volume

        # Направление CVD
        cvd_direction = "bullish" if cvd > 0 else "bearish" if cvd < 0 else "neutral"

        # CVD подтверждение тренда
        current_trend = "bullish" if candles.iloc[-1]['close'] > candles.iloc[0]['close'] else "bearish"
        cvd_confirms = cvd_direction == current_trend or cvd_direction == "neutral"

        return {
            "cvd_value": cvd,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "cvd_direction": cvd_direction,
            "cvd_confirms": cvd_confirms,
            "total_delta": buy_volume - sell_volume
        }

    def generate_clusters(self, orderbook: Dict, price: float, volatility: float = 0.02) -> Dict:
        """
        Генерирование cluster данных из orderbook

        Args:
            orderbook: Данные orderbook
            price: Текущая цена
            volatility: Волатильность

        Returns:
            Dict с cluster метриками
        """
        bids = orderbook['bids']
        asks = orderbook['asks']

        # POC (Point of Control) - уровень с наибольшим объёмом
        all_levels = bids + asks
        if all_levels:
            poc_level = max(all_levels, key=lambda x: x[1])
            poc_price = poc_level[0]
            poc_volume = poc_level[1]
        else:
            poc_price = price
            poc_volume = 0

        # Detect stacked imbalance (несколько уровней с дисбалансом)
        stacked_imbalance_up = 0
        stacked_imbalance_down = 0

        for i in range(len(bids) - 1):
            if bids[i][1] > bids[i + 1][1] * 1.5:
                stacked_imbalance_up += 1

        for i in range(len(asks) - 1):
            if asks[i][1] > asks[i + 1][1] * 1.5:
                stacked_imbalance_down += 1

        # POC shift (смещение POC вверх или вниз)
        poc_shift_up = stacked_imbalance_up > stacked_imbalance_down
        poc_shift_down = stacked_imbalance_down > stacked_imbalance_up

        # Absorption (защита уровня - большой объём не пробил)
        absorption_level = None
        if price > poc_price:
            # Цена выше POC, ищем absorption вверху
            top_ask_vol = sum(a[1] for a in asks[:5])
            if top_ask_vol > poc_volume * 0.8:
                absorption_level = "above"
        else:
            # Цена ниже POC, ищем absorption внизу
            top_bid_vol = sum(b[1] for b in bids[:5])
            if top_bid_vol > poc_volume * 0.8:
                absorption_level = "below"

        return {
            "poc_price": poc_price,
            "poc_volume": poc_volume,
            "stacked_imbalance_up": stacked_imbalance_up,
            "stacked_imbalance_down": stacked_imbalance_down,
            "poc_shift_up": poc_shift_up,
            "poc_shift_down": poc_shift_down,
            "absorption_level": absorption_level,
            "bid_delta": sum(b[1] for b in bids) - sum(a[1] for a in asks),
            "total_imbalance": abs(sum(b[1] for b in bids) - sum(a[1] for a in asks)),
            "real": False  # ← ДОБАВИЛИ ФЛАГ! (симулированные данные)
        }

    def generate_news_sentiment(self, current_idx: int, total_candles: int) -> Dict:
        """
        Генерирование новостной активности

        Args:
            current_idx: Текущий индекс
            total_candles: Всего свечей

        Returns:
            Dict с настроением новостей
        """
        # Случайные новости с 5% вероятностью
        has_news = np.random.random() < 0.05

        if has_news:
            # Сентимент: -1 до +1
            sentiment = np.random.uniform(-1, 1)
        else:
            sentiment = 0

        return {
            "overall_score": sentiment,
            "overall": "bullish" if sentiment > 0.2 else "bearish" if sentiment < -0.2 else "neutral",
            "has_news": has_news,
            "impact": abs(sentiment)
        }

    def generate_full_market_data(
        self,
        df: pd.DataFrame,
        current_idx: int,
        indicators: Dict
    ) -> Dict:
        """
        Генерирование ПОЛНОГО набора рыночных данных для matcher

        Args:
            df: DataFrame с OHLCV
            current_idx: Текущий индекс
            indicators: Рассчитанные индикаторы (RSI, ADX, etc)

        Returns:
            Полный набор данных для ScenarioMatcher
        """
        current_candle = df.iloc[current_idx]
        price = current_candle['close']

        # Генерируем компоненты
        orderbook = self.generate_orderbook(price)
        cvd = self.generate_cvd(df, current_idx)
        clusters = self.generate_clusters(orderbook, price)
        news = self.generate_news_sentiment(current_idx, len(df))

        # MTF trends (из indicators)
        lookback_data = df.iloc[max(0, current_idx - 100):current_idx + 1]

        def calc_trend(data):
            if len(data) < 2:
                return "neutral"
            ema_20 = data['close'].ewm(span=20).mean().iloc[-1] if len(data) >= 20 else data['close'].iloc[-1]
            current_price = data['close'].iloc[-1]
            return "bullish" if current_price > ema_20 else "bearish"

        mtf_trends = {
            "1H": calc_trend(lookback_data[-24:]) if len(lookback_data) >= 24 else "neutral",
            "4H": calc_trend(lookback_data[-96:]) if len(lookback_data) >= 96 else "neutral",
            "1D": calc_trend(lookback_data)
        }

        # Volume Profile (упрощённый - симулированные данные!)
        vp = {
            "poc": clusters['poc_price'],
            "vah": clusters['poc_price'] * 1.02,
            "val": clusters['poc_price'] * 0.98,
            "vwap": price,
            "real": False  # ← ДОБАВИЛИ ФЛАГ!
        }

        # Собираем полные данные
        market_data = {
            "price": price,
            "high": current_candle['high'],
            "low": current_candle['low'],
            "volume": current_candle['volume'],
            "timestamp": current_candle['timestamp'],

            # Indicator data
            "indicators": {
                "rsi": indicators.get('rsi', 50),
                "adx": indicators.get('adx', 25),
                "volume_ratio": indicators.get('volume_ratio', 1.0),
                "momentum": indicators.get('momentum', 0)
            },

            # MTF
            "mtf_trends": mtf_trends,

            # Volume Profile
            "volume_profile": vp,

            # Orderbook
            "orderbook": orderbook,

            # CVD
            "cvd": cvd,

            # Clusters
            "clusters": clusters,

            # News
            "news_sentiment": news,

            # Veto checks (пусты - нет ограничений)
            "veto_checks": {
                "high_volatility": False,
                "low_liquidity": False,
                "news_impact": news['impact'] > 0.7
            }
        }

        return market_data


def create_simulator() -> MarketDataSimulator:
    """Создание экземпляра симулятора"""
    return MarketDataSimulator()
