"""
Shared test configuration for OCE backend tests.
Adds the backend directory to sys.path so imports work.
"""

import os
import sys

# Add the backend directory to sys.path so `from execution_engine import ...` works
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
