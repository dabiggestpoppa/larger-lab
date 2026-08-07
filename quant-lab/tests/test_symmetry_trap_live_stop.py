import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mt5 import symmetry_trap_executor as executor


def test_touch_exit_detected_for_long_and_short():
    assert executor.get_exit_trigger("LONG", 1.1000, 1.1000, 1.1010, 1.1030) == "SL"
    assert executor.get_exit_trigger("LONG", 1.1030, 1.1000, 1.1010, 1.1030) == "TP"
    assert executor.get_exit_trigger("SHORT", 1.1010, 1.1000, 1.1010, 1.0990) == "SL"
    assert executor.get_exit_trigger("SHORT", 1.1000, 1.0990, 1.1010, 1.0990) == "TP"


def test_touch_exit_detected_with_enum_direction():
    assert executor.get_exit_trigger(executor.TradeDirection.LONG, 1.1000, 1.1000, 1.1020, 1.1040) == "SL"
    assert executor.get_exit_trigger(executor.TradeDirection.SHORT, 1.1010, 1.1000, 1.1010, 1.0990) == "SL"
