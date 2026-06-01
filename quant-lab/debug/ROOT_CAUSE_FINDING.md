# XAUUSD Trade Count Discrepancy - Root Cause Analysis

## Problem
- Nautilus: 1,718 trades
- Python runner: 604 trades
- Ratio: 2.84x difference

## Root Cause
The Python runner (`SymmetryTrapBacktest.run()`) groups bars by EST date, but the Asian session (7PM-3AM EST) spans TWO EST dates:
- 7PM-11PM EST on day N (belongs to EST date N, UTC midnight = 7PM EST)
- 12AM-3AM EST on day N+1 (belongs to EST date N+1)

When the Python runner groups by EST date, it only gets the 12AM-3AM portion for day N+1, missing the 7PM-11PM portion from day N.

### Evidence
For EST date 2022-01-19:
- Python runner Asian range: 119.8 pips (only 12AM-3AM EST bars)
- Nautilus-style Asian range: 330.7 pips (includes 7PM-11PM EST 01-18 + 12AM-3AM EST 01-19)
- Difference: 210.9 pips

### Session Count Impact
- Python runner: 316 active sessions, 1046 NO-GO sessions
- Nautilus-style: 735 active sessions, 384 NO-GO sessions

The Python runner skips days with incomplete Asian ranges (no bars at 7PM EST), while the Nautilus strategy accumulates Asian range across day boundaries.

## Fix Required
The Python runner needs to accumulate Asian range across day boundaries, similar to how the Nautilus strategy does it in `on_bar()`:

```python
# Current (WRONG): Groups by EST date, misses 7PM-11PM portion
days = {}
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=self.est_offset)
    dk = est_dt.strftime("%Y-%m-%d")  # This splits Asian session!
    days[dk].append(bar)

# Fix: Track Asian range sequentially, don't split across day boundaries
# OR: Pre-compute Asian range by finding all bars that belong to each session
```

## Recommendation
Modify `SymmetryTrapBacktest.run()` to:
1. Process bars sequentially (not pre-grouped)
2. Track Asian range on-the-fly across day boundaries
3. Initialize session at 3AM EST when `asian_locked` is False
4. Reset state on new EST day, but preserve accumulated Asian range until 3AM