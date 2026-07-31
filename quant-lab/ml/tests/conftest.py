"""
CEREBUS ML Test Configuration
===============================
Handles import paths for the quant-lab package.
"""

import sys
from pathlib import Path

# Add quant-lab directory to sys.path so imports work
QUANT_LAB_DIR = Path(__file__).resolve().parent.parent.parent
if str(QUANT_LAB_DIR) not in sys.path:
    sys.path.insert(0, str(QUANT_LAB_DIR))

# Also add workspace root for quant_lab.* imports
WORKSPACE_ROOT = QUANT_LAB_DIR.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))
