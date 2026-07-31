---
name: mt5-strategy-tester
description: Run MT5 Strategy Tester on compiled EAs via MCP, analyze results, and iterate on strategy parameters
---

# MT5 Strategy Tester Skill

## Core Principle
**ALWAYS use actual MT5 Strategy Tester, NEVER Python backtest simulation**

## Why MT5 Strategy Tester Only
- Python backtest uses default EMA crossover logic, NOT actual EA code
- MT5 Strategy Tester uses real tick data and actual EA execution
- Only MT5 Strategy Tester shows true performance with intra-bar logic
- Python simulation cannot replicate the intra-bar event detection

## Workflow

### 1. Compile EA
```python
from mt5_mcp_server import mt5_compile_file
result = mt5_compile_file(r"C:\path\to\EA.mq5")
```

### 2. Run Strategy Tester (via terminal)
```bash
# MT5 Strategy Tester is GUI-based, use terminal for automation
# Or use controller_ea.mq5 for automated testing
```

### 3. Analyze Results
- Check trade count (target: 2-3 trades/day)
- Check win rate (target: 80%+)
- Check profit factor
- Check max drawdown

## MCP Tools Available
- `mt5_connect` - Connect to MT5 terminal
- `mt5_get_market_data` - Fetch historical data for analysis
- `mt5_compile_file` - Compile MQL5 files
- `mt5_backtest_python` - Python simulation (DO NOT USE for validation)

## Common Issues & Fixes

### Issue: Positions opening then immediately closing
**Cause:** EWS filter triggering on entry bar
**Fix:** Remove EWS filter or skip current bar (shift 2-11 instead of 1-10)

### Issue: Too many trades
**Cause:** Impulse detection too sensitive
**Fix:** Increase tier trigger thresholds

### Issue: Low win rate
**Cause:** SL too tight or wrong placement
**Fix:** Adjust SL logic - use tier-based or static SL

## Quick Commands

### Compile and Test
```python
# Compile
mt5_compile_file(r"C:\Users\...\MQL5\Experts\EA.mq5")

# Check .ex5 exists
import os
os.path.exists(r"C:\Users\...\EA.ex5")
```

### Run Multiple Iterations
1. Compile EA
2. Run Strategy Tester in MT5 terminal
3. Note results
4. Adjust parameters
5. Repeat until 80%+ win rate with 2-3 trades/day