import re

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live.py", "r") as f:
    c = f.read()

# 1. Add get_asian_range_from_bars function
new_func = """
def get_asian_range_from_bars(bars, current_time):
    if not bars:
        return (0.0, 0.0)
    if current_time.hour >= 3:
        session_end = current_time.replace(hour=3, minute=0, second=0, microsecond=0)
    else:
        yesterday = current_time - timedelta(days=1)
        session_end = yesterday.replace(hour=3, minute=0, second=0, microsecond=0)
    session_start = session_end - timedelta(hours=8)
    asian = [b for b in bars if b["time"] >= session_start and b["time"] <= session_end]
    if not asian:
        return (0.0, 0.0)
    return (max(b["high"] for b in asian), min(b["low"] for b in asian))

"""
c = c.replace("def classify_tier(", new_func + "def classify_tier(", 1)

# 2. Add initialize_session method
init_method = """
    def initialize_session(self, bars, current_time):
        if self.asian_locked:
            return
        ah, al = get_asian_range_from_bars(bars, current_time)
        if ah == 0.0 and al == 0.0:
            return
        self.asian_high = ah
        self.asian_low = al
        self.asian_locked = True
        ar_pips = (ah - al) / self.ps
        self.tier_name, self.au_pips, self.trigger_pips = classify_tier(ar_pips)
        self.session_active = self.tier_name != "NO_GO"
        if bars:
            self.swing_origin = bars[-1]["close"]
        if self.session_active:
            self.st_state = "SEARCH"
            self.p90_state = "SEARCH_P90"
            logging.info("[%s] Session INIT: tier=%%s AR=%%.1fp origin=%%.5f" %% (self.symbol, self.tier_name, ar_pips, self.swing_origin))
        else:
            logging.info("[%s] NO-GO: AR=%%.1fp" %% (self.symbol, ar_pips))
"""
c = c.replace("    def reset_session(self):", init_method + "    def reset_session(self):", 1)

# 3. Add initialization block in run_live
init_block = """
    # Initialize sessions from startup bar data (one-time)
    now = datetime.now(EST)
    for symbol in symbols:
        bars = get_bars(symbol, 500)
        if bars:
            states[symbol].initialize_session(bars, now)

"""
c = c.replace("    scan_count = 0", init_block + "    scan_count = 0")

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live.py", "w") as f:
    f.write(c)
print("DONE - v2.1 patched")

# Verify
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live.py", "r") as f:
    c2 = f.read()
print("initialize_session found:", "initialize_session" in c2)
print("get_asian_range_from_bars found:", "get_asian_range_from_bars" in c2)
