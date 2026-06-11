"""Seed the sniper database with 100+ prop firms."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'quant-lab'))
from sniper.database import init_database, seed_sample_data, DB_PATH

# Remove stale DB
if DB_PATH.exists():
    DB_PATH.unlink()

init_database()
seed_sample_data()
print(f"Done! DB at {DB_PATH}")
