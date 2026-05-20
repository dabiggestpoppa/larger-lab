"""
SRRA-OPH API Wrapper
====================
FastAPI wrapper exposing SRRA-OPH module status, topology, tests, and events.
"""

from .main import app

__all__ = ["app"]
