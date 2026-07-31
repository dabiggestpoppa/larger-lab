import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('cerebus.symmetry_trap').setLevel(logging.WARNING)
logging.getLogger('cerebus.symmetry_trap_backtest').setLevel(logging.WARNING)

from pathlib import Path
import json

REPO_ROOT = Path(r'C:\Users\wifik\Desktop\projects\larger-lab')
QUANT_LAB = REPO_ROOT / 'quant-lab'
DATA_DIR = QUANT_LAB / 'data'
REPORTS_DIR = QUANT_LAB / 'reports'
CONFIGS_DIR = QUANT_LAB / 'configs'
ENGINES_DIR = QUANT_LAB / 'engines'

sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, BacktestResult, load_m5_csv

asset_key = 'EURGBP'
csv_path = DATA_DIR / 'EURGBP_PRO_M5.csv'
config = ASSET_CONFIGS[asset_key]
print(f'Running {asset_key} | trigger={config["tiers"]["T1"]["trigger"]}p | csv={csv_path.name}')
sys.stdout.flush()

bt = SymmetryTrapBacktest(pip_size=config['pip_value'], tier_config=config['tiers'], symbol=asset_key, config=config)
result = bt.run_from_csv(str(csv_path))

tpd = result.total_trades / result.data_days if result.data_days > 0 else 0
print(f'Result: {result.total_trades} trades | {result.data_days} days | {tpd:.2f} tr/day | WR={result.win_rate:.1f}% | PF={result.profit_factor:.2f}')
