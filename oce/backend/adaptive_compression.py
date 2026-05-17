"""
OCE Adaptive Compression — Phase 9.3
=====================================
Memory layer compression with anchor preservation.

Ensures recoverability anchors are never compressed while
allowing non-critical data to be compressed to reduce resource consumption.
"""

import sqlite3
import json
import logging
import uuid
import zlib
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.compression")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "compression.db"

# ─── Compression Policies ──────────────────────────────────────────────────

COMPRESSION_POLICIES = {
    "aggressive": {"ratio": 0.3, "exclude_anchors": True, "min_age_hours": 1},
    "moderate": {"ratio": 0.6, "exclude_anchors": True, "min_age_hours": 6},
    "conservative": {"ratio": 0.8, "exclude_anchors": True, "min_age_hours": 24},
    "none": {"ratio": 1.0, "exclude_anchors": True, "min_age_hours": 0},
}

# Anchor keys that must never be compressed
ANCHOR_KEYS = {
    "attractor_state", "observer_config", "topology_map", "repair_log",
    "continuity_anchor", "session_state", "identity", "sovereignty_boundaries",
}


class AdaptiveCompression:
    """
    Singleton adaptive compression engine for OCE.

    Compresses memory layer data while preserving recoverability anchors.
    """

    _instance: Optional["AdaptiveCompression"] = None
    _lock = Lock()

    def __new__(cls) -> "AdaptiveCompression":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._policies: Dict[str, Dict] = {}
        self._compression_stats: Dict[str, Dict] = {}

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("AdaptiveCompression initialized")

    def _init_db(self):
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compression_history (
                    record_id TEXT PRIMARY KEY,
                    layer TEXT NOT NULL,
                    original_size INTEGER NOT NULL,
                    compressed_size INTEGER NOT NULL,
                    ratio REAL NOT NULL,
                    policy TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def compress_layer(self, layer: str, data: Dict[str, Any],
                       target_ratio: float = 0.6) -> Dict[str, Any]:
        """
        Compress memory layer data while preserving anchors.
        Returns compressed data with metadata.
        """
        if layer not in self._compression_stats:
            self._compression_stats[layer] = {
                "original_size": 0, "compressed_size": 0, "compressions": 0
            }

        # Separate anchors from compressible data
        anchors = {}
        compressible = {}
        for key, value in data.items():
            if key in ANCHOR_KEYS or key.startswith("anchor_"):
                anchors[key] = value
            else:
                compressible[key] = value

        # Compress the compressible portion
        original_size = len(json.dumps(compressible).encode())
        if compressible:
            compressed_bytes = zlib.compress(
                json.dumps(compressible).encode(),
                level=6
            )
            compressed_size = len(compressed_bytes)
        else:
            compressed_bytes = b""
            compressed_size = 0

        # Build result: anchors (uncompressed) + compressed blob
        result = {
            "_anchors": anchors,
            "_compressed": compressed_bytes.hex() if compressed_bytes else "",
            "_metadata": {
                "layer": layer,
                "original_size": original_size + len(json.dumps(anchors).encode()),
                "compressed_size": compressed_size + len(json.dumps(anchors).encode()),
                "ratio": round(compressed_size / max(original_size, 1), 3),
                "policy": f"target_{target_ratio}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

        # Update stats
        stats = self._compression_stats[layer]
        stats["original_size"] += original_size
        stats["compressed_size"] += compressed_size
        stats["compressions"] += 1

        # Log compression
        self._log_compression(layer, original_size, compressed_size, target_ratio)

        logger.info(f"Compressed layer {layer}: {original_size} -> {compressed_size} bytes")
        return result

    def decompress_layer(self, compressed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decompress layer data, restoring anchors."""
        anchors = compressed_data.get("_anchors", {})
        compressed_hex = compressed_data.get("_compressed", "")

        result = dict(anchors)

        if compressed_hex:
            try:
                compressed_bytes = bytes.fromhex(compressed_hex)
                decompressed = zlib.decompress(compressed_bytes)
                data = json.loads(decompressed)
                result.update(data)
            except Exception as e:
                logger.error(f"Decompression failed: {e}")
                result["_decompression_error"] = str(e)

        return result

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics per layer."""
        stats = {}
        for layer, data in self._compression_stats.items():
            original = data["original_size"]
            compressed = data["compressed_size"]
            stats[layer] = {
                "original_size": original,
                "compressed_size": compressed,
                "ratio": round(compressed / max(original, 1), 3),
                "savings_pct": round((1 - compressed / max(original, 1)) * 100, 1),
                "compressions": data["compressions"],
            }
        return stats

    def set_compression_policy(self, layer: str, policy: str) -> None:
        """Set compression policy for a layer (aggressive, moderate, conservative, none)."""
        if policy not in COMPRESSION_POLICIES:
            raise ValueError(f"Unknown policy: {policy}. Choose from: {list(COMPRESSION_POLICIES.keys())}")
        self._policies[layer] = dict(COMPRESSION_POLICIES[policy])
        logger.info(f"Compression policy for '{layer}': {policy}")

    def preserve_anchors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and preserve recoverability anchors from data."""
        anchors = {}
        for key in ANCHOR_KEYS:
            if key in data:
                anchors[key] = data[key]
        # Also preserve any key starting with "anchor_"
        for key in data:
            if key.startswith("anchor_"):
                anchors[key] = data[key]
        return anchors

    def _log_compression(self, layer: str, original_size: int,
                         compressed_size: int, ratio: float):
        """Log compression to SQLite."""
        record_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT INTO compression_history
                    (record_id, layer, original_size, compressed_size, ratio, policy, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (record_id, layer, original_size, compressed_size, ratio, f"target_{ratio}", now),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log compression: {e}")


def get_adaptive_compression() -> AdaptiveCompression:
    """Get the singleton AdaptiveCompression instance."""
    return AdaptiveCompression()
