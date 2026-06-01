"""
Patch Nautilus strategy configs to use per-asset configs from asset_configs.py.
This is loaded by run_cerebus_backtest.py before creating strategies.

Usage: from naut_asset_config import get_naut_config_for_symbol
"""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab/configs')

from quant_lab.configs.asset_configs import ASSET_CONFIGS

# Nautilus default pip divisors for forefx
FOREX_PIP_DIVISOR = 10000.0
JPY_PIP_DIVISOR = 100.0

def get_pip_divisor(symbol: str, pip_value: float) -> float:
    """Convert pip_value to Nautilus pip divisor.
    
    Nautilus works in integer 'price units'. For EURUSD at 1.0500 with pip=0.0001:
      divisor = 1/0.0001 = 10000 → price_in_pips = price * 10000
    
    For BTCUSD at 105000 with pip=1.0:
      divisor = 1/1.0 = 1.0 → price_in_pips = price * 1.0 (= price itself)
    """
    if pip_value <= 0:
        return 10000.0
    return 1.0 / pip_value


def get_naut_config_for_symbol(symbol: str) -> dict:
    """Get Nautilus-compatible configuration for a symbol from asset_configs.py.
    
    Returns dict with:
      - pip_divisor: float (for converting price to pips)
      - tier_config: dict {T1/T2/T3: {ar_max, au, trigger}}
      - k_factor: float
      - pip_value: float
      - scale_factor: float (Nautilus lot_size adjustment)
    """
    cfg = ASSET_CONFIGS.get(symbol)
    if not cfg:
        # Default to EURUSD config
        cfg = ASSET_CONFIGS['EURUSD']
    
    pip_value = cfg['pip_value']
    k_factor = cfg['k_factor']
    tiers = cfg['tiers']
    
    pip_divisor = get_pip_divisor(symbol, pip_value)
    
    # Scale factor: Nautilus default lot_size=1000 works for FX (1000 units = 0.1 lot)
    # For BTCUSD (pip=1.0, price~105000), we want smaller position scaling
    # For XAUUSD (pip=0.1, price~3300), moderate scaling
    if pip_value >= 1.0:
        # Crypto/indices with large pip values — reduce effective lot size in pip calc
        scale_factor = 1.0 / pip_value
    elif pip_value >= 0.1:
        # Gold (pip=0.1)
        scale_factor = 0.1 / pip_value
    else:
        # Standard FX (pip=0.0001 or 0.01 for JPY)
        scale_factor = 0.0001 / pip_value if pip_value < 0.01 else 1.0
    
    return {
        'symbol': symbol,
        'pip_value': pip_value,
        'pip_divisor': pip_divisor,
        'k_factor': k_factor,
        'tier_config': tiers,
        'scale_factor': scale_factor,
        'sl_buffer': cfg.get('sl_buffer', {}),
        'gear_shifts': cfg.get('gear_shifts', {}),
        'p90_threshold': cfg.get('p90_threshold', 0),
        'fixed_tp': cfg.get('fixed_tp', 0),
        'class': cfg.get('class', 'Unknown'),
    }


# Quick reference for key crypto symbols
CRYPTO_CONFIGS = {
    'BTCUSD': lambda: get_naut_config_for_symbol('BTCUSD'),
    'ETHUSD': lambda: get_naut_config_for_symbol('ETHUSD'),
    'XAUUSD': lambda: get_naut_config_for_symbol('XAUUSD'),
    'XAGUSD': lambda: get_naut_config_for_symbol('XAGUSD'),
}


if __name__ == '__main__':
    # Print all crypto configs for verification
    for sym in ['BTCUSD', 'ETHUSD', 'XAUUSD', 'XAGUSD', 'EURUSD']:
        c = get_naut_config_for_symbol(sym)
        print(f"\n=== {sym} ===")
        print(f"  pip_value={c['pip_value']}, divisor={c['pip_divisor']}, k={c['k_factor']}")
        print(f"  scale_factor={c['scale_factor']}")
        print(f"  tiers: T1={c['tier_config']['T1']}")
        print(f"         T2={c['tier_config']['T2']}")
        print(f"         T3={c['tier_config']['T3']}")
