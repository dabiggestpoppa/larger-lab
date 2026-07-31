"""
Phase 11.1 — Metrics Exporter
Exports Phase 11.1 metrics to various formats.
"""

import time
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ExportResult:
    """Result of metrics export."""
    export_id: str
    timestamp: float
    format: str
    file_path: str
    records_exported: int
    success: bool


class MetricsExporter:
    """
    Exports Phase 11.1 metrics to various formats.
    Part of Phase 11.1 long-horizon testing.
    """
    
    def __init__(self, db_path: str = "stability/metrics_export.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_exports (
                export_id TEXT PRIMARY KEY,
                timestamp REAL,
                format TEXT,
                file_path TEXT,
                records_exported INTEGER,
                success INTEGER
            )
        """)
        conn.commit()
        conn.close()
        
    def export_runtime_metrics(self, output_path: str, 
                                hours: int = 24) -> ExportResult:
        """Export runtime metrics to JSON."""
        cutoff = time.time() - (hours * 3600)
        
        # Read from runtime_metrics table
        conn = sqlite3.connect("stability/runtime_metrics.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM runtime_metrics WHERE timestamp > ?
        """, (cutoff,))
        
        records = cursor.fetchall()
        conn.close()
        
        # Write to JSON
        data = []
        for row in records:
            data.append({
                "timestamp": row[0],
                "cpu_percent": row[1],
                "memory_mb": row[2],
                "disk_percent": row[3],
                "network_bytes": row[4],
                "uptime_seconds": row[5]
            })
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        result = ExportResult(
            export_id=f"export_{int(time.time()*1000)}",
            timestamp=time.time(),
            format="json",
            file_path=output_path,
            records_exported=len(data),
            success=True
        )
        
        self._save_export(result)
        return result
    
    def export_drift_scores(self, output_path: str,
                            hours: int = 24) -> ExportResult:
        """Export drift scores to JSON."""
        cutoff = time.time() - (hours * 3600)
        
        conn = sqlite3.connect("stability/drift_scores.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM drift_scores WHERE timestamp > ?
        """, (cutoff,))
        
        records = cursor.fetchall()
        conn.close()
        
        data = []
        for row in records:
            data.append({
                "timestamp": row[1],
                "score": row[2],
                "component": row[3],
                "details": row[4]
            })
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        result = ExportResult(
            export_id=f"export_{int(time.time()*1000)}",
            timestamp=time.time(),
            format="json",
            file_path=output_path,
            records_exported=len(data),
            success=True
        )
        
        self._save_export(result)
        return result
    
    def export_all_metrics(self, output_dir: str,
                           hours: int = 24) -> List[ExportResult]:
        """Export all Phase 11.1 metrics."""
        results = []
        
        results.append(self.export_runtime_metrics(
            f"{output_dir}/runtime_metrics.json", hours
        ))
        results.append(self.export_drift_scores(
            f"{output_dir}/drift_scores.json", hours
        ))
        
        return results
    
    def _save_export(self, result: ExportResult):
        """Save export record to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrics_exports VALUES (
                :export_id, :timestamp, :format, :file_path,
                :records_exported, :success
            )
        """, {
            "export_id": result.export_id,
            "timestamp": result.timestamp,
            "format": result.format,
            "file_path": result.file_path,
            "records_exported": result.records_exported,
            "success": 1 if result.success else 0
        })
        conn.commit()
        conn.close()


if __name__ == "__main__":
    exporter = MetricsExporter()
    
    # Example usage
    results = exporter.export_all_metrics("stability/exports")
    for r in results:
        print(f"Exported {r.records_exported} records to {r.file_path}")