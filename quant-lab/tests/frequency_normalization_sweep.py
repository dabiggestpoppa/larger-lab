"""
FREQUENCY NORMALIZATION SWEEP — EUR Basket
===========================================
ARC Directive: Calibrate trigger parameters for sub-2.5 tr/day pairs
to hit 2.5-3.0 tr/day floor while maintaining WR>80%, PF>10.0.

Deficit pairs: EURGBP, EURCHF, EURCAD, EURNZD, EURAUD, EURJPY
Sweep multipliers: 0.75x, 0.65x, 0.55x, 0.45x of native trigger
Guardrail: PF >= 10.0, WR >= 80.0
"""
import sys, os

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')

# Only the deficit pairs
DEFICIT_PAIRS = {
    "EURGBP": {
        "csv": "EURGBP_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 20.98, "au": 7.0, "trigger": 8.0},
                  "T2": {"ar_max": 40.33, "au": 14.0, "trigger": 17.0},
                  "T3": {"ar_max": 40.33, "au": 19.0, "trigger": 23.0}},
    },
    "EURCHF": {
        "csv": "EURCHF_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 28.55, "au": 9.0, "trigger": 11.0},
                  "T2": {"ar_max": 53.15, "au": 19.0, "trigger": 23.0},
                  "T3": {"ar_max": 53.15, "au": 22.0, "trigger": 27.0}},
    },
    "EURCAD": {
        "csv": "EURCAD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 38.86, "au": 13.0, "trigger": 16.0},
                  "T2": {"ar_max": 75.87, "au": 25.0, "trigger": 31.0},
                  "T3": {"ar_max": 75.87, "au": 32.0, "trigger": 38.0}},
    },
    "EURNZD": {
        "csv": "EURNZD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 77.48, "au": 28.0, "trigger": 34.0},
                  "T2": {"ar_max": 143.25, "au": 49.0, "trigger": 59.0},
                  "T3": {"ar_max": 143.25, "au": 61.0, "trigger": 73.0}},
    },
    "EURAUD": {
        "csv": "EURAUD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 77.51, "au": 27.0, "trigger": 32.0},
                  "T2": {"ar_max": 135.4, "au": 51.0, "trigger": 61.0},
                  "T3": {"ar_max": 135.4, "au": 58.0, "trigger": 69.0}},
    },
    "EURJPY": {
        "csv": "EURJPY_PRO_M5.csv",
        "pip_value": 0.01,
        "tiers": {"T1": {"ar_max": 91.57, "au": 29.0, "trigger": 35.0},
                  "T2": {"ar_max": 160.35, "au": 63.0, "trigger": 75.0},
                  "T3": {"ar_max": 160.35, "au": 63.0, "trigger": 76.0}},
    },
}

SWEEP_MULTIPLIERS = [0.75, 0.65, 0.55, 0.45]
GUARDRAIL_PF = 10.0
GUARDRAIL_WR = 80.0
TARGET_TR_DAY = 2.5


def apply_vector_with_multiplier(native_tiers, multiplier):
    """Apply AR expansion + custom trigger multiplier."""
    optimized = {}
    for tier_name, tier_cfg in native_tiers.items():
        optimized[tier_name] = {
            "ar_max": round(tier_cfg["ar_max"] * 3.0, 2),  # AR expansion always 3x
            "au": tier_cfg["au"],
            "trigger": round(tier_cfg["trigger"] * multiplier, 1),
        }
    return optimized


def run_pair_with_mult(asset_key, native_config, multiplier):
    """Run a single pair with a specific trigger multiplier."""
    csv_path = os.path.join(DATA_DIR, native_config["csv"])
    if not os.path.exists(csv_path):
        return None

    optimized_tiers = apply_vector_with_multiplier(native_config["tiers"], multiplier)

    bt = SymmetryTrapBacktest(
        pip_size=native_config["pip_value"],
        tier_config=optimized_tiers,
        symbol=asset_key,
        config={"pip_value": native_config["pip_value"], "tiers": optimized_tiers}
    )
    bt.session_cutoff = 16  # 4PM EST

    result = bt.run_from_csv(csv_path)
    trades = result.trades

    if not trades:
        return {"trades": 0, "days": result.data_days, "wr": 0, "pnl": 0, "pf": 0,
                "max_cl": 0, "tr_per_day": 0, "tiers": {}}

    wins = sum(1 for t in trades if t.pnl_pips > 0)
    losses = sum(1 for t in trades if t.pnl_pips < 0)
    wr = wins / len(trades) * 100

    max_cw = max_cl = cur_w = cur_l = 0
    for t in trades:
        if t.pnl_pips > 0:
            cur_w += 1; cur_l = 0; max_cw = max(max_cw, cur_w)
        elif t.pnl_pips < 0:
            cur_l += 1; cur_w = 0; max_cl = max(max_cl, cur_l)
        else:
            cur_w = cur_l = 0

    tier_counts = {}
    for t in trades:
        tier = getattr(t, 'tier', 'UNK')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    days = result.data_days if result.data_days else 1

    return {
        "trades": len(trades),
        "days": days,
        "wr": wr,
        "pnl": result.total_pnl_pips,
        "pf": result.profit_factor,
        "max_cl": max_cl,
        "tr_per_day": len(trades) / days,
        "tiers": tier_counts,
        "optimized_tiers": optimized_tiers,
    }


if __name__ == '__main__':
    print("=" * 90)
    print("FREQUENCY NORMALIZATION SWEEP — EUR Basket Deficit Pairs")
    print("Target: >= 2.5 tr/day | Guardrail: WR >= 80%, PF >= 10.0")
    print("=" * 90)

    # Store all results: {asset: {multiplier: result}}
    all_sweep = {}
    # Store baseline (0.833x) for comparison
    baselines = {}

    for asset_key in DEFICIT_PAIRS:
        native = DEFICIT_PAIRS[asset_key]
        print("\n>>> {} (Native T1 trigger: {}p)".format(asset_key, native["tiers"]["T1"]["trigger"]))

        # Baseline at 0.833x
        baseline = run_pair_with_mult(asset_key, native, 0.833)
        if baseline:
            baselines[asset_key] = baseline
            print("  Baseline 0.833x: {} tr | {:.1f}% WR | PF {:.2f} | {:.2f} tr/day".format(
                baseline["trades"], baseline["wr"], baseline["pf"], baseline["tr_per_day"]))

        all_sweep[asset_key] = {}
        best_valid = None

        for mult in SWEEP_MULTIPLIERS:
            r = run_pair_with_mult(asset_key, native, mult)
            if r is None:
                continue
            all_sweep[asset_key][mult] = r

            t1_trigger = round(native["tiers"]["T1"]["trigger"] * mult, 1)
            guardrail_pass = r["pf"] >= GUARDRAIL_PF and r["wr"] >= GUARDRAIL_WR
            status = "OK" if guardrail_pass else "FAIL"

            print("  {:.2f}x (T1={}p): {} tr | {:.1f}% WR | PF {:.2f} | {:.2f} tr/day | {}".format(
                mult, t1_trigger, r["trades"], r["wr"], r["pf"], r["tr_per_day"], status))

            if guardrail_pass and r["tr_per_day"] >= TARGET_TR_DAY:
                if best_valid is None or r["tr_per_day"] > best_valid["tr_per_day"]:
                    best_valid = {**r, "mult": mult, "t1_trigger": t1_trigger}

        if best_valid:
            print("  >>> BEST VALID: {:.2f}x (T1={}p) -> {:.2f} tr/day | WR {:.1f}% | PF {:.2f}".format(
                best_valid["mult"], best_valid["t1_trigger"],
                best_valid["tr_per_day"], best_valid["wr"], best_valid["pf"]))
        else:
            # Find the best we can do without breaching guardrail
            best_safe = None
            for mult in SWEEP_MULTIPLIERS:
                if mult in all_sweep[asset_key]:
                    r = all_sweep[asset_key][mult]
                    if r["pf"] >= GUARDRAIL_PF and r["wr"] >= GUARDRAIL_WR:
                        if best_safe is None or r["tr_per_day"] > best_safe["tr_per_day"]:
                            t1_trigger = round(native["tiers"]["T1"]["trigger"] * mult, 1)
                            best_safe = {**r, "mult": mult, "t1_trigger": t1_trigger}
            if best_safe:
                print("  >>> CANNOT REACH 2.5 tr/day. Best safe: {:.2f}x (T1={}p) -> {:.2f} tr/day | WR {:.1f}% | PF {:.2f}".format(
                    best_safe["mult"], best_safe["t1_trigger"],
                    best_safe["tr_per_day"], best_safe["wr"], best_safe["pf"]))
            else:
                print("  >>> ALL MULTIPLIERS BREACH GUARDRAIL at lower triggers")

    # ── FINAL SUMMARY TABLE ──────────────────────────────────────────────
    print("\n" + "=" * 100)
    print("FREQUENCY NORMALIZATION — FINAL OUTPUT MATRIX")
    print("=" * 100)
    print("{:<10} {:>8} {:>10} {:>10} {:>8} {:>8} {:>8} {:>8}".format(
        "Asset", "Old_Mult", "Old_Tr/D", "New_Mult", "New_Tr/D", "New_WR%", "New_PF", "New_T1p"))
    print("-" * 100)

    for asset_key in DEFICIT_PAIRS:
        native = DEFICIT_PAIRS[asset_key]
        old = baselines.get(asset_key)
        if not old:
            continue

        # Find best valid for this pair
        best = None
        for mult in SWEEP_MULTIPLIERS:
            if mult in all_sweep.get(asset_key, {}):
                r = all_sweep[asset_key][mult]
                if r["pf"] >= GUARDRAIL_PF and r["wr"] >= GUARDRAIL_WR:
                    if r["tr_per_day"] >= TARGET_TR_DAY:
                        if best is None or r["tr_per_day"] > best["tr_per_day"]:
                            t1_trigger = round(native["tiers"]["T1"]["trigger"] * mult, 1)
                            best = {**r, "mult": mult, "t1_trigger": t1_trigger}

        # If no multiplier hits 2.5, pick best safe
        if best is None:
            for mult in SWEEP_MULTIPLIERS:
                if mult in all_sweep.get(asset_key, {}):
                    r = all_sweep[asset_key][mult]
                    if r["pf"] >= GUARDRAIL_PF and r["wr"] >= GUARDRAIL_WR:
                        if best is None or r["tr_per_day"] > best["tr_per_day"]:
                            t1_trigger = round(native["tiers"]["T1"]["trigger"] * mult, 1)
                            best = {**r, "mult": mult, "t1_trigger": t1_trigger}

        if best:
            print("{:<10} {:>8.3f} {:>10.2f} {:>10.3f} {:>10.2f} {:>8.1f} {:>8.2f} {:>8.1f}".format(
                asset_key, 0.833, old["tr_per_day"], best["mult"], best["tr_per_day"],
                best["wr"], best["pf"], best["t1_trigger"]))
        else:
            print("{:<10} {:>8.3f} {:>10.2f} {:>10} {:>10} {:>8} {:>8} {:>8}".format(
                asset_key, 0.833, old["tr_per_day"], "N/A", "N/A", "N/A", "N/A", "N/A"))

    # ── FREQUENCY COEFFICIENTS ───────────────────────────────────────────
    print("\n" + "=" * 80)
    print("FREQUENCY COEFFICIENTS — Optimal Trigger = Native_Trigger * Coefficient")
    print("=" * 80)
    for asset_key in DEFICIT_PAIRS:
        native = DEFICIT_PAIRS[asset_key]
        best = None
        for mult in SWEEP_MULTIPLIERS:
            if mult in all_sweep.get(asset_key, {}):
                r = all_sweep[asset_key][mult]
                if r["pf"] >= GUARDRAIL_PF and r["wr"] >= GUARDRAIL_WR:
                    if r["tr_per_day"] >= TARGET_TR_DAY:
                        if best is None or r["tr_per_day"] > best["tr_per_day"]:
                            t1_trigger = round(native["tiers"]["T1"]["trigger"] * mult, 1)
                            best = {**r, "mult": mult, "t1_trigger": t1_trigger}
        if best is None:
            for mult in SWEEP_MULTIPLIERS:
                if mult in all_sweep.get(asset_key, {}):
                    r = all_sweep[asset_key][mult]
                    if r["pf"] >= GUARDRAIL_PF and r["wr"] >= GUARDRAIL_WR:
                        if best is None or r["tr_per_day"] > best["tr_per_day"]:
                            t1_trigger = round(native["tiers"]["T1"]["trigger"] * mult, 1)
                            best = {**r, "mult": mult, "t1_trigger": t1_trigger}
        if best:
            print("  {}: coefficient = {:.3f}  (Native T1={}p -> Optimized T1={}p) -> {:.2f} tr/day".format(
                asset_key, best["mult"], native["tiers"]["T1"]["trigger"], best["t1_trigger"], best["tr_per_day"]))
