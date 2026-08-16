"""Deterministic result persistence for the MVE runner.

Writes phase/diagnostic artifacts (CSV/JSON/Markdown), records output hashes,
and refuses to overwrite outputs produced by a different run config.

This is infrastructure only - no scientific logic lives here.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Dict

import pandas as pd


class PersistenceError(Exception):
    """Raised when outputs cannot be persisted safely (fail-closed)."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj) -> str:
    """Canonical JSON hash (sorted keys, compact separators, stable types)."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_bytes(payload.encode("utf-8"))


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_text(path: str, content: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def write_json(path: str, obj) -> None:
    write_text(path, json.dumps(obj, indent=2, default=str) + "\n")


def write_csv(path: str, df: pd.DataFrame) -> None:
    ensure_dir(os.path.dirname(path))
    df.to_csv(path, index=False)


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def prior_manifest_config_hash(output_dir: str):
    manifest_path = os.path.join(output_dir, "RUN_MANIFEST.json")
    if os.path.exists(manifest_path):
        m = read_json(manifest_path)
        return m.get("config_hash")
    return None


def persist_run(
    output_dir: str,
    config_hash: str,
    artifacts: Dict[str, str],
    manifest: Dict,
) -> Dict[str, str]:
    """Persist artifacts + manifest, protecting against incompatible overwrite.

    artifacts: {relative_filename: content_string}. CSV entries must be passed
    via write_csv separately; this helper handles text artifacts and, for
    entries whose content is a pandas DataFrame, serializes to CSV.

    Returns the output artifact hash map {filename: sha256}.
    """
    # Refuse overwrite when a prior run with a different config exists.
    prior_hash = prior_manifest_config_hash(output_dir)
    if prior_hash is not None and prior_hash != config_hash:
        raise PersistenceError(
            f"Refusing to overwrite {output_dir}: prior run config_hash "
            f"{prior_hash} != requested {config_hash}"
        )

    ensure_dir(output_dir)

    output_hashes: Dict[str, str] = {}
    for filename, content in artifacts.items():
        path = os.path.join(output_dir, filename)
        if isinstance(content, pd.DataFrame):
            write_csv(path, content)
            output_hashes[filename] = sha256_file(path)
        else:
            write_text(path, str(content))
            output_hashes[filename] = sha256_bytes(str(content).encode("utf-8"))

    # Attach output hashes to the manifest before persisting it.
    manifest = dict(manifest)
    manifest["output_hashes"] = output_hashes
    write_json(os.path.join(output_dir, "RUN_MANIFEST.json"), manifest)

    # Record the manifest's own hash for attribution.
    manifest_hash = sha256_json(manifest)
    return {**output_hashes, "RUN_MANIFEST.json": manifest_hash}
