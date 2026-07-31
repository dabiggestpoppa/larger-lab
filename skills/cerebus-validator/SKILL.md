# Cerebus Setup Validator Skill

## Purpose
Validates that the CEREBUS live engine is firing on all valid setups and that signals are being executed correctly on MT5. Run this anytime you want to check:
1. Did the engine miss any valid setups today?
2. Are signals being executed on MT5?
3. What's today's P&L and open positions?

## Usage
```
Run the validator: `python quant-lab/mt5/validator_report.py`
```

Or ask: "Validate today's setups" or "Did the engine miss any trades?"

## What It Does
1. Pulls today's live MT5 price data
2. Runs ST + P90 engines bar-by-bar against today's data
3. Compares engine output against actual MT5 trade history
4. Reports: matched signals, missed signals, execution quality

## Output
- Account summary (balance, equity, positions)
- All signals sent today
- All MT5 entries/exits today
- Signal-to-execution match analysis
- Missed setup detection
