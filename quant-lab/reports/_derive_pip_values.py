"""
Derive the dollar value of 1 engine-pip at 0.01 lot for each asset.
Uses: pip_size from asset_configs and standard MT5 contract sizes.
"""
import json
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')

from asset_configs import ASSET_CONFIGS

# MT5 standard contract sizes (units per standard lot)
CONTRACT_SIZES = {
    # Forex: 1 lot = 100,000 units of base currency
    "EURUSD": 100000, "GBPUSD": 100000, "USDJPY": 100000,
    "USDCHF": 100000, "AUDUSD": 100000, "NZDUSD": 100000,
    "USDCAD": 100000, "EURGBP": 100000, "EURJPY": 100000,
    "EURCHF": 100000, "EURCAD": 100000, "EURNZD": 100000,
    "EURAUD": 100000, "GBPJPY": 100000, "GBPCHF": 100000,
    "GBPCAD": 100000, "GBPAUD": 100000, "GBPNZD": 100000,
    "AUDJPY": 100000, "AUDCHF": 100000, "AUDCAD": 100000,
    "AUDNZD": 100000, "NZDJPY": 100000, "NZDCHF": 100000,
    "NZDCAD": 100000, "CADJPY": 100000, "CADCHF": 100000,
    "CHFJPY": 100000,
    # Metals: XAU 1 lot = 100 oz, XAG 1 lot = 5000 oz
    "XAUUSD": 100,       # 100 oz per lot
    "XAGUSD": 5000,      # 5000 oz per lot
    # Crypto: 1 lot = 1 coin
    "BTCUSD": 1,
    "ETHUSD": 1,
    # Indices: 1 lot = 1 contract, point value varies
    # USD-denominated indices: 1 point = $1 per lot
    "US500": 1,          # 1 lot = 1 contract, $1/point
    "NAS100": 1,
    "DE30": 1,           # EUR-denominated but engine records in EUR points
    "FR40": 1,
    "HK50": 1,           # HKD-denominated
}

# Average price levels (from CSV data samples) for conversion
AVG_PRICES = {
    "EURUSD": 1.08, "GBPUSD": 1.26, "USDJPY": 145.0,
    "USDCHF": 0.91, "AUDUSD": 0.67, "NZDUSD": 0.62,
    "USDCAD": 1.36, "EURGBP": 0.86, "EURJPY": 160.0,
    "EURCHF": 0.97, "EURCAD": 1.48, "EURNZD": 1.75,
    "EURAUD": 1.60, "GBPJPY": 180.0, "GBPCHF": 1.14,
    "GBPCAD": 1.72, "GBPAUD": 1.92, "GBPNZD": 2.15,
    "AUDJPY": 97.0, "AUDCHF": 0.60, "AUDCAD": 0.91,
    "AUDNZD": 1.08, "NZDJPY": 82.0, "NZDCHF": 0.55,
    "NZDCAD": 0.80, "CADJPY": 108.0, "CADCHF": 0.68,
    "CHFJPY": 162.0,
    "XAUUSD": 2000.0,     # $/oz
    "XAGUSD": 25.0,       # $/oz
    "BTCUSD": 50000.0,    # $/coin
    "ETHUSD": 3000.0,     # $/coin
    "US500": 4800.0,      # points
    "NAS100": 15000.0,    # points
    "DE30": 16000.0,      # points (EUR)
    "FR40": 7000.0,       # points (EUR)
    "HK50": 20000.0,      # points (HKD)
}

"""
For each asset, compute:
  1 engine_pip = pip_size of price movement
  $ per engine_pip per lot = pip_size * contract_size (in quote currency)
  
For forex: pip_size * 100,000 units = $ per pip for standard lot
  EURUSD: 0.0001 * 100,000 = $10/pip/lot
  USDJPY: 0.01 * 100,000 = ¥1000/pip/lot = $1000/rate per pip

For metals: 
  XAU: pip_size(0.1) * 100 oz = $10 * price/1000? No...
  Actually for XAU quoted as USD/oz: 0.1 price move * 100 oz = $10/pip/lot
  XAG: pip_size(0.01) * 5000 oz = $50/pip/lot

For crypto:
  BTC: pip_size(1.0) * 1 BTC * $50,000 = $50,000? No...
  BTC is quoted as USD per BTC. 1.0 price move = $1 per BTC.
  1 lot = 1 BTC. So 1 pip = $1/lot. At price $50k, 1 pip = $1.
  Actually no — pip is just the price unit. BTC price is ~$50,000.
  If pip_size=1.0, then 1 pip = $1 price move = $1 per 1 BTC = $1/lot.
  
For indices:
  US500: pip_size(1.0) * 1 contract. 1 point of S&P 500 = $1 per contract (micro).
  Actually standard: 1 ES point = $50. But MT5 micro = $1/point.
  Let's assume $1/point per lot for MT5 indices (micro contracts).
"""

print(f"{'Asset':<12} {'pip_size':>8} {'contr':>6} {'$/pip/lot':>10} {'$/pip/0.01':>10} {'comm_pips':>10}")
print("-" * 60)

for sym, cfg in ASSET_CONFIGS.items():
    pip_size = cfg["pip_value"]
    contract = CONTRACT_SIZES.get(sym, 100000)
    avg_price = AVG_PRICES.get(sym, 1.0)
    
    # Base $ per pip per standard lot
    # For forex: pip_size * contract = $ per pip (in quote currency, which is USD for XXXUSD)
    if sym in ["EURGBP", "EURCHF", "EURAUD", "EURCAD", "EURNZD", 
               "GBPCHF", "GBPCAD", "GBPAUD", "GBPNZD",
               "AUDCHF", "AUDCAD", "AUDNZD",
               "NZDCHF", "NZDCAD", "CADCHF"]:
        # These are XXXYYY where YYY is not USD
        # PnL is in YYY, need to convert to USD
        # For simplicity: the engine records pips based on price diff/pip_size
        # The dollar value depends on the quote currency
        $per_pip_per_lot = pip_size * contract  # in quote currency
        # For EURGBP, quote is GBP. 1 pip = 0.0001 * 100,000 = GBP 10
        # EUR/USD ~ 1.08, so GBP ~ 1.26 USD... approximately same as forex
        # For our purposes all forex is approximately $10/pip/lot
        $per_pip_per_lot = 10.0  # approximate for all forex
    elif sym in ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"]:
        # JPY pairs: pip is in JPY, need USD conversion
        # pip_size(0.01) * 100,000 = ¥1000 per pip per lot
        # At rate 145, ¥1000 = $6.90 per pip per lot
        ¥_per_pip = pip_size * contract  # ¥ per pip per lot
        $per_pip_per_lot = ¥_per_pip / avg_price if "USD" in sym else 10.0
        # For XXXJPY (non-USD), similar forex logic
        if sym != "USDJPY":
            $per_pip_per_lot = 10.0  # approximate
    elif sym in ["XAUUSD", "XAGUSD"]:
        # Metals quoted in USD/oz
        # pip_size * contract_size_in_oz = $ per pip per lot
        $per_pip_per_lot = pip_size * contract  # $ per price_move * oz
        # XAU: 0.1 * 100 = $10/pip/lot
        # XAG: 0.01 * 5000 = $50/pip/lot
    elif sym in ["BTCUSD", "ETHUSD"]:
        # Crypto quoted in USD per coin
        # pip_size * 1 coin = $ per pip per lot
        $per_pip_per_lot = pip_size * contract * avg_price / avg_price 
        # Actually: price is $/coin. pip_size in price units.
        # 1 pip = pip_size * $/coin * 1 coin = pip_size * $1 * (price/price) 
        # BTC: pip_size=1.0, 1 lot = 1 BTC, 1 pip = $1 * (1 BTC) * (price_at_$1/$confusion)
        # Simplest: 1 BTC at $50k. If pip_size=1, 1 pip = $1 of BTC price.
        # Since 1 lot = 1 BTC, $1 price move = $1 PnL for 1 lot.
        $per_pip_per_lot = pip_size  # $ per pip per lot (1 lot = 1 BTC, pip=$1)
    elif sym in ["US500", "NAS100", "DE30", "FR40", "HK50"]:
        # Indices: $1 per point per contract (MT5/micro)
        $per_pip_per_lot = pip_size * 1.0  # $ per point per lot
        # US500: pip_size=1.0 → $1/pip/lot
    else:
        # Standard forex XXXUSD
        $per_pip_per_lot = pip_size * contract  # 0.0001 * 100000 = $10
    
    $per_pip_at_001 = $per_pip_per_lot * 0.01  # $ per pip at 0.01 lot
    comm_per_trade = 7.0 * 0.01  # $0.07
    comm_pips = comm_per_trade / $per_pip_at_001 if $per_pip_at_001 > 0 else 0
    
    print(f"{sym:<12} {pip_size:>8} {contract:>6} ${$per_pip_per_lot:>9.2f} ${$per_pip_at_001:>9.4f} {comm_pips:>10.4f}")
