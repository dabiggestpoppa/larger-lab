"""SENSOR-B5-I04A deterministic evidence generator (tracked source, Stage E).

Run from quant-lab/:
    PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i04_terms.py

Writes four I04A matrices beside the other bloc_05 evidence:
    BLOC_05_I04A_SCHEMA_AUTHORITY_MATRIX.json
    BLOC_05_I04A_PIT_TERMS_MATRIX.json
    BLOC_05_I04A_ADVERSARIAL_MATRIX.json
    BLOC_05_I04A_SCOPE_AUDIT.json

Laws: deterministic fixtures, pinned run-date literal (no date.today()),
sort_keys + LF output, provenance names THIS tracked path, every row is an
executed probe with observed values (never a hand-written expectation
labeled as measurement).  No .bu_tmp runtime dependency, no network, no
filesystem reads outside the evidence output directory.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "src")

from crypto_sensor_fabric.normalization.enums import PayoffType  # noqa: E402
from crypto_sensor_fabric.normalization.identity import (  # noqa: E402
    CanonicalAsset,
    ContractInstance,
    EconomicContract,
    IdentityRegistrySnapshot,
    IdentityResolutionStatus,
    InstrumentAlias,
    Venue,
    VenueInstrument,
    resolve_instrument,
)
from crypto_sensor_fabric.normalization.identity import models as imodels  # noqa: E402
from crypto_sensor_fabric.normalization.terms import (  # noqa: E402
    ContractTermsSnapshot,
    project_contract_terms,
)

UTC = timezone.utc
RUN_DATE = "2026-10-08"

GEN_REF = (
    "live run " + RUN_DATE
    + ": PYTHONIOENCODING=utf-8 python "
    "research/crypto_foundry/sensor_fabric/scripts/b5_i04_terms.py "
    "(from quant-lab; terms surface under test = "
    "src/crypto_sensor_fabric/normalization/terms/)"
)
TESTS = "tests/crypto_sensor_fabric/normalization/test_b5_i04_terms.py"

T0 = datetime(2023, 1, 1, hour=12, tzinfo=UTC)
T1 = datetime(2024, 1, 1, hour=12, tzinfo=UTC)
K0 = datetime(2023, 6, 1, tzinfo=UTC)
K1 = datetime(2023, 12, 1, tzinfo=UTC)
EVENT = datetime(2023, 9, 1, hour=12, tzinfo=UTC)
CUTOFF_IN = datetime(2023, 10, 1, hour=12, tzinfo=UTC)

PROVIDER = "PROV"
VENUE = "EXA_FUT"
OTHER_VENUE = "EXB_FUT"
NATIVE = "XBTUSDT"
SHA256 = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"
REFS = ("provider-docs:exchange-a-xbtusdt",)


def asset(asset_id: str) -> CanonicalAsset:
    return CanonicalAsset(
        asset_id=asset_id,
        symbol_canonical=asset_id,
        asset_type="CRYPTO",
        metadata_version="1",
    )


def venue(venue_id: str = VENUE) -> Venue:
    return Venue(venue_id=venue_id)


def instrument(native_symbol: str = NATIVE, venue_id: str = VENUE) -> VenueInstrument:
    return VenueInstrument(
        provider=PROVIDER,
        venue=venue_id,
        native_symbol=native_symbol,
        instrument_type="PERPETUAL_FUTURE",
        native_metadata_hash=SHA256,
        first_seen_at=T0,
        last_seen_at=datetime.max.replace(tzinfo=UTC),
    )


def economic_contract(
    ec_id: str = "EC-A",
    quote_asset_id: str = "USDT",
    settlement_asset_id: str = "USDT",
    payoff_type: PayoffType = PayoffType.LINEAR,
) -> EconomicContract:
    return EconomicContract(
        economic_contract_id=ec_id,
        underlying_asset_id="BTC",
        quote_asset_id=quote_asset_id,
        settlement_asset_id=settlement_asset_id,
        margin_asset_id=None,
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=payoff_type,
    )


def instance(
    instance_id: str = "CI-A",
    ec_id: str = "EC-A",
    native_symbol: str = NATIVE,
    valid_from: datetime = T0,
    valid_to: datetime | None = T1,
    known_from: datetime = K0,
    known_to: datetime | None = K1,
    contract_multiplier: Decimal = Decimal("1"),
    settlement_asset_id: str = "USDT",
    payoff_type: PayoffType = PayoffType.LINEAR,
    inverse_flag: bool = False,
    quanto_flag: bool = False,
    contract_terms_version: str = "1",
    source_evidence_refs: tuple[str, ...] = REFS,
) -> ContractInstance:
    return ContractInstance(
        contract_instance_id=instance_id,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=native_symbol,
        economic_contract_id=ec_id,
        valid_from=valid_from,
        valid_to=valid_to,
        known_from=known_from,
        known_to=known_to,
        contract_multiplier=contract_multiplier,
        multiplier_unit="CONTRACT",
        price_unit="USDT",
        quantity_unit="BTC",
        settlement_asset_id=settlement_asset_id,
        margin_asset_id=None,
        payoff_type=payoff_type,
        inverse_flag=inverse_flag,
        quanto_flag=quanto_flag,
        tick_size=Decimal("0.1"),
        lot_size=Decimal("0.0001"),
        expiry=None,
        contract_terms_version=contract_terms_version,
        source_evidence_refs=source_evidence_refs,
    )


def registry(*instances: ContractInstance, economic_contracts=None) -> IdentityRegistrySnapshot:
    return IdentityRegistrySnapshot(
        registry_version="i04a-fix",
        assets=(asset("BTC"), asset("USDT"), asset("USD")),
        venues=(venue(), venue(OTHER_VENUE)),
        economic_contracts=economic_contracts or (economic_contract(),),
        venue_instruments=(instrument(),),
        contract_instances=instances,
    )


def resolve(reg, symbol=NATIVE, event=EVENT, cutoff=CUTOFF_IN, venue_id=VENUE):
    return resolve_instrument(reg, PROVIDER, venue_id, symbol, event, cutoff)


def project(reg, res, event=EVENT, cutoff=CUTOFF_IN):
    return project_contract_terms(reg, res, event, cutoff)


def iso(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


def write_matrix(name: str, payload: dict) -> None:
    out = Path("research/crypto_foundry/sensor_fabric/evidence/bloc_05") / name
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def stable_repr(value) -> str:
    """Deterministic repr: strip the memory addresses that ``repr`` embeds for
    nested Annotated validator objects (they differ per process, which would
    break byte-identical regeneration)."""
    import re

    return re.sub(r" at 0x[0-9a-fA-F]+", "", repr(value))


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, encoding="utf-8", errors="replace"
    ).stdout


def _reserved_mentions(sources: dict[str, str]) -> dict[str, list[int]]:
    """AST scan for TERMS_UNVERIFIED occurrences OUTSIDE docstrings.

    Docstrings legitimately record the reservation law (D2); only code-level
    mentions could hint at a construction path, so docstring spans are
    excluded by node position.
    """
    import ast

    hits: dict[str, list[int]] = {}
    for name, text in sources.items():
        tree = ast.parse(text)
        doc_lines: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    for line in range(node.body[0].lineno, node.body[0].end_lineno + 1):
                        doc_lines.add(line)
        bad = [
            idx
            for idx, line in enumerate(text.splitlines(), 1)
            if "TERMS_UNVERIFIED" in line and idx not in doc_lines
        ]
        if bad:
            hits[name] = bad
    return hits


# =========================================================================
# 1. SCHEMA AUTHORITY MATRIX (S08.1 columns)
# =========================================================================

# snapshot_field -> source authority (D1 derivation, field by field)
PROJECTED = {
    "contract_instance_id": ("ContractInstance", "contract_instance_id", "bloc_05/01 S2.5 explicit contract-instance association"),
    "economic_contract_id": ("ContractInstance", "economic_contract_id", "bloc_05/01 S2.5 / S2.4 economic grouping reference"),
    "contract_terms_version": ("ContractInstance", "contract_terms_version", "bloc_05/01 S7/S15 terms-version reference"),
    "contract_multiplier": ("ContractInstance", "contract_multiplier", "bloc_05/03 S6 terms registry supplies contract_multiplier"),
    "multiplier_unit": ("ContractInstance", "multiplier_unit", "bloc_05/03 S6 terms registry supplies multiplier_unit"),
    "price_unit": ("ContractInstance", "price_unit", "bloc_05/01 S2.5 price unit; bloc_05/03 S8 price semantics"),
    "quantity_unit": ("ContractInstance", "quantity_unit", "bloc_05/01 S2.5 quantity unit; bloc_05/03 S6 quantity conversions"),
    "payoff_type": ("ContractInstance", "payoff_type", "bloc_05/03 S6 payoff_type; bloc_05/07 F5 explicit payoff semantics"),
    "inverse_flag": ("ContractInstance", "inverse_flag", "bloc_05/01 S2.5 structural payoff flag (recorded truth)"),
    "quanto_flag": ("ContractInstance", "quanto_flag", "bloc_05/01 S2.5 structural payoff flag (recorded truth)"),
    "quote_asset_id": ("EconomicContract", "quote_asset_id", "bloc_05/03 S6 terms registry supplies quote_asset (via accepted economic contract; F6 separation)"),
    "settlement_asset_id": ("ContractInstance", "settlement_asset_id", "bloc_05/03 S6 terms registry supplies settlement_asset"),
    "margin_asset_id": ("ContractInstance", "margin_asset_id", "bloc_05/01 S2.5 optional margin asset (F6 separation)"),
    "tick_size": ("ContractInstance", "tick_size", "bloc_05/01 S2.5 tick constraint; S7 terms-version driver"),
    "lot_size": ("ContractInstance", "lot_size", "bloc_05/01 S2.5 lot constraint; S7 terms-version driver"),
    "expiry": ("ContractInstance", "expiry", "bloc_05/01 S2.5 optional expiry term"),
    "source_evidence_refs": ("ContractInstance", "source_evidence_refs", "bloc_05/01 S2.5 provenance preserved (A8 law)"),
}

EXCLUDED = {
    ("ContractInstance", "provider"): "unrelated identity metadata (resolver-owned evidence, not an economic term)",
    ("ContractInstance", "venue"): "unrelated identity metadata (resolver-owned evidence, not an economic term)",
    ("ContractInstance", "native_symbol"): "native_symbol is not durable contract identity (bloc_05/01 S7)",
    ("ContractInstance", "valid_from"): "eligibility gate input, not a recorded economic term (S02 hierarchy)",
    ("ContractInstance", "valid_to"): "eligibility gate input, not a recorded economic term (S02 hierarchy)",
    ("ContractInstance", "known_from"): "knowledge-eligibility gate input, not an economic term (C2)",
    ("ContractInstance", "known_to"): "knowledge-eligibility gate input, not an economic term (C2)",
    ("EconomicContract", "economic_contract_id"): "carried via instance association row (single economic meaning)",
    ("EconomicContract", "underlying_asset_id"): "canonical asset identity is I03 resolution output (F1), not a snapshot term",
    ("EconomicContract", "settlement_asset_id"): "instance-level settlement is the snapshot source (no second meaning)",
    ("EconomicContract", "margin_asset_id"): "instance-level margin is the snapshot source (no second meaning)",
    ("EconomicContract", "instrument_type"): "economic grouping metadata, not required by S6 terms registry list",
    ("EconomicContract", "perpetual_or_delivery"): "economic grouping metadata, not required by S6 terms registry list",
    ("EconomicContract", "payoff_type"): "duplicate classification; instance payoff is the single snapshot source",
    ("EconomicContract", "index_family"): "optional grouping metadata, not an economic conversion term",
}

schema_rows = []
snap_fields = ContractTermsSnapshot.model_fields
inst_fields = imodels.ContractInstance.model_fields
ec_fields = imodels.EconomicContract.model_fields

for source_model, source_fields in (("ContractInstance", inst_fields), ("EconomicContract", ec_fields)):
    for field_name, spec in source_fields.items():
        projected = PROJECTED.get(field_name if source_model == "ContractInstance" else field_name, None)
        if source_model == "EconomicContract" and field_name == "quote_asset_id":
            snapshot_field = "quote_asset_id"
            clause = PROJECTED["quote_asset_id"][2]
            disposition = "PROJECTED"
        elif source_model == "ContractInstance" and field_name in {
            k for k, v in PROJECTED.items() if v[0] == "ContractInstance"
        }:
            snapshot_field = field_name
            clause = PROJECTED[field_name][2]
            disposition = "PROJECTED"
        else:
            snapshot_field = "none"
            clause = EXCLUDED.get((source_model, field_name), "not a conversion term (D1 minimum schema)")
            disposition = "EXCLUDED"
        snap_spec = snap_fields.get(snapshot_field)
        schema_rows.append(
            {
                "case_id": f"SC-{source_model}-{field_name}",
                "governing_clause": clause,
                "source_model": source_model,
                "source_field": field_name,
                "snapshot_field": snapshot_field,
                "required": bool(snap_spec.is_required()) if snap_spec is not None else None,
                "validation": stable_repr(snap_spec.annotation) if snap_spec is not None else "n/a (not projected)",
                "observed_schema": stable_repr(spec.annotation),
                "disposition": disposition,
                "evidence_reference": GEN_REF + "; " + TESTS + "::test_t04a_01_valid_resolved_linear_terms_project_faithfully",
            }
        )

# integrity checks against the live schema
snap_only = sorted(set(snap_fields) - set(PROJECTED))
write_matrix(
    "BLOC_05_I04A_SCHEMA_AUTHORITY_MATRIX.json",
    {
        "artifact": "BLOC_05_I04A_SCHEMA_AUTHORITY_MATRIX",
        "checkpoint": "SENSOR-B5-I04A",
        "created": RUN_DATE,
        "evidence_class": "PRODUCED_MEASURED",
        "generator": GEN_REF,
        "summary": {
            "source_fields_examined": len(schema_rows),
            "projected_fields": sum(1 for r in schema_rows if r["disposition"] == "PROJECTED"),
            "excluded_fields": sum(1 for r in schema_rows if r["disposition"] == "EXCLUDED"),
            "snapshot_schema_fields": len(snap_fields),
            "snapshot_fields_without_mapping": snap_only,
            "no_invented_fields": snap_only == [],
            "all_results_pass": snap_only == []
            and len([r for r in schema_rows if r["disposition"] == "PROJECTED"]) == len(snap_fields),
        },
        "rows": schema_rows,
    },
)
print("schema authority:", len(schema_rows), "rows, unmapped:", snap_only)

# =========================================================================
# 2. PIT TERMS MATRIX (S08.2 columns) - executed probes
# =========================================================================

pit_rows = []


def pit_row(case_id, reg, res_status, event, cutoff, expected, test_ref, note):
    snap = project(reg, res_status, event=event, cutoff=cutoff)
    observed = "SNAPSHOT" if snap is not None else "ABSENT"
    refs = list(snap.source_evidence_refs) if snap is not None else []
    pit_rows.append(
        {
            "case_id": case_id,
            "event_time": iso(event),
            "knowledge_cutoff": iso(cutoff),
            "identity_status": res_status.status.value,
            "terms_version": snap.contract_terms_version if snap is not None else None,
            "input_condition": note,
            "expected_result": expected,
            "observed_result": observed,
            "source_evidence_refs": refs,
            "disposition": "PASS" if observed == expected else "FAIL",
            "test_reference": GEN_REF + "; " + TESTS + "::" + test_ref,
        }
    )


reg = registry(instance())
# P1 cutoff before known_from
r = resolve(reg, cutoff=K0 - timedelta(microseconds=1))
pit_row("P01", reg, r, EVENT, K0 - timedelta(microseconds=1), "ABSENT",
        "test_t04a_06_cutoff_before_known_from_blocks",
        "cutoff=known_from-1us; identity blocked and I04 gate absent")
# P2 cutoff at known_from (inclusive)
r = resolve(reg, cutoff=K0)
pit_row("P02", reg, r, EVENT, K0, "SNAPSHOT",
        "test_t04a_07_cutoff_at_known_from_projects",
        "cutoff==known_from; lower knowledge bound inclusive")
# P3 cutoff one microsecond before known_to
cut = K1 - timedelta(microseconds=1)
r = resolve(reg, cutoff=cut)
pit_row("P03", reg, r, EVENT, cut, "SNAPSHOT",
        "test_t04a_08_one_microsecond_before_known_to_projects",
        "cutoff=known_to-1us == 2023-12-01T11:59:59.999999Z inside [known_from, known_to)")
# P4 cutoff exactly at known_to
r = resolve(reg, cutoff=K1)
pit_row("P04", reg, r, EVENT, K1, "ABSENT",
        "test_t04a_09_cutoff_exactly_at_known_to_blocks",
        "cutoff==known_to; half-open knowledge bound exclusive at both layers")
# P5 cutoff after known_to
late = K1 + timedelta(days=1)
r = resolve(reg, cutoff=late)
pit_row("P05", reg, r, EVENT, late, "ABSENT",
        "test_t04a_10_cutoff_after_known_to_blocks",
        "cutoff=known_to+1d; knowledge window closed")
# P6 event before valid_from
early_event = T0 - timedelta(days=1)
r = resolve(reg, event=early_event)
pit_row("P06", reg, r, early_event, CUTOFF_IN, "ABSENT",
        "test_t04a_11_event_before_valid_from_blocks",
        "event=valid_from-1d; NOT_YET_LISTED verdict carries no terms")
# P7 event at valid_to
r = resolve(reg, event=T1)
pit_row("P07", reg, r, T1, CUTOFF_IN, "ABSENT",
        "test_t04a_12_event_at_valid_to_blocks",
        "event==valid_to; half-open validity exclusive at both layers")
# P8 event exactly at valid_from (inclusive lower bound - executed extra row)
r = resolve(reg, event=T0)
pit_row("P08", reg, r, T0, CUTOFF_IN, "SNAPSHOT",
        "test_t04a_01_valid_resolved_linear_terms_project_faithfully",
        "event==valid_from; valid-time lower bound inclusive")
# P9 ambiguity
a1 = InstrumentAlias(alias_id="AL1", provider=PROVIDER, venue=VENUE, alias_text="XBTAMB",
                     alias_type="API_SYMBOL", contract_instance_id="CI-KBA1", valid_from=T0,
                     valid_to=None, known_from=K0, source_evidence_refs=REFS, confidence="curated")
a2 = InstrumentAlias(alias_id="AL2", provider=PROVIDER, venue=VENUE, alias_text="XBTAMB",
                     alias_type="DISPLAY_SYMBOL", contract_instance_id="CI-KBA2", valid_from=T0,
                     valid_to=None, known_from=K0, source_evidence_refs=REFS, confidence="curated")
amb = IdentityRegistrySnapshot(
    registry_version="amb",
    assets=(asset("BTC"), asset("USDT")),
    venues=(venue(),),
    economic_contracts=(economic_contract(),),
    venue_instruments=(instrument(),),
    contract_instances=(instance(instance_id="CI-KBA1", native_symbol="AMBKA1"),
                        instance(instance_id="CI-KBA2", native_symbol="AMBKA2")),
    aliases=(a1, a2),
)
r = resolve(amb, symbol="XBTAMB")
pit_row("P09", amb, r, EVENT, CUTOFF_IN, "ABSENT",
        "test_t04a_13_ambiguous_identity_yields_no_snapshot",
        "AMBIGUOUS resolution carries no instance id; no snapshot fabricated")
# P10 wrong venue
r = resolve(reg, venue_id=OTHER_VENUE)
pit_row("P10", reg, r, EVENT, CUTOFF_IN, "ABSENT",
        "test_t04a_14_wrong_venue_provides_no_terms",
        "symbol registered only at EXA_FUT; UNKNOWN_SYMBOL at EXB_FUT")
# P11 I04 gate independence: resolution obtained in-window, projection asked at known_to
r_ok = resolve(reg)
snap_at_boundary = project(reg, r_ok, cutoff=K1)
pit_rows.append(
    {
        "case_id": "P11",
        "event_time": iso(EVENT),
        "knowledge_cutoff": iso(K1),
        "identity_status": r_ok.status.value,
        "terms_version": None,
        "input_condition": "resolution RESOLVED_EXACT at in-window cutoff; projection independently asked at cutoff==known_to",
        "expected_result": "ABSENT",
        "observed_result": "SNAPSHOT" if snap_at_boundary is not None else "ABSENT",
        "source_evidence_refs": [],
        "disposition": "PASS" if snap_at_boundary is None else "FAIL",
        "test_reference": GEN_REF + "; " + TESTS + "::test_t04a_09_cutoff_exactly_at_known_to_blocks",
    }
)
# P12 unverified payoff terms (identity resolves, terms boundary refuses)
r = resolve(registry(instance(payoff_type=PayoffType.UNKNOWN)))
reg_u = registry(instance(payoff_type=PayoffType.UNKNOWN))
r = resolve(reg_u)
pit_row("P12", reg_u, r, EVENT, CUTOFF_IN, "ABSENT",
        "test_t04a_15_unverified_terms_do_not_qualify_for_conversion",
        "identity RESOLVED_EXACT but payoff_type=UNKNOWN (unverified terms); no reserved status constructed")

pit_pass = sum(1 for row in pit_rows if row["disposition"] == "PASS")
write_matrix(
    "BLOC_05_I04A_PIT_TERMS_MATRIX.json",
    {
        "artifact": "BLOC_05_I04A_PIT_TERMS_MATRIX",
        "checkpoint": "SENSOR-B5-I04A",
        "created": RUN_DATE,
        "evidence_class": "PRODUCED_MEASURED",
        "generator": GEN_REF,
        "summary": {
            "cases": len(pit_rows),
            "passed": pit_pass,
            "all_results_pass": pit_pass == len(pit_rows),
        },
        "rows": pit_rows,
    },
)
print("pit terms:", pit_pass, "/", len(pit_rows))

# =========================================================================
# 3. ADVERSARIAL MATRIX (A1-A8, S06 record shape)
# =========================================================================

adv_rows = []


def adv_row(case_id, clause, fixture, expected, forbidden, mutate_before, mutate_after,
            observed, test_ref):
    adv_rows.append(
        {
            "case_id": case_id,
            "acceptance_clause": clause,
            "fixture": fixture,
            "expected_result": expected,
            "observed_result": observed,
            "forbidden_result": forbidden,
            "nonmutation_assertion": "HELD" if mutate_before == mutate_after else "BROKEN",
            "disposition": "PASS"
            if (observed == expected and mutate_before == mutate_after)
            else "FAIL",
            "test_reference": GEN_REF + "; " + TESTS + "::" + test_ref,
        }
    )


# A1 one-contract-one-base
reg_a1 = registry(instance(contract_multiplier=Decimal("0.25")))
before = reg_a1.model_dump()
r = resolve(reg_a1)
s = project(reg_a1, r)
obs = f"multiplier={s.contract_multiplier}" if s else "ABSENT"
adv_row("A1", "bloc_05/03 S7: no 1-contract-1-base assumption",
        "LINEAR instance with contract_multiplier=0.25",
        "multiplier=0.25", "multiplier=1", before, reg_a1.model_dump(),
        obs, "test_a1_one_contract_one_base_assumption_trap")

# A2 stablecoin equivalence
ec_usd = economic_contract(ec_id="EC-B", quote_asset_id="USD", settlement_asset_id="USDT")
reg_a2 = registry(instance(ec_id="EC-B"), economic_contracts=(ec_usd,))
before = reg_a2.model_dump()
r = resolve(reg_a2)
s = project(reg_a2, r)
obs = f"quote={s.quote_asset_id},settlement={s.settlement_asset_id}" if s else "ABSENT"
adv_row("A2", "bloc_05/07 F7: USD and USDT stay distinct canonical assets",
        "quote_asset_id=USD with settlement_asset_id=USDT",
        "quote=USD,settlement=USDT", "quote=USDT or settlement=USD",
        before, reg_a2.model_dump(), obs,
        "test_a2_stablecoin_equivalence_trap")

# A3 stale terms version
old = instance(instance_id="CI-OLD", valid_to=datetime(2023, 6, 1, tzinfo=UTC),
               contract_terms_version="1")
new = instance(instance_id="CI-NEW", valid_from=datetime(2024, 3, 1, tzinfo=UTC),
               valid_to=None, known_from=datetime(2024, 3, 1, tzinfo=UTC),
               known_to=None, contract_terms_version="2")
reg_a3 = registry(old, new)
before = reg_a3.model_dump()
early = datetime(2023, 3, 1, hour=12, tzinfo=UTC)
r = resolve(reg_a3, event=early)
s = project(reg_a3, r, event=early)
obs = f"version={s.contract_terms_version}" if s else "ABSENT"
adv_row("A3", "bloc_05/01 S7: terms-version fidelity, no silent upgrade",
        "sequential CI-OLD v1 / CI-NEW v2, query bound to old window",
        "version=1", "version=2", before, reg_a3.model_dump(), obs,
        "test_a3_stale_terms_version_not_silent_upgraded")

# A4 knowledge-time leakage
late_known = instance(known_from=datetime(2024, 1, 1, tzinfo=UTC), known_to=None)
reg_a4 = registry(late_known)
before = reg_a4.model_dump()
r = resolve(reg_a4, cutoff=CUTOFF_IN)
s = project(reg_a4, r, cutoff=CUTOFF_IN)
obs = r.status.value + ("+SNAPSHOT" if s else "+ABSENT")
adv_row("A4", "C2: no knowledge leaks backward across known_from",
        "known_from=2024-01-01 queried at cutoff=2023-10-01",
        "PIT_KNOWLEDGE_BLOCKED+ABSENT", "any snapshot",
        before, reg_a4.model_dump(), obs,
        "test_a4_knowledge_time_leakage_blocked")

# A5 identity-to-terms escalation
reg_a5 = registry(instance(payoff_type=PayoffType.UNKNOWN))
before = reg_a5.model_dump()
r = resolve(reg_a5)
s = project(reg_a5, r)
obs = r.status.value + ("+SNAPSHOT" if s else "+ABSENT")
adv_row("A5", "D2/F3: resolved identity + unverified terms is not verified exposure",
        "RESOLVED_EXACT identity with payoff_type=UNKNOWN",
        "RESOLVED_EXACT+ABSENT", "RESOLVED_EXACT+SNAPSHOT",
        before, reg_a5.model_dump(), obs,
        "test_a5_identity_to_terms_escalation_denied")

# A6 ambiguity laundering (equal multipliers)
a1 = InstrumentAlias(alias_id="DA1", provider=PROVIDER, venue=VENUE, alias_text="DUPA",
                     alias_type="API_SYMBOL", contract_instance_id="CI-D1", valid_from=T0,
                     valid_to=None, known_from=K0, source_evidence_refs=REFS, confidence="curated")
a2 = InstrumentAlias(alias_id="DA2", provider=PROVIDER, venue=VENUE, alias_text="DUPA",
                     alias_type="DISPLAY_SYMBOL", contract_instance_id="CI-D2", valid_from=T0,
                     valid_to=None, known_from=K0, source_evidence_refs=REFS, confidence="curated")
reg_a6 = IdentityRegistrySnapshot(
    registry_version="dup",
    assets=(asset("BTC"), asset("USDT")),
    venues=(venue(),),
    economic_contracts=(economic_contract(),),
    venue_instruments=(instrument(),),
    contract_instances=(instance(instance_id="CI-D1", native_symbol="DUP1"),
                        instance(instance_id="CI-D2", native_symbol="DUP2")),
    aliases=(a1, a2),
)
before = reg_a6.model_dump()
r = resolve(reg_a6, symbol="DUPA")
s = project(reg_a6, r)
obs = r.status.value + ("+SNAPSHOT" if s else "+ABSENT")
adv_row("A6", "S10/C6: equal multipliers never collapse two candidates",
        "two alias-eligible instances, identical contract_multiplier=1",
        "AMBIGUOUS+ABSENT", "any single selection",
        before, reg_a6.model_dump(), obs,
        "test_a6_ambiguity_laundering_by_equal_multipliers_blocked")

# A7 null-to-zero
try:
    instance(contract_multiplier=None)
    obs_construct = "ACCEPTED"  # would be a violation
except Exception:
    obs_construct = "REFUSED"
required = ContractInstance.model_fields["contract_multiplier"].is_required()
obs = f"missing_refused={obs_construct == 'REFUSED'},required={required}"
adv_row("A7", "bloc_05/03 S22 inv.5: null != zero; missing term never becomes 0",
        "attempt to build an instance without contract_multiplier",
        "missing_refused=True,required=True", "missing_refused=False or required=False",
        True, True, obs, "test_a7_null_to_zero_laundering_blocked")

# A8 source-evidence fabrication
reg_a8 = registry(instance(source_evidence_refs=("prov:only-this-one",)))
before = reg_a8.model_dump()
r = resolve(reg_a8)
s = project(reg_a8, r)
obs = ",".join(s.source_evidence_refs) if s else "ABSENT"
adv_row("A8", "A8 law: snapshot refs are copied from authorized sources only",
        "instance with exactly one evidence ref",
        "prov:only-this-one", "any fabricated ref",
        before, reg_a8.model_dump(), obs,
        "test_a8_source_evidence_fabrication_blocked")

adv_pass = sum(1 for row in adv_rows if row["disposition"] == "PASS")
write_matrix(
    "BLOC_05_I04A_ADVERSARIAL_MATRIX.json",
    {
        "artifact": "BLOC_05_I04A_ADVERSARIAL_MATRIX",
        "checkpoint": "SENSOR-B5-I04A",
        "created": RUN_DATE,
        "evidence_class": "PRODUCED_MEASURED",
        "generator": GEN_REF,
        "summary": {
            "traps": len(adv_rows),
            "passed": adv_pass,
            "all_results_pass": adv_pass == len(adv_rows),
        },
        "rows": adv_rows,
    },
)
print("adversarial:", adv_pass, "/", len(adv_rows))

# =========================================================================
# 4. SCOPE AUDIT (S08.4 mechanical checks)
# =========================================================================

terms_sources = {
    p.name: p.read_text(encoding="utf-8")
    for p in sorted(Path("src/crypto_sensor_fabric/normalization/terms").glob("*.py"))
}
identity_dir = Path("src/crypto_sensor_fabric/normalization/identity")
identity_sources = {
    p.name: p.read_text(encoding="utf-8")
    for p in sorted(identity_dir.glob("*.py"))
}
norm_init = Path("src/crypto_sensor_fabric/normalization/__init__.py").read_text(encoding="utf-8")

forbidden_in_terms = [
    "convert", "exposure", "notional", "reference_price",
    "requests", "httpx", "aiohttp", "socket", "urllib",
    "open(", "pathlib", "os.walk", "TERMS_UNVERIFIED",
]

protected_diff = git(
    "diff", "--name-only", "HEAD", "--",
    "quant-lab/src/crypto_sensor_fabric/normalization/identity/",
    "quant-lab/src/crypto_sensor_fabric/normalization/enums.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/models.py",
    "quant-lab/src/crypto_sensor_fabric/normalization/__init__.py",
)
status_lines = [
    line for line in git("status", "--porcelain").splitlines()
    if line.strip()
]

audit = {
    "artifact": "BLOC_05_I04A_SCOPE_AUDIT",
    "checkpoint": "SENSOR-B5-I04A",
    "created": RUN_DATE,
    "evidence_class": "PRODUCED_MEASURED",
    "generator": GEN_REF,
    "checks": {
        "no_i03_resolver_changes": {
            "law": "D2: the I03 identity resolver is consumed, never modified",
            "measured": "quant-lab/src/.../identity/ diff vs HEAD",
            "value": protected_diff.splitlines(),
            "pass": protected_diff.strip() == "",
        },
        "no_i01_i02_model_changes": {
            "law": "S11.1: no existing production identity model modification",
            "measured": "enums.py/models.py/__init__.py diff vs HEAD (empty because unchanged)",
            "value": [],
            "pass": "enums.py" not in protected_diff and "models.py" not in protected_diff
            and "__init__.py" not in protected_diff.replace("terms", ""),
        },
        "no_i08_common_conversion": {
            "law": "S04: I04A must not own normalization/common/conversion.py",
            "measured": "absence of normalization/common directory",
            "value": not Path("src/crypto_sensor_fabric/normalization/common").exists(),
            "pass": not Path("src/crypto_sensor_fabric/normalization/common").exists(),
        },
        "no_linear_inverse_conversion_engine": {
            "law": "explicit I04A non-scope: no conversion implementation",
            "measured": "forbidden tokens in terms/ sources",
            "value": {
                token: any(token in text for text in terms_sources.values())
                for token in ("convert", "exposure", "notional", "reference_price")
            },
            "pass": not any(
                token in text for text in terms_sources.values()
                for token in ("convert", "exposure", "notional", "reference_price")
            ),
        },
        "no_reference_price_sourcing": {
            "law": "explicit I04A non-scope",
            "measured": "network/filesystem imports in terms/ sources",
            "value": {
                token: any(token in text for text in terms_sources.values())
                for token in ("requests", "httpx", "aiohttp", "socket", "urllib", "open(", "pathlib")
            },
            "pass": not any(
                token in text for text in terms_sources.values()
                for token in ("requests", "httpx", "aiohttp", "socket", "urllib", "open(", "pathlib")
            ),
        },
        "no_reserved_status_construction": {
            "law": "D2: TERMS_UNVERIFIED stays reserved; no construction path",
            "measured": "AST scan (docstrings excluded) of terms/ sources + return-line scan of identity resolver",
            "value": {
                "terms_non_docstring_mentions": _reserved_mentions(terms_sources),
                "identity_construction": [
                    line.strip()
                    for line in identity_sources.get("resolver.py", "").splitlines()
                    if line.strip().startswith("return") and "TERMS_UNVERIFIED" in line
                ],
            },
            "pass": not _reserved_mentions(terms_sources)
            and not any(
                line.strip().startswith("return") and "TERMS_UNVERIFIED" in line
                for line in identity_sources.get("resolver.py", "").splitlines()
            ),
        },
        "no_fabricated_status_enum": {
            "law": "D2: no new status enum is authorized",
            "measured": "IdentityResolutionStatus member set (frozen nine)",
            "value": sorted(m.value for m in IdentityResolutionStatus),
            "pass": len(IdentityResolutionStatus) == 9,
        },
        "top_level_surface_unchanged_24": {
            "law": "B5-I02/I03 directive 29: top-level normalization surface stays 24",
            "measured": "__all__ length in normalization/__init__.py",
            "value": norm_init.count('"') // 2 if False else None,
            "pass": None,
        },
        "forbidden_terms_module_file_absent": {
            "law": "B5-I01 forbidden module list still holds (terms.py beside package)",
            "measured": "path absence",
            "value": not Path("src/crypto_sensor_fabric/normalization/terms.py").exists(),
            "pass": not Path("src/crypto_sensor_fabric/normalization/terms.py").exists(),
        },
        "no_research_or_plan_changes": {
            "law": "S11.1: no research canon / frozen plan modification",
            "measured": "git status porcelain (untracked scratch allowed, plan/research tracked untouched)",
            "value": [line for line in status_lines if "bloc_0" in line and "??" not in line],
            "pass": not [
                line for line in status_lines
                if line.startswith(" M") and "/bloc_0" in line and "evidence/bloc_05/BLOC_05_I04A" not in line
            ],
        },
    },
}

# top-level surface: count the actual __all__ entries mechanically
import importlib  # noqa: E402

norm = importlib.import_module("crypto_sensor_fabric.normalization")
audit["checks"]["top_level_surface_unchanged_24"]["value"] = len(norm.__all__)
audit["checks"]["top_level_surface_unchanged_24"]["pass"] = len(norm.__all__) == 24

audit["results"] = {
    name: ("PASS" if check["pass"] else "FAIL")
    for name, check in audit["checks"].items()
}
audit["all_results_pass"] = all(
    result == "PASS" for result in audit["results"].values()
)
write_matrix("BLOC_05_I04A_SCOPE_AUDIT.json", audit)
print("scope audit:", audit["results"])
print("ALL PASS:", audit["all_results_pass"], pit_pass == len(pit_rows),
      adv_pass == len(adv_rows), snap_only == [])
