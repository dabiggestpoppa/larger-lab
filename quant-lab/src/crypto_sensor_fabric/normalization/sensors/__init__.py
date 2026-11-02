"""SENSOR-B5-I10E1 - checkpoint-local public API of the Bloc 5 sensor normalizers.

The ``normalization/sensors/`` namespace (bloc_05/03 section 2 and section 18;
``BLOC_05_I10D1_DECISION_PACKAGE.md`` section 9.1) ships exactly two concerns at
I10:

* ``side_maps`` -- provider-neutral source-side evidence, the one declared
  Binance USD-M ``isBuyerMaker`` rule, the provisional-versus-admitted split and
  the typed refusal path;
* ``trade`` -- the typed trade observation input, the trade-specific T1 record
  over the accepted ``T1BaseEnvelope``, and the pure ``normalize_trade``.

Two boundaries this package deliberately keeps:

**The ratified root API is untouched.**  ``crypto_sensor_fabric.normalization``
keeps its 24 I01 symbols and does NOT re-export anything from here, so the sensor
surface is reachable only by its explicit path.  That is what keeps the I01
scope audit's absolute module and symbol measurements honest.

**The composite envelope stays unexported.**  ``T1ObservationEnvelope`` is not a
name this package offers: the frozen full envelope also carries
identity/methodology/replay fields owned by other checkpoints, so exposing the
name here would let a consumer mistake a partial record for the finished
contract.  What this package offers is a trade-specific record that EXTENDS the
accepted base, plus the two record-level methodology slots
``normalization_methodology_id`` / ``_version`` under bloc_05/03 section 2's own
field names -- so a later composite release is a move, not a rename.

Only the symbols below are public contract for this package.  No network, no wall
clock, no filesystem, no provider package import: evidence in, answer out.
"""

from __future__ import annotations

from .side_maps import (
    BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID,
    BINANCE_PROVIDER_ID,
    ProvisionalSideMapping,
    SideEvidence,
    SideEvidenceKind,
    SideMappingStatus,
    UnsupportedSideMappingError,
    admit_aggressor_side,
    apply_side_map,
    binance_side_from_is_buyer_maker,
    require_side_mapping,
    resolve_side_mapping,
)
from .trade import (
    I04B_METHODOLOGY_ID,
    I08_UNITS_METHODOLOGY_ID,
    DerivedAmount,
    T1TradeRecord,
    TradeObservationInput,
    normalize_trade,
)

__all__ = [
    # side evidence + the one declared rule
    "BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID",
    "BINANCE_PROVIDER_ID",
    "ProvisionalSideMapping",
    "SideEvidence",
    "SideEvidenceKind",
    "SideMappingStatus",
    "UnsupportedSideMappingError",
    "admit_aggressor_side",
    "apply_side_map",
    "binance_side_from_is_buyer_maker",
    "require_side_mapping",
    "resolve_side_mapping",
    # trade normalization
    "I04B_METHODOLOGY_ID",
    "I08_UNITS_METHODOLOGY_ID",
    "DerivedAmount",
    "T1TradeRecord",
    "TradeObservationInput",
    "normalize_trade",
]
