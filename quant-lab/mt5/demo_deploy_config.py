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
            "T1": {"ar_max": 60.0, "au": 205.0, "trigger": 12.0},
            "T2": {"ar_max": 60.0, "au": 545.0, "trigger": 12.0},
            "T3": {"ar_max": 60.0, "au": 1160.0, "trigger": 12.0},
        },
        "expected": {"wr": 92.6, "pf": 26.5, "tr_per_day": 0.50, "rr": 2.1},
    },
    "ETHUSD.DEMO": {
        "name": "ETHUSD",
        "pip_value": 0.01,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 35.0, "trigger": 12.0},
            "T2": {"ar_max": 60.0, "au": 42.0, "trigger": 12.0},
            "T3": {"ar_max": 60.0, "au": 52.0, "trigger": 12.0},
        },
        "expected": {"wr": 96.9, "pf": 50.3, "tr_per_day": 0.34, "rr": 1.6},
    },
    "EURNZD.DEMO": {
        "name": "EURNZD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 17.0, "trigger": 16.3},
            "T2": {"ar_max": 60.0, "au": 23.0, "trigger": 16.3},
            "T3": {"ar_max": 60.0, "au": 34.0, "trigger": 16.3},
        },
        "expected": {"wr": 79.4, "pf": 11.9, "tr_per_day": 1.76, "rr": 3.0},
    },
    "GBPNZD.DEMO": {
        "name": "GBPNZD",
        "pip_value": 0.0001,
        "mode": "floor",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 24.0, "trigger": 18.2},
            "T2": {"ar_max": 60.0, "au": 36.0, "trigger": 18.2},
            "T3": {"ar_max": 60.0, "au": 59.0, "trigger": 18.2},
        },
        "expected": {"wr": 88.4, "pf": 20.9, "tr_per_day": 0.49, "rr": 2.7},
    },
}

DEPLOY_SYMBOLS = list(DEPLOYMENT_CONFIGS.keys())

LOT_SIZE = 0.01
MAX_DRAWNOWN_PCT = 20.0
HARD_STOP_PCT = 25.0
KILL_THRESHOLD_WR = 70.0