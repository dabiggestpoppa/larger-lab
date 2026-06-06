"""
CEREBUS DEMO DEPLOYMENT CONFIG — Profit Quad (Demo)
=====================================================
Demo account config for parallel forward testing alongside live.

Pairs: BTCUSD + ETHUSD + EURNZD + GBPNZD (Profit Quad)
All FLOOR mode. Same sweep-optimized AU values as live config.

IMPORTANT: Symbol suffix is .demo — adjust if your broker uses different demo symbol format.
"""

DEPLOYMENT_CONFIGS = {
    "BTCUSD.DEMO": {
        "name": "BTCUSD",
        "pip_value": 0.01,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
            "T2": {"ar_max": 60.0, "au": 14.0, "trigger": 12.0},
            "T3": {"ar_max": 60.0, "au": 20.0, "trigger": 12.0},
        },
        "expected": {"wr": 85.0, "pf": 15.0, "tr_per_day": 1.5, "rr": 2.5},
    },
    "ETHUSD.DEMO": {
        "name": "ETHUSD",
        "pip_value": 0.01,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
            "T2": {"ar_max": 60.0, "au": 14.0, "trigger": 12.0},
            "T3": {"ar_max": 60.0, "au": 20.0, "trigger": 12.0},
        },
        "expected": {"wr": 85.0, "pf": 15.0, "tr_per_day": 1.5, "rr": 2.5},
    },
    "EURNZD.DEMO": {
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
    "GBPNZD.DEMO": {
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
}

DEPLOY_SYMBOLS = list(DEPLOYMENT_CONFIGS.keys())

LOT_SIZE = 0.01
MAX_DRAWNOWN_PCT = 20.0
HARD_STOP_PCT = 25.0
KILL_THRESHOLD_WR = 70.0