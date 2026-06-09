"""
CEREBUS DEPLOYMENT CONFIG — LOW COST HEX (Phase 1)
===================================================
MAD Directive 2026-06-05: Deploy low-cost hex, swap out Sign 7 config.

Low-Cost Hex (6 assets, all FLOOR):
  EURJPY — FLOOR  |  EURNZD — FLOOR  |  GBPNZD — FLOOR
  EURAUD — FLOOR  |  GBPAUD — FLOOR  |  GBPCAD — FLOOR

Per-pair AU values from sweep data.
Each pair uses its OWN custom AU - NOT a universal AU. This is a core strategy rule.
ar_max = 60 (session filter only, not tier classifier).

RULE: AU is ALWAYS per-pair, never universal. Each market has its own volatility profile.
   When adding/swapping assets, you MUST run a sweep to find that asset native AU.
   Never copy AU from one pair to another.

ENGINE DOES ALL COMPUTING. Bridge just reads bars, feeds engine, places orders.

SIGN 7 CONFIG (old, archived):
  EURUSD/USDJPY/CHFJPY (floor) + NZDUSD/AUDUSD/USDCHF (ceiling) + GBPJPY (knee)
  Replaced by Low-Cost Hex per MAD directive 2026-06-05.
"""

DEPLOYMENT_CONFIGS = {
    "EURJPY.PRO": {
        "name": "EURJPY",
        "pip_value": 0.01,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 14.0, "trigger": 16.0},
            "T2": {"ar_max": 60.0, "au": 18.0, "trigger": 16.0},
            "T3": {"ar_max": 60.0, "au": 24.0, "trigger": 16.0},
        },
        "expected": {"wr": 88.1, "pf": 18.0, "tr_per_day": 0.35, "rr": 2.4},
    },
    "EURNZD.PRO": {
        "name": "EURNZD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 12.0, "trigger": 16.3},
            "T2": {"ar_max": 60.0, "au": 15.0, "trigger": 16.3},
            "T3": {"ar_max": 60.0, "au": 20.0, "trigger": 16.3},
        },
        "expected": {"wr": 79.4, "pf": 11.9, "tr_per_day": 1.76, "rr": 3.0},
    },
    "GBPNZD.PRO": {
        "name": "GBPNZD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 12.0, "trigger": 18.2},
            "T2": {"ar_max": 60.0, "au": 16.0, "trigger": 18.2},
            "T3": {"ar_max": 60.0, "au": 22.0, "trigger": 18.2},
        },
        "expected": {"wr": 79.2, "pf": 11.4, "tr_per_day": 1.74, "rr": 3.0},
    },
    "EURAUD.PRO": {
        "name": "EURAUD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 12.0, "trigger": 18.7},
            "T2": {"ar_max": 60.0, "au": 15.0, "trigger": 18.7},
            "T3": {"ar_max": 60.0, "au": 20.0, "trigger": 18.7},
        },
        "expected": {"wr": 80.7, "pf": 12.3, "tr_per_day": 1.01, "rr": 2.9},
    },
    "GBPAUD.PRO": {
        "name": "GBPAUD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 11.0, "trigger": 18.8},
            "T2": {"ar_max": 60.0, "au": 14.0, "trigger": 18.8},
            "T3": {"ar_max": 60.0, "au": 19.0, "trigger": 18.8},
        },
        "expected": {"wr": 80.8, "pf": 10.6, "tr_per_day": 1.74, "rr": 2.5},
    },
    "GBPCAD.PRO": {
        "name": "GBPCAD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 14.0},
            "T2": {"ar_max": 60.0, "au": 13.0, "trigger": 14.0},
            "T3": {"ar_max": 60.0, "au": 18.0, "trigger": 14.0},
        },
        "expected": {"wr": 80.0, "pf": 10.9, "tr_per_day": 2.01, "rr": 2.7},
    },
    "FR40.PRO": {
        "name": "FR40",
        "pip_value": 0.01,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 12.0, "trigger": 16.0},
            "T2": {"ar_max": 60.0, "au": 16.0, "trigger": 16.0},
            "T3": {"ar_max": 60.0, "au": 22.0, "trigger": 16.0},
        },
        "expected": {"wr": 80.0, "pf": 12.0, "tr_per_day": 1.5, "rr": 2.8},
    },
}

DEPLOY_SYMBOLS = list(DEPLOYMENT_CONFIGS.keys())

LOT_SIZE = 0.01
MAX_DRAWNOWN_PCT = 20.0
HARD_STOP_PCT = 25.0
KILL_THRESHOLD_WR = 70.0
