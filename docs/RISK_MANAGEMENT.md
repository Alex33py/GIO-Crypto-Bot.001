text
# 🎯 GIO.BOT Risk Management System

**Version:** 2.0 (Optimized)
**Date:** November 1, 2025
**Status:** Production Ready

---

## 📊 Overview

GIO.BOT implements a **dynamic risk management system** optimized through systematic grid search testing. The system achieved a **Profit Factor of 3.77** with a **Risk/Reward ratio of 3.75:1**.

---

## 🔧 Components

### 1. **Dynamic Stop Loss (SL)**

**Formula:**
SL = Entry Price ± (ATR × SL_MULTIPLIER)

text

**Optimized Value:**
- `SL_MULTIPLIER = 1.2` (from grid search of 1.2, 1.5, 1.8, 2.0)

**Rationale:**
- Tighter SL (1.2x ATR) reduces loss per trade
- Avg Loss: $0.21 (vs $0.26 baseline)
- 19% reduction in average loss

**Implementation:**
if signal_type == "LONG":
stop_loss = entry_price - (atr * 1.2)
else: # SHORT
stop_loss = entry_price + (atr * 1.2)

text

---

### 2. **Dynamic Take Profit (TP)**

**Formula:**
TP = Entry Price ± (ATR × TP_MULTIPLIER)

text

**Optimized Value:**
- `TP_MULTIPLIER = 4.5` (from grid search of 3.0, 3.5, 4.0, 4.5)

**Rationale:**
- Higher TP (4.5x ATR) captures larger moves
- Avg Win: $0.80 (vs $0.62 baseline)
- 29% increase in average win

**Implementation:**
if signal_type == "LONG":
take_profit = entry_price + (atr * 4.5)
else: # SHORT
take_profit = entry_price - (atr * 4.5)

text

---

### 3. **Position Sizing**

**Base Formula:**
Position Size = (Capital × RISK_PERCENTAGE) / Entry Price

text

**Parameters:**
- Base risk: **2% of capital per trade**
- Max position: **5% of capital**
- Confidence adjustment: **0.5x to 1.5x multiplier**

**Confidence Scaling:**
confidence_multiplier = 0.5 + confidence # Range: 0.5 to 1.5

Example:
confidence=0.3 → multiplier=0.8 → 1.6% position
confidence=0.5 → multiplier=1.0 → 2.0% position
confidence=0.7 → multiplier=1.2 → 2.4% position
text

**Implementation:**
base_size_value = current_capital * 0.02
adjusted_size_value = base_size_value * (0.5 + confidence)
final_size_value = min(adjusted_size_value, max_size_value)
position_size = final_size_value / entry_price

text

---

### 4. **Risk/Reward Validation**

**Minimum RR Ratio:** 2.0:1

**Current RR Ratio:** 3.75:1 (4.5 / 1.2)

**Validation Logic:**
risk = abs(entry_price - stop_loss)
reward = abs(take_profit - entry_price)
rr_ratio = reward / risk

if rr_ratio < 2.0:
# Reject trade
return "RR ratio too low"

text

---

### 5. **Daily Loss Limits**

**Max Daily Loss:** 10% of capital

**Implementation:**
if total_risk_today + new_risk > capital * 0.10:
# Stop trading for the day
return "Daily loss limit reached"

text

---

### 6. **Maximum Drawdown Monitoring**

**Max Drawdown:** 15% from peak

**Implementation:**
peak_capital = max(peak_capital, current_capital)
drawdown = (peak_capital - current_capital) / peak_capital

if drawdown > 0.15:
# Reduce position sizes or pause trading
return "Max drawdown reached"

text

---

## 📈 Grid Search Results

### SL/TP Optimization (16 configurations tested)

| Rank | SL | TP | RR | Profit Factor | Win Rate | Trades | ROI |
|------|----|----|-------|---------------|----------|--------|-----|
| **1** | **1.2** | **4.5** | **3.75** | **3.77** | 31.3% | 131 | 0.14% |
| 2 | 1.2 | 4.0 | 3.33 | 3.35 | 31.9% | 138 | 0.11% |
| 3 | 1.5 | 4.5 | 3.00 | 3.01 | 32.0% | 128 | 0.10% |
| 4 | 1.2 | 3.5 | 2.92 | 2.93 | 34.3% | 143 | 0.11% |
| 5 | 1.5 | 4.0 | 2.67 | 2.68 | 32.6% | 135 | 0.07% |

**Winner:** SL=1.2x, TP=4.5x (RR 3.75:1)

---

## 🎯 Performance Metrics

### Before Optimization (Baseline)
- Profit Factor: 2.38
- Win Rate: 36.8%
- Avg Win: $0.62
- Avg Loss: $0.26
- Max DD: -0.8%

### After Optimization (Current)
- Profit Factor: **3.77** (+58%)
- Win Rate: 31.3% (-5.5pp)
- Avg Win: **$0.80** (+29%)
- Avg Loss: **$0.21** (-19%)
- Max DD: **-0.3%** (-62%)

### Trade-offs
✅ **Higher Profit Factor** (+58%)
✅ **Better Avg Win/Loss Ratio** (+60%)
✅ **Lower Max Drawdown** (-62%)
⚠️ **Lower Win Rate** (-5.5pp) - acceptable with high PF

---

## 🔍 Risk Metrics Analysis

### Expected Values
Expected Profit per Trade = (Win Rate × Avg Win) - ((1 - Win Rate) × Avg Loss)
= (0.313 × $0.80) - (0.687 × $0.21)
= $0.25 - $0.14
= $0.11 per trade

text

### Kelly Criterion (Optimal Position Size)
Kelly % = (Win Rate × (RR + 1) - 1) / RR
= (0.313 × (3.75 + 1) - 1) / 3.75
= (1.487 - 1) / 3.75
= 0.130 = 13%

text

**Half Kelly (Conservative):** 6.5%
**Current Usage:** 2% (safe, conservative)

---

## 💡 Usage Guide

### Basic Usage

from analytics.risk_manager import RiskManager, RiskConfig

Initialize
risk_mgr = RiskManager(config=RiskConfig())

Calculate position
calculation = risk_mgr.calculate_position(
signal_type="LONG",
entry_price=50000,
atr=200,
current_capital=10000,
confidence=0.7
)

if calculation.is_valid:
# Execute trade
execute_trade(
entry=50000,
sl=calculation.stop_loss,
tp=calculation.take_profit,
size=calculation.position_size
)
else:
# Reject trade
log_rejection(calculation.rejection_reason)

text

### Integration with Backtest

In backtest loop
if signal:
calculation = risk_mgr.calculate_position(
signal_type=signal['type'],
entry_price=current_price,
atr=signal['atr'],
current_capital=self.current_capital,
confidence=signal['confidence']
)

text
if calculation.is_valid:
    self.execute_trade(calculation)
text

---

## 🚨 Risk Warnings

### Daily Limits
- **Max 10% daily loss** - Stop trading if limit reached
- **Max 5 trades per day** - Avoid overtrading

### Drawdown Management
- **15% max drawdown** - Reduce positions at 10% DD
- **20% circuit breaker** - Stop all trading

### Position Limits
- **Max 5% per position** - Never exceed
- **Max 3 concurrent positions** - Diversification limit

---

## 📚 References

1. Grid Search Results: `tests/results/grid_search/sl_tp_grid_20251101_204809.csv`
2. Optimal Config: `config/optimal_config.py`
3. Backtest Results: `tests/results/backtest_full_sim_*.csv`

---

## 🔄 Version History

### v2.0 (November 1, 2025)
- ✅ Grid search optimization (16 configs)
- ✅ Optimal SL/TP: 1.2x/4.5x ATR
- ✅ Profit Factor: 3.77
- ✅ Documented in risk_manager.py

### v1.0 (October 31, 2025)
- ✅ Initial risk management
- ✅ Baseline SL/TP: 1.5x/3.5x ATR
- ✅ Profit Factor: 2.38

---

## 📞 Contact

For questions or optimization suggestions:
- GitHub Issues: [github.com/your-repo/GIO.BOT.002]
- Email: [your-email]

---

**Status:** ✅ Production Ready
**Last Updated:** November 1, 2025, 21:15 EET
