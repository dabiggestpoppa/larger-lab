import MetaTrader5 as mt5
from datetime import datetime
mt5.initialize()

# Check total available bars
rates_all = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M5, 0, 1000000)
if rates_all is not None:
    print("Total bars available (max fetch):", len(rates_all))
    print("Earliest:", datetime.utcfromtimestamp(rates_all[0][0]))
    print("Latest:", datetime.utcfromtimestamp(rates_all[-1][0]))
else:
    print("Error fetching:", mt5.last_error())

# Try date range
rates_range = mt5.copy_rates_range("EURUSD", mt5.TIMEFRAME_M5, datetime(2022, 1, 1), datetime(2022, 2, 1))
if rates_range is not None:
    print("Jan 2022 bars:", len(rates_range))
    print("First:", datetime.utcfromtimestamp(rates_range[0][0]))
    print("Last:", datetime.utcfromtimestamp(rates_range[-1][0]))
else:
    print("No Jan 2022 data:", mt5.last_error())

mt5.shutdown()
