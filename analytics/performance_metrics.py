# -*- coding: utf-8 -*-
"""
Performance Metrics: Sharpe Ratio + Others
"""

import numpy as np
import pandas as pd

class PerformanceMetrics:
    """Calculate advanced performance metrics"""

    @staticmethod
    def calculate_sharpe_ratio(returns, risk_free_rate=0.02, periods=252):
        """
        Calculate Sharpe Ratio

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate (default 2%)
            periods: Trading periods per year (default 252 for daily)
        """
        if len(returns) < 2:
            return 0.0

        # Convert to array if needed
        if isinstance(returns, pd.Series):
            returns = returns.values

        # Calculate mean return and volatility
        mean_return = np.mean(returns)
        volatility = np.std(returns)

        if volatility == 0:
            return 0.0

        # Annualize
        annual_return = mean_return * periods
        annual_volatility = volatility * np.sqrt(periods)

        # Sharpe Ratio
        sharpe = (annual_return - risk_free_rate) / annual_volatility
        return sharpe

    @staticmethod
    def calculate_sortino_ratio(returns, risk_free_rate=0.02, periods=252):
        """Calculate Sortino Ratio (downside volatility only)"""
        if len(returns) < 2:
            return 0.0

        if isinstance(returns, pd.Series):
            returns = returns.values

        mean_return = np.mean(returns)
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            downside_volatility = 0.0
        else:
            downside_volatility = np.std(downside_returns)

        if downside_volatility == 0:
            return 0.0

        annual_return = mean_return * periods
        annual_downside_volatility = downside_volatility * np.sqrt(periods)

        sortino = (annual_return - risk_free_rate) / annual_downside_volatility
        return sortino


if __name__ == "__main__":
    # Test
    returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015, 0.003])

    metrics = PerformanceMetrics()
    sharpe = metrics.calculate_sharpe_ratio(returns)
    sortino = metrics.calculate_sortino_ratio(returns)

    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Sortino Ratio: {sortino:.2f}")
