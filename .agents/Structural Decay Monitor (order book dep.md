 Structural Decay Monitor (order book depth + funding rate)
❌ Self-Healing Telemetry (slippage → auto-patch config)
❌ Risk Litigator (PROP_TRAILING vs KELLY_MAX toggle)




files : [6/1/2026 1:10 AM] OC2: 3. The Nautilus session init might happen on a DIFFERENT bar than Python's, causing swing_origin to be set at a different price level, which cascades into different impulse/retrace/OCC outcomes

FILES INVESTIGATED

• quant-lab/engines/symmetry_trap.py — Python engine (TRUTH SOURCE)
• quant-lab/strategies/symmetry_trap_strategy.py — Nautilus strategy
• quant-lab/backtests/run_cerebus_backtest_fixed.py — Nautilus runner
[6/1/2026 1:10 AM] OC2: • quant-lab/configs/asset_configs.py — Per-asset configs
• quant-lab/engines/symmetry_trap_backtest.py — Python CSV loader

DIAGNOSTIC SCRIPTS WRITTEN

• tools/diag_xauusd.py — Initial single-session trace
• tools/diag_xauusd2.py — Multi-session comparison
• tools/diag_xauusd3.py — Detailed state machine trace
• tools/diag_compare.py — Full funnel analysis (ran successfully)
• tools/diag_bars.py — Bar count analysis
• tools/diag_sidebyside.py — Side-by-side session trace
• tools/diag_final.py — Full diagnostic (crashed on Unicode, data collected)

───

Passing this to the architect. The key question: what structural difference between Nautilus on_bar + BarDataWrangler vs Python run() + load_m5_csv causes Nautilus to produce 2.84x more trades on XAUUSD specifically?



SYSTEM ARCHITECT RESPONSE INITIATED.
MODULE: XAUUSD DISCREPANCY DEBUG PROTOCOL.
STATUS: CRITICAL DIVERGENCE ISOLATED.
MODE: MECHANICAL / FORENSIC / NON-NEGOTIABLE.

You have done excellent forensic work isolating the logic layers. The logic is identical, which means the divergence is happening at the **data translation layer** or the **unit of measurement layer**. 

When logic is confirmed identical but trade counts diverge by 2.84x on XAUUSD, the culprit is almost always a **Point vs. Pip scaling trap** or a **Timestamp Boundary Shift**. 

Here is the exact debug protocol to isolate and kill the discrepancy.

---

### 🔴 THE SMOKING GUN: THE XAUUSD "POINT vs PIP" UNIT TRAP

Look closely at your diagnostic report and the manual:
*   **Manual:** `XAU/USD | Pip: 1.0 | T1 AR < 32pts | AU: 16pts`
*   **Your Python Config:** `pip_value = 0.1 | ar_max = 32p`

**The Math Divergence:**
If XAUUSD moves from $2030.50 to $2031.50, that is a **$1.00 move**.
*   **Nautilus (Raw Price/Points):** `2031.50 - 2030.50 = 1.0`. It compares `1.0 < 32`. (Threshold = **$32.00**)
*   **Python (Pip Scaled):** `(2031.50 - 2030.50) / 0.1 = 10`. It compares `10 < 32`. (Threshold = **$3.20**)

**The Consequence:**
XAUUSD Asian Ranges routinely hit $10 to $25. 
*   **Python** is rejecting 76.8% of days because it thinks the NO-GO threshold is **$3.20** (32 pips × 0.1).
*   **Nautilus** is accepting those days because it is using raw price points, making the NO-GO threshold **$32.00**.

**ACTION 1: VERIFY NAUTILUS AR CALCULATION**
Check your Nautilus strategy code where it calculates the Asian Range. 
```python
# NAUTILUS CODE CHECK
asian_range = asian_high - asian_low  # THIS IS IN RAW DOLLARS (POINTS)
if asian_range < 32.0:  # THIS MEANS $32.00, NOT 32 PIPS
```
**FIX:** Ensure both engines use the exact same unit. The manual defines XAUUSD `Pip = 1.0`. Change your Python `pip_value` to `1.0` for XAUUSD, OR multiply your Python thresholds by 10. If Python's NO-GO rate drops from 76.8% to ~20%, **you have found the 2.84x multiplier.**

---

### 🟡 HYPOTHESIS 2: THE DENOMINATOR MISMATCH (Active Days)

If the Unit Trap is cleared and the discrepancy remains, we must prove the denominator (Active Trading Days) is identical. Nautilus might be failing to reset the Asian Range at 03:00 EST, causing it to bleed into the London session and artificially inflate/deflate the AR.

**ACTION 2: EXPORT NAUTILUS SESSION FLAGS**
Add a debug logger to the Nautilus strategy that prints the session state at 03:05 EST.
```python
# NAUTILUS DEBUG INJECTION
if current_time.hour == 3 and current_time.minute == 5:
    self.log.info(f"SESSION INIT | Date: {current_time.date()} | AR: {asian_range:.2f} | Tier: {tier} | Status: {status}")
```
**COMPARE:** Export this Nautilus log and your Python `initialize_session()` log to a CSV. 
*   Do they have the exact same number of "ACTIVE" days?
*   Do they flag the exact same days as "NO-GO"?
*   *If Nautilus has 800 active days and Python has 316, the Asian Range calculation window (19:00-03:00) is misaligned in Nautilus.*

---

### 🟡 HYPOTHESIS 3: THE NUMERATOR MISMATCH (Loop Bleed)

You noted Python produces 604 trades across 316 active days (~1.9 trades/day). Nautilus produces 1,718 trades. If Nautilus also has ~316 active days, it is averaging **5.4 trades per day**. Since `max_loops = 5`, this is mathematically impossible unless Nautilus is **bleeding loops across midnight** or failing to reset the loop counter.

**ACTION 3: CHECK NAUTILUS LOOP RESET**
Verify that the Nautilus strategy explicitly resets the loop counter at the session boundary.
```python
# NAUTILUS LOOP RESET CHECK
if is_new_session:
    self.loop_count = 0  # MUST BE ZEROED
    self.state = State.SEARCH
```
If Nautilus uses a continuous state machine that doesn't hard-reset `loop_count` at 03:00 EST, a loop that starts at 02:45 AM might carry over its count into the new day, or conversely, a day that hits 5 loops might not reset, but if the session init fails, it might just keep trading. 
*Actually, if it doesn't reset, it would trade LESS. The danger is if Nautilus counts partial fills or trailing stop adjustments as multiple trades in the trade log.*

---

### 🟡 HYPOTHESIS 4: BAR DATA WRANGLER TIMESTAMP SHIFT

Nautilus `BarDataWrangler` is notorious for timezone assumptions. If your CSV is UTC, and Python explicitly converts to EST, but Nautilus wrangler assumes the CSV is *already* in the exchange timezone (or UTC), the 03:00 EST boundary will shift by 4 or 5 hours.

**ACTION 4: THE 5-BAR ALIGNMENT TEST**
Pick **ONE specific active day** (e.g., the first active day in the dataset).
Print the exact OHLC and Timestamp of the **first 5 bars of the 03:00 EST session** in both engines.

```text
PYTHON BAR 1: 2024-01-15 03:00:00-05:00 | O: 2050.10 | H: 2051.50
NAUTILUS BAR 1: 2024-01-15 08:00:00 UTC | O: 2050.10 | H: 2051.50
```
If the timestamps do not map to the exact same UTC millisecond, the `swing_origin` is being set on a completely different candle. A different `swing_origin` means the 19p/35p/58p impulse thresholds are measured from a different baseline, entirely changing the trade funnel.

---

### ⚙️ EXECUTION DIRECTIVE FOR THE AGENT

Pause all other development. Execute these 4 checks in order:

1.  **Check the XAUUSD Pip/Point Math:** Verify if Nautilus is comparing raw dollars to 32, while Python is comparing pips (divided by 0.1) to 32. **(90% probability this is the culprit).**
2.  **Export Active Day Counts:** Compare the exact number of days that passed the NO-GO filter in both engines.
3.  **Verify Loop Resets:** Ensure Nautilus `loop_count` zeroes out at the session boundary.
4.  **Align the First 5 Bars:** Print the first 5 bars of the first active session in both engines to guarantee `swing_origin` is identical.

The physics are sound. The manual is validated. The discrepancy is a unit-scaling or timestamp-boundary artifact. Isolate the denominator (Active Days) and the unit of measurement (Points vs Pips), and the 2.84x gap will collapse to zero. 

Report back with the Active Day count from Nautilus and the exact XAUUSD AR calculation line from the Nautilus strategy. 🔥