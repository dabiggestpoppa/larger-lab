"""Seed the sniper database."""
import sys
from pathlib import Path
# Add project root and quant-lab to path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'quant-lab'))
from sniper.database import init_database, seed_sample_data, DB_PATH

# Remove stale DB before creating fresh
p = Path(DB_PATH)
if p.exists():
    p.unlink()
init_database()
seed_sample_data()
print(f"Done! DB at {DB_PATH}")
