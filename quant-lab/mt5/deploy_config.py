"""
CEREBUS DEPLOYMENT CONFIG — 7 Pairs
====================================
MAD Directive 2026-06-04:
  Floor (3): EURUSD, USDJPY, CHFJPY
  Ceiling (3): NZDUSD, AUDUSD, USDCHF
  Hedge/Knee (1): GBPJPY

Configs extracted from trigger_sweep_max_accuracy.json.
T1 trigger = the sweep-optimized trigger for each pair's operating point.
AU and tier logic from the engine's classify_tier_by_impulse (T1<20p, T2=20-30p, T3>30p).

ENGINE DOES ALL COMPUTING. Bridge just reads bars, feeds engine, places orders.
"""

# ── Per-pair deployment configs ──────────────────────────────────
# T1 trigger = sweep-optimized value for the selected operating point
# AU values: T1=8p, T2=10p, T3=12p (from backtest calibration)
# ar_max = 60 (session filter only, not tier classifier)

DEPLOYMENT_CONFIGS = {
    # ═══════════════════════════════════════════════════════════════
    # FLOOR PAIRS — Max trade frequency, ~83% WR
    # ═══════════════════════════════════════════════════════════════
    "EURUSD.PRO": {
        "name": "EURUSD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 12.0},
            "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
            "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 12.0},
        },
        "expected": {"wr": 82.9, "pf": 12.5, "tr_per_day": 4.17, "rr": 2.52},
    },
    "USDJPY.PRO": {
        "name": "USDJPY",
        "pip_value": 0.01,  # JPY pair
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 19.0},
            "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 19.0},
            "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 19.0},
        },
        "expected": {"wr": 83.6, "pf": 13.8, "tr_per_day": 2.62, "rr": 2.66},
    },
    "CHFJPY.PRO": {
        "name": "CHFJPY",
        "pip_value": 0.01,  # JPY pair
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 17.0},
            "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 17.0},
            "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 17.0},
        },
        "expected": {"wr": 83.3, "pf": 13.4, "tr_per_day": 4.19, "rr": 2.64},
    },
    # ═══════════════════════════════════════════════════════════════
    # CEILING PAIRS — Max accuracy, ~93-95% WR
    # ═══════════════════════════════════════════════════════════════
    "NZDUSD.PRO": {
        "name": "NZDUSD",
        "pip_value": 0.0001,
        "mode": "ceiling",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 26.0},
            "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 26.0},
            "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 26.0},
        },
        "expected": {"wr": 95.5, "pf": 58.4, "tr_per_day": 0.59, "rr": 2.69},
    },
    "AUDUSD.PRO": {
        "name": "AUDUSD",
        "pip_value": 0.0001,
        "mode": "ceiling",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 27.0},
            "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 27.0},
            "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 27.0},
        },
        "expected": {"wr": 94.2, "pf": 63.1, "tr_per_day": 0.59, "rr": 3.73},
    },
    "USDCHF.PRO": {
        "name": "USDCHF",
        "pip_value": 0.0001,
        "mode": "ceiling",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 25.81},
            "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 25.81},
            "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 25.81},
        },
        "expected": {"wr": 93.2, "pf": 26.1, "tr_per_day": 0.72, "rr": 1.88},
    },
    # ═══════════════════════════════════════════════════════════════
    # HEDGE/KNEE PAIR — GBPJPY at knee, ~87% WR
    # ═══════════════════════════════════════════════════════════════
    "GBPJPY.PRO": {
        "name": "GBPJPY",
        "pip_value": 0.01,  # JPY pair
        "mode": "knee",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 35.0},
            "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 35.0},
            "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 35.0},
        },
        "expected": {"wr": 86.9, "pf": 19.1, "tr_per_day": 0.92, "rr": 2.83},
    },
}

# ── Deployment symbol list ────────────────────────────────────────
DEPLOY_SYMBOLS = list(DEPLOYMENT_CONFIGS.keys())

# ── Risk parameters ───────────────────────────────────────────────
LOT_SIZE = 0.01
MAX_DRAWNOWN_PCT = 20.0  # Alert at 20%
HARD_STOP_PCT = 25.0     # Hard stop at 25%
KILL_THRESHOLD_WR = 70.0  # Rolling 30-day WR kill threshold
