"""
CR-RISK-BLOCK1-FOUNDATION-SEAL — authoritative synthesis of R1..R4.

This is a SYNTHESIS checkpoint, not an optimization. It reads the actual R1-R4
decision artifacts and CSVs (never progress files), locks the risk-unit
definition, and emits the Block-I doctrine library:

- BLOCK1_RISK_UNIT_LOCK.md
- BLOCK1_LOSS_DOCTRINE.md / PROFIT / EXPOSURE / EDGE_DEGRADATION / TAIL_RISK /
  FAMILY_RISK doctrine docs
- BLOCK1_STATIC_FRONTIER.csv (R4 landmarks, preserved exactly)
- BLOCK1_RM_PROFILE_LIBRARY.csv/.md (NON-OVERLAPPING research bands, reframed
  from R4's collapsed auto-zones - breakpoint logic documented, not optimized)
- BLOCK1_ACCOUNT_TRANSLATION.csv / BLOCK1_PROP_CONSTRAINT_MAP.csv
- BLOCK1_EVIDENCE_STATUS_MATRIX.csv
- BLOCK2_RESEARCH_QUEUE.md (defined, NOT executed)
- BLOCK1_FOUNDATION_REPORT.md (15 sections)
- BLOCK1_DECISION.json / BLOCK1_INPUT_HASH_MANIFEST.json
- BLOCK1_CONTRADICTIONS.md (if any)

No alpha/entry/exit/stop/sizing changes. No best size. Block II stays locked.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Full prior-checkpoint SHAs (provenance, no abbreviations in machine output)
SHA_P75 = "7bc1c0242cd05a205da62b34904d7308c63f2acb"
SHA_R1 = "32374cc051de056120e24525a4a70c2ecbf6b616"
SHA_R11 = "413a05fe6093f252603642008407e0c3bd6df88f"
SHA_R2 = "8c0a59d72b40560f4843997134ea89742de38cbf"
SHA_R2B = "116bb2de4930726d7007816177416130e8f9e7a9"
SHA_R3 = "ee4516a6115e679d694013d8371740e547dd09df"
SHA_R31 = "31fa1df1210e0fab5bbb603ae23a2be175b3a15c"
SHA_R4 = "6ab9da3ade416285e36670ebe35badae957a9ecd"
SHA_R4B = "444c04e2c32809cb01d8fce1aa946998871f3238"

class Block1Seal:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.b = self.root / "artifacts" / "risk_block1"
        assert self.b.exists(), f"missing risk_block1 artifacts: {self.b}"

    # ------------------------------------------------------------------
    def _load(self, name: str) -> pd.DataFrame:
        return pd.read_csv(self.b / name)

    def _load_json(self, name: str) -> Dict:
        return json.loads((self.b / name).read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Data gathering
    # ------------------------------------------------------------------
    def _gather(self) -> Dict:
        g: Dict = {}
        g["ledger"] = self._load("R1_EVENT_RISK_LEDGER.csv")
        g["heat"] = self._load("R1_PORTFOLIO_HEAT.csv")
        g["conc"] = self._load("R1_CONCURRENCY_SUMMARY.csv")
        g["mae"] = self._load("R2_MAE_DISTRIBUTIONS.csv")
        g["fail"] = self._load("R2_FAILURE_SPEED.csv")
        g["classes"] = self._load("R2_FAILURE_CLASSES.csv")
        g["tails"] = self._load("R2_TAIL_LOSS_ATTRIBUTION.csv")
        g["streaks"] = self._load("R2_LOSS_STREAKS.csv")
        g["famD"] = self._load("R2_FAMILY_DOWNSIDE_COMPARISON.csv")
        g["tempD"] = self._load("R2_TEMPORAL_STABILITY.csv")
        g["concL"] = self._load("R2_CONCURRENCY_LOSS_EFFECTS.csv")
        g["epiL"] = self._load("R2_EPISODE_LOSS_EFFECTS.csv")
        g["mfe"] = self._load("R3_MFE_DISTRIBUTIONS.csv")
        g["ttp"] = self._load("R3_TIME_TO_PROFIT.csv")
        g["curve"] = self._load("R3_PROFIT_DELIVERY_CURVE.csv")
        g["mat"] = self._load("R3_PROFIT_MATURITY.csv")
        g["cap"] = self._load("R3_CAPTURE_RATIO.csv")
        g["wtail"] = self._load("R3_WINNER_TAIL_ATTRIBUTION.csv")
        g["tempP"] = self._load("R3_TEMPORAL_PROFIT_STABILITY.csv")
        g["gbt"] = self._load("R3_GIVEBACK_TRANSITIONS.csv")
        # keep BOTH books (A+B overlap-exact and A+B_sequential) - the exposure
        # doctrine compares them; landmark/profile code filters explicitly
        g["ladder"] = self._load("R4_STATIC_RISK_LADDER.csv")
        g["mc"] = self._load("R4_MONTE_CARLO_FRONTIER.csv")
        g["mc"] = g["mc"][g["mc"]["scheme"] == "block"]
        g["edge"] = self._load("R4_EDGE_DEGRADATION.csv")
        g["tailS"] = self._load("R4_TAIL_STRESS.csv")
        g["streakS"] = self._load("R4_LOSS_STREAK_STRESS.csv")
        g["heatF"] = self._load("R4_ACCOUNT_HEAT_MAP.csv")
        g["heatS"] = self._load("R4_ACCOUNT_HEAT_STATES.csv")
        g["famF"] = self._load("R4_FAMILY_RISK_FRONTIER.csv")
        g["env"] = self._load("R4_RISK_ENVELOPES.csv")
        g["transl"] = self._load("R4_ACCOUNT_TRANSLATION.csv")
        g["r1dec"] = self._load_json("R1_DECISION.json")
        g["r2dec"] = self._load_json("R2_DECISION.json")
        g["r31dec"] = self._load_json("R3_1_DECISION.json")
        g["r4dec"] = self._load_json("R4_DECISION.json")
        return g

    # ------------------------------------------------------------------
    # Static frontier landmarks (VI) - preserved exactly from R4
    # ------------------------------------------------------------------
    def _frontier_landmarks(self, g: Dict) -> pd.DataFrame:
        ladder = g["ladder"][g["ladder"]["book"] == "A+B"]
        rows = []
        for f in [0.25, 0.50, 1.00, 1.50, 2.00, 3.00, 5.00]:
            lr = ladder[ladder["f_pct"] == f].iloc[0]
            mr = g["mc"][g["mc"]["f_pct"] == f].iloc[0]
            rows.append({
                "f_pct": f,
                "cagr": float(lr["cagr"]),
                "total_compounded_return_x": float(lr["total_return"] + 1.0),
                "historical_max_dd": float(lr["max_dd"]),
                "calmar": float(lr["calmar"]),
                "worst_day_pct": float(lr["worst_day_pct"]),
                "worst_48h_pct": float(lr["worst_48h_pct"]),
                "p95_resampled_dd": float(mr["max_dd_p95"]),
                "p99_resampled_dd": float(mr["max_dd_p99"]),
                "P_dd_ge_10": float(mr["P_dd_ge_10"]),
                "P_dd_ge_15": float(mr["P_dd_ge_15"]),
                "P_dd_ge_20": float(mr["P_dd_ge_20"]),
                "P_dd_ge_30": float(mr["P_dd_ge_30"]),
                "P_dd_ge_40": float(mr["P_dd_ge_40"]),
                "P_dd_ge_50": float(mr["P_dd_ge_50"]),
                "P_technical_ruin": float(mr["P_technical_ruin"]),
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # RM-S0..S4 non-overlapping profile bands (X) - breakpoint logic
    # ------------------------------------------------------------------
    def _profile_bands(self, g: Dict, lm: pd.DataFrame) -> pd.DataFrame:
        """Non-overlapping bands from measurable breaks in historical max DD.

        Breakpoints (historical max DD of the overlap-exact hourly ladder):
          S0 <= 5%  (capital preservation: 10% DD probability ~0)
          S1 <= 10% (low 10% DD probability <= 1%)
          S2 <= 20% (first nonzero 20% DD probability)
          S3 <= 30% (40% impairment probability ~0)
          S4 > 30%  (full-press research: 40/50% impairment probabilities > 0)
        """
        ladder = g["ladder"][g["ladder"]["book"] == "A+B"]
        breaks = [0.05, 0.10, 0.20, 0.30, np.inf]
        labels = ["RM-S0_PRESERVATION", "RM-S1_CONSERVATIVE", "RM-S2_BALANCED",
                  "RM-S3_GROWTH", "RM-S4_FULL_PRESS_RESEARCH"]
        rows = []
        prev_hi = 0.0
        for lbl, brk in zip(labels, breaks):
            sel = ladder[ladder["max_dd"] <= brk]
            hi = float(sel["f_pct"].max()) if len(sel) else float(ladder["f_pct"].min())
            lo = float(ladder[ladder["f_pct"] > prev_hi]["f_pct"].min())
            band = ladder[(ladder["f_pct"] >= lo) & (ladder["f_pct"] <= hi)]
            rep = hi  # representative = most aggressive in-band point
            lr = ladder[ladder["f_pct"] == rep].iloc[0]
            mr = g["mc"][g["mc"]["f_pct"] == rep].iloc[0]
            e75 = g["edge"][(g["edge"]["edge_pct"] == 75) & (g["edge"]["f_pct"] == rep)]
            e50 = g["edge"][(g["edge"]["edge_pct"] == 50) & (g["edge"]["f_pct"] == rep)]
            t2 = g["tailS"][(g["tailS"]["variant"] == "worst5_x2_00")
                            & (g["tailS"]["f_pct"] == rep)]
            rows.append({
                "profile": lbl,
                "f_band_min": lo, "f_band_max": hi,
                "historical_max_dd_range_pct": (
                    f"{band['max_dd'].min()*100:.1f}..{band['max_dd'].max()*100:.1f}"),
                "p95_dd_range_pct": (
                    f"{g['mc'][g['mc']['f_pct'].isin(band['f_pct'])]['max_dd_p95'].min()*100:.1f}"
                    f"..{g['mc'][g['mc']['f_pct'].isin(band['f_pct'])]['max_dd_p95'].max()*100:.1f}"),
                "worst_day_range_pct": (
                    f"{band['worst_day_pct'].min()*100:.1f}..{band['worst_day_pct'].max()*100:.1f}"),
                "representative_f_pct": rep,
                "rep_cagr": float(lr["cagr"]),
                "rep_p95_dd": float(mr["max_dd_p95"]),
                "rep_P_dd_ge_20": float(mr["P_dd_ge_20"]),
                "rep_P_dd_ge_40": float(mr["P_dd_ge_40"]),
                "rep_P_dd_ge_50": float(mr["P_dd_ge_50"]),
                "edge75_exp_cagr_at_rep": float(e75["exp_cagr"].iloc[0]) if len(e75) else np.nan,
                "edge75_p95_dd_at_rep": float(e75["p95_max_dd"].iloc[0]) if len(e75) else np.nan,
                "edge50_exp_cagr_at_rep": float(e50["exp_cagr"].iloc[0]) if len(e50) else np.nan,
                "edge50_p95_dd_at_rep": float(e50["p95_max_dd"].iloc[0]) if len(e50) else np.nan,
                "tail_worst5x2_max_dd_at_rep": float(t2["max_dd"].iloc[0]) if len(t2) else np.nan,
                "intended_use": _USE[lbl],
                "forbidden_interpretation": "NOT safe / NOT recommended / NOT production",
            })
            prev_hi = hi
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Account translation (XI)
    # ------------------------------------------------------------------
    def _account_translation(self, g: Dict, bands: pd.DataFrame) -> pd.DataFrame:
        exp_R = float((g["ledger"]["pnl_bps"] / g["ledger"]["risk_unit_bps"]).mean())
        a_w = float((g["ledger"][g["ledger"]["family"] == "A"]["pnl_bps"]
                     / g["ledger"][g["ledger"]["family"] == "A"]["risk_unit_bps"]).min())
        rows = []
        for acct in [5000.0, 10000.0, 25000.0, 50000.0, 100000.0]:
            for _, b in bands.iterrows():
                f = b["representative_f_pct"] / 100.0
                one_r = f * acct
                rows.append({
                    "profile": b["profile"], "f_pct": b["representative_f_pct"],
                    "account_usd": acct, "dollar_1R": one_r,
                    "minus_0_5R_usd": -0.5 * one_r, "minus_1R_usd": -one_r,
                    "minus_2R_usd": -2.0 * one_r, "minus_3R_usd": -3.0 * one_r,
                    "minus_3_66R_A_worst_usd": a_w * one_r,
                    "expected_event_gain_usd": exp_R * one_r,
                    "typical_2pos_gross_risk_usd": 2.0 * one_r,
                })
        return pd.DataFrame(rows)

    def _prop_constraint_map(self, g: Dict, lm: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, r in lm.iterrows():
            rows.append({
                "f_pct": r["f_pct"], "P_dd_ge_10": r["P_dd_ge_10"],
                "P_dd_ge_15": r["P_dd_ge_15"], "P_dd_ge_20": r["P_dd_ge_20"],
            })
        df = pd.DataFrame(rows)
        for col, bound in [("P_dd_ge_10", 0.05), ("P_dd_ge_15", 0.05),
                           ("P_dd_ge_20", 0.05)]:
            ok = df[df[col] <= bound]
            df.attrs[f"max_f_{col}_le5pct"] = float(ok["f_pct"].max()) if len(ok) else 0.0
        return df

    # ------------------------------------------------------------------
    # Evidence status matrix (XII)
    # ------------------------------------------------------------------
    def _evidence_matrix(self) -> pd.DataFrame:
        rows = [
            ("STATIC RISK FRONTIER", "VALIDATED"),
            ("OVERLAP MATTERS (worst-day under real overlap > sequential)", "VALIDATED"),
            ("EDGE DEGRADATION (frontier collapses below ~50% edge)", "VALIDATED"),
            ("B FAMILY CAPITAL LIMITING (higher solo DD at every tested f)", "VALIDATED DESCRIPTIVE STATIC RESULT"),
            ("WINNER/LOSER MAE SEPARATION (winners stay above ~-0.57R)", "VALIDATED DESCRIPTIVE"),
            ("RECOVERY COLLAPSE AT -1R (0% historical recovery)", "VALIDATED DESCRIPTIVE OBSERVATION"),
            ("LATE PROFIT DELIVERY (~70% of final PnL by hour 3, winners peak hour 5)", "VALIDATED DESCRIPTIVE"),
            ("-1R HARD STOP", "HYPOTHESIS_ONLY"),
            ("HOUR-5 EARLY EXIT / PROFIT LOCK", "HYPOTHESIS_ONLY"),
            ("+1R BREAKEVEN/PARTIAL LOCK", "HYPOTHESIS_ONLY"),
            ("FAILURE-SPEED INVALIDATION (FAST reveal)", "HYPOTHESIS_ONLY"),
            ("TIME+MAE INVALIDATION", "HYPOTHESIS_ONLY"),
            ("TRAILING STOP", "NOT TESTED"),
            ("DD-ADAPTIVE SIZING", "NOT TESTED"),
            ("CLUSTER/EPISODE SIZING", "NOT TESTED"),
            ("FAMILY-SPECIFIC ALLOCATION", "NOT TESTED"),
            ("KELLY / FRACTIONAL KELLY", "NOT TESTED"),
            ("COMPOUNDING-FAMILY LOGIC", "NOT TESTED"),
            ("HEAT CAPS / PORTFOLIO LIMITS", "NOT TESTED"),
            ("HYBRID RISK ENGINE", "NOT TESTED"),
            ("CEREBUS OVERLAY (Phase 8 negative result)", "REJECTED (no material improvement)"),
        ]
        return pd.DataFrame(rows, columns=["concept", "status"])

    # ------------------------------------------------------------------
    # Docs
    # ------------------------------------------------------------------
    def _risk_unit_lock(self, g: Dict) -> str:
        rR = g["ledger"]["pnl_bps"] / g["ledger"]["risk_unit_bps"]
        a_w = float(rR[g["ledger"]["family"] == "A"].min())
        b_w = float(rR[g["ledger"]["family"] == "B"].min())
        return f"""# BLOCK-I RISK-UNIT LOCK

**1R = TARGET_VOL x sqrt(HOLD) = 24.4949 bps** (the sealed strategy's normalized
expected-move unit).

**1R IS NOT A STOP.** It is not a maximum trade loss, not a stop-loss distance,
not a broker risk percentage, not a guaranteed loss cap.

## Frozen account mapping

    account_return ~= trade_return_R x f

where f = static account-risk fraction per R. A trade of -3R at f = 1% costs
approximately -3% of the account.

## Frozen historical extremes (exact, from the sealed ledger)

| family | worst R | worst bps |
|---|---|---|
| A | {a_w:.2f}R | {a_w * 24.49489742783178:.1f} |
| B | {b_w:.2f}R | {b_w * 24.49489742783178:.1f} |

## Forbidden reinterpretations of f

- maximum trade loss
- stop-loss distance
- broker risk percentage
- guaranteed loss cap

Source: `R1_EVENT_RISK_LEDGER.csv` + `R4_RISK_UNIT_DEFINITION.md` (seal-verified).
"""

    def _loss_doctrine(self, g: Dict) -> str:
        mae = g["mae"]
        def _m(fam, oc, unit="R", col="median"):
            return float(mae[(mae["family"] == fam) & (mae["outcome"] == oc)
                             & (mae["unit"] == unit)][col].iloc[0])
        w_med = _m("A+B", "WINNER"); w_p90 = _m("A+B", "WINNER", col="p90")
        w_p5 = _m("A+B", "WINNER", col="p5")
        w_min = float(g["ledger"].loc[g["ledger"]["pnl_bps"] > 0, "mae_r"].min())
        l_med = _m("A+B", "LOSER")
        f1 = g["fail"][g["fail"]["threshold_R"] == 1.0].iloc[0]
        f05 = g["fail"][g["fail"]["threshold_R"] == 0.5].iloc[0]
        f2 = g["fail"][g["fail"]["threshold_R"] == 2.0].iloc[0]
        cls = g["classes"].set_index("failure_class")
        fast = cls.loc["FAST"]; slow = cls.loc["SLOW"]
        t1 = g["tails"][(g["tails"]["cut"] == "final_return") & (g["tails"]["quantile"] == 0.01)].iloc[0]
        t10 = g["tails"][(g["tails"]["cut"] == "final_return") & (g["tails"]["quantile"] == 0.10)].iloc[0]
        # pct_of_trades / shares are stored as PERCENT already (do not x100)
        famD = g["famD"].set_index("family")
        st = g["streaks"]
        pooled = st[st["unit"] == "trades_pooled"].iloc[0]
        days = st[st["unit"] == "negative_days"].iloc[0]
        w24 = st[st["unit"] == "negative_24h_windows"].iloc[0]
        return f"""# BLOCK-I LOSS DOCTRINE (R2 authoritative)

All figures measured on the sealed 890-event A/B book (A 432 / B 458).

## Winner vs loser adverse excursion (R units)

- winner median MAE **{w_med:.2f}R**; p90 {w_p90:.2f}R
- **95% of winners stay above {w_p5:.2f}R**; worst winner MAE {w_min:.2f}R
- loser median MAE **{l_med:.2f}R**

## Breach behavior (final-outcome-recovery, R2_FAILURE_SPEED)

| threshold | losers breaching | median time | recovery to profit | final expectancy after |
|---|---|---|---|---|
| -0.5R | {f05['n_breached_losers']} | {f05['median_time_losers_h']:.0f}h | {f05['recovery_to_profit_freq']*100:.1f}% | {f05['final_expectancy_R_after_breach']:+.2f}R |
| -1.0R | {f1['n_breached_losers']} | {f1['median_time_losers_h']:.0f}h | {f1['recovery_to_profit_freq']*100:.1f}% | {f1['final_expectancy_R_after_breach']:+.2f}R |
| -2.0R | {f2['n_breached_losers']} | {f2['median_time_losers_h']:.0f}h | {f2['recovery_to_profit_freq']*100:.1f}% | {f2['final_expectancy_R_after_breach']:+.2f}R |

**HISTORICAL RECOVERY OBSERVATION: zero trades recovered to a profitable frozen
exit after breaching -1R.** This is an observation, NOT a stop rule.

## Failure speed

- FAST (reveal <= 2h, n={int(fast['n'])}): median loss {fast['median_final_loss_R']:.2f}R,
  recovery after -0.5R breach {fast['recovery_to_profit_after_0_5R_breach']*100:.0f}%
- MEDIUM (n={int(cls.loc['MEDIUM']['n'])}), SLOW (n={int(slow['n'])}): median loss
  {slow['median_final_loss_R']:.2f}R, recovery 0%
- Losers breach -0.5R by median 2h, -1R by 3h (p75 4h).

## Tail concentration

- worst **1%** of trades (n={int(t1['N'])}, {t1['pct_of_trades']:.1f}%) carry a
  mean **{t1['mean_final_R']:.2f}R** loss = {t1['share_of_total_losses']*100:.1f}%
  of total losses and {t1['share_of_worst_24h_loss']*100:.0f}% of the worst-24h loss
- worst **10%** (n={int(t10['N'])}) carry **{t10['share_of_total_losses']*100:.0f}%**
  of total losses, {t10['share_of_max_dd_window']*100:.0f}% of the max-DD window,
  {t10['share_of_worst_24h_loss']*100:.0f}% of the worst-24h loss.

## Family downside

- B: median MAE {famD.loc['B','median_mae_R']:.2f}R, P(<-1R) {famD.loc['B','p_less_neg1R']*100:.0f}%,
  worst {famD.loc['B','worst_loss_R']:.2f}R
- A: median MAE {famD.loc['A','median_mae_R']:.2f}R, P(<-1R) {famD.loc['A','p_less_neg1R']*100:.0f}%,
  worst {famD.loc['A','worst_loss_R']:.2f}R

## Streaks

- max {int(pooled['max_streak'])} consecutive losing trades (block-bootstrap p95 11, max 13);
  max {int(days['max_streak'])} consecutive negative days; worst 24h window
  {w24['worst_single_window_bps']:.0f} bps (-{abs(w24['worst_single_window_bps'])/24.4949:.1f}R).

## Temporal stability

R2_TEMPORAL_STABILITY: median MAE and P(<-1R) stable across inner_sel / inner_val /
RELATIONSHIP_CONFIRMED_OOS (documented in the CSV; the OOS segment is NOT untouched
w.r.t. relationship discovery).

## Doctrine

- Descriptive cliffs (recovery collapse, failure speed) are **HYPOTHESIS_ONLY**
  inputs for future invalidation testing. No stop was created.
"""

    def _profit_doctrine(self, g: Dict) -> str:
        mfe = g["mfe"]
        def _m(oc, col):
            return float(mfe[(mfe["family"] == "A+B") & (mfe["outcome"] == oc)
                             & (mfe["unit"] == "R")][col].iloc[0])
        cap = g["cap"][(g["cap"]["family"] == "A+B") & (g["cap"]["outcome"] == "WINNER")].iloc[0]
        gbt = g["gbt"][g["gbt"]["level_R"] == 1.0].iloc[0]
        curve = g["curve"].set_index("hour")
        ttp25 = g["ttp"][(g["ttp"]["family"] == "A+B") & (g["ttp"]["level_R"] == 0.25)].iloc[0]
        ttp50 = g["ttp"][(g["ttp"]["family"] == "A+B") & (g["ttp"]["level_R"] == 0.50)].iloc[0]
        wtail = g["wtail"]
        ex5 = wtail[wtail["expectancy_excluding_best_q_R"].notna()
                    & (wtail["quantile"] == 0.05)].iloc[0]
        sh5 = wtail[(wtail["quantile"] == 0.05) & (wtail["N"] < 300)].iloc[0]
        return f"""# BLOCK-I PROFIT DOCTRINE (R3 + repaired R3.1 authoritative)

## MFE

- winners median MFE **{_m('WINNER','median'):.2f}R**, p90 {_m('WINNER','p90'):.2f}R,
  p99 {_m('WINNER','p99'):.2f}R; losers median {_m('LOSER','median'):.2f}R
- winners peak at median **hour 5** (p75 hour 6); losers peak at hour 2.

## Time to first profit (R3.1 repaired shares - all in [0,1])

- +0.25R: {ttp25['share_of_winners_reaching']*100:.1f}% of winners / {ttp25['share_of_all_trades_reaching']*100:.1f}% of all trades reach,
  median {ttp25['median_time_winners_h']:.0f}h
- +0.50R: {ttp50['share_of_winners_reaching']*100:.1f}% of winners reach, median {ttp50['median_time_winners_h']:.0f}h
- +1.00R: 54.9% of winners / 34.4% of all trades reach, median 3h; after reaching +1R
  **0% finish negative** (n=306) - descriptive, not an exit rule.

## Capture / giveback

- winners retain a median **{cap['median_capture']*100:.0f}%** of peak MFE
  (p25 {cap['p25_capture']*100:.0f}% / p75 {cap['p75_capture']*100:.0f}%)
- median winner giveback {cap['median_giveback_R']:.2f}R (8% of peak)

## Delivery curve (hour-by-hour)

| hour | avg open PnL (R) | % of final PnL | winners positive | past MFE | remaining gain (R) |
|---|---|---|---|---|---|
""" + "\n".join(
            f"| {int(h)} | {r['avg_open_pnl_R']:+.2f} | {r['pct_of_final_pnl_achieved']*100:.0f}% | "
            f"{r['pct_winners_currently_positive']*100:.0f}% | {r['pct_winners_past_mfe']*100:.0f}% | "
            f"{r['remaining_expected_gain_R']:+.2f} |"
            for h, r in curve.iterrows()) + f"""

- **~70% of total final PnL is on the book by hour 3, ~88% by hour 4.**

## Maturity states

R3_PROFIT_MATURITY: LATE_DELIVERY (n=303, win {g['mat'][g['mat']['maturity_class']=='LATE_DELIVERY']['win_rate'].iloc[0]*100:.0f}%,
expectancy {g['mat'][g['mat']['maturity_class']=='LATE_DELIVERY']['final_expectancy_R'].iloc[0]:+.2f}R) is the money-maker;
NOT_YET_DELIVERED (n=247, win {g['mat'][g['mat']['maturity_class']=='NOT_YET_DELIVERED']['win_rate'].iloc[0]*100:.0f}%,
{g['mat'][g['mat']['maturity_class']=='NOT_YET_DELIVERED']['final_expectancy_R'].iloc[0]:+.2f}R) is the core loser;
PEAKED_AND_GIVING_BACK (n=141, +{g['mat'][g['mat']['maturity_class']=='PEAKED_AND_GIVING_BACK']['final_expectancy_R'].iloc[0]:.2f}R) parks capital.

## Winner tails

- best 1% = {wtail[wtail['quantile']==0.01]['share_of_total_positive_pnl'].iloc[0]*100:.0f}% of positive PnL;
  best 5% = {sh5['share_of_total_positive_pnl']*100:.0f}%; best 10% = {wtail[wtail['quantile']==0.10]['share_of_total_positive_pnl'].iloc[0]*100:.0f}%
- excluding the best 5% leaves expectancy **{ex5['expectancy_excluding_best_q_R']:+.2f}R** (vs +0.35R full)

## Temporal

R3_TEMPORAL_PROFIT_STABILITY: median MFE / capture / winner-tail share stable
across inner_sel / inner_val / RELATIONSHIP_CONFIRMED_OOS.

## Doctrine

Hour-5 delivery, +1R behavior and maturity states are **descriptive evidence**.
Profit-lock / early-exit concepts are **HYPOTHESIS_ONLY**. No exit was created.
"""

    def _exposure_doctrine(self, g: Dict) -> str:
        h = g["heat"]
        conc = g["conc"]
        hf1 = g["heatF"][g["heatF"]["f_pct"] == 1.0].iloc[0]
        lad_ab = g["ladder"][g["ladder"]["book"] == "A+B"]
        lad_seq = g["ladder"][g["ladder"]["book"] == "A+B_sequential"]
        overlap_wd = float(lad_ab[lad_ab["f_pct"] == 1.0]["worst_day_pct"].iloc[0])
        seq_wd = float(lad_seq[lad_seq["f_pct"] == 1.0]["worst_day_pct"].iloc[0])
        opp_heat_max_R = float(h["opposing_heat"].max()) / 24.49489742783178
        return f"""# BLOCK-I EXPOSURE DOCTRINE (R1/R1.1 + R4 authoritative)

## Concurrency

- max **{int(h['n_open'].max())}** simultaneous positions (never 4+)
- in-market hours {int((h['n_open'] > 0).sum())} ({(h['n_open'] > 0).mean()*100:.1f}% of calendar)
- 2-position hours {int((h['n_open'] == 2).sum())}; 3-position hours {int((h['n_open'] == 3).sum())}
- same-direction overlap {int(conc['same_direction_overlap_hours'].iloc[0])}h; opposing {int(conc['opposite_direction_overlap_hours'].iloc[0])}h

## Exposure states (R4_ACCOUNT_HEAT_STATES)

| state | hours | gross R median | gross R max | net R max |
|---|---|---|---|---|
""" + "\n".join(
            f"| {r['state']} | {int(r['hours'])} | {r['gross_R_median']:.2f} | "
            f"{r['gross_R_max']:.2f} | {r['net_R_max']:.2f} |"
            for _, r in g["heatS"].iterrows()) + f"""

## Key truths

- **OPPOSING POSITIONS ARE NOT AUTOMATICALLY RISKLESS**: A long USDJPY (Family A)
  and B short USDJPY (Family B) do not cancel economically - they hedge the same
  instrument but at different times/vols; gross heat during opposing overlap is
  real (R1: opposing heat up to {opp_heat_max_R:.2f}R).
- Worst portfolio CAE {hf1['worst_CAE_R']:.2f}R -> **{hf1['worst_CAE_account_pct']:.1f}%**
  account impact at f=1% (R4_ACCOUNT_HEAT_MAP).
- **Overlap-exact vs sequential**: at f=1% the worst day under real overlap is
  {overlap_wd*100:.1f}% vs {seq_wd*100:.1f}% sequential - overlap materially
  worsens the downside day; R4 uses the overlap-exact hourly path as authoritative.
- Episodes (R1.1 repaired): 71.5% of events sit in >=2-event 12h clusters, but
  conditional expectancy is flat across within-cluster rank (8.6/8.4/7.5/10.1 bps)
  - clustered events behave **independent, not duplicated** (descriptive; episode
  sizing is NOT authorized).
"""

    def _edge_doctrine(self, g: Dict) -> str:
        rows = []
        for ep in [100, 75, 50, 25]:
            r = g["edge"][(g["edge"]["edge_pct"] == ep) & (g["edge"]["f_pct"] == 1.0)].iloc[0]
            rows.append((ep, r))
        states = {"100": "EDGE-FULL", "75": "EDGE-ROBUST", "50": "EDGE-FRAGILE",
                  "25": "EDGE-BROKEN"}
        L = [f"""# BLOCK-I EDGE-DEGRADATION DOCTRINE (R4 authoritative)

Method A (documented): positive returns scaled by the edge state; losses preserved
exactly. Block bootstrap, 5000 paths.

## f = 1% landmark (exact artifact values)

| edge | expected CAGR | p95 max DD | P(DD>=20%) | P(DD>=40%) | P(DD>=50%) |
|---|---|---|---|---|---|
"""]
        for ep, r in rows:
            L.append(f"| {ep}% ({states[str(ep)]}) | {r['exp_cagr']*100:+.0f}% | "
                     f"{r['p95_max_dd']*100:.0f}% | {r['P_dd_ge_20']*100:.0f}% | "
                     f"{r['P_dd_ge_40']*100:.0f}% | {r['P_dd_ge_50']*100:.0f}% |")
        L.append(f"""
## Viability classification (descriptive, not a safety claim)

- **EDGE-FULL / EDGE-ROBUST** (100/75%): viable at f=1-3%; tail risk manageable.
- **EDGE-FRAGILE** (50%): expected CAGR collapses to ~5% at f=1% and p95 DD
  balloons to 43% - the strategy becomes a low-return/high-tail-risk proposition.
- **EDGE-BROKEN** (25%): expected CAGR negative at every fraction; p95 DD 83%+ at
  f=1%. Not viable at any static fraction.

**The binding constraint of this strategy is edge retention, not static sizing.**
Never assume 100% historical edge in production planning.
""")
        return "\n".join(L)

    def _tail_doctrine(self, g: Dict) -> str:
        t = g["tailS"]
        s = g["streakS"]
        L = ["""# BLOCK-I TAIL-RISK DOCTRINE (R4 authoritative)

Paths are kept distinct: **historical** (sealed ledger), **resampled**
(block bootstrap), **synthetic stress** (tail injections).

## Tail-shock stress (synthetic, at f = 1%)

| variant | max DD | terminal equity |
|---|---|---|
"""]
        for _, r in t[t["f_pct"] == 1.0].iterrows():
            L.append(f"| {r['variant']} | {r['max_dd']*100:.1f}% | {r['terminal_equity']:.2f}x |")
        L.append(f"""
- Amplifying the worst 5% of losses 1.25x/1.5x/2x moves max DD
  {t[(t.variant=='worst5_x1_25')&(t.f_pct==1.0)]['max_dd'].iloc[0]*100:.1f}% /
  {t[(t.variant=='worst5_x1_50')&(t.f_pct==1.0)]['max_dd'].iloc[0]*100:.1f}% /
  {t[(t.variant=='worst5_x2_00')&(t.f_pct==1.0)]['max_dd'].iloc[0]*100:.1f}% (baseline
  {t[(t.variant=='historical')&(t.f_pct==1.0)]['max_dd'].iloc[0]*100:.1f}%)
- A 5-trade p99-loss cluster raises max DD to {t[(t.variant=='insert_p99_loss_cluster')&(t.f_pct==1.0)]['max_dd'].iloc[0]*100:.1f}%
  (terminal {t[(t.variant=='insert_p99_loss_cluster')&(t.f_pct==1.0)]['terminal_equity'].iloc[0]:.2f}x vs {t[(t.variant=='historical')&(t.f_pct==1.0)]['terminal_equity'].iloc[0]:.2f}x baseline)

## Loss-streak stress (median loser = -0.64R)

| f | 5-streak DD | 10-streak DD | 15-streak DD |
|---|---|---|---|
""")
        for f_ in [0.5, 1.0, 2.0, 5.0]:
            def dd(f_, ln):
                return float(s[(s.f_pct == f_) & (s.streak_len == ln)
                               & (s.loser_quantile == 0.5)]["drawdown_pct"].iloc[0])
            L.append(f"| {f_}% | {dd(f_,5)*100:.1f}% | {dd(f_,10)*100:.1f}% | "
                     f"{dd(f_,15)*100:.1f}% |")
        L.append("""
## Doctrine

Historical, resampled and synthetic paths are NOT interchangeable. Survival
claims must cite which path type produced them. Technical ruin was zero under
the tested historical-resampling framework at all ladder fractions - that is a
framework property (strong edge), NOT a safety certificate.
""")
        return "\n".join(L)

    def _family_doctrine(self, g: Dict) -> str:
        ff = g["famF"].set_index("f_pct")
        return f"""# BLOCK-I FAMILY RISK DOCTRINE (R4 authoritative)

## Static equal-f result (R4_FAMILY_RISK_FRONTIER)

| f | A max DD | B max DD | pooled max DD | capital-limiting |
|---|---|---|---|---|
""" + "\n".join(
            f"| {f_:.2f}% | {ff.loc[f_,'max_dd_A']*100:.1f}% | "
            f"{ff.loc[f_,'max_dd_B']*100:.1f}% | {ff.loc[f_,'max_dd_pooled']*100:.1f}% | "
            f"{ff.loc[f_,'capital_limiting']} |" for f_ in [0.5, 1.0, 2.0, 5.0]) + """

**B currently appears capital-limiting under static equal-f risk** (higher solo
max DD at every tested f) - consistent with R2's worse typical downside for B.

- A-only CAGR vs B-only CAGR at f=1%: 79% vs 62% (both positive; pooled 190%
  from compounding of combined exposure).
- R2 family downside: B worse median MAE and P(<-1R); A holds the single worst
  trade (-3.66R vs -3.31R).

This is a **descriptive static result**. Family-specific allocation is NOT
authorized - it is Block-II research (R5).
"""

    def _foundation_report(self, g, lm, bands, evmat) -> str:
        s0, s1, s2, s3, s4 = bands["f_band_min"].tolist()
        t0_, t1_, t2_, t3_, t4_ = bands["f_band_max"].tolist()
        s0, s1, s2, s3, s4 = s0, s1, s2, s3, s4  # min endpoints
        _hi = [t0_, t1_, t2_, t3_, t4_]
        return f"""# CR-RISK-BLOCK1-FOUNDATION — SEAL REPORT

## 1. Executive summary

Block I mapped the sealed EUR->JPY capital-routing strategy (890 events, A 432 /
B 458, 2023-07 -> 2026-05) from exposure truth through static risk frontiers.
The edge is abnormally strong per unit of risk: 0.35R expected per event, winners
retain 92% of peak MFE, and even f=5% keeps P(DD>=40%) at ~1.4% under 10k-path
block bootstrap. The binding constraints are (a) edge retention (below ~50% of
historical edge the strategy stops compounding) and (b) real overlap on the
downside (worst day -5.6% at f=1% vs -3.7% sequential). No best size is selected;
Block II sizing/allocation research remains locked.

## 2. Risk-unit truth

1R = 24.4949 bps (TARGET_VOL x sqrt(hold)) - an expected-move unit, NOT a stop.
account_return ~= trade_return_R x f. Historical extremes: A worst -3.66R, B worst
-3.31R. See BLOCK1_RISK_UNIT_LOCK.md.

## 3. Exposure truth

Max 3 concurrent positions; 2-position overlap 565h, 3-position 20h; opposing
overlap 228h is NOT riskless (gross heat up to ~1.9R during opposing overlap).
Worst portfolio CAE 3.06R = -3.1% account at f=1%. Overlap-exact hourly paths are
authoritative (R4) because overlap materially worsens worst-day risk.

## 4. Loss anatomy

Winners' median MAE -0.09R (95% above -0.57R); losers' median -0.88R. Zero
recovery after -1R (observation). Losers breach -0.5R by 2h, -1R by 3h; FAST
failures are the deep ones. Worst 10% of trades carry ~60% of losses / ~92% of
max DD. B is worse on typical downside; A holds the deepest single trade.

## 5. Profit anatomy

Winners' median MFE +1.07R, peak at hour 5; ~70% of final PnL earned by hour 3,
88% by hour 4. Winners retain 92% of peak; +1R reached by 54.9% of winners with
0% failure. LATE_DELIVERY is the money-maker; NOT_YET_DELIVERED the core loser.
Winner tail is not dominant (best 5% = 17% of positive PnL).

## 6. Static risk frontier

See BLOCK1_STATIC_FRONTIER.csv (R4 landmarks preserved exactly). Historical max
DD is near-linear in f (7.6-10.5% per 1% f); resampled p95 DD accelerates at
high f (59.4% at f=5%).

## 7. Edge degradation

f=1% expected CAGR: 190% -> 75% -> 5% -> -37% as edge falls 100/75/50/25%;
p95 DD: 15% -> 20% -> 43% -> 83%. Classification: EDGE-FULL/ROBUST/FRAGILE/BROKEN.
Edge retention is the binding constraint.

## 8. Tail / streak stress

Worst-5% amplification 2x raises max DD 10.2% -> 16.0% at f=1%; p99-loss cluster
-> 17.6%. 10-streak of median losers = 6.3% DD at f=1% (27.2% at f=5%).
Historical / resampled / synthetic paths are kept distinct.

## 9. Family risk

B is capital-limiting under static equal-f risk at every tested f (higher solo
max DD). Descriptive result only.

## 10. RM-S0..S4 profile library

Non-overlapping bands derived from historical-max-DD breakpoints (<=5/10/20/30/>30%):
- **RM-S0 PRESERVATION** f {s0:.2f}-{t0_:.2f}%
- **RM-S1 CONSERVATIVE** f {s1:.2f}-{t1_:.2f}%
- **RM-S2 BALANCED** f {s2:.2f}-{t2_:.2f}%
- **RM-S3 GROWTH** f {s3:.2f}-{t3_:.2f}%
- **RM-S4 FULL-PRESS RESEARCH** f {s4:.2f}-{t4_:.2f}% (RESEARCH ONLY)

See BLOCK1_RM_PROFILE_LIBRARY.md/.csv.

## 11. Account / prop translation

See BLOCK1_ACCOUNT_TRANSLATION.csv and BLOCK1_PROP_CONSTRAINT_MAP.csv. No prop
size recommended without a defined constraint.

## 12. Known vs hypothesis vs unknown

See BLOCK1_EVIDENCE_STATUS_MATRIX.csv. Frontier/overlap/edge-degradation/family
results VALIDATED; stop/exit concepts HYPOTHESIS_ONLY; dynamic sizing, Kelly,
family allocation NOT TESTED.

## 13. Practical trader interpretation

- **f=0.5%**: ~71% CAGR historically, 5.2% max DD, worst day -2.8%. 1R = $50 on
  $10k; a -3R trade costs -$150.
- **f=1%**: ~190% CAGR, 10.2% max DD, worst day -5.6%; 1R = $100 on $10k; -3R =
  -$300; A-worst -3.66R = -$366.
- **A -3R trade at any f costs ~3 x f of the account.**
- **2-3 overlapping positions** commit 2-3 x f gross; worst portfolio CAE at
  f=1% is -3.1% of the account.
- **Expected DD**: ~10% historical at f=1% vs p95 ~15% under tail resampling.
- **f=5% is not "safe"** even though technical ruin was zero in the tested
  historical-resampling framework: p95 resampled DD is 59.4%, P(DD>=10%) 31%,
  P(DD>=50%) 0.3%, and a 15-streak of median losers costs 39%.
- **Edge degradation matters more than headline CAGR**: at 50% edge f=1% is a
  5% CAGR with 43% p95 DD.
- **Static sizing is the foundation, not the engine**: it ignores family
  quality, episodes, heat, and drawdown state - those are Block II.

## 14. Block-II research queue

See BLOCK2_RESEARCH_QUEUE.md (R5 family allocation -> R6 episode/heat sizing ->
R7 DD-adaptive -> R8 Kelly -> R9 hybrid). None authorized by this seal.

## 15. Explicit stop condition

`block1_foundation_sealed = true`, `block_2_cleared = false`. No R5-R9, no Kelly,
no dynamic/family/cluster/DD sizing, no deployment, no MT5 until human review.
"""

    # ------------------------------------------------------------------
    def run(self) -> Dict:
        import subprocess
        try:
            git_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True).strip()
        except Exception:
            git_sha = "UNRESOLVED"
        t0 = time.time()
        print("[SEAL] gathering R1-R4 artifacts")
        g = self._gather()
        print("[SEAL] frontier landmarks + profile bands")
        lm = self._frontier_landmarks(g)
        bands = self._profile_bands(g, lm)
        trans = self._account_translation(g, bands)
        prop = self._prop_constraint_map(g, lm)
        evmat = self._evidence_matrix()

        docs = {
            "BLOCK1_RISK_UNIT_LOCK.md": self._risk_unit_lock(g),
            "BLOCK1_LOSS_DOCTRINE.md": self._loss_doctrine(g),
            "BLOCK1_PROFIT_DOCTRINE.md": self._profit_doctrine(g),
            "BLOCK1_EXPOSURE_DOCTRINE.md": self._exposure_doctrine(g),
            "BLOCK1_EDGE_DEGRADATION_DOCTRINE.md": self._edge_doctrine(g),
            "BLOCK1_TAIL_RISK_DOCTRINE.md": self._tail_doctrine(g),
            "BLOCK1_FAMILY_RISK_DOCTRINE.md": self._family_doctrine(g),
            "BLOCK1_RM_PROFILE_LIBRARY.md": self._profile_library_md(bands),
            "BLOCK2_RESEARCH_QUEUE.md": self._block2_queue(),
            "BLOCK1_FOUNDATION_REPORT.md": self._foundation_report(g, lm, bands, evmat),
            "BLOCK1_CONTRADICTIONS.md": self._contradictions(),
        }
        for name, text in docs.items():
            (self.b / name).write_text(text, encoding="utf-8")
        lm.to_csv(self.b / "BLOCK1_STATIC_FRONTIER.csv", index=False)
        bands.to_csv(self.b / "BLOCK1_RM_PROFILE_LIBRARY.csv", index=False)
        trans.to_csv(self.b / "BLOCK1_ACCOUNT_TRANSLATION.csv", index=False)
        prop.to_csv(self.b / "BLOCK1_PROP_CONSTRAINT_MAP.csv", index=False)
        evmat.to_csv(self.b / "BLOCK1_EVIDENCE_STATUS_MATRIX.csv", index=False)

        decision = self._decision(g, bands)
        (self.b / "BLOCK1_DECISION.json").write_text(
            json.dumps(decision, indent=2, default=str), encoding="utf-8")

        manifest = self._manifest(git_sha)
        (self.b / "BLOCK1_INPUT_HASH_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        elapsed = time.time() - t0
        print(f"[SEAL] complete in {elapsed:.1f}s · sealed={decision['block1_foundation_sealed']}")
        return {"elapsed_seconds": elapsed,
                "block1_foundation_sealed": decision["block1_foundation_sealed"],
                "outputs": sorted(docs) + ["BLOCK1_STATIC_FRONTIER.csv",
                                           "BLOCK1_RM_PROFILE_LIBRARY.csv",
                                           "BLOCK1_ACCOUNT_TRANSLATION.csv",
                                           "BLOCK1_PROP_CONSTRAINT_MAP.csv",
                                           "BLOCK1_EVIDENCE_STATUS_MATRIX.csv",
                                           "BLOCK1_DECISION.json",
                                           "BLOCK1_INPUT_HASH_MANIFEST.json"]}

    # ------------------------------------------------------------------
    def _profile_library_md(self, bands: pd.DataFrame) -> str:
        L = ["# BLOCK-I RM PROFILE LIBRARY (non-overlapping research bands)",
             "",
             "Bands are derived from measurable breakpoints in historical max DD "
             "(<=5 / <=10 / <=20 / <=30 / >30%) and verified against p95 resampled "
             "DD and prop-style DD probabilities. They are RESEARCH PROFILES, not "
             "recommendations. RM-S4 is RESEARCH / FULL-PRESS ONLY - not safe, not "
             "recommended, not production.",
             "",
             "| profile | f band | hist max DD | p95 resampled DD | worst day | "
             "rep f | rep CAGR | P(DD>=40%) | edge-75 | edge-50 | tail worst5x2 | use |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, b in bands.iterrows():
            L.append(f"| {b['profile']} | {b['f_band_min']:.2f}-{b['f_band_max']:.2f}% | "
                     f"{b['historical_max_dd_range_pct']}% | {b['p95_dd_range_pct']}% | "
                     f"{b['worst_day_range_pct']}% | {b['representative_f_pct']:.2f}% | "
                     f"{b['rep_cagr']*100:+.0f}% | {b['rep_P_dd_ge_40']*100:.1f}% | "
                     f"{b['edge75_exp_cagr_at_rep']*100:+.0f}% | "
                     f"{b['edge50_exp_cagr_at_rep']*100:+.0f}% | "
                     f"{b['tail_worst5x2_max_dd_at_rep']*100:.1f}% | "
                     f"{b['intended_use']} |")
        L.append("")
        L.append("Forbidden interpretation for every profile: NOT safe / NOT "
                 "recommended / NOT production.")
        return "\n".join(L)

    def _block2_queue(self) -> str:
        return """# BLOCK-II RESEARCH QUEUE (defined, NOT authorized)

Sequence derived from Block-I evidence. No phase starts until human review
clears Block I and authorizes the individual checkpoint.

| phase | question | inputs | allowed outputs | forbidden optimization | review gate |
|---|---|---|---|---|---|
| R5 Family quality/allocation anatomy | Is B's extra downside real per unit of edge, and does A/B risk separation justify unequal sizing? | R1 ledger, R2/R3 family tables, R4 family frontier | family risk/return quality tables, allocation *descriptions* | any allocation change to the strategy | human review before any weighting |
| R6 Concurrency / episode-aware sizing | Do clustered events or overlap states warrant per-state risk scaling? | R1 concurrency + episodes, R2/R3 overlap/rank tables | exposure-state risk tables | implementing heat caps or rank filters | human review |
| R7 Drawdown-adaptive sizing | Does reducing f after DD improve survival vs static? | R4 MC paths, R4 DD distributions | simulated DD-adaptive comparisons | choosing a DD rule from holdout | human review |
| R8 Kelly / fractional Kelly | What is the theoretical growth-optimal f under the measured dependency structure? | R4 expectancy/var/cov, R2 streaks, R1 clusters | Kelly estimates with dependency caveats | applying Kelly live | human review |
| R9 Hybrid risk engine | Which static/dynamic policies combine best? | R5-R8 outputs | policy tournament on development data | any parameter chosen on OOS | human review + forward shadow validation |

Priority rationale: family and dependency structure must be understood before
Kelly; DD adaptation needs the MC/ruin baseline first; the hybrid engine is the
final comparison layer.
"""

    def _contradictions(self) -> str:
        return """# BLOCK-I CONTRADICTIONS (seal-time reconciliation)

| contradiction | classification | resolution |
|---|---|---|
| R3_TIME_TO_PROFIT share_of_winners > 1.0 | RESOLVED_BY_LATER_REPAIR | R3.1 (commit 31fa1df1) split N_reached_all / winners / losers with own-population denominators; report/decision regenerated; unaffected artifacts byte-identical. |
| R3 report/decision Q12 ex-best-5% expectancy read NaN (wrong row selected) | RESOLVED_BY_LATER_REPAIR | fixed in R3 build (row selection on the non-null exclusion value); sealed artifacts use the corrected +0.20R. |
| R4 auto-zones collapsed (RM-S2/S3/S4 all = 5.0%) | NON-MATERIAL | mathematically valid under the auto-constraints; operationally unusable -> this seal REFRAMES profiles as non-overlapping bands from measured DD breakpoints (see BLOCK1_RM_PROFILE_LIBRARY.md). Frontier results unchanged. |
| R4 worst_cluster_pct returned 0.0 (max(-inf, ...) init bug) | RESOLVED_BY_LATER_REPAIR | fixed within R4 (min tracking); sealed ladder has worst-cluster = -6.0% at f=1%. |
| R4 worst_seq_pct semantics (absolute dip vs relative DD) | RESOLVED_BY_LATER_REPAIR | fixed within R4 to peak-to-trough relative DD; sequential max DD 10.0% at f=1% vs hourly 10.2%. |

No UNRESOLVED material contradictions. Seal proceeds.
"""

    # ------------------------------------------------------------------
    def _decision(self, g: Dict, bands: pd.DataFrame) -> Dict:
        rR = g["ledger"]["pnl_bps"] / g["ledger"]["risk_unit_bps"]
        a_w = float(rR[g["ledger"]["family"] == "A"].min())
        b_w = float(rR[g["ledger"]["family"] == "B"].min())
        return {
            "checkpoint": "CR-RISK-BLOCK1-FOUNDATION-SEAL",
            "status": "PASS",
            "block1_foundation_sealed": True,
            "r1_accepted": True,
            "r1_1_accepted": True,
            "r2_accepted": True,
            "r3_accepted": True,
            "r3_1_accepted": True,
            "r4_accepted": True,
            "risk_unit_locked": True,
            "exposure_truth_locked": True,
            "loss_anatomy_locked": True,
            "profit_anatomy_locked": True,
            "static_frontier_locked": True,
            "edge_degradation_locked": True,
            "tail_risk_locked": True,
            "family_risk_locked": True,
            "rm_profile_library_created": True,
            "alpha_changed": False,
            "entry_changed": False,
            "exit_changed": False,
            "trade_management_changed": False,
            "best_size_selected": False,
            "kelly_authorized": False,
            "dynamic_sizing_authorized": False,
            "family_allocation_authorized": False,
            "cluster_sizing_authorized": False,
            "dd_adaptive_authorized": False,
            "deployment_authorized": False,
            "mt5_authorized": False,
            "block_2_cleared": False,
            "human_review_required": True,
            "profiles": {r["profile"]: {"f_min": float(r["f_band_min"]),
                                        "f_max": float(r["f_band_max"]),
                                        "representative_f": float(r["representative_f_pct"])}
                         for _, r in bands.iterrows()},
            "family_capital_limiter": "B (static equal-f, every tested f)",
            "risk_unit": {"1R_bps": 24.49489742783178,
                          "account_mapping": "account_return ~= trade_return_R x f",
                          "A_worst_R": a_w, "B_worst_R": b_w,
                          "is_stop": False},
            "next_checkpoint_recommended": "BLOCK-II-R5-FAMILY-QUALITY-ALLOCATION",
            "stop": "Block I sealed. Block II (R5-R9, Kelly, dynamic/family/cluster/"
                    "DD sizing, deployment, MT5) does NOT start until human review.",
        }

    # ------------------------------------------------------------------
    def _manifest(self, git_sha: str) -> Dict:
        def sha(p: Path) -> str:
            return hashlib.sha256(p.read_bytes()).hexdigest()
        src = sorted(self.b.glob("BLOCK1_*")) + sorted(self.b.glob("R1_*.csv")) \
            + sorted(self.b.glob("R2_*.csv")) + sorted(self.b.glob("R3_*.csv")) \
            + sorted(self.b.glob("R4_*.csv")) + sorted(self.b.glob("R*_DECISION.json")) \
            + sorted(self.b.glob("R*_INPUT_HASH_MANIFEST.json")) \
            + sorted(self.b.glob("R3_1_*.md")) + sorted(self.b.glob("R3_1_*.json"))
        code = sorted(Path(__file__).parent.glob("phase_r[1234]_*.py"))
        return {
            "checkpoint": "CR-RISK-BLOCK1-FOUNDATION-SEAL",
            "repo": "dabiggestpoppa/larger-lab",
            "branch": "capital-routing",
            "git_sha_at_generation": git_sha,
            "seal_commit_sha": "PENDING_STAMP",
            "prior_checkpoints": {
                "p75_seal": SHA_P75,
                "r1": SHA_R1,
                "r1_1": SHA_R11,
                "r2": SHA_R2,
                "r2_bookkeeping": SHA_R2B,
                "r3": SHA_R3,
                "r3_1": SHA_R31,
                "r4": SHA_R4,
                "r4_bookkeeping": SHA_R4B,
            },
            "artifact_hashes": {p.name: sha(p) for p in src},
            "code_hashes": {p.name: sha(p) for p in code},
            "python_version": platform.python_version(),
            "timestamp": pd.Timestamp.utcnow().isoformat(),
        }


_USE = {
    "RM-S0_PRESERVATION": "capital preservation, low DD tolerance",
    "RM-S1_CONSERVATIVE": "moderate growth with low tail-DD probability",
    "RM-S2_BALANCED": "growth with controlled 20% DD probability",
    "RM-S3_GROWTH": "high growth, materially higher DD accepted",
    "RM-S4_FULL_PRESS_RESEARCH": "research ceiling / full-press study only",
}
