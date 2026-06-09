"""
CEREBUS P90 V5 — Per-Asset Config Generator
Generates Pine Script with per-asset P90 thresholds from asset_configs.py
"""

# Per-asset P90 thresholds from quant-lab/configs/asset_configs.py
# Format: "TICKER_KEY": {"p90": float, "pip": float, "name": str}
ASSET_P90_CONFIGS = {
    # Forex Majors
    "EURUSD": {"p90": 4.6,  "pip": 0.0001, "name": "EUR/USD"},
    "GBPUSD": {"p90": 5.98, "pip": 0.0001, "name": "GBP/USD"},
    "USDCHF": {"p90": 5.06, "pip": 0.0001, "name": "USD/CHF"},
    "USDJPY": {"p90": 7.36, "pip": 0.01,   "name": "USD/JPY"},
    "AUDUSD": {"p90": 5.06, "pip": 0.0001, "name": "AUD/USD"},
    "NZDUSD": {"p90": 6.44, "pip": 0.0001, "name": "NZD/USD"},
    # Forex Crosses
    "CHFJPY": {"p90": 6.72,  "pip": 0.01,   "name": "CHF/JPY"},
    "GBPJPY": {"p90": 9.12,  "pip": 0.01,   "name": "GBP/JPY"},
    "GBPAUD": {"p90": 10.08, "pip": 0.0001, "name": "GBP/AUD"},
    "GBPNZD": {"p90": 11.52, "pip": 0.0001, "name": "GBP/NZD"},
    "GBPCHF": {"p90": 8.64,  "pip": 0.0001, "name": "GBP/CHF"},
    "EURGBP": {"p90": 3.36,  "pip": 0.0001, "name": "EUR/GBP"},
    "EURJPY": {"p90": 13.92, "pip": 0.01,   "name": "EUR/JPY"},
    "EURAUD": {"p90": 12.96, "pip": 0.0001, "name": "EUR/AUD"},
    "EURNZD": {"p90": 13.44, "pip": 0.0001, "name": "EUR/NZD"},
    "EURCHF": {"p90": 4.32,  "pip": 0.0001, "name": "EUR/CHF"},
    "EURCAD": {"p90": 6.24,  "pip": 0.0001, "name": "EUR/CAD"},
    "USDCAD": {"p90": 5.28,  "pip": 0.0001, "name": "USD/CAD"},
    "AUDJPY": {"p90": 10.08, "pip": 0.01,   "name": "AUD/JPY"},
    "AUDNZD": {"p90": 5.76,  "pip": 0.0001, "name": "AUD/NZD"},
    "AUDCHF": {"p90": 4.8,   "pip": 0.0001, "name": "AUD/CHF"},
    "AUDCAD": {"p90": 6.24,  "pip": 0.0001, "name": "AUD/CAD"},
    "NZDJPY": {"p90": 9.6,   "pip": 0.01,   "name": "NZD/JPY"},
    "NZDCHF": {"p90": 4.32,  "pip": 0.0001, "name": "NZD/CHF"},
    "NZDCAD": {"p90": 5.76,  "pip": 0.0001, "name": "NZD/CAD"},
    "CADJPY": {"p90": 9.12,  "pip": 0.01,   "name": "CAD/JPY"},
    "CADCHF": {"p90": 3.36,  "pip": 0.0001, "name": "CAD/CHF"},
    "GBPCAD": {"p90": 9.6,   "pip": 0.0001, "name": "GBP/CAD"},
    # Metals
    "XAUUSD": {"p90": 8.0,   "pip": 0.1,    "name": "XAU/USD"},
    "XAGUSD": {"p90": 0.45,  "pip": 0.01,   "name": "XAG/USD"},
    # Crypto
    "BTCUSD": {"p90": 106.6, "pip": 1.0,    "name": "BTC/USD"},
    "ETHUSD": {"p90": 18.2,  "pip": 1.0,    "name": "ETH/USD"},
    # Indices
    "NAS100": {"p90": 16.32, "pip": 1.0,    "name": "NAS100"},
    "US500":  {"p90": 9.12,  "pip": 1.0,    "name": "US500"},
    "DE30":   {"p90": 10.56, "pip": 1.0,    "name": "DE30"},
    "FR40":   {"p90": 9.12,  "pip": 1.0,    "name": "FR40"},
    "HK50":   {"p90": 44.16, "pip": 1.0,    "name": "HK50"},
}
