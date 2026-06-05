"""
CEREBUS DEPLOYMENT CONFIG - 7 Pairs
====================================
MAD Directive 2026-06-04:
  Floor (3): EURUSD, USDJPY, CHFJPY
  Ceiling (3): NZDUSD, AUDUSD, USDCHF
  Hedge/Knee (1): GBPJPY

Per-pair AU values from native sweep configs (trigger_sweep_max_accuracy_all.py NATIVE_CONFIGS).
Each pair uses its OWN custom AU - NOT a universal AU. This is a core strategy rule.
T1 trigger = sweep-optimal trigger (best WR with >500 trades from per-pair sweep files).
ar_max = 60 (session filter only, not tier classifier).

RULE: AU is ALWAYS per-pair, never universal. Each market has its own volatility profile.
   When adding/swapping assets, you MUST run a sweep to find that asset native AU.
   Never copy AU from one pair to another.

ENGINE DOES ALL COMPUTING. Bridge just reads bars, feeds engine, places orders.
"""

DEPLOYMENT_CONFIGS = {
    "EURUSD.PRO": {
        "name": "EURUSD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
            "T2": {"ar_max": 60.0, "au": 12.0, "trigger": 12.0},
            "T3": {"ar_max": 60.0, "au": 15.0, "trigger": 12.0},
        },
        "expected": {"wr": 85.3, "pf": 13.2, "tr_per_day": 4.17, "rr": 2.21},
    },
    "USDJPY.PRO": {
        "name": "USDJPY",
        "pip_value": 0.01,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 16.0, "trigger": 15.0},
            "T2": {"ar_max": 60.0, "au": 26.0, "trigger": 15.0},
            "T3": {"ar_max": 60.0, "au": 44.0, "trigger": 15.0},
        },
        "expected": {"wr": 82.2, "pf": 11.1, "tr_per_day": 4.63, "rr": 2.36},
    },
    "CHFJPY.PRO": {
        "name": "CHFJPY",
        "pip_value": 0.01,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 14.0, "trigger": 11.7},
            "T2": {"ar_max": 60.0, "au": 24.0, "trigger": 11.7},
            "T3": {"ar_max": 60.0, "au": 42.0, "trigger": 11.7},
        },
        "expected": {"wr": 82.6, "pf": 11.7, "tr_per_day": 7.14, "rr": 2.39},
    },
    "NZDUSD.PRO": {
        "name": "NZDUSD",
        "pip_value": 0.0001,
        "mode": "ceiling",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 14.0, "trigger": 10.0},
            "T2": {"ar_max": 60.0, "au": 17.0, "trigger": 10.0},
            "T3": {"ar_max": 60.0, "au": 21.0, "trigger": 10.0},
        },
        "expected": {"wr": 82.1, "pf": 12.8, "tr_per_day": 3.39, "rr": 2.67},
    },
    "AUDUSD.PRO": {
        "name": "AUDUSD",
        "pip_value": 0.0001,
        "mode": "ceiling",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 11.0, "trigger": 10.8},
            "T2": {"ar_max": 60.0, "au": 14.0, "trigger": 10.8},
            "T3": {"ar_max": 60.0, "au": 18.0, "trigger": 10.8},
        },
        "expected": {"wr": 82.9, "pf": 13.3, "tr_per_day": 3.37, "rr": 2.64},
    },
    "USDCHF.PRO": {
        "name": "USDCHF",
        "pip_value": 0.0001,
        "mode": "ceiling",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 11.0, "trigger": 11.7},
            "T2": {"ar_max": 60.0, "au": 15.0, "trigger": 11.7},
            "T3": {"ar_max": 60.0, "au": 20.0, "trigger": 11.7},
        },
        "expected": {"wr": 81.5, "pf": 11.9, "tr_per_day": 3.69, "rr": 2.61},
    },
    "GBPJPY.PRO": {
        "name": "GBPJPY",
        "pip_value": 0.01,
        "mode": "knee",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 19.0, "trigger": 18.7},
            "T2": {"ar_max": 60.0, "au": 29.0, "trigger": 18.7},
            "T3": {"ar_max": 60.0, "au": 48.0, "trigger": 18.7},
        },
        "expected": {"wr": 82.0, "pf": 12.3, "tr_per_day": 3.92, "rr": 2.60},
    },
}

DEPLOY_SYMBOLS = list(DEPLOYMENT_CONFIGS.keys())

LOT_SIZE = 0.01
MAX_DRAWNOWN_PCT = 20.0
HARD_STOP_PCT = 25.0
KILL_THRESHOLD_WR = 70.0
