#!/usr/bin/env python3
"""Launcher for panel rebuild — runs synchronously."""
import subprocess, sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
result = subprocess.run(
    [sys.executable, "-u", "quant-lab/research/crypto_foundry/derivatives/lower_field/scripts/lf_build_panel.py"],
    capture_output=False
)
sys.exit(result.returncode)
