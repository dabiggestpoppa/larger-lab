"""
Crypto Foundry DATA-1 Schema Validator

Validates normalized records against the frozen schema registry.
Every normalized record MUST pass schema validation before storage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

SCHEMA_VERSION = "1.0.0"

# Frozen schemas from CRYPTO_SCHEMA_REGISTRY.json
REQUIRED_COMMON_FIELDS = [
    "venue",
    "market_id",
    "event_time_utc",
    "ingest_time_utc",
    "source",
    "source_version",
    "raw_identifier",
    "schema_version",
]

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "PERP_TRADE": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "instrument_id",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "trade_id", "price", "size", "side", "liquidation_flag",
            "matching_engine_id",
        ],
        "numeric_fields": {"price", "size"},
        "enum_fields": {"side": {"BUY", "SELL", "buy", "sell", "bid", "ask", None}},
        "required": {"venue", "market_id", "event_time_utc", "source",
                      "source_version", "schema_version", "price", "size", "side"},
    },
    "PERP_BOOK_SNAPSHOT": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "instrument_id",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version", "bids", "asks", "checksum",
        ],
        "required": {"venue", "market_id", "event_time_utc", "source",
                      "source_version", "schema_version", "bids", "asks"},
    },
    "PERP_FUNDING": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "instrument_id",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "funding_rate", "funding_time_utc", "mark_price", "index_price",
        ],
        "numeric_fields": {"funding_rate", "mark_price", "index_price"},
        "required": {"venue", "market_id", "event_time_utc", "source",
                      "source_version", "schema_version", "funding_rate"},
    },
    "PERP_OPEN_INTEREST": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "instrument_id",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "open_interest", "open_interest_value_usd",
        ],
        "numeric_fields": {"open_interest", "open_interest_value_usd"},
        "required": {"venue", "market_id", "event_time_utc", "source",
                      "source_version", "schema_version", "open_interest"},
    },
    "PERP_MARK_INDEX": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "instrument_id",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "mark_price", "index_price", "oracle_price", "premium",
        ],
        "numeric_fields": {"mark_price", "index_price", "oracle_price", "premium"},
        "required": {"venue", "market_id", "event_time_utc", "source",
                      "source_version", "schema_version", "mark_price", "index_price"},
    },
    "PERP_LIQUIDATION": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "instrument_id",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "side", "size", "price", "liquidated_account", "estimated_loss",
        ],
        "numeric_fields": {"size", "price", "estimated_loss"},
        "required": {"venue", "market_id", "event_time_utc", "source",
                      "source_version", "schema_version", "side", "size", "price"},
    },
    "SPOT_BAR_REFERENCE": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "instrument_id",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "open", "high", "low", "close", "volume", "trades_count", "interval",
        ],
        "numeric_fields": {"open", "high", "low", "close", "volume", "trades_count"},
        "required": {"venue", "market_id", "event_time_utc", "source",
                      "source_version", "schema_version", "open", "high", "low",
                      "close", "volume"},
    },
    "AMM_SWAP": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "pool_address",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "block_number", "tx_hash", "log_index", "sender", "recipient",
            "amount0", "amount1", "sqrt_price_x96", "tick", "fee_tier",
            "pool_fee_amount0", "pool_fee_amount1",
        ],
        "numeric_fields": {"block_number", "log_index", "amount0", "amount1",
                            "sqrt_price_x96", "tick", "fee_tier",
                            "pool_fee_amount0", "pool_fee_amount1"},
        "required": {"venue", "market_id", "pool_address", "event_time_utc",
                      "source", "source_version", "schema_version",
                      "block_number", "tx_hash", "log_index",
                      "amount0", "amount1", "sqrt_price_x96", "tick"},
    },
    "AMM_LIQUIDITY_EVENT": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "pool_address",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "block_number", "tx_hash", "log_index", "event_type", "owner",
            "amount", "amount0", "amount1", "tick_lower", "tick_upper",
            "liquidity",
        ],
        "numeric_fields": {"block_number", "log_index", "amount", "amount0",
                            "amount1", "tick_lower", "tick_upper", "liquidity"},
        "required": {"venue", "market_id", "pool_address", "event_time_utc",
                      "source", "source_version", "schema_version",
                      "block_number", "tx_hash", "log_index", "event_type"},
    },
    "AMM_POOL_STATE": {
        "fields": [
            "venue", "chain_if_applicable", "market_id", "pool_address",
            "event_time_utc", "ingest_time_utc", "source", "source_version",
            "raw_identifier", "schema_version",
            "block_number", "sqrt_price_x96", "tick", "liquidity",
            "fee_growth_global_0_x128", "fee_growth_global_1_x128",
        ],
        "numeric_fields": {"block_number", "sqrt_price_x96", "tick", "liquidity"},
        "required": {"venue", "market_id", "pool_address", "event_time_utc",
                      "source", "source_version", "schema_version",
                      "block_number", "sqrt_price_x96", "tick", "liquidity"},
    },
}


@dataclass
class SchemaViolation:
    schema_name: str
    field_name: str
    violation_type: str  # missing, invalid_type, invalid_enum, invalid_numeric
    message: str
    value: Any = None


@dataclass
class ValidationResult:
    schema_name: str
    record_index: int
    passed: bool
    violations: List[SchemaViolation] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "schema_name": self.schema_name,
            "record_index": self.record_index,
            "passed": self.passed,
            "violation_count": len(self.violations),
            "violations": [
                {
                    "field": v.field_name,
                    "type": v.violation_type,
                    "message": v.message,
                }
                for v in self.violations
            ],
        }


class SchemaValidator:
    """Validates records against frozen schemas."""

    def __init__(self):
        self.schemas = SCHEMAS
        self.version = SCHEMA_VERSION

    def validate_record(
        self, record: Dict[str, Any], schema_name: str, record_index: int = 0
    ) -> ValidationResult:
        """Validate a single record against a named schema."""
        violations: List[SchemaViolation] = []

        if schema_name not in self.schemas:
            violations.append(SchemaViolation(
                schema_name=schema_name,
                field_name="_schema",
                violation_type="unknown_schema",
                message=f"Unknown schema: {schema_name}",
            ))
            return ValidationResult(schema_name, record_index, False, violations)

        schema = self.schemas[schema_name]
        required = schema.get("required", set())
        numeric_fields = schema.get("numeric_fields", set())
        enum_fields = schema.get("enum_fields", {})

        # Check required fields
        for field_name in required:
            if field_name not in record:
                violations.append(SchemaViolation(
                    schema_name=schema_name,
                    field_name=field_name,
                    violation_type="missing",
                    message=f"Required field '{field_name}' is missing",
                ))
            elif record[field_name] is None and field_name in ("venue", "market_id", "source", "schema_version"):
                violations.append(SchemaViolation(
                    schema_name=schema_name,
                    field_name=field_name,
                    violation_type="missing",
                    message=f"Required field '{field_name}' is None",
                ))

        # Validate numeric fields
        for field_name in numeric_fields:
            if field_name in record and record[field_name] is not None:
                val = record[field_name]
                if not isinstance(val, (int, float)):
                    violations.append(SchemaViolation(
                        schema_name=schema_name,
                        field_name=field_name,
                        violation_type="invalid_type",
                        message=f"Field '{field_name}' must be numeric, got {type(val).__name__}",
                        value=val,
                    ))

        # Validate enum fields
        for field_name, allowed_values in enum_fields.items():
            if field_name in record and record[field_name] is not None:
                if record[field_name] not in allowed_values:
                    violations.append(SchemaViolation(
                        schema_name=schema_name,
                        field_name=field_name,
                        violation_type="invalid_enum",
                        message=f"Field '{field_name}' value '{record[field_name]}' not in {allowed_values}",
                        value=record[field_name],
                    ))

        # Validate event_time_utc is parseable
        if "event_time_utc" in record and record["event_time_utc"] is not None:
            et = record["event_time_utc"]
            if isinstance(et, str):
                try:
                    datetime.fromisoformat(et.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    violations.append(SchemaViolation(
                        schema_name=schema_name,
                        field_name="event_time_utc",
                        violation_type="invalid_datetime",
                        message=f"Cannot parse event_time_utc: {et}",
                        value=et,
                    ))
            elif isinstance(et, (int, float)):
                pass  # Unix timestamp is OK
            elif isinstance(et, datetime):
                pass
            else:
                violations.append(SchemaViolation(
                    schema_name=schema_name,
                    field_name="event_time_utc",
                    violation_type="invalid_type",
                    message=f"event_time_utc has unexpected type: {type(et).__name__}",
                    value=et,
                ))

        # Validate schema_version
        if "schema_version" in record and record["schema_version"] is not None:
            if record["schema_version"] != self.version:
                violations.append(SchemaViolation(
                    schema_name=schema_name,
                    field_name="schema_version",
                    violation_type="version_mismatch",
                    message=f"Expected schema_version={self.version}, got {record['schema_version']}",
                    value=record["schema_version"],
                ))

        passed = len(violations) == 0
        return ValidationResult(schema_name, record_index, passed, violations)

    def validate_batch(
        self, records: List[Dict[str, Any]], schema_name: str
    ) -> List[ValidationResult]:
        """Validate a batch of records."""
        return [
            self.validate_record(r, schema_name, i)
            for i, r in enumerate(records)
        ]

    def summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Summarize batch validation results."""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        all_violations = []
        for r in results:
            all_violations.extend(r.violations)

        violation_types: Dict[str, int] = {}
        for v in all_violations:
            violation_types[v.violation_type] = violation_types.get(v.violation_type, 0) + 1

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "total_violations": len(all_violations),
            "violation_types": violation_types,
        }
