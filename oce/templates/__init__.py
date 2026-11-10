"""OCE Golden System — template namespace (B6-I2).

A template is a deterministic, offline file set. Nothing here publishes, signs, uploads or
contacts a network; installation refuses anything that is not an exact, digest-bound archive.
"""
from __future__ import annotations

from . import archive, refusals, skeleton

__all__ = ["archive", "refusals", "skeleton"]
