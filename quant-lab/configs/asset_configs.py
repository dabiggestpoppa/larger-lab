"""
CEREBUS FX v4.0 — Master Asset Configuration Registry
======================================================
Source: CEREBUS FX v4 Complete Manual, Quick Reference Card (Pages 2-5)
Mode: DATA ONLY — no logic, no functions, no classes.

P90 k-Factors by Asset Class (cerebus_p90.md):
  Forex Majors: 0.46
  Forex Crosses: 0.48
  Indices:      0.48
  Metals:       0.50
  Crypto:       0.52

SL Method (cerebus_dual_engine.md):
  Forex Majors/Crosses: Zero-Buffer OCC Extreme (close-only invalidation)
  Indices/Metals/Crypto: Fixed point buffer from entry (spread protection)
"""

# ─────────────────────────────────────────────────────────
# FOREX MAJORS
# ─────────────────────────────────────────────────────────

ASSET_CONFIGS = {
    "EURUSD": {
        "name": "EUR/USD",
        "pip_value": 0.0001,
        "k_factor": 0.46,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 25.0, "au": 10.0, "trigger": 12.0},
            "T2": {"ar_max": 50.0, "au": 12.0, "trigger": 15.0},
            "T3": {"ar_max": 100.0, "au": 15.0, "trigger": 19.0},
        },
        "gear_shifts": {
            "T1": [(15.0, "T2"), (19.0, "T3")],
            "T2": [(19.0, "T3")],
        },
        "p90_threshold": 4.6,    # 10.0 * 0.46
        "fixed_tp": 20.0,        # 10.0 * 2.0
    },
    "GBPUSD": {
        "name": "GBP/USD",
        "pip_value": 0.0001,
        "k_factor": 0.46,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 30.0, "au": 13.0, "trigger": 16.0},
            "T2": {"ar_max": 60.0, "au": 16.0, "trigger": 19.0},
            "T3": {"ar_max": 120.0, "au": 20.0, "trigger": 24.0},
        },
        "gear_shifts": {
            "T1": [(19.0, "T2"), (24.0, "T3")],
            "T2": [(24.0, "T3")],
        },
        "p90_threshold": 5.98,   # 13.0 * 0.46
        "fixed_tp": 26.0,        # 13.0 * 2.0
    },
    "USDCHF": {
        "name": "USD/CHF",
        "pip_value": 0.0001,
        "k_factor": 0.46,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 25.0, "au": 11.0, "trigger": 11.0},
            "T2": {"ar_max": 50.0, "au": 15.0, "trigger": 15.0},
            "T3": {"ar_max": 100.0, "au": 20.0, "trigger": 20.0},
        },
        "gear_shifts": {
            "T1": [(15.0, "T2"), (20.0, "T3")],
            "T2": [(20.0, "T3")],
        },
        "p90_threshold": 5.06,   # 11.0 * 0.46  (manual calibration: ~4.8p)
        "fixed_tp": 22.0,        # 11.0 * 2.0
    },
    "USDJPY": {
        "name": "USD/JPY",
        "pip_value": 0.01,
        "k_factor": 0.46,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 40.0, "au": 16.0, "trigger": 19.0},
            "T2": {"ar_max": 80.0, "au": 26.0, "trigger": 31.0},
            "T3": {"ar_max": 150.0, "au": 44.0, "trigger": 53.0},
        },
        "gear_shifts": {
            "T1": [(31.0, "T2"), (53.0, "T3")],
            "T2": [(53.0, "T3")],
        },
        "p90_threshold": 7.36,   # 16.0 * 0.46
        "fixed_tp": 32.0,        # 16.0 * 2.0
    },
    "AUDUSD": {
        "name": "AUD/USD",
        "pip_value": 0.0001,
        "k_factor": 0.46,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 25.0, "au": 11.0, "trigger": 13.0},
            "T2": {"ar_max": 50.0, "au": 14.0, "trigger": 17.0},
            "T3": {"ar_max": 80.0, "au": 18.0, "trigger": 21.0},
        },
        "gear_shifts": {
            "T1": [(17.0, "T2"), (21.0, "T3")],
            "T2": [(21.0, "T3")],
        },
        "p90_threshold": 5.06,   # 11.0 * 0.46
        "fixed_tp": 22.0,        # 11.0 * 2.0
    },
    "NZDUSD": {
        "name": "NZD/USD",
        "pip_value": 0.0001,
        "k_factor": 0.46,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 14.0, "trigger": 17.0},
            "T2": {"ar_max": 60.0, "au": 17.0, "trigger": 20.0},
            "T3": {"ar_max": 60.0, "au": 21.0, "trigger": 25.0},
        },
        "gear_shifts": {
            "T1": [(20.0, "T2"), (25.0, "T3")],
            "T2": [(25.0, "T3")],
        },
        "p90_threshold": 6.44,   # 14.0 * 0.46
        "fixed_tp": 28.0,        # 14.0 * 2.0
    },
    # ─────────────────────────────────────────────────────
    # FOREX CROSSES (ORIGINAL)
    # ─────────────────────────────────────────────────────
    "CHFJPY": {
        "name": "CHF/JPY",
        "pip_value": 0.01,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 14.0, "trigger": 17.0},
            "T2": {"ar_max": 60.0, "au": 24.0, "trigger": 29.0},
            "T3": {"ar_max": 60.0, "au": 42.0, "trigger": 50.0},
        },
        "gear_shifts": {
            "T1": [(29.0, "T2"), (50.0, "T3")],
            "T2": [(50.0, "T3")],
        },
        "p90_threshold": 6.72,   # 14.0 * 0.48
        "fixed_tp": 28.0,        # 14.0 * 2.0
    },
    "GBPJPY": {
        "name": "GBP/JPY",
        "pip_value": 0.01,
        "k_factor": 0.48,
        "sl_method": "OCC_PLUS_5P",
        "sl_buffer": 5.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 19.0, "trigger": 23.0},
            "T2": {"ar_max": 60.0, "au": 29.0, "trigger": 35.0},
            "T3": {"ar_max": 60.0, "au": 48.0, "trigger": 58.0},
        },
        "gear_shifts": {
            "T1": [(35.0, "T2"), (58.0, "T3")],
            "T2": [(58.0, "T3")],
        },
        "p90_threshold": 9.12,   # 19.0 * 0.48
        "fixed_tp": 38.0,        # 19.0 * 2.0
    },
    "GBPAUD": {
        "name": "GBP/AUD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_PLUS_8P",
        "sl_buffer": 8.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 21.0, "trigger": 25.0},
            "T2": {"ar_max": 60.0, "au": 32.0, "trigger": 38.0},
            "T3": {"ar_max": 60.0, "au": 52.0, "trigger": 63.0},
        },
        "gear_shifts": {
            "T1": [(38.0, "T2"), (63.0, "T3")],
            "T2": [(63.0, "T3")],
        },
        "p90_threshold": 10.08,  # 21.0 * 0.48
        "fixed_tp": 42.0,        # 21.0 * 2.0
    },
    "GBPNZD": {
        "name": "GBP/NZD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_PLUS_8P",
        "sl_buffer": 8.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 24.0, "trigger": 29.0},
            "T2": {"ar_max": 60.0, "au": 36.0, "trigger": 43.0},
            "T3": {"ar_max": 60.0, "au": 59.0, "trigger": 71.0},
        },
        "gear_shifts": {
            "T1": [(43.0, "T2"), (71.0, "T3")],
            "T2": [(71.0, "T3")],
        },
        "p90_threshold": 11.52,  # 24.0 * 0.48
        "fixed_tp": 48.0,        # 24.0 * 2.0
    },
    "GBPCHF": {
        "name": "GBP/CHF",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_PLUS_6P",
        "sl_buffer": 6.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 18.0, "trigger": 21.0},
            "T2": {"ar_max": 60.0, "au": 27.0, "trigger": 32.0},
            "T3": {"ar_max": 60.0, "au": 44.0, "trigger": 53.0},
        },
        "gear_shifts": {
            "T1": [(32.0, "T2"), (53.0, "T3")],
            "T2": [(53.0, "T3")],
        },
        "p90_threshold": 8.64,   # 18.0 * 0.48
        "fixed_tp": 36.0,        # 18.0 * 2.0
    },
    # ─────────────────────────────────────────────────────
    # FOREX CROSSES (NEW — K-Means calibrated 2026-06-03)
    # Percentile capping: T1<p75, T3<p95, T3 AU from p90
    # ─────────────────────────────────────────────────────
    "EURGBP": {
        "name": "EUR/GBP",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 7, "trigger": 8},
            "T2": {"ar_max": 60.0, "au": 14, "trigger": 17},
            "T3": {"ar_max": 60.0, "au": 19, "trigger": 23},
        },
        "gear_shifts": {
            "T1": [(8, "T2"), (17, "T3")],
            "T2": [(17, "T3")],
        },
        "p90_threshold": 3.36,
        "fixed_tp": 14.0,
    },
    "EURJPY": {
        "name": "EUR/JPY",
        "pip_value": 0.01,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 29, "trigger": 35},
            "T2": {"ar_max": 60.0, "au": 63, "trigger": 75},
            "T3": {"ar_max": 60.0, "au": 63, "trigger": 76},
        },
        "gear_shifts": {
            "T1": [(35, "T2"), (75, "T3")],
            "T2": [(75, "T3")],
        },
        "p90_threshold": 13.92,
        "fixed_tp": 58.0,
    },
    "EURAUD": {
        "name": "EUR/AUD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 27, "trigger": 32},
            "T2": {"ar_max": 60.0, "au": 51, "trigger": 61},
            "T3": {"ar_max": 60.0, "au": 58, "trigger": 69},
        },
        "gear_shifts": {
            "T1": [(32, "T2"), (61, "T3")],
            "T2": [(61, "T3")],
        },
        "p90_threshold": 12.96,
        "fixed_tp": 54.0,
    },
    "EURNZD": {
        "name": "EUR/NZD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 28, "trigger": 34},
            "T2": {"ar_max": 60.0, "au": 49, "trigger": 59},
            "T3": {"ar_max": 60.0, "au": 61, "trigger": 73},
        },
        "gear_shifts": {
            "T1": [(34, "T2"), (59, "T3")],
            "T2": [(59, "T3")],
        },
        "p90_threshold": 13.44,
        "fixed_tp": 56.0,
    },
    "EURCHF": {
        "name": "EUR/CHF",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 9, "trigger": 11},
            "T2": {"ar_max": 60.0, "au": 19, "trigger": 23},
            "T3": {"ar_max": 60.0, "au": 22, "trigger": 27},
        },
        "gear_shifts": {
            "T1": [(11, "T2"), (23, "T3")],
            "T2": [(23, "T3")],
        },
        "p90_threshold": 4.32,
        "fixed_tp": 18.0,
    },
    "EURCAD": {
        "name": "EUR/CAD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 13, "trigger": 16},
            "T2": {"ar_max": 60.0, "au": 25, "trigger": 31},
            "T3": {"ar_max": 60.0, "au": 32, "trigger": 38},
        },
        "gear_shifts": {
            "T1": [(16, "T2"), (31, "T3")],
            "T2": [(31, "T3")],
        },
        "p90_threshold": 6.24,
        "fixed_tp": 26.0,
    },
    "USDCAD": {
        "name": "USD/CAD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 11, "trigger": 13},
            "T2": {"ar_max": 60.0, "au": 20, "trigger": 24},
            "T3": {"ar_max": 60.0, "au": 27, "trigger": 32},
        },
        "gear_shifts": {
            "T1": [(13, "T2"), (24, "T3")],
            "T2": [(24, "T3")],
        },
        "p90_threshold": 5.28,
        "fixed_tp": 22.0,
    },
    "AUDJPY": {
        "name": "AUD/JPY",
        "pip_value": 0.01,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 21, "trigger": 26},
            "T2": {"ar_max": 60.0, "au": 45, "trigger": 53},
            "T3": {"ar_max": 60.0, "au": 49, "trigger": 59},
        },
        "gear_shifts": {
            "T1": [(26, "T2"), (53, "T3")],
            "T2": [(53, "T3")],
        },
        "p90_threshold": 10.08,
        "fixed_tp": 42.0,
    },
    "AUDNZD": {
        "name": "AUD/NZD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 12, "trigger": 14},
            "T2": {"ar_max": 60.0, "au": 24, "trigger": 29},
            "T3": {"ar_max": 60.0, "au": 27, "trigger": 33},
        },
        "gear_shifts": {
            "T1": [(14, "T2"), (29, "T3")],
            "T2": [(29, "T3")],
        },
        "p90_threshold": 5.76,
        "fixed_tp": 24.0,
    },
    "AUDCHF": {
        "name": "AUD/CHF",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 10, "trigger": 12},
            "T2": {"ar_max": 60.0, "au": 18, "trigger": 22},
            "T3": {"ar_max": 60.0, "au": 23, "trigger": 28},
        },
        "gear_shifts": {
            "T1": [(12, "T2"), (22, "T3")],
            "T2": [(22, "T3")],
        },
        "p90_threshold": 4.8,
        "fixed_tp": 20.0,
    },
    "AUDCAD": {
        "name": "AUD/CAD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 13, "trigger": 16},
            "T2": {"ar_max": 60.0, "au": 24, "trigger": 29},
            "T3": {"ar_max": 60.0, "au": 28, "trigger": 33},
        },
        "gear_shifts": {
            "T1": [(16, "T2"), (29, "T3")],
            "T2": [(29, "T3")],
        },
        "p90_threshold": 6.24,
        "fixed_tp": 26.0,
    },
    "NZDJPY": {
        "name": "NZD/JPY",
        "pip_value": 0.01,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 20, "trigger": 24},
            "T2": {"ar_max": 60.0, "au": 44, "trigger": 53},
            "T3": {"ar_max": 60.0, "au": 43, "trigger": 51},
        },
        "gear_shifts": {
            "T1": [(24, "T2"), (53, "T3")],
            "T2": [(53, "T3")],
        },
        "p90_threshold": 9.6,
        "fixed_tp": 40.0,
    },
    "NZDCHF": {
        "name": "NZD/CHF",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 9, "trigger": 11},
            "T2": {"ar_max": 60.0, "au": 18, "trigger": 22},
            "T3": {"ar_max": 60.0, "au": 21, "trigger": 25},
        },
        "gear_shifts": {
            "T1": [(11, "T2"), (22, "T3")],
            "T2": [(22, "T3")],
        },
        "p90_threshold": 4.32,
        "fixed_tp": 18.0,
    },
    "NZDCAD": {
        "name": "NZD/CAD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 12, "trigger": 15},
            "T2": {"ar_max": 60.0, "au": 22, "trigger": 26},
            "T3": {"ar_max": 60.0, "au": 27, "trigger": 32},
        },
        "gear_shifts": {
            "T1": [(15, "T2"), (26, "T3")],
            "T2": [(26, "T3")],
        },
        "p90_threshold": 5.76,
        "fixed_tp": 24.0,
    },
    "CADJPY": {
        "name": "CAD/JPY",
        "pip_value": 0.01,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 19, "trigger": 23},
            "T2": {"ar_max": 60.0, "au": 43, "trigger": 51},
            "T3": {"ar_max": 60.0, "au": 42, "trigger": 50},
        },
        "gear_shifts": {
            "T1": [(23, "T2"), (51, "T3")],
            "T2": [(51, "T3")],
        },
        "p90_threshold": 9.12,
        "fixed_tp": 38.0,
    },
    "CADCHF": {
        "name": "CAD/CHF",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_EXACT",
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 7, "trigger": 9},
            "T2": {"ar_max": 60.0, "au": 14, "trigger": 17},
            "T3": {"ar_max": 60.0, "au": 17, "trigger": 21},
        },
        "gear_shifts": {
            "T1": [(9, "T2"), (17, "T3")],
            "T2": [(17, "T3")],
        },
        "p90_threshold": 3.36,
        "fixed_tp": 14.0,
    },
    "GBPCAD": {
        "name": "GBP/CAD",
        "pip_value": 0.0001,
        "k_factor": 0.48,
        "sl_method": "OCC_PLUS_6P",
        "sl_buffer": 6.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 20, "trigger": 24},
            "T2": {"ar_max": 60.0, "au": 45, "trigger": 55},
            "T3": {"ar_max": 60.0, "au": 42, "trigger": 50},
        },
        "gear_shifts": {
            "T1": [(24, "T2"), (55, "T3")],
            "T2": [(55, "T3")],
        },
        "p90_threshold": 9.6,
        "fixed_tp": 40.0,
    },
    # ─────────────────────────────────────────────────────
    # METALS
    # ─────────────────────────────────────────────────────
    "XAUUSD": {
        "name": "XAU/USD",
        "pip_value": 0.1,
        "k_factor": 0.50,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": {"T1": 12.0, "T2": 12.0, "T3": 18.0},
        "tiers": {
            "T1": {"ar_max": 100.0, "au": 16.0, "trigger": 19.0},
            "T2": {"ar_max": 200.0, "au": 29.0, "trigger": 35.0},
            "T3": {"ar_max": 400.0, "au": 48.0, "trigger": 58.0},
        },
        "gear_shifts": {
            "T1": [(35.0, "T2"), (58.0, "T3")],
            "T2": [(58.0, "T3")],
        },
        "p90_threshold": 8.0,    # 16.0 * 0.50
        "fixed_tp": 32.0,        # 16.0 * 2.0
        "class": "B-Tier",
    },
    "XAGUSD": {
        "name": "XAG/USD",
        "pip_value": 0.01,
        "k_factor": 0.50,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": {"T1": 0.5, "T2": 0.8, "T3": 1.2},
        "tiers": {
            "T1": {"ar_max": 200.0, "au": 25.0, "trigger": 30.0},
            "T2": {"ar_max": 400.0, "au": 35.0, "trigger": 42.0},
            "T3": {"ar_max": 800.0, "au": 50.0, "trigger": 60.0},
        },
        "gear_shifts": {
            "T1": [(1.9, "T2"), (3.1, "T3")],
            "T2": [(3.1, "T3")],
        },
        "p90_threshold": 0.45,   # 0.9 * 0.50
        "fixed_tp": 1.8,         # 0.9 * 2.0
        "class": "C-Tier",
    },
    # ─────────────────────────────────────────────────────
    # CRYPTO
    # ─────────────────────────────────────────────────────
    "BTCUSD": {
        "name": "BTC/USD",
        "pip_value": 1.0,
        "k_factor": 0.52,
        "sl_method": "OCC_PLUS_BUFFER",
        "sl_buffer": 50.0,
        "tiers": {
            "T1": {"ar_max": 15000.0, "au": 120.0, "trigger": 140.0},
            "T2": {"ar_max": 30000.0, "au": 300.0, "trigger": 360.0},
            "T3": {"ar_max": 55000.0, "au": 600.0, "trigger": 720.0},
        },
        "gear_shifts": {
            "T1": [(654.0, "T2"), (1392.0, "T3")],
            "T2": [(1392.0, "T3")],
        },
        "p90_threshold": 106.6,  # 205.0 * 0.52
        "fixed_tp": 410.0,       # 205.0 * 2.0
        "class": "B-Tier",
    },
    "ETHUSD": {
        "name": "ETH/USD",
        "pip_value": 1.0,
        "k_factor": 0.52,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": 5.0,
        "tiers": {
            "T1": {"ar_max": 750.0, "au": 35.0, "trigger": 42.0},
            "T2": {"ar_max": 1500.0, "au": 42.0, "trigger": 52.0},
            "T3": {"ar_max": 2500.0, "au": 52.0, "trigger": 65.0},
        },
        "gear_shifts": {
            "T1": [(52.0, "T2"), (65.0, "T3")],
            "T2": [(65.0, "T3")],
        },
        "p90_threshold": 18.2,   # 35.0 * 0.52
        "fixed_tp": 70.0,        # 35.0 * 2.0
        "class": "B-Tier",
    },
    "SOLUSD": {
        "name": "SOL/USD",
        "pip_value": 1.0,
        "k_factor": 0.52,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": 0.5,
        "tiers": {
            "T1": {"ar_max": 5.0, "au": 1.5, "trigger": 1.8},
            "T2": {"ar_max": 10.0, "au": 2.5, "trigger": 3.0},
            "T3": {"ar_max": 15.0, "au": 4.0, "trigger": 5.0},
        },
        "gear_shifts": {
            "T1": [(3.0, "T2"), (5.0, "T3")],
            "T2": [(5.0, "T3")],
        },
        "p90_threshold": 0.78,   # 1.5 * 0.52
        "fixed_tp": 3.0,         # 1.5 * 2.0
        "class": "B-Tier",
    },
    "XRPUSD": {
        "name": "XRP/USD",
        "pip_value": 0.0001,
        "k_factor": 0.52,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": 0.005,
        "tiers": {
            "T1": {"ar_max": 0.05, "au": 0.015, "trigger": 0.018},
            "T2": {"ar_max": 0.10, "au": 0.025, "trigger": 0.030},
            "T3": {"ar_max": 0.15, "au": 0.040, "trigger": 0.050},
        },
        "gear_shifts": {
            "T1": [(0.030, "T2"), (0.050, "T3")],
            "T2": [(0.050, "T3")],
        },
        "p90_threshold": 0.00078,  # 0.0015 * 0.52
        "fixed_tp": 0.0030,        # 0.0015 * 2.0
        "class": "B-Tier",
    },
    "USDSEK": {
        "name": "USD/SEK",
        "pip_value": 0.0001,
        "k_factor": 0.46,
        "sl_method": "OCC_PLUS_BUFFER",
        "sl_buffer": 5.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 15.0, "trigger": 18.0},
            "T2": {"ar_max": 80.0, "au": 20.0, "trigger": 24.0},
            "T3": {"ar_max": 100.0, "au": 25.0, "trigger": 30.0},
        },
        "gear_shifts": {
            "T1": [(24.0, "T2"), (30.0, "T3")],
            "T2": [(30.0, "T3")],
        },
        "p90_threshold": 6.9,   # 15.0 * 0.46
        "fixed_tp": 30.0,       # 15.0 * 2.0
        "class": "B-Tier",
    },
    # ─────────────────────────────────────────────────────
    # INDICES
    # ─────────────────────────────────────────────────────
    "NAS100": {
        "name": "NAS100",
        "pip_value": 1.0,
        "k_factor": 0.48,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": 12.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 34.0, "trigger": 41.0},
            "T2": {"ar_max": 60.0, "au": 64.0, "trigger": 77.0},
            "T3": {"ar_max": 60.0, "au": 122.0, "trigger": 146.0},
        },
        "gear_shifts": {
            "T1": [(77.0, "T2"), (146.0, "T3")],
            "T2": [(146.0, "T3")],
        },
        "p90_threshold": 16.32,  # 34.0 * 0.48
        "fixed_tp": 68.0,        # 34.0 * 2.0
        "class": "B-Tier",
    },
    "US500": {
        "name": "US500",
        "pip_value": 1.0,
        "k_factor": 0.48,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": 7.0,
        "tiers": {
            "T1": {"ar_max": 750.0, "au": 19.0, "trigger": 23.0},
            "T2": {"ar_max": 1500.0, "au": 37.0, "trigger": 44.0},
            "T3": {"ar_max": 2500.0, "au": 71.0, "trigger": 85.0},
        },
        "gear_shifts": {
            "T1": [(44.0, "T2"), (85.0, "T3")],
            "T2": [(85.0, "T3")],
        },
        "p90_threshold": 9.12,   # 19.0 * 0.48
        "fixed_tp": 38.0,        # 19.0 * 2.0
        "class": "B-Tier",
    },
    "DE30": {
        "name": "DE30",
        "pip_value": 1.0,
        "k_factor": 0.48,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": 9.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 22.0, "trigger": 27.0},
            "T2": {"ar_max": 60.0, "au": 42.0, "trigger": 51.0},
            "T3": {"ar_max": 60.0, "au": 80.0, "trigger": 96.0},
        },
        "gear_shifts": {
            "T1": [(51.0, "T2"), (96.0, "T3")],
            "T2": [(96.0, "T3")],
        },
        "p90_threshold": 10.56,  # 22.0 * 0.48
        "fixed_tp": 44.0,        # 22.0 * 2.0
        "class": "B-Tier",
    },
    "FR40": {
        "name": "FR40",
        "pip_value": 1.0,
        "k_factor": 0.48,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": 7.0,
        "tiers": {
            "T1": {"ar_max": 60.0, "au": 19.0, "trigger": 23.0},
            "T2": {"ar_max": 60.0, "au": 36.0, "trigger": 43.0},
            "T3": {"ar_max": 60.0, "au": 68.0, "trigger": 82.0},
        },
        "gear_shifts": {
            "T1": [(43.0, "T2"), (82.0, "T3")],
            "T2": [(82.0, "T3")],
        },
        "p90_threshold": 9.12,   # 19.0 * 0.48
        "fixed_tp": 38.0,        # 19.0 * 2.0
        "class": "C-Tier",
    },
    "HK50": {
        "name": "HK50",
        "pip_value": 1.0,
        "k_factor": 0.48,
        "sl_method": "FIXED_BUFFER",
        "sl_buffer": 35.0,
        "tiers": {
            "T1": {"ar_max": 10000.0, "au": 92.0, "trigger": 110.0},
            "T2": {"ar_max": 20000.0, "au": 170.0, "trigger": 204.0},
            "T3": {"ar_max": 35000.0, "au": 325.0, "trigger": 390.0},
        },
        "gear_shifts": {
            "T1": [(204.0, "T2"), (390.0, "T3")],
            "T2": [(390.0, "T3")],
        },
        "p90_threshold": 44.16,  # 92.0 * 0.48
        "fixed_tp": 184.0,       # 92.0 * 2.0
        "class": "C-Tier",
    },
}


def get_config(asset_key: str) -> dict:
    """
    Retrieve config dictionary for a given asset.
    Usage: config = get_config("USDCHF")
    """
    if asset_key not in ASSET_CONFIGS:
        raise KeyError(
            f"Asset '{asset_key}' not found. Available: {list(ASSET_CONFIGS.keys())}"
        )
    return ASSET_CONFIGS[asset_key]
