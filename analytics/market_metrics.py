# -*- coding: utf-8 -*-
"""
Market Metrics: COMPLETE VERSION (100%) - FIXED
"""

import requests
from datetime import datetime

class MarketMetrics:
    """Complete market-wide metrics with caching"""

    def __init__(self, symbol='BTCUSDT', cache_duration=300):
        self.symbol = symbol
        self.base_url = 'https://fapi.binance.com'
        self.cache_duration = cache_duration

        self.cache = {
            'funding_rate': None,
            'ls_ratio': None,
            'open_interest': None,
            'last_update': None
        }

    def _is_cache_fresh(self):
        """Check if cache is still valid"""
        if self.cache['last_update'] is None:
            return False
        return (datetime.now() - self.cache['last_update']).seconds < self.cache_duration

    def get_funding_rate(self, use_cache=True):
        """Get current funding rate"""
        if use_cache and self._is_cache_fresh():
            return self.cache['funding_rate']

        try:
            url = f"{self.base_url}/fapi/v1/premiumIndex?symbol={self.symbol}"
            response = requests.get(url, timeout=5)
            data = response.json()
            funding = float(data['lastFundingRate'])
            self.cache['funding_rate'] = funding
            self.cache['last_update'] = datetime.now()
            return funding
        except Exception as e:
            print(f"⚠️ Funding rate error: {e}")
            return self.cache['funding_rate'] or 0.0

    def get_long_short_ratio(self, use_cache=True):
        """Get Long/Short ratio"""
        if use_cache and self._is_cache_fresh():
            return self.cache['ls_ratio']

        try:
            url = f"{self.base_url}/futures/data/globalLongShortAccountRatio"
            params = {'symbol': self.symbol, 'period': '5m'}
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            latest = data[-1] if data else {}
            ls = float(latest.get('longShortRatio', 1.0))
            self.cache['ls_ratio'] = ls
            return ls
        except Exception as e:
            print(f"⚠️ L/S ratio error: {e}")
            return self.cache['ls_ratio'] or 1.0

    def get_open_interest(self, use_cache=True):
        """Get current open interest"""
        if use_cache and self._is_cache_fresh():
            return self.cache['open_interest']

        try:
            url = f"{self.base_url}/fapi/v1/openInterest?symbol={self.symbol}"
            response = requests.get(url, timeout=5)
            data = response.json()
            oi = float(data['openInterest'])
            self.cache['open_interest'] = oi
            return oi
        except Exception as e:
            print(f"⚠️ OI error: {e}")
            return self.cache['open_interest'] or 0.0

    def get_market_health(self, use_cache=True):
        """Calculate market health score"""
        funding = self.get_funding_rate(use_cache)
        ls_ratio = self.get_long_short_ratio(use_cache)

        health = 1.0

        # ← НОВОЕ: Safety checks for None values
        if funding is None:
            funding = 0.0
        if ls_ratio is None:
            ls_ratio = 1.0

        if abs(funding) > 0.01:
            health *= 0.8
        if abs(funding) > 0.02:
            health *= 0.7
        if abs(funding) > 0.03:
            health *= 0.5

        if ls_ratio > 2.5 or ls_ratio < 0.4:
            health *= 0.85
        if ls_ratio > 3.0 or ls_ratio < 0.33:
            health *= 0.7

        return health, funding, ls_ratio

    def get_market_signal(self):
        """Get market signal: BULLISH, NEUTRAL, BEARISH"""
        _, funding, ls = self.get_market_health()

        # ← НОВОЕ: Safety check
        if funding is None:
            funding = 0.0
        if ls is None:
            ls = 1.0

        signal_score = 0

        if funding > 0.01:
            signal_score += 1
        elif funding < -0.01:
            signal_score -= 1

        if ls > 1.5:
            signal_score += 1
        elif ls < 0.7:
            signal_score -= 1

        if signal_score >= 1:
            return 'BULLISH'
        elif signal_score <= -1:
            return 'BEARISH'
        else:
            return 'NEUTRAL'

    def apply_market_adjustment(self, confidence):
        """Adjust confidence based on market metrics"""
        health, funding, ls = self.get_market_health()

        # ← НОВОЕ: Safety check
        if health is None:
            health = 1.0

        confidence *= health

        if abs(funding) > 0.02:
            confidence *= 0.8
        if ls > 3.0 or ls < 0.33:
            confidence *= 0.8

        return max(0.0, min(1.0, confidence))

    def get_market_metrics_dict(self):
        """Return all metrics as dict"""
        health, funding, ls = self.get_market_health()
        oi = self.get_open_interest()
        signal = self.get_market_signal()

        # ← НОВОЕ: Safety checks
        if health is None:
            health = 1.0
        if funding is None:
            funding = 0.0
        if ls is None:
            ls = 1.0
        if oi is None:
            oi = 0.0

        return {
            'health': health,
            'funding_rate': funding,
            'ls_ratio': ls,
            'open_interest': oi,
            'market_signal': signal,
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    metrics = MarketMetrics()
    metrics_dict = metrics.get_market_metrics_dict()

    print(f"\n📊 MARKET METRICS:")
    print(f"   Funding Rate: {metrics_dict['funding_rate']:.4f}")
    print(f"   L/S Ratio: {metrics_dict['ls_ratio']:.2f}")
    print(f"   Market Health: {metrics_dict['health']:.2f}")
    print(f"   Market Signal: {metrics_dict['market_signal']}")
