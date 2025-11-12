# -*- coding: utf-8 -*-
"""
Clusters Detector: Bid/Ask Imbalance
"""

class ClustersDetector:
    """Detect order flow imbalances"""

    def __init__(self):
        self.bid_volume = 0.0
        self.ask_volume = 0.0

    def calculate_imbalance(self, buy_volume, sell_volume):
        """Calculate Bid/Ask imbalance"""
        total_volume = buy_volume + sell_volume

        if total_volume == 0:
            return 0.0

        imbalance = (buy_volume - sell_volume) / total_volume
        return imbalance

    def get_imbalance_signal(self, imbalance):
        """
        Get imbalance signal: BULLISH/NEUTRAL/BEARISH

        Args:
            imbalance: -1.0 to 1.0 (1.0 = all buy, -1.0 = all sell)
        """
        if imbalance > 0.3:
            return 'BULLISH', 'Strong buy pressure'
        elif imbalance > 0.1:
            return 'BULLISH_MILD', 'Mild buy pressure'
        elif imbalance < -0.3:
            return 'BEARISH', 'Strong sell pressure'
        elif imbalance < -0.1:
            return 'BEARISH_MILD', 'Mild sell pressure'
        else:
            return 'NEUTRAL', 'Balanced'


if __name__ == "__main__":
    detector = ClustersDetector()

    # Test
    imbalance = detector.calculate_imbalance(1000, 500)  # 67% buy
    signal, desc = detector.get_imbalance_signal(imbalance)

    print(f"Imbalance: {imbalance:.2f}")
    print(f"Signal: {signal} - {desc}")
