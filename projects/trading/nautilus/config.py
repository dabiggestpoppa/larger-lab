"""Nautilus Trader configuration for Quant Lab."""
import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

# ── Oanda Configuration ──────────────────────────────────────────
OANDA_API_KEY = os.getenv("OANDA_API_KEY", "")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID", "")
OANDA_ENVIRONMENT = os.getenv("OANDA_ENVIRONMENT", "practice")

# ── Data Directories ─────────────────────────────────────────────
DATA_DIR = os.getenv("NAUTILUS_DATA_DIR", r"C:\Users\wifik\Desktop\projects\larger-lab\data")
DOWNLOADS_DIR = r"C:\Users\wifik\Downloads"

# ── Trading Mode ─────────────────────────────────────────────────
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "100000"))

# ── Symmetry Trap Session Timing (UTC) ───────────────────────────
# Per CEREBUS FX v4.0 manual (page 143):
#   Asian Range: 7PM-3AM EST = 19:00-03:00 UTC
#   Bias Window: 3AM-12PM EST = 08:00-17:00 UTC
#   Hard Exit: 12:00 PM EST = 17:00 UTC
ASIAN_SESSION_START_UTC = 19    # 19:00 UTC = 7:00 PM EST (previous day)
ASIAN_SESSION_END_UTC = 3       # 03:00 UTC = 3:00 AM EST
BIAS_WINDOW_START_UTC = 8       # 08:00 UTC = 3:00 AM EST
BIAS_WINDOW_END_UTC = 17        # 17:00 UTC = 12:00 PM EST
HARD_EXIT_HOUR_UTC = 17         # 17:00 UTC = 12:00 PM EST
NEW_DAY_START_UTC = 18          # 18:00 UTC = 1:00 PM EST (reset for new day)

# ── P90 Activation Thresholds (pips) by time window ─────────────
ACTIVATION_THRESHOLDS = {
    "early": 4.1,   # 2:00-4:00 AM EST
    "mid": 4.6,     # 4:00-8:00 AM EST
    "late": 5.9,    # 8:00-10:00 AM EST
    "cutoff": 6.2,  # 10:00-11:00 AM EST
}

# ── Fibonacci Extension Levels (CEREBUS constraint states) ───────
FIB_LEVELS = {
    "ATOM_T1": 0.236,
    "ATOM_T2": 0.382,
    "ATOM_T3": 0.500,
    "GOLDEN": 0.618,
    "DEEP": 0.786,
    "FULL": 1.000,
    "EXT_127": 1.27,
    "EXT_138": 1.382,
    "EXT_150": 1.500,
    "STALL_162": 1.618,
    "STALL_168": 1.68,
    "DEEP_200": 2.00,
    "EXT_261": 2.618,
    "KILL_132": 1.32,
}

# ── Tier Configuration (Asian Range → Position Sizing) ───────────
# Per CEREBUS FX v4.0 manual (page 140):
#   T1: AR < 20p  | Atomic Unit = 10p
#   T2: AR 20-30p | Atomic Unit = 12p
#   T3: AR 30-45p | Atomic Unit = 15p
#   NO-GO: AR > 45p
TIER_CONFIG = {
    "T1": {"label": "Gold", "max_pips": 20, "size_pct": 1.0, "expansion": 3.12, "atomic": 10},
    "T2": {"label": "Standard", "min_pips": 20, "max_pips": 30, "size_pct": 0.75, "expansion": 2.68, "atomic": 12},
    "T3": {"label": "Caution", "min_pips": 30, "max_pips": 45, "size_pct": 0.50, "expansion": 2.18, "atomic": 15},
    "NO_GO": {"label": "Stand Down", "min_pips": 45, "size_pct": 0.0, "expansion": 1.52, "atomic": 0},
}

# ── Risk Management (CEREBUS v4.0 spec) ─────────────────────────
RISK_PER_ACTIVATION_PCT = Decimal("0.0012")
MAX_CONCURRENT_RISK_PCT = Decimal("0.0036")
PROP_HARD_LIMIT_PCT = Decimal("0.004")
DAILY_LOSS_LIMIT_PCT = Decimal("0.005")
ATOM_BUFFER_PCT = Decimal("0.90")
MAX_CASCADES = 3
TP1_PCT = Decimal("0.25")
TP2_PCT = Decimal("0.50")

# ── Pip Values per Instrument ────────────────────────────────────
PIP_VALUES = {
    "EUR/USD": 10.0, "GBP/USD": 10.0, "USD/JPY": 10.0,
    "USD/CHF": 10.0, "USD/CAD": 10.0, "AUD/USD": 10.0,
    "NZD/USD": 10.0, "XAU/USD": 100.0, "US500": 50.0,
    "USTEC100": 20.0, "DE30": 50.0, "FR40": 50.0,
    "HK50": 50.0, "CHFJPY": 10.0, "GBPJPY": 10.0, "EURJPY": 10.0,
}


def get_oanda_config():
    return {"api_key": OANDA_API_KEY, "account_id": OANDA_ACCOUNT_ID, "environment": OANDA_ENVIRONMENT}


def validate_config():
    errors = []
    if not OANDA_API_KEY or "your_" in OANDA_API_KEY:
        errors.append("OANDA_API_KEY not set in .env")
    if not OANDA_ACCOUNT_ID or "your_" in OANDA_ACCOUNT_ID:
        errors.append("OANDA_ACCOUNT_ID not set in .env")
    if errors:
        print("⚠️  Configuration issues:")
        for e in errors:
            print(f"   - {e}")
        return False
    print("✅ Nautilus Trader configuration valid")
    return True


def get_pip_value(instrument_name: str) -> float:
    return PIP_VALUES.get(instrument_name, 10.0)
