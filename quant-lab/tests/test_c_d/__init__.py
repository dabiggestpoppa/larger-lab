# Make quant_lab.engines.* resolve to quant-lab/engines/*.py
import os, sys
_real_engines = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "quant-lab", "engines"
)
if _real_engines not in sys.path:
    sys.path.insert(0, _real_engines)
