"""
OPTIMIZATION VECTOR — EUR Basket
=================================
Apply the same 4 transformations that unlocked EURUSD to all EUR pairs.

The Vector (not hardcoded numbers):
1. Trigger Scale: native_T1_trigger * 0.833 (same ratio as 12→10)
2. AR Gate Expansion: ar_max * 3.0 (same ratio as 20→60) — effectively disables daily kill-switch
3. Session Cutoff: 4PM EST (global)
4. DZ Flattening: flat 20-50% (inherently agnostic, already in engine)

Per MAD/ARC directive: "We are just swapping the name and applying the math."
"""
import sys, os

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')

# ── NATIVE CONFIGS (from asset_configs.py) ────────────────────────────────
NATIVE_CONFIGS = {
    "EURUSD": {
        "csv": "EURUSD_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
                  "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
                  "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0}},
    },
    "EURGBP": {
        "csv": "EURGBP_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 20.98, "au": 7.0, "trigger": 8.0},
                  "T2": {"ar_max": 40.33, "au": 14.0, "trigger": 17.0},
                  "T3": {"ar_max": 40.33, "au": 19.0, "trigger": 23.0}},
    },
    "EURJPY": {
        "csv": "EURJPY_PRO_M5.csv",
        "pip_value": 0.01,
        "tiers": {"T1": {"ar_max": 91.57, "au": 29.0, "trigger": 35.0},
                  "T2": {"ar_max": 160.35, "au": 63.0, "trigger": 75.0},
                  "T3": {"ar_max": 160.35, "au": 63.0, "trigger": 76.0}},
    },
    "EURAUD": {
        "csv": "EURAUD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 77.51, "au": 27.0, "trigger": 32.0},
                  "T2": {"ar_max": 135.4, "au": 51.0, "trigger": 61.0},
                  "T3": {"ar_max": 135.4, "au": 58.0, "trigger": 69.0}},
    },
    "EURNZD": {
        "csv": "EURNZD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 77.48, "au": 28.0, "trigger": 34.0},
                  "T2": {"ar_max": 143.25, "au": 49.0, "trigger": 59.0},
                  "T3": {"ar_max": 143.25, "au": 61.0, "trigger": 73.0}},
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
}

# ── OPTIMIZATION VECTOR ──────────────────────────────────────────────────
TRIGGER_SCALE = 0.833   # 12→10 = 0.833x
AR_EXPANSION = 3.0      # 20→60 = 3.0x


def apply_vector(native_tiers):
    """Apply the 4-step optimization vector to native tier config."""
    optimized = {}
    for tier_name, tier_cfg in native_tiers.items():
        optimized[tier_name] = {
            "ar_max": round(tier_cfg["ar_max"] * AR_EXPANSION, 2),
            "au": tier_cfg["au"],  # AU stays native (it's pair-specific)
            "trigger": round(tier_cfg["trigger"] * TRIGGER_SCALE, 1),
        }
    return optimized


def run_pair(asset_key, native_config):
    """Run a single pair with optimized config."""
    csv_path = os.path.join(DATA_DIR, native_config["csv"])
    if not os.path.exists(csv_path):
        print("  {}: MISSING DATA — {}".format(asset_key, native_config["csv"]))
        return None

    optimized_tiers = apply_vector(native_config["tiers"])

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
        return {"asset": asset_key, "trades": 0}

    wins = sum(1 for t in trades if t.pnl_pips > 0)
    losses = sum(1 for t in trades if t.pnl_pips < 0)
    wr = wins / len(trades) * 100

    # Consecutive
    max_cw = max_cl = cur_w = cur_l = 0
    for t in trades:
        if t.pnl_pips > 0:
            cur_w += 1; cur_l = 0; max_cw = max(max_cw, cur_w)
        elif t.pnl_pips < 0:
            cur_l += 1; cur_w = 0; max_cl = max(max_cl, cur_l)
        else:
            cur_w = cur_l = 0

    # Tier breakdown
    tier_counts = {}
    for t in trades:
        tier = getattr(t, 'tier', 'UNK')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    return {
        "asset": asset_key,
        "trades": len(trades),
        "days": result.data_days,
        "wr": wr,
        "pnl": result.total_pnl_pips,
        "pf": result.profit_factor,
        "avg_w": result.avg_win_pips,
        "avg_l": result.avg_loss_pips,
        "exp": result.expectancy_pips,
        "max_dd": result.max_drawdown_pips,
        "max_cw": max_cw,
        "max_cl": max_cl,
        "tiers": tier_counts,
        "native_tiers": native_config["tiers"],
        "optimized_tiers": optimized_tiers,
    }


if __name__ == '__main__':
    print("=" * 70)
    print("OPTIMIZATION VECTOR — EUR Basket")
    print("Trigger Scale: {:.3f}x | AR Expansion: {:.1f}x | Cutoff: 4PM EST".format(
        TRIGGER_SCALE, AR_EXPANSION))
    print("=" * 70)
    print("")

    all_results = []
    for asset_key in ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD"]:
        native = NATIVE_CONFIGS[asset_key]
        opt = apply_vector(native["tiers"])
        print("--- {} ---".format(asset_key))
        print("  Native:  {}".format(native["tiers"]))
        print("  Optimized: {}".format(opt))
        r = run_pair(asset_key, native)
        if r:
            all_results.append(r)
            print("  {} tr | {:.1f}% WR | {:.1f}p | PF {:.2f} | MaxCL {} | Tr/day {:.2f}".format(
                r["trades"], r["wr"], r["pnl"], r["pf"], r["max_cl"],
                r["trades"]/r["days"] if r["days"] else 0))
        print("")

    # ── SUMMARY TABLE ──────────────────────────────────────────────────────
    print("=" * 80)
    print("EUR BASKET SUMMARY — Optimization Vector Applied")
    print("=" * 80)
    print("{:<10} {:>6} {:>8} {:>10} {:>8} {:>8} {:>6} {:>8}".format(
        "Asset", "Trades", "WR%", "PnL", "PF", "MaxDD", "MaxCL", "Tr/Day"))
    print("-" * 80)

    total_trades = 0
    total_pnl = 0
    for r in all_results:
        print("{:<10} {:>6} {:>7.1f}% {:>10.1f} {:>8.2f} {:>8.1f} {:>6} {:>8.2f}".format(
            r["asset"], r["trades"], r["wr"], r["pnl"], r["pf"], r["max_dd"], r["max_cl"],
            r["trades"]/r["days"] if r["days"] else 0))
        total_trades += r["trades"]
        total_pnl += r["pnl"]

    # Weighted WR
    total_wins = sum(r["trades"] * r["wr"] / 100 for r in all_results)
    basket_wr = total_wins / total_trades * 100 if total_trades else 0

    print("-" * 80)
    print("{:<10} {:>6} {:>7.1f}% {:>10.1f}".format(
        "BASKET", total_trades, basket_wr, total_pnl))
    print("")

    # ── PER-PAIR DETAIL ────────────────────────────────────────────────────
    print("--- Tier Breakdown ---")
    for r in all_results:
        tier_str = " | ".join("{}:{}".format(t, c) for t, c in sorted(r["tiers"].items()))
        print("  {}: {}".format(r["asset"], tier_str))

    print("")
    print("--- Avg Win / Avg Loss ---")
    for r in all_results:
        print("  {}: AvgW {:.1f}p | AvgL {:.1f}p | Exp {:.1f}p".format(
            r["asset"], r["avg_w"], r["avg_l"], r["exp"]))
