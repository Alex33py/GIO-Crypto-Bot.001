# -*- coding: utf-8 -*-
"""
PAPER TRADING RUNNER (SIMPLIFIED)
"""

import sys
sys.path.append('.')

import pandas as pd
from datetime import datetime
from bot.live_signal_tracker import LiveSignalTracker
from bot.telegram_sender import TelegramSender
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperTradingRunner:
    """Paper trading simulator (SIMPLIFIED)"""

    def __init__(self, capital=10000):
        self.tracker = LiveSignalTracker()
        self.telegram = TelegramSender()

        # SIMPLE CAPITAL TRACKING
        self.initial_capital = capital
        self.current_capital = capital

        self.position = None
        self.trades = []
        self.start_time = datetime.now()
        logger.info(f"🏦 Paper Trading initialized | Capital: ${capital:,.2f}")

    def run_backtest_simulation(self, df, bars_per_iteration=1):
        """Simulate paper trading on historical data"""

        logger.info(f"📊 Starting paper trading simulation...")
        logger.info(f"   Total bars: {len(df)}")
        logger.info(f"   Period: {df.iloc[0]['timestamp']} to {df.iloc[-1]['timestamp']}")
        logger.info("")

        for i in range(100, len(df), bars_per_iteration):
            current_bar = df.iloc[i]
            window = df.iloc[i-100:i+1]

            # === ENTRY LOGIC ===
            if self.position is None:
                signal = self.tracker.check_signal(
                    window['close'],
                    window['high'],
                    window['low'],
                    window['volume']
                )

                if signal:
                    # SIMPLE POSITION (2% of capital)
                    position_size_usd = self.current_capital * 0.02
                    position_size_btc = position_size_usd / signal['entry']

                    self.position = {
                        'entry_bar': i,
                        'entry_time': current_bar['timestamp'],
                        'entry_price': signal['entry'],
                        'sl_price': signal['sl_price'],
                        'tp': signal['tp'],
                        'scenario': signal['scenario'],
                        'size_usd': position_size_usd,
                        'size_btc': position_size_btc,
                    }

                    logger.info(f"[{i:4d}] 🟢 ENTRY @ ${signal['entry']:,.2f} | {signal['scenario']}")
                    logger.info(f"       SL: ${signal['sl_price']:,.2f} | TP: ${signal['tp']:,.2f}")

                    # Send telegram
                    try:
                        self.telegram.send_signal(signal)
                    except:
                        pass  # Ignore telegram errors

            # === EXIT LOGIC ===
            elif self.position is not None:
                high = current_bar['high']
                low = current_bar['low']
                tp = self.position['tp']
                sl_price = self.position['sl_price']

                exit_price = None
                exit_reason = None

                if high >= tp:
                    exit_price = tp
                    exit_reason = 'TP'
                elif low <= sl_price:
                    exit_price = sl_price
                    exit_reason = 'SL'

                if exit_price:
                    # Calculate PnL
                    entry = self.position['entry_price']
                    pnl_pct = ((exit_price - entry) / entry) * 100
                    pnl_usd = self.position['size_usd'] * (pnl_pct / 100)

                    # Update capital
                    self.current_capital += pnl_usd

                    # Save trade
                    trade = {
                        'entry_time': self.position['entry_time'],
                        'exit_time': current_bar['timestamp'],
                        'entry_price': entry,
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'scenario': self.position['scenario'],
                        'pnl_pct': pnl_pct,
                        'pnl_usd': pnl_usd,
                        'capital_after': self.current_capital,
                    }

                    self.trades.append(trade)

                    status = "✅ WIN" if pnl_usd > 0 else "❌ LOSS"
                    logger.info(f"[{i:4d}] 🔴 EXIT @ ${exit_price:,.2f} | {exit_reason} | {status} {pnl_pct:+.2f}%")
                    logger.info(f"       Capital: ${self.current_capital:,.2f}")
                    logger.info("")

                    self.position = None

        self._print_final_report()

    def _print_final_report(self):
        """Print final statistics"""

        logger.info("\n" + "="*80)
        logger.info("📊 PAPER TRADING FINAL REPORT")
        logger.info("="*80)

        if not self.trades:
            logger.info("❌ No trades executed")
            return

        df = pd.DataFrame(self.trades)
        wins = df[df['pnl_usd'] > 0]
        losses = df[df['pnl_usd'] < 0]

        total_wins = wins['pnl_usd'].sum() if len(wins) > 0 else 0
        total_losses = abs(losses['pnl_usd'].sum()) if len(losses) > 0 else 1

        logger.info(f"📈 Total Trades: {len(df)}")
        logger.info(f"✅ Wins: {len(wins)} ({(len(wins)/len(df)*100):.1f}%)")
        logger.info(f"❌ Losses: {len(losses)} ({(len(losses)/len(df)*100):.1f}%)")
        logger.info(f"💰 Avg Win: {wins['pnl_pct'].mean():+.2f}%" if len(wins) > 0 else "N/A")
        logger.info(f"💸 Avg Loss: {losses['pnl_pct'].mean():.2f}%" if len(losses) > 0 else "N/A")
        logger.info(f"\n🏆 Profit Factor: {(total_wins / total_losses):.2f}")
        logger.info(f"🎯 Win Rate: {(len(wins)/len(df)*100):.1f}%")
        logger.info(f"💵 Total PnL: ${df['pnl_usd'].sum():,.2f} ({((self.current_capital - self.initial_capital) / self.initial_capital * 100):+.2f}%)")
        logger.info(f"💼 Final Capital: ${self.current_capital:,.2f}")
        logger.info("="*80 + "\n")

        # Save results
        import os
        os.makedirs('systems/results', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"systems/results/paper_trading_{timestamp}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"💾 Results saved: {filename}\n")


def main():
    """Main entry point"""

    logger.info("="*80)
    logger.info("🚀 GIO.BOT PAPER TRADING")
    logger.info("="*80 + "\n")

    # Load historical data
    df = pd.read_csv('data/historical/BTCUSDT_1h_90d.csv')

    # Create runner
    runner = PaperTradingRunner(capital=10000)

    # Run simulation
    runner.run_backtest_simulation(df, bars_per_iteration=1)


if __name__ == "__main__":
    main()
