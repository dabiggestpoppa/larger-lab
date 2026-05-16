"""Check Nautilus Trader environment and available components."""
import nautilus_trader
print(f"Nautilus Trader: {nautilus_trader.__version__}")
print(f"Location: {nautilus_trader.__file__}")

# Check available adapters
import os
adapter_path = os.path.join(os.path.dirname(nautilus_trader.__file__), "adapters")
if os.path.exists(adapter_path):
    print(f"\nAvailable adapters:")
    for item in os.listdir(adapter_path):
        print(f"  - {item}")
else:
    print(f"\nNo adapters directory found at {adapter_path}")

# Check test_kit
from nautilus_trader.test_kit.providers import TestInstrumentProvider
methods = [x for x in dir(TestInstrumentProvider) if not x.startswith("_")]
print(f"\nTestInstrumentProvider methods:")
for m in methods:
    print(f"  - {m}")

# Check if we can create FX instruments
try:
    audusd = TestInstrumentProvider.default_fx_ccy("AUD/USD")
    print(f"\n✅ FX instrument creation works: {audusd}")
except Exception as e:
    print(f"\n❌ FX instrument creation failed: {e}")

# Check data catalog
try:
    from nautilus_trader.persistence.catalog import ParquetDataCatalog
    print("✅ ParquetDataCatalog available")
except Exception as e:
    print(f"❌ ParquetDataCatalog: {e}")

# Check backtest engine
try:
    from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
    print("✅ BacktestEngine available")
except Exception as e:
    print(f"❌ BacktestEngine: {e}")
