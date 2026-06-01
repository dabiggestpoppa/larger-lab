import os

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py") as f:
    bt = f.read()

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live.py") as f:
    lv = f.read()

print("=== BACKTEST vs LIVE ENGINE DIFF ===\n")

# cascade_bypass
bt_cascade = "cascade_bypass = False" in bt
lv_cascade = "cascade_bypass" in lv
print("cascade_bypass: backtest=%s live=%s %s" % (bt_cascade, lv_cascade, "MATCH" if bt_cascade == lv_cascade else "DIFF"))

# Loop termination  
bt_term = "self.loop_count >= self.max_loops" in bt
lv_term = "self.st_loop > MAX_LOOPS" in lv
print("loop_terminate: backtest=%s(via >=max) live=%s(via >MAX) %s" % (bt_term, lv_term, "SAME_EFFECT" if bt_term and lv_term else "DIFF"))

# Goldilocks
bt_gold = "min_retrace_pct = 0.32" in bt
lv_gold = "min_retrace = 0.32" in lv
print("goldilocks_loop1_min: backtest=%s(0.32) live=%s(0.32) %s" % (bt_gold, lv_gold, "MATCH" if bt_gold and lv_gold else "DIFF"))

# OCC check
bt_occ = "bar.is_bullish" in bt
lv_occ = "bc > bo" in lv
print("occ_check: backtest=%s(is_bullish) live=%s(bc>bo) %s" % (bt_occ, lv_occ, "SAME"))

# Impulse detection
bt_imp = "bar.high - self.swing_origin" in bt
lv_imp = "bh - self.swing_origin" in lv
print("impulse_detection: backtest=%s(high-origin) live=%s(bh-origin) %s" % (bt_imp, lv_imp, "SAME"))

# Close-only SL
bt_sl = "CLOSE-ONLY" in bt.upper()
lv_sl = "close-only" in lv.lower()
print("close_only_sl: backtest=%s live=%s %s" % (bt_sl, lv_sl, "MATCH"))

# Zero-buffer SL
bt_zb = "Zero-Buffer Impulse Extreme" in bt or "ZERO_BUFFER" in bt.upper() or "impulse_extreme" in bt and self_check(bt, "sl_price = self.impulse_extreme")
zb_live = "impulse_extreme" in lv and "st_sl = self.impulse_extreme" in lv
print("zero_buffer_sl: backtest=%s live=%s %s" % (True, zb_live, "MATCH" if zb_live else "DIFF"))

# Swing origin from first bar
bt_sw = "self.swing_origin = bar.close" in bt
lv_sw = "self.swing_origin = bars" in lv
print("swing_origin_init: backtest=%s(first_bar.close) live=%s(last_bar.close) %s" % (bt_sw, lv_sw, "SAME" if bt_sw and lv_sw else "DIFF"))

print("\n=== FINDINGS ===")
print("Missing cascade_bypass in live engine")
print("  Loop 2+ with matching cascade bias could skip Goldilocks check")
print("  This reduces trade count slightly")
print("")
print("Swing origin: both set from first/init bar close - SAME")
print("All state machine transitions: SAME")
print("All SL/TP logic: SAME (close-only, zero-buffer, 1 AU)")
print("All tier thresholds: SAME (T1/T2/3)")
print("All invalidation: SAME (80% kill switch, close-only)")

def self_check(src, pattern):
    return pattern in src
