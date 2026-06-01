# -*- coding: utf-8 -*-
"""
Deep dive: Why Nautilus has 2186 trades vs Python's 1163 for ST EURUSD.

Hypothesis: Nautilus day boundary detection differs because:
1. Nautilus processes ALL bars (including Asian session bars 7PM-3AM)
   and does internal day detection via _ts_to_date() (UTC-based)
2. Python backtest groups by EST date BEFORE feeding to engine, skipping Asian bars properly
3. Nautilus _est_hour_from_bar may classify some bars differently

OR: The loop/re-entry logic differs - Nautilus may be re-entering more times.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from datetime import datetime, timedelta, timezone as tz
from collections import Counter

LAB = Path("C:/Users/wifik/Desktop/projects/larger-lab")
sys.path.insert(0, str(LAB / "quant-lab/engines"))

import pandas as pd

# === Load with the CORRECT loader ===
from symmetry_trap_backtest import load_m5_csv, SymmetryTrapBacktest

bars, sym = load_m5_csv(str(LAB / "quant-lab/data/EURUSD_M5.csv"))
print(f"Loaded {len(bars)} bars")

# === Run Python GT backtest with detailed logging ===
py_bt = SymmetryTrapBacktest(pip_size=0.0001)
result = py_bt.run(bars)

print(f"\n=== PYTHON GT ===")
print(f"Trades: {result.total_trades} | WR: {result.win_rate:.1f}% | PnL: {result.total_pnl_pips:.1f}p")
print(f"W: {result.wins} / L: {result.losses}")
print(f"Kills: {result.kills}")

# Loop distribution
print(f"\nLoop distribution (Python):")
for lk, ls in sorted(result.loop_stats.items(), key=lambda x: int(x[0])):
    print(f"  Loop {lk}: {ls['trades']} trades | {ls['wr']}% WR | {ls['pnl']}p")

# === Now simulate Nautilus day detection ===
# Nautilus uses _ts_to_date which converts UTC ns -> date
# Our EST formula is (UTC_hour - 5) % 24
# Key: bars with timestamp 00:00 UTC = 19:00 EST (previous day)
# So Nautilus day boundary is at 5AM UTC = midnight EST

# Let's check: how many sessions does Python see?
print(f"\n=== SESSION ANALYSIS ===")
# Python groups by EST day
py_days = {}
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=-5)
    dk = est_dt.strftime("%Y-%m-%d")
    if dk not in py_days:
        py_days[dk] = []
    py_days[dk].append(bar)

print(f"Python EST days: {len(py_days)}")

# Count active sessions (with valid Asian range)
active_days = 0
no_go_days = 0
skip_no_asian = 0
for dk in sorted(py_days.keys()):
    day_bars = sorted(py_days[dk], key=lambda b: b.timestamp)
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour - 5) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    if ah <= 0 or al >= 99999:
        skip_no_asian += 1
        continue
    ar = (ah - al) / 0.0001
    if ar > 45.0:
        no_go_days += 1
    else:
        active_days += 1

print(f"Active sessions: {active_days} | NO-GO: {no_go_days} | No Asian data: {skip_no_asian}")

# === Now check Nautilus day grouping ===
# Nautilus _ts_to_date uses datetime.fromtimestamp(ts_ns/1e9, tz=timezone.utc).date()
# bar.ts_event = UTC nanosecond timestamp
# For our CSV, column 'timestamp' is in naive datetime (no tz)
# Wrangler assigns UTC timezone to the index
# So bar.ts_event corresponds to the CSV timestamp AS IF it's UTC
# Then Nautilus EST hour = (UTC_hour + (-5)) % 24

# For Python: EST hour = (csv_timestamp_hour + (-5)) % 24  (same formula!)
# BUT Python groups by (csv_timestamp + (-5h)).date()
# Nautilus groups by date(UTC_timestamp) = date(csv_timestamp) because wrangler treats as UTC

# This means: for bars at 00:00 UTC (which Nautilus says is 19:00 EST)
# Python puts this in PREVIOUS day's date
# Nautilus puts this in SAME day's date (because date(00:00 UTC) = that day)
# WAIT - let me check this more carefully...

print(f"\n=== DAY BOUNDARY COMPARE ===")
# Sample: 2022-01-03 00:00:00 UTC
# Python EST: 2022-01-02 19:00:00 -> date = 2022-01-02 (previous day!)
# Nautilus UTC date: 2022-01-03 -> date = 2022-01-03 (same day)
# Nautilus EST hour: (0 + (-5)) % 24 = 19 -> Asian session

# This is the KEY DIFFERENCE:
# Python: bar at 00:00 UTC goes to PREVIOUS day's session (correct for trading)
# Nautilus: bar at 00:00 UTC goes to CURRENT day's session with EST=19 (Asian)
# But then Nautilus hard reset at 12PM EST = 17:00 UTC

# In Nautilus, the "day" starts at midnight UTC = 7PM EST (previous trading day's Asian!)
# In Python, the "day" starts at midnight EST = 5AM UTC

# So Nautilus processes: 
#   Day N: bars from 00:00 UTC (=7PM EST prev day) to 23:59 UTC (=6:59PM EST)
#   = Asian session of prev day + full London/NY of current day
# Python processes:
#   Day N: bars from 00:00 EST (=5AM UTC) to 23:59 EST (=4:59AM UTC next day)
#   = We need to check what range actually hits the Asian filter...

print("Python uses (csv_ts + (-5h)).date() for day grouping")
print("Nautilus uses date(UTC_timestamp) for day grouping")
print("For bar at midnight UTC:")
print("  Python: EST date = prev day | Nautilus: UTC date = same day")
print("  => Asian session bars (7PM-3AM EST = 0:00-08:00 UTC)")
print("  => Python puts 00:00-02:59 UTC into PREVIOUS day")
print("  => Nautilus puts 00:00-07:59 UTC into SAME day")
print("")
print("This means Nautilus 'days' contain bars from TWO trading sessions:")
print("  Previous day's Asian (7PM-11:59PM EST) + Current day's London+NY")
print("  But the Asian range only tracks 7PM-3AM EST within that 'day'")
print("  So 00:00-02:59 UTC bars ARE part of Asian (correct)")
print("  And 03:00-07:59 UTC bars are NOT Asian (London open)")
print("")
print("For Python:")
print("  Previous day contains: 00:00-23:59 EST = 05:00-04:59 UTC next day")
print("  Previous day's Asian: 19:00-23:59 EST = 00:00-04:59 UTC")
print("  So Asian bars have UTC dates != EST dates")
print("")
print("RESULT: Asian range detection should be IDENTICAL for both")
print("The REAL question is: does Nautilus produce more trades per session?")

# === Hypothesis 2: Nautilus processes bars in different order or processes twice ===
# Let's look at actual Nautilus logs to compare trade counts per session

print(f"\n=== CHECK: TRADES PER SESSION ===")
print(f"Python: {result.total_trades} trades / {active_days} active sessions = {result.total_trades/max(active_days,1):.1f} trades/session")
# Nautilus: 2186 trades / ? sessions

# === Hypothesis 3: The Nautilus strategy processes Sunday Asian differently ===
# Weekday check: bars before Monday 3AM should be Sunday's Asian session
# Some data feeds include Sunday evening bars

print(f"\n=== WEEKDAY DISTRIBUTION (first 20 bars) ===")
for b in bars[:20]:
    est_h = (b.timestamp.hour - 5) % 24
    est_date = (b.timestamp + timedelta(hours=-5)).strftime("%Y-%m-%d")
    utc_dow = b.timestamp.strftime("%A")
    print(f"  UTC: {b.timestamp} ({utc_dow}) | EST: {est_h:02d}:xx | EST_date: {est_date}")

# === KEY CHECK: Does the Python engine skip Asian bars entirely from process_bar? ===
print(f"\n=== DOES PYTHON SKIP ASIAN BARS? ===")
# In the Python backtest, ALL bars (including Asian) are fed to process_bar
# But in process_bar, nothing checks for Asian hours - the session is pre-initialized
# The process_bar only has SEARCH, WAIT_RETRACE, WAIT_OCC, IN_TRADE
# Asian detection is done in SymmetryTrapBacktest._find_asian_range per day
# Then bars are fed to process_bar which processes them in time order

# WAIT - but what about bars during Asian hours? They ARE fed to process_bar!
# process_bar doesn't filter by hour - it processes every bar through the state machine
# During Asian hours, state is SEARCH, so it looks for impulse
# Could an impulse trigger during Asian hours? YES!
# That's extra trades that shouldn't count!

print("Checking if Python engine triggers impulse during Asian hours...")
# Check by looking at trade entry times
for t in result.trades[:5]:
    print(f"  Entry: {t.entry_time} EST_hour:{(t.entry_time.hour - 5) % 24}")

# Check Nautilus entry times similarly
print(f"\n=== NAUTILUS ENTRY TIMES (first 5 that we can recover) ===")

# === Hypothesis 4: The 12PM hard reset ===
# Python: breaks out of day loop when est_hour >= 12 and state == SEARCH
# Nautilus: returns on est_hour >= 12, but continues processing
# If Nautilus continues processing bars between 12PM-5PM in non-SEARCH state
# (e.g., WAIT_RETRACE or WAIT_OCC), it could enter trades after 12PM!

print(f"\n=== 12PM HARDCHECK ===")
print("Python: for bar in day_bars: if bar_est_h >= 12 and state == SEARCH: break")
print("Nautilus: if est_hour >= hard_reset_hour: _close_all_positions; return")
print("Key difference: Python only breaks if state==SEARCH")
print("Nautilus closes positions and exits REGARDLESS of state")
print("This means if Nautilus is in WAIT_RETRACE at 12PM, it kills the session")
print("If Python is in WAIT_RETRACE at 12PM, it continues (!)")

# Check: how many Python trades enter after 12PM?
entries_after_12 = sum(1 for t in result.trades if ((t.entry_time.hour - 5) % 24) >= 12)
print(f"Python entries after 12PM EST: {entries_after_12}")

# === Hypothesis 5: AU price calculation and pip divisor ===
# Nautilus: active_au_price = self.au_pips / self.pip_divisor
#   For EURUSD: au_pips=10, pip_divisor=10000 => active_au_price = 0.0010
# Python: active_au = self.au_pips * self.pip_size
#   For EURUSD: au_pips=10, pip_size=0.0001 => active_au = 0.0010
# Same!

# === The REAL test: Run Python engine WITHOUT the day-grouping wrapper ===
print(f"\n=== RAW PYTHON ENGINE TEST ===")
from symmetry_trap import SymmetryTrapEngine, Bar

# Feed ALL bars through engine WITHOUT session management
raw_engine = SymmetryTrapEngine(pip_size=0.0001)

# We need to replicate Nautilus's approach: detect day boundaries internally
# But the Python engine doesn't have that - it relies on external session init
# So the real question is: does the day grouping AND session init produce different results?

# Let me check Nautilus more carefully. The Nautilus strategy on_bar:
# 1. Checks 12PM hard reset
# 2. Checks 5PM hard exit
# 3. Detects new day via _ts_to_date
# 4. Tracks Asian range 7PM-3AM EST
# 5. Initializes session at 3AM EST
# 6. Processes impulse after 3AM

# Python SymmetryTrapBacktest.run():
# 1. Groups bars by EST date
# 2. For each day, finds Asian range from 7PM-3AM EST bars
# 3. Initializes session once per day via engine.initialize_session()
# 4. Feeds all day bars through process_bar
# 5. Breaks at 12PM if state==SEARCH

# KEY DIFFERENCE: The Python runner breaks the loop at 12PM only if state==SEARCH
# But Nautilus returns from on_bar at 12PM REGARDLESS
# This means Python could continue entering trades between 12PM-whatever
# while Nautilus would not!

# Actually wait - let me re-read the Nautilus code more carefully
# Nautilus: if est_hour >= hard_reset_hour: close_all, _reset_all_state, return
# So Nautilus STOPS processing completely at 12PM
# Python: if est_hour >= 12 and state == SEARCH: break
# So Python continues if state is WAIT_RETRACE/WAIT_OCC/IN_TRADE

# This gives Python MORE trades, not fewer. So that's not the explanation.

# The explanation must be that Nautilus is MORE liberal in entering trades.
# Let me check: does the Python backtest count filtered trades differently?

# Actually - could it be that Python backtest loads MORE data?
# Python: loads all 273,909 bars
# Nautilus: wrangler.process() might filter/skip bars

print(f"\n=== DATA FILTERING CHECK ===")
print(f"Python bars from backtest loader: {len(bars)}")
print(f"Nautilus bars from wrangler: 273909 (from earlier)")
print(f"These should be the same since both read the same CSV")

# === Let me check if the issue is Sunday bars data ===
# Nautilus handles Sunday bars: Sunday evening = start of new week
# But Python grouping by EST date might group Sunday with Monday

print(f"\nLet me run a controlled test: same session, same bars")
print("Python approach: group by EST day, init Asian, feed bars")
print("Nautilus approach: let strategy detect day internally")

# Check: which approach produces more sessions?
nautilus_days = set()
for b in bars:
    # Nautilus uses UTC date (no EST conversion for date)
    utc_date = b.timestamp.strftime("%Y-%m-%d")
    nautilus_days.add(utc_date)

py_days_set = set()
for b in bars:
    est_date = (b.timestamp + timedelta(hours=-5)).strftime("%Y-%m-%d")
    py_days_set.add(est_date)

print(f"Python EST unique dates: {len(py_days_set)}")
print(f"Nautilus UTC unique dates: {len(nautilus_days)}")
print(f"Difference: {len(nautilus_days) - len(py_days_set)}")

# The day grouping IS different! 
# Some bars will be in different sessions between the two approaches
# This leads to different Asian ranges -> different tiers -> different trade counts

print(f"\n=== COUNTING ASIAN RANGES DIFFERENTLY ===")
# For Python: Asian = bars where EST hour is 19-23 on date D, plus 0-2 on date D
# But wait - Python groups by EST date, so:
#   A bar at 2022-01-03 00:00 UTC = 2022-01-02 19:00 EST
#   Python puts this in date 2022-01-02's bars
#   EST hour = 19 -> Asian
# For Nautilus: 
#   A bar at 2022-01-03 00:00 UTC 
#   Nautilus date = 2022-01-03 (UTC date)
#   EST hour = (0 + (-5)) % 24 = 19 -> Asian
#   Nautilus puts this in date 2022-01-03's Asian range!
#
# So: A bar that Python says belongs to Jan 2 Asian
#     Nautilus says belongs to Jan 3 Asian!
# => Two completely different Asian range calculations!

print("CONCLUSION: Different day grouping = different Asian ranges = different trade triggers")
print("This is the ROOT CAUSE of the trade count discrepancy")
print("\nWhich is correct for trading?")
print("Trading sessions: Asian starts at 7PM EST on day D, ends at 3AM EST on day D+1")
print("A trading session 'Monday' = Monday 7PM to Tuesday 3AM")
print("Python groups by EST date: Jan 2 7PM - Jan 3 3AM all in Jan 2 -> CORRECT")
print("Nautilus groups by UTC date: Jan 2 7PM-11:59PM in Jan 2, Jan 3 12AM-3AM in Jan 3 -> SPLIT!")
print("\nNautilus TRADING DAY should be: 7PM EST (day D) to 5PM EST (day D+1)")
print("But Nautilus uses UTC date which starts at midnight UTC = 7PM EST")
print("So Nautilus puts 12AM-3AM UTC (=7PM-10PM EST prev day?) No wait...")

# Let me be very precise:
# CSV timestamp: '2022-01-03 00:00:00' (no timezone)
# Wrangler treats as UTC -> ts_event = 2022-01-03 00:00:00 UTC
# Nautilus: UTC date = Jan 3, EST hour = (0-5)%24 = 19 (7PM)
# Python: EST datetime = Jan 2 19:00, EST date = Jan 2

# For trading: Is the bar at Jan 3 00:00 UTC = Jan 2 19:00 EST part of:
# - Session starting Sunday Jan 2 (if it's Sunday evening)
# - Session starting Monday Jan 3?
# In forex: Sunday 5PM EST = new week start. Sunday 7PM EST = Monday session Asian.
# So if Jan 2 is Sunday: Sunday 7PM = Jan 3 00:00 UTC -> Monday session Asian
# Python correctly assigns to Sunday's date (which contains Monday's Asian)
# Nautilus assigns to Monday's date (which ALSO contains Monday's Asian)
# Wait... both should be correct for the Monday session?

# Actually: the Python code does (timestamp + (-5h)).date()
# So Jan 3 00:00 UTC -> Jan 2 19:00 -> date = Jan 2
# The Asian finder then picks up EST hour 19 from bars grouped under Jan 2

# Nautilus: date(Jan 3 00:00 UTC) = Jan 3
# The Asian finder picks up EST hour 19 from bars grouped under Jan 3

# So the Asian range for Monday session:
# Python: computed from Jan 2 group (contains bars from ~Jan 2 05:00 UTC to Jan 3 04:59 UTC)
#   Asian bars in Jan 2 group: 19:00-23:59 EST = 00:00-04:59 UTC on Jan 3
#   AND 00:00-02:59 EST on Jan 2 = 05:00-07:59 UTC on Jan 2
#   Wait no - Jan 2 00:00 UTC = Jan 1 19:00 EST. That's PREVIOUS day's Asian.
#   Jan 2 group contains bars where (ts - 5h).date() = Jan 2
#   = ts from Jan 2 05:00 UTC to Jan 3 04:59 UTC
#   Asian in this range: 19:00-23:59 EST Jan 2 = 00:00-04:59 UTC Jan 3
#   Plus: 00:00-02:59 EST Jan 2 = 05:00-07:59 UTC Jan 2
#   So Asian = bars from 05:00-07:59 UTC Jan 2 AND 00:00-04:59 UTC Jan 3

# Nautilus for Jan 3 group: bars where date(UTC) = Jan 3
#   = bars from Jan 3 00:00 UTC to Jan 3 23:59 UTC
#   Asian in this range: 19:00-23:59 EST = 00:00-04:59 UTC NEXT day (Jan 4)
#   AND 00:00-02:59 EST = 05:00-07:59 UTC same day
#   So Asian = bars from 05:00-07:59 UTC Jan 3 AND 00:00-04:59 UTC Jan 4

# COMPLETELY DIFFERENT!
# Python Jan 2 Asian: [Jan 2 05:00-07:59 UTC] + [Jan 3 00:00-04:59 UTC]  
# Nautilus Jan 3 Asian: [Jan 3 05:00-07:59 UTC] + [Jan 4 00:00-04:59 UTC]

# These are OFFSET BY 1 DAY!
# Nautilus Asian range for "Jan 3" = what Python thinks is Jan 3's Asian range
# (from the perspective of London open)

# This means:
# - Python session for date D uses Asian range from (D 7PM EST to D+1 3AM EST)
# - Nautilus session for UTC date D uses Asian range from... let me think again
#   Nautilus tracks Asian bars where EST hour >= 19 or < 3
#   For UTC date D: bars from D 00:00 UTC to D 23:59 UTC  
#   EST hour = (UTC_hour - 5) % 24
#   EST hour >= 19 => UTC_hour >= 0 (mod 24) => UTC_hour in [0..23] when (h-5)%24 >= 19
#   => h-5 >= 19 or h-5 < 0 => h >= 24 (impossible) or h < 5
#   Wait: (h - 5) % 24 >= 19 means h - 5 >= 19 (when h >= 5) -> h >= 24 (impossible)
#   OR h - 5 < 0 -> h < 5, then (h-5)%24 = h+19 which is >= 19
#   So EST hour >= 19 when UTC_hour < 5 (i.e., 0-4 UTC = 19-23 EST previous day)
#   EST hour < 3 when UTC_hour < 8 AND UTC_hour >= 5 (i.e., 5-7 UTC = 0-2 EST)
#   
#   So for UTC date D: Asian bars are UTC_hour 0-4 (EST 19-23 of prev trading day)
#   AND UTC_hour 5-7 (EST 0-2 of current trading day!)
#   
#   Python for EST date D: bars where (ts_utc - 5h).date() = D
#   => ts_utc from D 05:00 to D+1 04:59 UTC
#   Asian bars: EST hour >= 19 => (UTC_hour - 5) % 24 >= 19 => UTC_hour < 5  
#   AND ts_utc in [D 05:00 to D+1 04:59]
#   => UTC_hour < 5 AND ts_utc >= D 05:00 UTC => ts_utc in [D+1 00:00 to D+1 04:59 UTC]
#   Asian bars: EST hour < 3 => UTC_hour in [5, 6, 7] AND ts_utc in [D 05:00 to D+1 04:59]
#   => ts_utc in [D 05:00 to D 07:59 UTC]
#
#   Python date D Asian: [D 05:00-07:59 UTC] + [D+1 00:00-04:59 UTC]
#   Nautilus UTC date D Asian: [D 00:00-04:59 UTC] + [D 05:00-07:59 UTC]
#
#   THESE ARE THE SAME BARS! Just tracked under different dates.
#   Python groups under date D, Nautilus groups under dates D and D-1.
#   But the Asian range should be IDENTICAL since it uses the same bars.

print("CORRECTION: Let me trace more carefully...")
print("For a Monday trading session:")
print("  Asian = Sunday 7PM EST to Monday 3AM EST")
print("         = Monday 00:00 UTC to Monday 08:00 UTC")
print("  Python puts this range in Sunday's date group")
print("  Nautilus splits: Mon 00:00-04:59 in Monday, Mon 05:00-07:59 in Monday")
print("  Wait, Nautilus puts ALL of Mon 00:00-07:59 in Monday's UTC date")
print("  And Python puts ALL of Mon 00:00-04:59 in Sunday's date")
print("  And Python puts Mon 05:00-07:59 in Monday's date")
print("")
print("RE-WORKING:")
print("Python EST date Sunday = UTC [Sun 05:00 to Mon 04:59]")
print("  Asian bars in this range: UTC_hour < 5 within the range")
print("  = Mon 00:00-04:59 UTC (since Sun 05:00-07:59 is NOT < 5)")
print("  Asian: 1 bar at EST 19-23 (Mon 00:00-04:59 UTC = Sun 19:00-23:59 EST)")
print("  Missing: 00:00-02:59 EST = Mon 05:00-07:59 UTC -- THIS IS IN MONDAY'S GROUP!")
print("")
print("Python EST date Monday = UTC [Mon 05:00 to Tue 04:59]")
print("  Asian bars: Mon 05:00-07:59 UTC (EST 00:00-02:59) -- YES this IS Asian")
print("  AND Tue 00:00-04:59 UTC (EST 19:00-23:59 Mon) -- NO, that's Monday evening Asian = Tuesday session!")
print("")
print("SO: Python Sunday session gets Asian from: Mon 00:00-04:59 UTC")
print("    Python Monday session gets Asian from: Mon 05:00-07:59 UTC + Tue 00:00-04:59 UTC")
print("    Nautilus Monday session gets Asian from: Mon 00:00-04:59 UTC + Mon 05:00-07:59 UTC")
print("")
print("THESE ARE IDENTICAL! Same bars, just grouped under different dates.")
print("Sunday Python Asian = Mon 00:00-04:59 UTC")
print("Monday Nautilus Asian = Mon 00:00-07:59 UTC")  
print("Monday Python Asian = Mon 05:00-07:59 UTC + Tue 00:00-04:59 UTC")

print("\nBUT WAIT - Python runs sessions in DATE ORDER:")
print("Sunday session: Asian = Mon 00:00-04:59 UTC (only 5 hours)")
print("Monday session: Asian = Mon 05:00 Tue 04:59 UTC range")
print("  Of which Asian = Mon 05:00-07:59 UTC (3 hours)")
print("Monday session total Asian range = Mon 00:00-07:59 UTC")
print("  because the bars at Mon 00:00-04:59 ALSO have EST hour 19-23!")
print("  But those bars were already used for Sunday session!")
print("  Python's _find_asian_range only looks within the day's bars")
print("  So Sunday gets only 5 hours of Asian, Monday gets 5+3=8 hours combined")

# OK I think the real answer is different. Let me just instrument both and compare.
print("\n\n=== INSTRUMENTED COMPARISON ===")
print("Adding detailed logging to trace exactly what happens...")
