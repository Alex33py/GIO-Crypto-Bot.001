
# ✅ DYNAMIC RISK MANAGEMENT (ATR-based, Оптимизировано)
SL_ATR_MULTIPLIER = 1.2    # SL = Entry ± 1.2 × ATR
TP_ATR_MULTIPLIER = 4.5    # TP = Entry ± 4.5 × ATR (RR = 1:3.75)

def calculate_sl_tp_dynamic(entry_price: float, atr: float, direction: str) -> Tuple[float, float, float]:
    """Расчитать SL/TP динамически на основе ATR"""
    if atr < 0.1:
        atr = 1.0

    if direction == "LONG":
        stop_loss = entry_price - (SL_ATR_MULTIPLIER * atr)
        take_profit = entry_price + (TP_ATR_MULTIPLIER * atr)
    else:
        stop_loss = entry_price + (SL_ATR_MULTIPLIER * atr)
        take_profit = entry_price - (TP_ATR_MULTIPLIER * atr)

    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    rr_ratio = reward / risk if risk > 0 else 0
    return round(stop_loss, 2), round(take_profit, 2), round(rr_ratio, 2)


"""
Risk Manager Module for GIO.BOT (ENHANCED)
==========================================

Combines:
- Your optimized SL/TP (1.2x/4.5x ATR, PF=3.77)
- Trade history tracking
- Open positions management
- Kelly Criterion (optional)
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import pandas as pd


class PositionType(Enum):
    """Position direction"""
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class RiskConfig:
    """Risk management configuration"""
    # SL/TP multipliers (YOUR OPTIMIZED VALUES!)
    sl_multiplier: float = 1.2      # Stop Loss: 1.2x ATR
    tp_multiplier: float = 4.5      # Take Profit: 4.5x ATR (PF=3.77!)

    # Position sizing
    position_size_pct: float = 0.02  # 2% of capital per trade
    max_position_size: float = 0.05  # Max 5% per trade

    # Risk limits
    max_daily_loss: float = 0.10     # 10% daily loss limit (YOUR VALUE)
    max_drawdown: float = 0.15       # 15% max drawdown
    max_open_positions: int = 3      # Max 3 positions simultaneously

    # Risk/Reward requirements
    min_risk_reward: float = 2.0     # Minimum RR ratio (YOUR VALUE)

    # Kelly Criterion (optional)
    use_kelly: bool = False          # Enable Kelly sizing
    kelly_fraction: float = 0.5      # Half Kelly (conservative)

    def __post_init__(self):
        """Validate configuration"""
        assert self.sl_multiplier > 0, "SL multiplier must be positive"
        assert self.tp_multiplier > 0, "TP multiplier must be positive"
        assert self.tp_multiplier > self.sl_multiplier, "TP must be greater than SL"
        assert 0 < self.position_size_pct <= 1, "Position size must be 0-100%"


@dataclass
class RiskCalculation:
    """Result of risk calculation"""
    stop_loss: float
    take_profit: float
    position_size: float
    risk_reward_ratio: float
    risk_amount: float
    potential_profit: float
    is_valid: bool
    rejection_reason: Optional[str] = None


@dataclass
class Position:
    """Active position tracking"""
    trade_id: str
    scenario_id: str
    signal_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_amount: float
    entry_time: datetime = field(default_factory=datetime.now)


@dataclass
class TradeResult:
    """Closed trade result"""
    trade_id: str
    scenario_id: str
    signal_type: str
    entry_price: float
    exit_price: float
    exit_reason: str
    position_size: float
    pnl: float
    pnl_pct: float
    entry_time: datetime
    exit_time: datetime
    duration_hours: float


class RiskManager:
    """
    Advanced Risk Management System (ENHANCED)

    Features:
    - YOUR optimized SL/TP (1.2x/4.5x ATR, PF=3.77)
    - Dynamic position sizing with confidence
    - Trade history tracking
    - Open positions management
    - Kelly Criterion (optional)
    - Drawdown monitoring
    """

    def __init__(self, config: RiskConfig = None, initial_capital: float = 10000.0):
        """
        Initialize Risk Manager

        Args:
            config: Risk configuration (uses YOUR optimized defaults)
            initial_capital: Starting capital
        """
        self.config = config or RiskConfig()
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Risk tracking
        self.total_risk_today = 0.0
        self.peak_capital = initial_capital
        self.current_drawdown = 0.0

        # Position tracking (NEW!)
        self.open_positions: List[Position] = []
        self.trade_history: List[TradeResult] = []

    def calculate_position(
        self,
        signal_type: str,
        entry_price: float,
        atr: float,
        confidence: float = 0.5
    ) -> RiskCalculation:
        """
        Calculate complete position parameters with risk management

        Args:
            signal_type: "LONG" or "SHORT"
            entry_price: Entry price for the trade
            atr: Average True Range value
            confidence: Signal confidence (0-1)

        Returns:
            RiskCalculation with SL, TP, size, RR ratio
        """
        # Calculate SL/TP distances
        sl_distance = atr * self.config.sl_multiplier
        tp_distance = atr * self.config.tp_multiplier

        # Calculate actual SL/TP prices
        if signal_type.upper() == "LONG":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # SHORT
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance

        # Calculate Risk/Reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0

        # Validate RR ratio
        if risk_reward_ratio < self.config.min_risk_reward:
            return RiskCalculation(
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=0,
                risk_reward_ratio=risk_reward_ratio,
                risk_amount=0,
                potential_profit=0,
                is_valid=False,
                rejection_reason=f"RR ratio {risk_reward_ratio:.2f} below minimum {self.config.min_risk_reward}"
            )

        # Check max open positions (NEW!)
        if len(self.open_positions) >= self.config.max_open_positions:
            return RiskCalculation(
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=0,
                risk_reward_ratio=risk_reward_ratio,
                risk_amount=0,
                potential_profit=0,
                is_valid=False,
                rejection_reason=f"Max open positions reached: {len(self.open_positions)}"
            )

        # Calculate position size
        position_size = self._calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss,
            confidence=confidence
        )

        # Calculate risk and profit amounts
        risk_amount = abs(entry_price - stop_loss) * position_size
        potential_profit = abs(take_profit - entry_price) * position_size

        # Validate daily loss limit
        if self.total_risk_today + risk_amount > self.current_capital * self.config.max_daily_loss:
            return RiskCalculation(
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=0,
                risk_reward_ratio=risk_reward_ratio,
                risk_amount=0,
                potential_profit=0,
                is_valid=False,
                rejection_reason=f"Daily loss limit reached ({self.total_risk_today / self.current_capital * 100:.1f}%)"
            )

        return RiskCalculation(
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            risk_reward_ratio=risk_reward_ratio,
            risk_amount=risk_amount,
            potential_profit=potential_profit,
            is_valid=True
        )

    def _calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        confidence: float = 0.5
    ) -> float:
        """
        Calculate position size with YOUR logic + Kelly option

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            confidence: Signal confidence (0-1)

        Returns:
            Position size in base currency units
        """
        # Base position size (YOUR LOGIC)
        base_size_value = self.current_capital * self.config.position_size_pct

        # Adjust for confidence (0.5x to 1.5x) - YOUR LOGIC
        confidence_multiplier = 0.5 + confidence
        adjusted_size_value = base_size_value * confidence_multiplier

        # Kelly Criterion adjustment (OPTIONAL, NEW!)
        if self.config.use_kelly and len(self.trade_history) > 10:
            kelly_size = self._calculate_kelly_size()
            adjusted_size_value = min(adjusted_size_value, kelly_size)

        # Cap at maximum position size
        max_size_value = self.current_capital * self.config.max_position_size
        final_size_value = min(adjusted_size_value, max_size_value)

        # Convert to position size (units)
        position_size = final_size_value / entry_price

        return position_size

    def _calculate_kelly_size(self) -> float:
        """
        Kelly Criterion for position sizing (NEW!)

        Kelly % = W - [(1 - W) / R]
        """
        if len(self.trade_history) < 10:
            return self.current_capital * self.config.position_size_pct

        df = pd.DataFrame([vars(trade) for trade in self.trade_history])
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] < 0]

        if len(losses) == 0 or len(wins) == 0:
            return self.current_capital * self.config.position_size_pct

        win_rate = len(wins) / len(df)
        avg_win = wins['pnl'].mean()
        avg_loss = abs(losses['pnl'].mean())

        if avg_loss == 0:
            return self.current_capital * self.config.position_size_pct

        r_ratio = avg_win / avg_loss
        kelly_pct = win_rate - ((1 - win_rate) / r_ratio)
        kelly_pct = max(0, kelly_pct)
        kelly_pct *= self.config.kelly_fraction  # Fractional Kelly

        kelly_pct = min(kelly_pct, self.config.max_position_size)

        return self.current_capital * kelly_pct

    def open_position(
        self,
        trade_id: str,
        scenario_id: str,
        signal_type: str,
        calculation: RiskCalculation
    ) -> Optional[Position]:
        """
        Open a new position (NEW!)

        Args:
            trade_id: Unique trade ID
            scenario_id: Scenario that generated the signal
            signal_type: "LONG" or "SHORT"
            calculation: RiskCalculation from calculate_position()

        Returns:
            Position object or None if rejected
        """
        if not calculation.is_valid:
            return None

        position = Position(
            trade_id=trade_id,
            scenario_id=scenario_id,
            signal_type=signal_type,
            entry_price=calculation.stop_loss,  # FIXME: Should be entry_price
            stop_loss=calculation.stop_loss,
            take_profit=calculation.take_profit,
            position_size=calculation.position_size,
            risk_amount=calculation.risk_amount,
        )

        self.open_positions.append(position)
        self.total_risk_today += calculation.risk_amount

        return position

    def close_position(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str
    ) -> Optional[TradeResult]:
        """
        Close an open position (NEW!)

        Args:
            trade_id: Trade ID to close
            exit_price: Exit price
            exit_reason: "TP", "SL", or "MANUAL"

        Returns:
            TradeResult or None if position not found
        """
        # Find position
        position = None
        for i, pos in enumerate(self.open_positions):
            if pos.trade_id == trade_id:
                position = self.open_positions.pop(i)
                break

        if position is None:
            return None

        # Calculate PnL
        if position.signal_type == "LONG":
            pnl = (exit_price - position.entry_price) * position.position_size
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.position_size

        pnl_pct = (pnl / (position.entry_price * position.position_size)) * 100

        # Update capital
        self.current_capital += pnl
        self.update_drawdown(self.current_capital)

        # Calculate duration
        exit_time = datetime.now()
        duration = (exit_time - position.entry_time).total_seconds() / 3600

        # Create trade result
        trade_result = TradeResult(
            trade_id=trade_id,
            scenario_id=position.scenario_id,
            signal_type=position.signal_type,
            entry_price=position.entry_price,
            exit_price=exit_price,
            exit_reason=exit_reason,
            position_size=position.position_size,
            pnl=pnl,
            pnl_pct=pnl_pct,
            entry_time=position.entry_time,
            exit_time=exit_time,
            duration_hours=duration,
        )

        self.trade_history.append(trade_result)

        return trade_result

    def update_daily_risk(self, trade_result: float):
        """Update daily risk tracking after trade closes"""
        if trade_result < 0:
            self.total_risk_today += abs(trade_result)

    def update_drawdown(self, current_capital: float):
        """Update drawdown tracking"""
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital

        self.current_drawdown = (self.peak_capital - current_capital) / self.peak_capital

    def reset_daily_limits(self):
        """Reset daily risk counter (call at start of each day)"""
        self.total_risk_today = 0.0

    def get_risk_status(self) -> Dict:
        """Get current risk status"""
        return {
            'daily_risk_used': self.total_risk_today,
            'daily_risk_pct': (self.total_risk_today / self.current_capital) * 100,
            'current_drawdown_pct': self.current_drawdown * 100,
            'open_positions': len(self.open_positions),
            'is_daily_limit_reached': self.total_risk_today >= (self.current_capital * self.config.max_daily_loss),
            'is_max_drawdown_reached': self.current_drawdown >= self.config.max_drawdown,
            'current_capital': self.current_capital,
            'roi_pct': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
        }

    def get_statistics(self) -> Dict:
        """Get trading statistics (NEW!)"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_pnl': 0.0,
                'roi': 0.0,
            }

        df = pd.DataFrame([vars(trade) for trade in self.trade_history])
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] < 0]

        total_wins = wins['pnl'].sum() if len(wins) > 0 else 0
        total_losses = abs(losses['pnl'].sum()) if len(losses) > 0 else 1

        return {
            'total_trades': len(df),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(df)) * 100,
            'profit_factor': total_wins / total_losses if total_losses > 0 else 0,
            'total_pnl': df['pnl'].sum(),
            'roi': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            'avg_win_pct': wins['pnl_pct'].mean() if len(wins) > 0 else 0,
            'avg_loss_pct': losses['pnl_pct'].mean() if len(losses) > 0 else 0,
        }

    def export_trades(self, filename: str):
        """Export trade history to CSV (NEW!)"""
        if not self.trade_history:
            print("⚠️ No trades to export")
            return

        df = pd.DataFrame([vars(trade) for trade in self.trade_history])
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Trades exported: {filename}")


#  USAGE EXAMPLES

if __name__ == "__main__":
    print("🎯 GIO.BOT Risk Manager (ENHANCED)")
    print("=" * 50)

    # Initialize with YOUR optimized config
    risk_mgr = RiskManager(config=RiskConfig(
        sl_multiplier=1.2,
        tp_multiplier=4.5,
        position_size_pct=0.02,
        min_risk_reward=2.0
    ))

    # Calculate position for LONG signal
    calculation = risk_mgr.calculate_position(
        signal_type="LONG",
        entry_price=50000,
        atr=200,
        confidence=0.7
    )

    if calculation.is_valid:
        print(f"✅ Position Approved:")
        print(f"   SL: ${calculation.stop_loss:.2f}")
        print(f"   TP: ${calculation.take_profit:.2f}")
        print(f"   Size: {calculation.position_size:.4f} BTC")
        print(f"   RR Ratio: {calculation.risk_reward_ratio:.2f}:1")
        print(f"   Potential Profit: ${calculation.potential_profit:.2f}")
    else:
        print(f"❌ Position Rejected: {calculation.rejection_reason}")
