"""
Generate CEREBUS P90 V6 PER-ASSET strategy with proper per-asset, per-hour thresholds.
Based on P90_Strategy.md SYMBOL_P90 logic: scale EUR/USD base thresholds by asset ratio.
"""
from pathlib import Path

# ─── Base EUR/USD P90 thresholds by EST hour ───
BASE_THRESHOLDS = {
    2: 4.1, 3: 4.1,
    4: 4.6, 5: 4.6,
    6: 4.6, 7: 5.9,
    8: 5.9, 9: 6.2,
    10: 6.2,
}

# ─── Asset p90_thresholds from asset_configs.py ───
ASSETS = {
    "EURUSD":  4.6,   "GBPUSD":  5.98,  "USDCHF":  5.06,  "USDJPY":  7.36,
    "AUDUSD":  5.06,  "NZDUSD":  6.44,  "CHFJPY":  6.72,  "GBPJPY":  9.12,
    "GBPAUD":  10.08, "GBPNZD":  11.52, "GBPCHF":  8.64,  "EURGBP":  3.36,
    "EURJPY":  13.92, "EURAUD":  12.96, "EURNZD":  13.44, "EURCHF":  4.32,
    "EURCAD":  6.24,  "USDCAD":  5.28,  "AUDJPY":  10.08, "AUDNZD":  5.76,
    "AUDCHF":  4.8,   "AUDCAD":  6.24,  "NZDJPY":  9.6,   "NZDCHF":  4.32,
    "NZDCAD":  5.76,  "CADJPY":  9.12,  "CADCHF":  3.36,  "GBPCAD":  9.6,
    "XAUUSD":  8.0,   "XAGUSD":  0.45,  "BTCUSD":  106.6, "ETHUSD":  18.2,
    "NAS100":  16.32,  "US500":   9.12,  "DE30":    10.56, "FR40":    9.12,
    "HK50":    44.16,
}

# ─── Ticker detection patterns ───
TICKER_PATTERNS = {
    "EURUSD": ['EURUSD'],
    "GBPUSD": ['GBPUSD'],
    "USDCHF": ['USDCHF'],
    "USDJPY": ['USDJPY'],
    "AUDUSD": ['AUDUSD'],
    "NZDUSD": ['NZDUSD'],
    "CHFJPY": ['CHFJPY'],
    "GBPJPY": ['GBPJPY'],
    "GBPAUD": ['GBPAUD'],
    "GBPNZD": ['GBPNZD'],
    "GBPCHF": ['GBPCHF'],
    "EURGBP": ['EURGBP'],
    "EURJPY": ['EURJPY'],
    "EURAUD": ['EURAUD'],
    "EURNZD": ['EURNZD'],
    "EURCHF": ['EURCHF'],
    "EURCAD": ['EURCAD'],
    "USDCAD": ['USDCAD'],
    "AUDJPY": ['AUDJPY'],
    "AUDNZD": ['AUDNZD'],
    "AUDCHF": ['AUDCHF'],
    "AUDCAD": ['AUDCAD'],
    "NZDJPY": ['NZDJPY'],
    "NZDCHF": ['NZDCHF'],
    "NZDCAD": ['NZDCAD'],
    "CADJPY": ['CADJPY'],
    "CADCHF": ['CADCHF'],
    "GBPCAD": ['GBPCAD'],
    "XAUUSD": ['XAUUSD', 'GOLD'],
    "XAGUSD": ['XAGUSD', 'SILVER'],
    "BTCUSD": ['BTCUSD', 'BTC'],
    "ETHUSD": ['ETHUSD', 'ETH'],
    "NAS100": ['NAS100', 'USTEC', 'US100', 'NASDAQ'],
    "US500":  ['US500', 'SPX500', 'SP500'],
    "DE30":   ['DE30', 'GER40', 'DAX'],
    "FR40":   ['FR40', 'CAC40'],
    "HK50":   ['HK50', 'HSI'],
}

# ─── Pip sizes ───
PIP_SIZES = {
    "USDJPY": 0.01, "GBPJPY": 0.01, "CHFJPY": 0.01, "EURJPY": 0.01,
    "AUDJPY": 0.01, "NZDJPY": 0.01, "CADJPY": 0.01,
    "BTCUSD": 1.0, "ETHUSD": 1.0, "NAS100": 1.0, "US500": 1.0,
    "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
    "XAUUSD": 0.1, "XAGUSD": 0.01,
}

def gen_hour_threshold_fn(hour_val_map, fn_name):
    """Generate a Pine Script function that returns per-asset P90 threshold for a given hour."""
    lines = [f'{fn_name}() =>']
    lines.append('    h = get_est_hour()')
    lines.append('    _t = syminfo.ticker')
    lines.append('')
    
    # Group by hour
    hours = sorted(set(BASE_THRESHOLDS.keys()))
    
    for i, h in enumerate(hours):
        if i == 0:
            lines.append(f'    h == {h} ?')
        else:
            lines.append(f'    : h == {h} ?')
        
        # Per-asset thresholds for this hour
        for j, (asset, base_p90) in enumerate(ASSETS.items()):
            ratio = base_p90 / 4.6
            val = round(BASE_THRESHOLDS[h] * ratio, 2)
            patterns = TICKER_PATTERNS[asset]
            cond = ' or '.join([f'str.contains(_t, "{p}")' for p in patterns])
            if j == 0 and asset == "EURUSD":
                lines.append(f'        {cond} ? {val}')
            else:
                lines.append(f'        : {cond} ? {val}')
        lines.append(f'        : {round(BASE_THRESHOLDS[h], 1)}')
        lines.append('')
    
    lines.append('    : 0.0')
    return '\n'.join(lines)


def gen_pip_size_lookup():
    """Generate pip_size ternary chain."""
    lines = []
    for asset, pip in PIP_SIZES.items():
        patterns = TICKER_PATTERNS[asset]
        cond = ' or '.join([f'str.contains(_t, "{p}")' for p in patterns])
        lines.append(f'           {cond} ? {pip}')
    lines.append('           : 0.0001')
    return '\n'.join(lines)


def gen_asset_name_lookup():
    """Generate asset name ternary chain."""
    lines = []
    for i, (asset, name) in enumerate([(a, a[:3]+'/'+a[3:]) if len(a) == 6 and a.isalpha() else (a, a) for a in ASSETS.keys()]):
        patterns = TICKER_PATTERNS[asset]
        cond = ' or '.join([f'str.contains(_t, "{p}")' for p in patterns])
        display_name = name if '/' in name else ASSETS.get(asset, asset)
        if i == 0:
            lines.append(f'    {cond} ? "{display_name}"')
        else:
            lines.append(f'    : {cond} ? "{display_name}"')
    lines.append('    : "UNKNOWN"')
    return '\n'.join(lines)


# ─── Generate the full Pine Script ───
output = []

# Read the base template
base_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\_tmp_p90_current.pine')
base_content = base_path.read_text(encoding='utf-8')

# We need to replace the threshold functions and input defaults
# Strategy: Replace the input defaults and the get_p90_threshold functions

# Generate new per-hour threshold function
def gen_combined_threshold_fn():
    """Generate a single function that returns the P90 threshold based on current hour and asset."""
    lines = ['get_p90_threshold() =>']
    lines.append('    h = get_est_hour()')
    lines.append('    _t = syminfo.ticker')
    lines.append('')
    
    hours = sorted(BASE_THRESHOLDS.keys())
    for i, h in enumerate(hours):
        prefix = '    ' if i == 0 else '    :'
        lines.append(f'{prefix} h == {h} ?')
        
        for j, (asset, base_p90) in enumerate(ASSETS.items()):
            ratio = base_p90 / 4.6
            val = round(BASE_THRESHOLDS[h] * ratio, 2)
            patterns = TICKER_PATTERNS[asset]
            cond = ' or '.join([f'str.contains(_t, "{p}")' for p in patterns])
            indent = '        '
            if j == 0:
                lines.append(f'{indent}{cond} ? {val}')
            else:
                lines.append(f'{indent}: {cond} ? {val}')
        lines.append(f'{indent}: {round(BASE_THRESHOLDS[h], 1)}')
        lines.append('')
    
    lines.append('    : 0.0')
    return '\n'.join(lines)


# ─── Build the complete new strategy ───
# We'll take the base file and surgically replace the key sections

# Read base lines
base_lines = base_content.split('\n')

# Find sections to replace
# 1. Replace strategy name
# 2. Replace input defaults with per-asset aware values
# 3. Replace get_p90_threshold_bull() and get_p90_threshold_bear() with combined function
# 4. Update info panel to show per-hour threshold

# Instead of surgical editing, let's generate the complete file from scratch
# using the base as a template for the non-P90 sections

pine_script = '''//@version=6
// CEREBUS P90 V6 PER-ASSET — All 35 assets with per-hour P90 thresholds
// Generated from asset_configs.py + P90_Strategy.md SYMBOL_P90 logic
// Original: CEREBUS 👁️ V5 LIVE PERFECT FORM FIXED v5 (untouched)
// This copy: per-asset, per-hour P90 thresholds (not single base * multiplier)

strategy("CEREBUS 👁️ P90 V6 PER-ASSET [ALL HOURS]", 
         overlay=true, 
         default_qty_type=strategy.percent_of_equity, 
         default_qty_value=100, 
         commission_type=strategy.commission.percent, 
         commission_value=0.01,
         max_labels_count=500)

// ============================================================================
// ⚙️ GLOBAL SETTINGS
// ============================================================================

enable_p90 = input.bool(true, "🔷 Enable Asian Range P90 System")
alert_on = input.bool(true, "Enable Alerts")
session_filter = input.bool(true, "Only Trade Prime Hours (2 AM - 12 PM EST)?")
max_drawdown_pct = input.float(3.0, "Max Daily Drawdown %")

// ============================================================================
// 📊 ASIAN RANGE P90 SYSTEM SETTINGS [EST TIMES]
// ============================================================================

asian_start_hour_est = input.int(19, "【P90】Asian Range Start Hour (EST)", minval=0, maxval=23, group="Asian Range P90")
asian_end_hour_est = input.int(3, "【P90】Asian Range End Hour (EST)", minval=0, maxval=23, group="Asian Range P90")
entry_start_hour_est = input.int(2, "【P90】Entry Start Hour (EST)", minval=0, maxval=23, group="Asian Range P90")
entry_end_hour_est = input.int(11, "【P90】Entry End Hour (EST)", minval=0, maxval=23, group="Asian Range P90")

ar_go_threshold = input.int(30, "【P90】Asian Range GO Threshold (pips)", minval=10, group="Asian Range P90")
ar_caution_threshold = input.int(45, "【P90】Asian Range CAUTION Threshold (pips)", minval=30, group="Asian Range P90")
ar_nogo_threshold = input.int(55, "【P90】Asian Range NO-GO Threshold (pips)", minval=45, group="Asian Range P90")

// Per-asset P90 thresholds are auto-looked-up. These inputs are fallback defaults (EUR/USD).
p90_bull_2_4am = input.float(4.1, "【P90 Bull】2-4 AM EST Fallback (pips)", group="Asian Range P90")
p90_bull_4_6am = input.float(4.6, "【P90 Bull】4-6 AM EST Fallback (pips)", group="Asian Range P90")
p90_bull_6_8am = input.float(4.6, "【P90 Bull】6-8 AM EST Fallback (pips)", group="Asian Range P90")
p90_bull_8_10am = input.float(5.9, "【P90 Bull】8-10 AM EST Fallback (pips)", group="Asian Range P90")
p90_bull_10_11am = input.float(6.2, "【P90 Bull】10-11 AM EST Fallback (pips)", group="Asian Range P90")

p90_bear_2_4am = input.float(4.1, "【P90 Bear】2-4 AM EST Fallback (pips)", group="Asian Range P90")
p90_bear_4_6am = input.float(4.6, "【P90 Bear】4-6 AM EST Fallback (pips)", group="Asian Range P90")
p90_bear_6_8am = input.float(4.6, "【P90 Bear】6-8 AM EST Fallback (pips)", group="Asian Range P90")
p90_bear_8_10am = input.float(5.9, "【P90 Bear】8-10 AM EST Fallback (pips)", group="Asian Range P90")
p90_bear_10_11am = input.float(6.2, "【P90 Bear】10-11 AM EST Fallback (pips)", group="Asian Range P90")

ext_25 = input.float(0.25, "【P90】Extension -25% Level", group="Asian Range P90")
ext_50 = input.float(0.50, "【P90】Extension -50% Level (Primary)", group="Asian Range P90")

sl_80fib_mult = input.float(0.80, "【P90】Position 1 SL - 80% Fib Multiplier", group="Asian Range P90")
sl_1_5x_mult = input.float(1.50, "【P90】Position 2 SL - 1.5x Candle Multiplier", group="Asian Range P90")
hold_time_minutes = input.int(120, "【P90】Hold Time (minutes)", group="Asian Range P90")
hard_exit_hour_est = input.int(12, "【P90】Hard Exit Hour (EST) - 12 PM EST", group="Asian Range P90")

pos1_size = input.float(40, "【P90】Position 1 Size (%)", minval=10, maxval=50, group="Asian Range P90")
pos2_size = input.float(40, "【P90】Position 2 Size (%)", minval=10, maxval=50, group="Asian Range P90")
pos3_size = input.float(20, "【P90】Position 3 Size (%)", minval=10, maxval=30, group="Asian Range P90")

add_time_minutes = input.int(45, "【P90】Add Position Time (minutes)", group="Asian Range P90")
add_extension_pips = input.float(8.0, "【P90】Add Position Extension Required (pips)", group="Asian Range P90")
violation_mult = input.float(1.32, "【P90】132% Violation Multiplier", group="Asian Range P90")

// ============================================================================
// 🧮 HELPER FUNCTIONS
// ============================================================================

get_est_hour() =>
    (hour(time, "UTC") - 5 + 24) % 24

get_est_minute() =>
    minute(time, "UTC")

in_asian_session() =>
    h = get_est_hour()
    (h >= asian_start_hour_est or h < asian_end_hour_est)

in_p90_entry_window() =>
    h = get_est_hour()
    (h >= entry_start_hour_est and h < entry_end_hour_est)

is_hard_exit_time() =>
    h = get_est_hour()
    h >= hard_exit_hour_est

// ============================================================================
// 🔍 PER-ASSET DETECTION (35 assets)
// ============================================================================

_sym = syminfo.ticker

// ─── Forex Majors ───
_eurusd = str.contains(_sym, "EURUSD")
_gbpusd = str.contains(_sym, "GBPUSD")
_usdchf = str.contains(_sym, "USDCHF")
_usdjpy = str.contains(_sym, "USDJPY")
_audusd = str.contains(_sym, "AUDUSD")
_nzdusd = str.contains(_sym, "NZDUSD")

// ─── Forex Crosses ───
_chfjpy = str.contains(_sym, "CHFJPY")
_gbpjpy = str.contains(_sym, "GBPJPY")
_gbpaud = str.contains(_sym, "GBPAUD")
_gbpnzd = str.contains(_sym, "GBPNZD")
_gbpchf = str.contains(_sym, "GBPCHF")
_eurgbp = str.contains(_sym, "EURGBP")
_eurjpy = str.contains(_sym, "EURJPY")
_euraud = str.contains(_sym, "EURAUD")
_eurnzd = str.contains(_sym, "EURNZD")
_eurchf = str.contains(_sym, "EURCHF")
_eurcad = str.contains(_sym, "EURCAD")
_usdcad = str.contains(_sym, "USDCAD")
_audjpy = str.contains(_sym, "AUDJPY")
_audnzd = str.contains(_sym, "AUDNZD")
_audchf = str.contains(_sym, "AUDCHF")
_audcad = str.contains(_sym, "AUDCAD")
_nzdjpy = str.contains(_sym, "NZDJPY")
_nzdchf = str.contains(_sym, "NZDCHF")
_nzdcad = str.contains(_sym, "NZDCAD")
_cadjpy = str.contains(_sym, "CADJPY")
_cadchf = str.contains(_sym, "CADCHF")
_gbpcad = str.contains(_sym, "GBPCAD")

// ─── Metals ───
_xauusd = str.contains(_sym, "XAUUSD") or str.contains(_sym, "GOLD")
_xagusd = str.contains(_sym, "XAGUSD") or str.contains(_sym, "SILVER")

// ─── Crypto ───
_btcusd = str.contains(_sym, "BTCUSD") or str.contains(_sym, "BTC")
_ethusd = str.contains(_sym, "ETHUSD") or str.contains(_sym, "ETH")

// ─── Indices ───
_nas100 = str.contains(_sym, "NAS100") or str.contains(_sym, "USTEC") or str.contains(_sym, "US100") or str.contains(_sym, "NASDAQ")
_us500  = str.contains(_sym, "US500") or str.contains(_sym, "SPX500") or str.contains(_sym, "SP500")
_de30   = str.contains(_sym, "DE30") or str.contains(_sym, "GER40") or str.contains(_sym, "DAX")
_fr40   = str.contains(_sym, "FR40") or str.contains(_sym, "CAC40")
_hk50   = str.contains(_sym, "HK50") or str.contains(_sym, "HSI")

// ─── Pip Size Auto-Detection ───
pip_size = _usdjpy or _gbpjpy or _chfjpy or _eurjpy or _audjpy or _nzdjpy or _cadjpy ? 0.01 :
           _btcusd or _ethusd or _nas100 or _us500 or _de30 or _fr40 or _hk50 ? 1.0 :
           _xauusd ? 0.1 :
           _xagusd ? 0.01 :
           0.0001

// ============================================================================
// ⏰ PER-ASSET, PER-HOUR P90 THRESHOLD LOOKUP
// Based on P90_Strategy.md SYMBOL_P90 logic:
//   asset_threshold[hour] = base_EURUSD_threshold[hour] * (asset_p90 / 4.6)
// Covers all 35 assets × 9 time windows (2AM-11AM EST)
// ============================================================================
'''

# Add the combined threshold function
pine_script += gen_combined_threshold_fn()
pine_script += '\n\n'

# Add asset name lookup
pine_script += '''// ─── Asset Name for Display ───
get_active_asset_name() =>
'''
name_lines = gen_asset_name_lookup()
pine_script += name_lines
pine_script += '\n\n'

# Now add the rest of the strategy (from the base file, the non-P90-specific parts)
# We need: shared drawdown, Asian range calc, signal detection, entries, exits, alerts, visualization, tables

pine_script += '''// ============================================================================
// 🛡️ SHARED DAILY DRAWDOWN PROTECTION
// ============================================================================

var float day_equity_start = na
new_day = ta.change(time("D"))
if new_day != 0
    day_equity_start := strategy.equity

drawdown_today = 100 * (strategy.equity - day_equity_start) / day_equity_start
drawdown_triggered = drawdown_today < -max_drawdown_pct

can_trade_shared = session_filter ? (get_est_hour() >= 2 and get_est_hour() < 12) : true
allow_trade_shared = can_trade_shared and not drawdown_triggered

// ============================================================================
// 📊 ASIAN RANGE CALCULATION
// ============================================================================

var float asian_high = na
var float asian_low = na
var bool asian_range_complete = false
var int asian_range_day = na
var int asian_open_bar = na
var int asian_close_bar = na

if get_est_hour() == asian_start_hour_est and get_est_minute() == 0
    asian_high := high
    asian_low := low
    asian_open_bar := bar_index
    asian_range_complete := false
    asian_range_day := dayofmonth

if in_asian_session() and not asian_range_complete
    asian_high := math.max(asian_high, high)
    asian_low := math.min(asian_low, low)
    
if get_est_hour() == asian_end_hour_est and get_est_minute() == 0
    asian_close_bar := bar_index - 1
    asian_range_complete := true

asian_range_pips = asian_range_complete ? (asian_high - asian_low) / pip_size : na

ext_25_long = asian_range_complete ? asian_high + (asian_range_pips * ext_25 * pip_size) : na
ext_50_long = asian_range_complete ? asian_high + (asian_range_pips * ext_50 * pip_size) : na
ext_25_short = asian_range_complete ? asian_low - (asian_range_pips * ext_25 * pip_size) : na
ext_50_short = asian_range_complete ? asian_low - (asian_range_pips * ext_50 * pip_size) : na

violation_long = asian_range_complete ? asian_high + (asian_range_pips * violation_mult * pip_size) : na
violation_short = asian_range_complete ? asian_low - (asian_range_pips * violation_mult * pip_size) : na

// ============================================================================
// 📊 P90 SIGNAL DETECTION
// ============================================================================

var int last_signal_time = na
var int last_entry_time = na
var float p90_entry_price = na
var float p90_candle_body = na
var string p90_direction = ""
var bool in_hold_period = false
var int signals_today = 0

var float entry_ext_25_long = na
var float entry_ext_50_long = na
var float entry_ext_25_short = na
var float entry_ext_50_short = na
var bool entry_ext_25_hit = false
var bool entry_ext_50_hit = false
var bool entry_violation_triggered = false

if get_est_hour() == 0 and get_est_minute() == 0
    signals_today := 0
    last_signal_time := na
    last_entry_time := na

candle_body_pips = math.abs(close - open) / pip_size

// Use the combined per-asset, per-hour threshold function
p90_threshold = get_p90_threshold()

p90_bull_candle = close > open and candle_body_pips >= p90_threshold
p90_bull_signal = enable_p90 and in_p90_entry_window() and asian_range_complete and p90_bull_candle and not in_hold_period and allow_trade_shared

p90_bear_candle = close < open and candle_body_pips >= p90_threshold
p90_bear_signal = enable_p90 and in_p90_entry_window() and asian_range_complete and p90_bear_candle and not in_hold_period and allow_trade_shared

if p90_bull_signal or p90_bear_signal
    signals_today := signals_today + 1
    last_signal_time := time
    p90_entry_price := close
    p90_candle_body := candle_body_pips
    p90_direction := p90_bull_signal ? "LONG" : "SHORT"
    entry_ext_25_long := asian_high + (asian_range_pips * ext_25 * pip_size)
    entry_ext_50_long := asian_high + (asian_range_pips * ext_50 * pip_size)
    entry_ext_25_short := asian_low - (asian_range_pips * ext_25 * pip_size)
    entry_ext_50_short := asian_low - (asian_range_pips * ext_50 * pip_size)
    entry_ext_25_hit := false
    entry_ext_50_hit := false
    entry_violation_triggered := false

if p90_bull_signal or p90_bear_signal
    last_entry_time := time
    in_hold_period := true

bool hold_period_expired = false

if not na(last_entry_time)
    minutes_since_entry = (time - last_entry_time) / 60000
    hold_period_expired := minutes_since_entry >= hold_time_minutes
else
    hold_period_expired := true

if hold_period_expired
    in_hold_period := false

// ============================================================================
// 📊 EXTENSION HIT TRACKING
// ============================================================================

if p90_direction == "LONG" and asian_range_complete
    if not entry_ext_25_hit and high >= entry_ext_25_long
        entry_ext_25_hit := true
    if not entry_ext_50_hit and high >= entry_ext_50_long
        entry_ext_50_hit := true
    if not entry_violation_triggered and high >= violation_long
        entry_violation_triggered := true

if p90_direction == "SHORT" and asian_range_complete
    if not entry_ext_25_hit and low <= entry_ext_25_short
        entry_ext_25_hit := true
    if not entry_ext_50_hit and low <= entry_ext_50_short
        entry_ext_50_hit := true
    if not entry_violation_triggered and low <= violation_short
        entry_violation_triggered := true

// ============================================================================
// 📊 ASIAN RANGE FILTER
// ============================================================================

get_ar_status() =>
    if asian_range_pips < ar_go_threshold
        "GO"
    else if asian_range_pips >= ar_go_threshold and asian_range_pips < ar_caution_threshold
        "GO"
    else if asian_range_pips >= ar_caution_threshold and asian_range_pips < ar_nogo_threshold
        "CAUTION"
    else
        "NO-GO"

ar_status = get_ar_status()

filter_25_50_hit = entry_ext_25_hit and entry_ext_50_hit

valid_p90_entry = (p90_bull_signal or p90_bear_signal) and ar_status != "NO-GO" and not filter_25_50_hit and not entry_violation_triggered

// ============================================================================
// 📊 P90 POSITION ENTRY
// ============================================================================

tp1_price_long = entry_ext_50_long
tp1_price_short = entry_ext_50_short

calc_qty(size_percent, entry_price) =>
    (strategy.equity * size_percent / 100) / entry_price

if valid_p90_entry
    sl1_pips = p90_candle_body * sl_80fib_mult
    sl1_price = p90_direction == "LONG" ? p90_entry_price - (sl1_pips * pip_size) : p90_entry_price + (sl1_pips * pip_size)
    tp1_price = p90_direction == "LONG" ? tp1_price_long : tp1_price_short
    qty1 = calc_qty(pos1_size, p90_entry_price)
    strategy.entry("P90_Pos1_Long", strategy.long, qty=qty1, comment="P90 Pos1 Entry")
    strategy.exit("P90_Pos1_Exit", "P90_Pos1_Long", stop=sl1_price, limit=tp1_price, comment="P90 Pos1 Exit")
    sl2_pips = p90_candle_body * sl_1_5x_mult
    sl2_price = p90_direction == "LONG" ? p90_entry_price - (sl2_pips * pip_size) : p90_entry_price + (sl2_pips * pip_size)
    qty2 = calc_qty(pos2_size, p90_entry_price)
    strategy.entry("P90_Pos2_Long", strategy.long, qty=qty2, comment="P90 Pos2 Entry")
    strategy.exit("P90_Pos2_Exit", "P90_Pos2_Long", stop=sl2_price, limit=tp1_price, comment="P90 Pos2 Exit")

var bool pos3_entered = false

if not na(last_entry_time) and not pos3_entered and enable_p90
    minutes_elapsed = (time - last_entry_time) / 60000
    if minutes_elapsed >= add_time_minutes and minutes_elapsed < (add_time_minutes + 5)
        extension_achieved = p90_direction == "LONG" ? (high - p90_entry_price) / pip_size >= add_extension_pips : (p90_entry_price - low) / pip_size >= add_extension_pips
        if extension_achieved and not entry_violation_triggered
            sl3_pips = p90_candle_body * sl_1_5x_mult
            sl3_price = p90_direction == "LONG" ? p90_entry_price - (sl3_pips * pip_size) : p90_entry_price + (sl3_pips * pip_size)
            tp1_price = p90_direction == "LONG" ? tp1_price_long : tp1_price_short
            qty3 = calc_qty(pos3_size, p90_entry_price)
            strategy.entry("P90_Pos3_Long", strategy.long, qty=qty3, comment="P90 Pos3 Entry (45-min)")
            strategy.exit("P90_Pos3_Exit", "P90_Pos3_Long", stop=sl3_price, limit=tp1_price, comment="P90 Pos3 Exit")
            pos3_entered := true

if get_est_hour() == 0 and get_est_minute() == 0
    pos3_entered := false

// ============================================================================
// 📊 P90 EXIT CONDITIONS
// ============================================================================

if is_hard_exit_time() and enable_p90
    strategy.close_all(comment="P90 Hard Exit (12 PM EST)")

if entry_violation_triggered and enable_p90
    strategy.close_all(comment="P90 132% Violation Exit")

if not na(last_entry_time) and enable_p90
    minutes_held = (time - last_entry_time) / 60000
    if minutes_held >= hold_time_minutes
        strategy.close_all(comment="P90 Hold Time Exit (120 min)")
        last_entry_time := na
        in_hold_period := false

// ============================================================================
// 🔔 ALERTS (P90 ONLY)
// ============================================================================

if alert_on
    if p90_bull_signal and enable_p90
        alert("🟢 P90 BULL Signal - " + str.tostring(candle_body_pips, "#.##") + " pips [" + get_active_asset_name() + "]", alert.freq_once_per_bar)
    if p90_bear_signal and enable_p90
        alert("🔴 P90 BEAR Signal - " + str.tostring(candle_body_pips, "#.##") + " pips [" + get_active_asset_name() + "]", alert.freq_once_per_bar)
    if entry_violation_triggered and enable_p90
        alert("⚠️ P90 132% Violation - Exit All [" + get_active_asset_name() + "]", alert.freq_once_per_bar)
    if is_hard_exit_time() and enable_p90
        alert("⏰ P90 Hard Exit Time (12 PM EST) [" + get_active_asset_name() + "]", alert.freq_once_per_bar)

// ============================================================================
// 👁️ P90P DISTRIBUTION TRACKER - VISUALIZATION ONLY
// ============================================================================

get_tier() =>
    if not na(asian_range_pips)
        if asian_range_pips < 20
            "T1"
        else if asian_range_pips >= 20 and asian_range_pips < 30
            "T2"
        else if asian_range_pips >= 30 and asian_range_pips < 45
            "T3"
        else
            "NO-GO"
    else
        "N/A"

tier_status = get_tier()

get_base_factor() =>
    if tier_status == "T1"
        3.12
    else if tier_status == "T2"
        2.68
    else if tier_status == "T3"
        2.18
    else
        1.52

base_factor = get_base_factor()

get_precision_zone() =>
    if tier_status == "T1"
        2.5
    else if tier_status == "T2"
        3.0
    else if tier_status == "T3"
        3.5
    else
        5.0

base_precision = get_precision_zone()

base_target_pips = asian_range_complete ? asian_range_pips * base_factor : na

var bool p90_confirmed_2_6am = false
if get_est_hour() >= 2 and get_est_hour() < 6 and (p90_bull_signal or p90_bear_signal)
    p90_confirmed_2_6am := true

if get_est_hour() == 0 and get_est_minute() == 0
    p90_confirmed_2_6am := false

var float range_7pm_6am = na
var float expected_6am_pips = na
var float adjusted_target_6am = na
var float precision_6am = na
var bool checkpoint_6am_done = false
var int checkpoint_6am_bar = na

if get_est_hour() == 6 and get_est_minute() == 0 and asian_range_complete and not checkpoint_6am_done
    range_7pm_6am := (high - asian_low) / pip_size
    expected_6am_pips := base_target_pips * 0.65
    p90_adjustment = p90_confirmed_2_6am ? 1.05 : 1.00
    adjusted_target_6am := (range_7pm_6am / 0.65) * p90_adjustment
    precision_6am := p90_confirmed_2_6am ? 2.5 : 3.5
    checkpoint_6am_done := true
    checkpoint_6am_bar := bar_index

if get_est_hour() == 0 and get_est_minute() == 0
    checkpoint_6am_done := false
    range_7pm_6am := na
    expected_6am_pips := na
    adjusted_target_6am := na
    precision_6am := na
    checkpoint_6am_bar := na

var float range_3am_9am = na
var float regime_ratio = na
var string regime_status = ""
var float completion_pct_9am = na
var float regime_boost = na
var float final_target_9am = na
var float precision_9am = na
var bool checkpoint_9am_done = false
var int checkpoint_9am_bar = na
var float high_3am_9am = na
var float low_3am_9am = na

if get_est_hour() == 3 and get_est_minute() == 0
    high_3am_9am := high
    low_3am_9am := low

if get_est_hour() > 3 and get_est_hour() < 9
    high_3am_9am := math.max(high_3am_9am, high)
    low_3am_9am := math.min(low_3am_9am, low)

if get_est_hour() == 9 and get_est_minute() == 0 and asian_range_complete and not checkpoint_9am_done
    range_3am_9am := (high_3am_9am - low_3am_9am) / pip_size
    regime_ratio := asian_range_pips != 0 ? range_3am_9am / asian_range_pips : 0
    if regime_ratio >= 1.50
        regime_status := "CONFIRMED"
        completion_pct_9am := 0.902
        regime_boost := 1.10
    else if regime_ratio >= 1.45 and regime_ratio < 1.50
        regime_status := "CAUTION"
        completion_pct_9am := 0.861
        regime_boost := 1.05
    else
        regime_status := "FAILED"
        completion_pct_9am := 0.738
        regime_boost := 0.90
    float range_7pm_9am = (high - asian_low) / pip_size
    final_target_9am := (range_7pm_9am / completion_pct_9am) * regime_boost
    precision_9am := regime_status == "CONFIRMED" ? 2.0 : regime_status == "CAUTION" ? 2.5 : 3.5
    checkpoint_9am_done := true
    checkpoint_9am_bar := bar_index

if get_est_hour() == 0 and get_est_minute() == 0
    checkpoint_9am_done := false
    range_3am_9am := na
    regime_ratio := na
    regime_status := ""
    completion_pct_9am := na
    regime_boost := na
    final_target_9am := na
    precision_9am := na
    checkpoint_9am_bar := na
    high_3am_9am := na
    low_3am_9am := na

accuracy_est = regime_status == "CONFIRMED" and p90_confirmed_2_6am and tier_status != "NO-GO" ? "94-95%" : 
               regime_status == "CAUTION" ? "90-92%" : 
               regime_status == "FAILED" ? "85-88%" : "N/A"

if get_est_hour() == 2 and get_est_minute() == 0 and asian_range_complete
    label.new(bar_index, high, text = "🌙 2 AM\\n" + str.tostring(base_target_pips, "#") + " pips (±" + str.tostring(base_precision, "#.#") + ")\\nTier: " + tier_status, style = label.style_label_down, color = color.new(color.blue, 50), textcolor = color.white, size = size.normal)

if checkpoint_6am_done and bar_index == checkpoint_6am_bar
    label.new(bar_index, high, text = "🌅 6 AM\\n" + str.tostring(adjusted_target_6am, "#") + " pips (±" + str.tostring(precision_6am, "#.#") + ")\\nP90: " + (p90_confirmed_2_6am ? "✓" : "✗"), style = label.style_label_down, color = color.new(color.orange, 50), textcolor = color.white, size = size.normal)

if checkpoint_9am_done and bar_index == checkpoint_9am_bar
    label.new(bar_index, high, text = "☀️ 9 AM\\n" + str.tostring(final_target_9am, "#") + " pips (±" + str.tostring(precision_9am, "#.#") + ")\\nRegime: " + regime_status, style = label.style_label_down, color = color.new(color.green, 50), textcolor = color.white, size = size.normal)

// ============================================================================
// 📊 VISUALIZATION
// ============================================================================

plot(asian_range_complete ? asian_high : na, "Asian High", color=color.new(color.green, 0), style=plot.style_linebr, linewidth=2)
plot(asian_range_complete ? asian_low : na, "Asian Low", color=color.new(color.red, 0), style=plot.style_linebr, linewidth=2)

plotshape(asian_range_complete and bar_index == asian_open_bar, "Asian Open (7 PM)", shape.flag, location.top, color=color.new(color.blue, 0), size=size.small, text="7PM")
plotshape(asian_range_complete and bar_index == asian_close_bar, "Asian Close (2:55 AM)", shape.flag, location.top, color=color.new(color.orange, 0), size=size.small, text="2:55AM")

plot(asian_range_complete ? entry_ext_25_long : na, "Entry Ext -25% Long", color=color.new(color.blue, 30), style=plot.style_linebr, linewidth=1)
plot(asian_range_complete ? entry_ext_50_long : na, "Entry Ext -50% Long", color=color.new(color.blue, 0), style=plot.style_linebr, linewidth=2)
plot(asian_range_complete ? entry_ext_25_short : na, "Entry Ext -25% Short", color=color.new(color.orange, 30), style=plot.style_linebr, linewidth=1)
plot(asian_range_complete ? entry_ext_50_short : na, "Entry Ext -50% Short", color=color.new(color.orange, 0), style=plot.style_linebr, linewidth=2)

plot(asian_range_complete ? violation_long : na, "132% Violation Long", color=color.new(color.red, 0), style=plot.style_linebr, linewidth=2)
plot(asian_range_complete ? violation_short : na, "132% Violation Short", color=color.new(color.red, 0), style=plot.style_linebr, linewidth=2)

plotshape(p90_bull_candle and enable_p90 and in_p90_entry_window(), "P90 Bull Signal (No Filter)", shape.triangleup, location.belowbar, color=color.new(color.yellow, 0), size=size.normal, text="")
plotshape(p90_bear_candle and enable_p90 and in_p90_entry_window(), "P90 Bear Signal (No Filter)", shape.triangledown, location.abovebar, color=color.new(color.yellow, 0), size=size.normal, text="")

bgcolor(in_p90_entry_window() and enable_p90 ? color.new(color.green, 95) : na)
bgcolor(in_asian_session() and enable_p90 ? color.new(color.blue, 97) : na)
bgcolor(in_hold_period and enable_p90 ? color.new(color.purple, 92) : na)

// ============================================================================
// 📊 INFO PANEL - TOP RIGHT
// ============================================================================

var table info_table = table.new(position.top_right, 2, 22, bgcolor=color.black, border_width=1)

if barstate.islast
    table.cell(info_table, 0, 0, "CEREBUS P90 V6 PER-ASSET [EST]", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 0, "STATUS", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 0, 1, "Active Asset", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 1, get_active_asset_name(), text_color=color.yellow, bgcolor=color.blue, text_size=size.small)
    table.cell(info_table, 0, 2, "Pip Size", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 2, str.tostring(pip_size, "#.####"), text_color=color.white, bgcolor=color.blue, text_size=size.small)
    table.cell(info_table, 0, 3, "P90 Threshold", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 3, str.tostring(p90_threshold, "#.##") + " pips", text_color=color.yellow, bgcolor=color.blue, text_size=size.small)
    table.cell(info_table, 0, 4, "Current Time (EST)", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 4, str.tostring(get_est_hour(), "00") + ":" + str.tostring(get_est_minute(), "00"), text_color=color.white, bgcolor=color.blue, text_size=size.small)
    table.cell(info_table, 0, 5, "P90 Signals Today", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 5, str.tostring(signals_today), text_color=color.white, bgcolor=color.green, text_size=size.small)
    table.cell(info_table, 0, 6, "In Hold Period", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 6, in_hold_period ? "YES" : "NO", text_color=color.white, bgcolor=in_hold_period ? color.purple : color.green, text_size=size.small)
    if not na(last_entry_time)
        mins_since = (time - last_entry_time) / 60000
        table.cell(info_table, 0, 7, "Mins Since Entry", text_color=color.white, bgcolor=color.gray, text_size=size.small)
        table.cell(info_table, 1, 7, str.tostring(mins_since, "#") + " / " + str.tostring(hold_time_minutes), text_color=color.white, bgcolor=mins_since >= hold_time_minutes ? color.green : color.orange, text_size=size.small)
    else
        table.cell(info_table, 0, 7, "Mins Since Entry", text_color=color.white, bgcolor=color.gray, text_size=size.small)
        table.cell(info_table, 1, 7, "N/A", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 0, 8, "Asian Range", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 8, str.tostring(asian_range_pips, "#.##") + " pips", text_color=color.white, bgcolor=ar_status == "GO" ? color.green : ar_status == "CAUTION" ? color.orange : color.red, text_size=size.small)
    table.cell(info_table, 0, 9, "AR Status", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 9, ar_status, text_color=color.white, bgcolor=ar_status == "GO" ? color.green : ar_status == "CAUTION" ? color.orange : color.red, text_size=size.small)
    table.cell(info_table, 0, 10, "P90 Direction", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 10, p90_direction, text_color=color.white, bgcolor=p90_direction == "LONG" ? color.green : p90_direction == "SHORT" ? color.red : color.gray, text_size=size.small)
    table.cell(info_table, 0, 11, "-25% Hit", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 11, entry_ext_25_hit ? "YES" : "NO", text_color=color.white, bgcolor=entry_ext_25_hit ? color.green : color.gray, text_size=size.small)
    table.cell(info_table, 0, 12, "-50% Hit", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 12, entry_ext_50_hit ? "YES" : "NO", text_color=color.white, bgcolor=entry_ext_50_hit ? color.green : color.gray, text_size=size.small)
    table.cell(info_table, 0, 13, "132% Violation", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 13, entry_violation_triggered ? "YES" : "NO", text_color=color.white, bgcolor=entry_violation_triggered ? color.red : color.green, text_size=size.small)
    table.cell(info_table, 0, 14, "Filter Status", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 14, filter_25_50_hit ? "BLOCKED" : "OK", text_color=color.white, bgcolor=filter_25_50_hit ? color.red : color.green, text_size=size.small)
    table.cell(info_table, 0, 15, "──── P90P Tracker ────", text_color=color.yellow, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 15, "", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 0, 16, "Tier Status", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 16, tier_status, text_color=color.white, bgcolor=tier_status == "T1" ? color.green : tier_status == "T2" ? color.blue : tier_status == "T3" ? color.orange : color.red, text_size=size.small)
    table.cell(info_table, 0, 17, "P90 Confirmed 2-6AM", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 17, p90_confirmed_2_6am ? "YES ✓" : "NO ✗", text_color=color.white, bgcolor=p90_confirmed_2_6am ? color.green : color.red, text_size=size.small)
    table.cell(info_table, 0, 18, "Regime Status (9AM)", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 18, regime_status, text_color=color.white, bgcolor=regime_status == "CONFIRMED" ? color.green : regime_status == "CAUTION" ? color.orange : regime_status == "FAILED" ? color.red : color.gray, text_size=size.small)
    table.cell(info_table, 0, 19, "2 AM Target", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 19, asian_range_complete ? str.tostring(base_target_pips, "#") + " (±" + str.tostring(base_precision, "#.#") + ")" : "WAITING", text_color=color.white, bgcolor=asian_range_complete ? color.blue : color.gray, text_size=size.small)
    table.cell(info_table, 0, 20, "6 AM Target", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 20, checkpoint_6am_done ? str.tostring(adjusted_target_6am, "#") + " (±" + str.tostring(precision_6am, "#.#") + ")" : "WAITING", text_color=color.white, bgcolor=checkpoint_6am_done ? color.orange : color.gray, text_size=size.small)
    table.cell(info_table, 0, 21, "9 AM Target", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(info_table, 1, 21, checkpoint_9am_done ? str.tostring(final_target_9am, "#") + " (±" + str.tostring(precision_9am, "#.#") + ")" : "WAITING", text_color=color.white, bgcolor=checkpoint_9am_done ? color.green : color.gray, text_size=size.small)

// ============================================================================
// 📊 P90P DISTRIBUTION TRACKER - BOTTOM RIGHT
// ============================================================================

var table p90p_table = table.new(position.bottom_right, 2, 10, bgcolor=color.black, border_width=1)

if barstate.islast
    table.cell(p90p_table, 0, 0, "👁️ P90P DISTRIBUTION", text_color=color.yellow, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 0, "TRACKER", text_color=color.yellow, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 0, 1, "Asian Range", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 1, asian_range_complete ? str.tostring(asian_range_pips, "#.##") + " pips" : "CALCULATING...", text_color=color.white, bgcolor=asian_range_complete ? color.blue : color.gray, text_size=size.small)
    table.cell(p90p_table, 0, 2, "Tier", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 2, tier_status, text_color=color.white, bgcolor=tier_status == "T1" ? color.green : tier_status == "T2" ? color.blue : tier_status == "T3" ? color.orange : color.red, text_size=size.small)
    table.cell(p90p_table, 0, 3, "Base Factor", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 3, asian_range_complete ? str.tostring(base_factor, "#.##") + "x" : "N/A", text_color=color.white, bgcolor=asian_range_complete ? color.purple : color.gray, text_size=size.small)
    table.cell(p90p_table, 0, 4, "🌙 2 AM Target", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 4, asian_range_complete ? str.tostring(base_target_pips, "#") + " (±" + str.tostring(base_precision, "#.#") + ")" : "WAITING", text_color=color.white, bgcolor=asian_range_complete ? color.blue : color.gray, text_size=size.small)
    table.cell(p90p_table, 0, 5, "🌅 6 AM Target", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 5, checkpoint_6am_done ? str.tostring(adjusted_target_6am, "#") + " (±" + str.tostring(precision_6am, "#.#") + ")" : "WAITING", text_color=color.white, bgcolor=checkpoint_6am_done ? color.orange : color.gray, text_size=size.small)
    table.cell(p90p_table, 0, 6, "☀️ 9 AM Target", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 6, checkpoint_9am_done ? str.tostring(final_target_9am, "#") + " (±" + str.tostring(precision_9am, "#.#") + ")" : "WAITING", text_color=color.white, bgcolor=checkpoint_9am_done ? color.green : color.gray, text_size=size.small)
    table.cell(p90p_table, 0, 7, "Regime Ratio", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 7, checkpoint_9am_done ? str.tostring(regime_ratio, "#.##") + "x" : "N/A", text_color=color.white, bgcolor=checkpoint_9am_done ? color.purple : color.gray, text_size=size.small)
    table.cell(p90p_table, 0, 8, "Regime Status", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 8, regime_status, text_color=color.white, bgcolor=regime_status == "CONFIRMED" ? color.green : regime_status == "CAUTION" ? color.orange : regime_status == "FAILED" ? color.red : color.gray, text_size=size.small)
    table.cell(p90p_table, 0, 9, "🎯 Accuracy", text_color=color.white, bgcolor=color.gray, text_size=size.small)
    table.cell(p90p_table, 1, 9, accuracy_est, text_color=color.white, bgcolor=regime_status == "CONFIRMED" and p90_confirmed_2_6am ? color.green : color.gray, text_size=size.small)
'''

# Write the file
output_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\_p90_v6_per_asset.pine')
output_path.write_text(pine_script, encoding='utf-8')
print(f"Generated: {output_path}")
print(f"Size: {len(pine_script)} chars, {len(pine_script.splitlines())} lines")
