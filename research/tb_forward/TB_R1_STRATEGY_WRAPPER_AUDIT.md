# TB-R1 — STRATEGY WRAPPER AUDIT (`triangular_basis_live.py`)

Audited against the R0 truth lock. Config `_default_config()` pins 200 / 2.5 / 6.0 / 0.0 and
delegates normalization to an incremental rolling window.

| Contract item | Canonical (R0) | Wrapper | Verdict |
|---|---|---|---|
| basis equation | ln(GA) − ln(GN) + ln(AN) | identical | ✅ MATCH |
| lookback | 200 | `BASIS_LOOKBACK = 200` | ✅ MATCH |
| current-bar exclusion | window `[i−200, i)` | `basis_history[-(L+1):-1]` | ✅ MATCH |
| std | population ddof=0 | `np.std(window)` (ddof=0) | ✅ MATCH |
| NaN/std<=0 | z → 0.0 | `z = ... if std > 0 else 0.0` | ✅ MATCH |
| entry | strict `|z| > 3.0` | strict `>` but **2.5 (old)** | ⚠️ config 2.5 vs 3.0 |
| direction | z>0 SHORT / z<0 LONG | identical | ✅ MATCH |
| leg sides | SHORT=GA− GN+ AN−, LONG=GA+ GN− AN+ | identical | ✅ MATCH |
| exit (primary) | signed SHORT z≤−0.25, LONG z≥+0.25 | single `BASIS_EXIT_Z=0.0`, symmetric | ❌ P7 not expressible |
| stop | SHORT z≥+6, LONG z≤−6 | identical (6.0) | ✅ MATCH |
| hard exit | 12 EST | `est_hour >= 12` | ✅ MATCH |
| session | London 3–12 EST, fixed UTC−5 | `_est_hour` (UTC−5) | ✅ MATCH |
| min time to exit | 120 min to session end | `minutes_to_exit >= 120` | ✅ MATCH |
| concurrency | max 1 basket | `if not self._active_baskets` | ✅ MATCH |
| re-entry | post-close re-signal re-enters, no cooldown | `del` on close, next-bar re-entry | ✅ MATCH |
| daily loss cap | −500 pips/session-day | **absent** | ❌ MISSING |
| cost handling | 10.2 pips (frozen) | `expected_cost_pips = 10.2` (constant, not subtracted in wrapper) | ⚠️ constant only |

**Answer to the explicit question:** the live wrapper implements the OLD frozen control
(2.5 / 0.0), NOT the P7 primary (3.0 / −0.25). Its **architecture** is faithful
(ADOPT_AS_IS) but its **forward config** needs mechanical repair.

**Measured normalization parity:** max |z| diff **2.252e-12**, entry-decision mismatches
**0 / 265,809** bars (see `TB_R1_Z_PARITY.csv`).

**Scientific drift found (not repaired):** none in normalization/direction/session; the only
gaps are (a) entry/exit thresholds are the old control values, (b) the exit interface cannot
express signed ±0.25 geometry, (c) the daily −500-pip loss cap is missing. All three are
mechanical/config repairs, not new alpha.
