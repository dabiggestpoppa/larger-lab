"""Repo-local filesystem paths for the sensor fabric.

Only code-adjacent paths are resolved here (config, evidence).  No market-data
paths live in this module: actual T0/T1/T2 data stays outside Git and is owned
by later blocs.
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent  # .../quant-lab/src/crypto_sensor_fabric
QUANT_LAB_ROOT = PACKAGE_ROOT.parents[1]  # .../quant-lab
REPO_ROOT = PACKAGE_ROOT.parents[2]  # git worktree root

CONFIG_DIR = QUANT_LAB_ROOT / "config" / "crypto_sensor_fabric"

SENSOR_FABRIC_RESEARCH_DIR = (
    QUANT_LAB_ROOT / "research" / "crypto_foundry" / "sensor_fabric"
)
EVIDENCE_BLOC_01_DIR = SENSOR_FABRIC_RESEARCH_DIR / "evidence" / "bloc_01"
