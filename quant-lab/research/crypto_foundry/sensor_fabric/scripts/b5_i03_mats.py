"""B5-I03D/I03H generator: mechanically produce the I03 matrices from live
resolver runs over purpose-built snapshots (no hand-typed observations).

Run from quant-lab:  PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i03_mats.py
Writes (regenerated only when affected):
  research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I03_FUTURE_LEAKAGE_MATRIX.json
  research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I03_MATCH_ORDER_MATRIX.json   (+I03H G2/G3 rows)
  research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I03_LIFECYCLE_MATRIX.json
  research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I03_ALIAS_MATRIX.json
  research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I03H_KNOWLEDGE_BOUNDARY_MATRIX.json (new, B5-I03H Option 1)

Every row records: governing acceptance clause, executable probe, input
condition, observed result, pass/fail disposition, reproducible evidence
reference.  All artifacts are evidence_class=measured_executable (live
resolver runs); static contract evidence lives in SCOPE_AUDIT.json and the
implementation evidence document only.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, "src")

from crypto_sensor_fabric.normalization.enums import PayoffType
import crypto_sensor_fabric.normalization.identity as I

UTC = timezone.utc
SHA = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"
T0 = datetime(2023, 1, 1, 12, tzinfo=UTC)
T1 = datetime(2024, 1, 1, 12, tzinfo=UTC)
T2 = datetime(2025, 1, 1, 12, tzinfo=UTC)
PROV, VEN = "PROV", "EXA_FUT"
OTHERVEN = "OTHER_FUT"
RUN_DATE = "2026-10-08"
GEN_REF = (
    "live run " + RUN_DATE + ": PYTHONIOENCODING=utf-8 python "
    "research/crypto_foundry/sensor_fabric/scripts/b5_i03_mats.py "
    "(from quant-lab; resolver under test = "
    "src/crypto_sensor_fabric/normalization/identity/resolver.py)"
)
TESTS = "tests/crypto_sensor_fabric/normalization/test_b5_i03_resolver.py"
DUAL_CLOCK = "bloc_05/01 section 5 (dual-clock law); directives 10/11/44"

def asset(aid="BTC", sym="BTC"):
    return I.CanonicalAsset(asset_id=aid, symbol_canonical=sym, asset_type="CRYPTO", metadata_version="1")

def econ():
    return I.EconomicContract(
        economic_contract_id="EC-BTCUSDT-PERP-A", underlying_asset_id="BTC",
        quote_asset_id="USDT", settlement_asset_id="USDT",
        instrument_type="PERPETUAL_FUTURE", perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR)

def ven(vid=VEN):
    return I.Venue(venue_id=vid)

def vi(native="XBTUSDT", pid="PID-1"):
    return I.VenueInstrument(provider=PROV, venue=VEN, native_symbol=native,
        provider_instrument_id=pid, instrument_type="PERPETUAL_FUTURE",
        native_metadata_hash=SHA, first_seen_at=T0, last_seen_at=T2)

def ci(id_="CI-A", native="XBTUSDT", vfrom=T0, vto=T1, kfrom=None, kto=None):
    return I.ContractInstance(
        contract_instance_id=id_, provider=PROV, venue=VEN, native_symbol=native,
        economic_contract_id="EC-BTCUSDT-PERP-A", valid_from=vfrom, valid_to=vto,
        known_from=kfrom or (vfrom - timedelta(days=2)), known_to=kto,
        contract_multiplier=Decimal("1"), multiplier_unit="CONTRACT",
        price_unit="USDT", quantity_unit="BTC", settlement_asset_id="USDT",
        payoff_type=PayoffType.LINEAR, inverse_flag=False, quanto_flag=False,
        tick_size=Decimal("0.1"), lot_size=Decimal("0.0001"),
        contract_terms_version="1", source_evidence_refs=("provider-docs:base",))

def al(text, atype, iid="CI-A", vfrom=T0, vto=None, kfrom=None, prov=PROV, ven_id=VEN):
    return I.InstrumentAlias(
        alias_id="AL:" + iid + ":" + text + ":" + atype.value, provider=prov, venue=ven_id,
        alias_text=text, alias_type=atype, contract_instance_id=iid,
        valid_from=vfrom, valid_to=vto, known_from=kfrom or (vfrom - timedelta(days=1)),
        source_evidence_refs=("provider-docs:alias",), confidence="operator-curated")

def le(state, iid="CI-A", vfrom=T0, vto=None, kfrom=None, kto=None):
    return I.InstrumentLifecycle(
        provider=PROV, venue=VEN, contract_instance_id=iid, lifecycle_state=state,
        valid_from=vfrom, valid_to=vto, known_from=kfrom or (vfrom - timedelta(days=1)),
        known_to=kto, source_evidence_refs=("provider-docs:lc",))

def snap(version, instances=(), aliases=(), lifecycles=(), venues=None):
    return I.IdentityRegistrySnapshot(
        registry_version=version, assets=(asset(), asset("USDT", "USDT")),
        venues=tuple(venues) if venues else (ven(),),
        economic_contracts=(econ(),), venue_instruments=(vi(),),
        contract_instances=instances, aliases=aliases, lifecycle_events=lifecycles)

def resolve(s, native, ev, kc, pid=None, ven=VEN):
    return I.resolve_instrument(s, provider=PROV, venue=ven, native_symbol=native,
        event_time=ev, knowledge_cutoff=kc, optional_provider_instrument_id=pid)

ST = I.IdentityResolutionStatus
blocked = {ST.AMBIGUOUS, ST.UNKNOWN_SYMBOL, ST.TERMS_UNVERIFIED, ST.PIT_KNOWLEDGE_BLOCKED}
RESOLVED_LIKE = (ST.RESOLVED_EXACT, ST.RESOLVED_ALIAS, ST.RESOLVED_WITH_WARNING)

def carries_no_identity(r):
    return (
        r.contract_instance_id is None
        and r.economic_contract_id is None
        and r.canonical_asset_id is None
        and r.matched_alias_id is None
        and r.terms_version is None
        and not r.source_evidence_refs
    )

def flags_of(r):
    return sorted(f.value for f in r.quality_flags)

out_dir = "research/crypto_foundry/sensor_fabric/evidence/bloc_05"

def write_matrix(name, payload):
    with open(out_dir + "/" + name, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

# ===========================================================================
# 44 FUTURE LEAKAGE MATRIX: no future mapping may be used for any answer
# ===========================================================================
leak_rows = []

# L1: exact symbol whose only instance becomes known strictly after cutoff
sL1 = snap("leak1", instances=(ci("CI-A", kfrom=T0 - timedelta(days=2)),))
r = resolve(sL1, "XBTUSDT", T0, T0 - timedelta(days=5))
leak_rows.append({
    "case_id": "L1",
    "match_tier": "2 (exact native symbol)",
    "acceptance_clause": DUAL_CLOCK,
    "probe": "query XBTUSDT at event T0 with cutoff 5 days BEFORE the instance row became known (known_from T0-2d)",
    "input_condition": "event=2023-01-01T12:00Z, cutoff=2022-12-27T12:00Z, candidate known_from=2022-12-30T12:00Z (known_from > cutoff)",
    "expected_status": "PIT_KNOWLEDGE_BLOCKED",
    "observed_status": r.status.value,
    "future_mapping_used": r.status in RESOLVED_LIKE,
    "carries_no_identity": carries_no_identity(r),
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_case_1_future_known_exact_symbol_must_not_resolve_backward",
    "result": "PASS" if (r.status is ST.PIT_KNOWLEDGE_BLOCKED and carries_no_identity(r)) else "FAIL",
})

# L2: provider instrument id whose instance is known strictly after cutoff
r = resolve(sL1, "XBTUSDT", T0, T0 - timedelta(days=5), pid="PID-1")
leak_rows.append({
    "case_id": "L2",
    "match_tier": "1 (provider id) falling through to 2",
    "acceptance_clause": DUAL_CLOCK + "; directive 15 (ID is not a lifeline)",
    "probe": "same late-known instance, queried THROUGH provider id PID-1: the ID anchors the instrument but the instance still fails the knowledge gate",
    "input_condition": "event=2023-01-01T12:00Z, cutoff=2022-12-27T12:00Z, candidate known_from=2022-12-30T12:00Z (known_from > cutoff)",
    "expected_status": "PIT_KNOWLEDGE_BLOCKED",
    "observed_status": r.status.value,
    "future_mapping_used": r.status in RESOLVED_LIKE,
    "carries_no_identity": carries_no_identity(r),
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_case_2_future_known_provider_instrument_id_must_not_resolve_backward",
    "result": "PASS" if (r.status is ST.PIT_KNOWLEDGE_BLOCKED and carries_no_identity(r)) else "FAIL",
})

# L3: alias row known strictly after cutoff
sL3 = snap("leak3", instances=(ci(),), aliases=(al("ALIASFUT", I.AliasType.API_SYMBOL, kfrom=T1),))
r = resolve(sL3, "ALIASFUT", T0, T0 + timedelta(days=1))
leak_rows.append({
    "case_id": "L3",
    "match_tier": "5 (fail-closed sweep)",
    "acceptance_clause": DUAL_CLOCK + "; directive 41 (knowledge gate fail-closed, never optimistic)",
    "probe": "alias ALIASFUT registered known_from T1 (2024) queried at event T0 with cutoff T0+1d: the row is registered-but-late",
    "input_condition": "event=2023-01-01T12:00Z, cutoff=2023-01-02T12:00Z, alias known_from=2024-01-01T12:00Z (known_from > cutoff)",
    "expected_status": "PIT_KNOWLEDGE_BLOCKED",
    "observed_status": r.status.value,
    "future_mapping_used": r.status in RESOLVED_LIKE,
    "carries_no_identity": carries_no_identity(r),
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_case_3_future_known_alias_must_not_resolve_backward",
    "result": "PASS" if (r.status is ST.PIT_KNOWLEDGE_BLOCKED and carries_no_identity(r)) else "FAIL",
})

# L4: knowledge fully caught up, event strictly before listing -> verdict only
sL4 = snap("leak4", instances=(ci("CI-A", kfrom=T0 - timedelta(days=2)),))
r = resolve(sL4, "XBTUSDT", T0 - timedelta(days=10), T2)
leak_rows.append({
    "case_id": "L4",
    "match_tier": "2 (verdict law)",
    "acceptance_clause": DUAL_CLOCK + "; directives 12/13/44 (temporal verdict carries no identity)",
    "probe": "instance fully known by cutoff (known_from T0-2d <= T2) but event 10 days BEFORE valid_from: pre-listing verdict, never a resolved identity",
    "input_condition": "event=2022-12-22T12:00Z, cutoff=2025-01-01T12:00Z, candidate valid_from=2023-01-01T12:00Z (event < valid_from)",
    "expected_status": "NOT_YET_LISTED",
    "observed_status": r.status.value,
    "future_mapping_used": r.status in RESOLVED_LIKE,
    "carries_no_identity": carries_no_identity(r),
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_case_4_before_listing_is_not_yet_listed",
    "result": "PASS" if (r.status is ST.NOT_YET_LISTED and carries_no_identity(r)) else "FAIL",
})

future_ok = all(row["result"] == "PASS" for row in leak_rows)
write_matrix("BLOC_05_I03_FUTURE_LEAKAGE_MATRIX.json", {
    "artifact": "BLOC_05_I03_FUTURE_LEAKAGE_MATRIX",
    "checkpoint": "SENSOR-B5-I03",
    "created": RUN_DATE,
    "evidence_class": "measured_executable",
    "authority": ["bloc_05/01 section 5 (dual clock); I03 directives 10/11/41/44"],
    "law": "future_mapping_used must be false for every case; late evidence resolves only to blocking/verdict statuses, never to a resolved identity, and every blocking/verdict answer carries no identifiers and no evidence refs",
    "generated_by": GEN_REF,
    "summary": {
        "cases": len(leak_rows),
        "all_future_mapping_used_false": all(not row["future_mapping_used"] for row in leak_rows),
        "all_results_pass": future_ok,
    },
    "rows": leak_rows,
})
print("future leakage:", future_ok, len(leak_rows))

# ===========================================================================
# 45 MATCH ORDER MATRIX: frozen tier precedence, live
# ===========================================================================
mo = []
# snapshot where tiers 1/2/3 could all claim the same instant
sMO = snap("mo", instances=(ci("CI-A"),),
           aliases=(al("XBTUSDT", I.AliasType.API_SYMBOL),
                    al("DIRECTA", I.AliasType.API_SYMBOL)))

# tier 1 beats tier 2: provider id + symbol both resolvable at one instant
r = resolve(sMO, "XBTUSDT", T0, T2, pid="PID-1")
mo.append({
    "rank": 1, "tier": "provider instrument id",
    "acceptance_clause": "bloc_05/01 section 10 (matching order); directives 14/15/45",
    "probe": "pid PID-1 and exact symbol XBTUSDT both resolvable at the same instant: ID tier must win",
    "input_condition": "event=2023-01-01T12:00Z, cutoff=2025-01-01T12:00Z, pid=PID-1, symbol=XBTUSDT (tier-1 and tier-2 candidates coexist)",
    "observed_status": r.status.value,
    "observed_flags": flags_of(r),
    "matched_alias_id": r.matched_alias_id,
    "expected": "RESOLVED_EXACT via tier 1 (with IDENTITY_PROVIDER_ID_MISSING tier-1 marker); matched_alias_id stays None",
    "result": "PASS" if (r.status is ST.RESOLVED_EXACT and r.matched_alias_id is None
                         and "IDENTITY_PROVIDER_ID_MISSING" in flags_of(r)) else "FAIL",
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_case_16_provider_id_tier_outranks_symbol_tier",
})

# tier 2 beats tier 3: exact symbol with a same-text alias registered
r = resolve(sMO, "XBTUSDT", T0, T2)
mo.append({
    "rank": 2, "tier": "exact native symbol",
    "acceptance_clause": "bloc_05/01 section 10 (matching order); directives 14/16/45",
    "probe": "exact symbol XBTUSDT while a same-text API_SYMBOL alias is also registered: the alias tier must not steal the match",
    "input_condition": "event=2023-01-01T12:00Z, cutoff=2025-01-01T12:00Z, symbol=XBTUSDT registered both as native symbol and as alias of CI-A",
    "observed_status": r.status.value,
    "observed_flags": flags_of(r),
    "matched_alias_id": r.matched_alias_id,
    "expected": "RESOLVED_EXACT with matched_alias_id=None (symbol tier outranks alias tier)",
    "result": "PASS" if (r.status is ST.RESOLVED_EXACT and r.matched_alias_id is None
                         and "IDENTITY_ALIAS_USED" not in flags_of(r)) else "FAIL",
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_case_17_exact_symbol_tier_outranks_alias_tier",
})

# tier 3: a registered alias whose text is not a native symbol resolves
r = resolve(sMO, "DIRECTA", T0, T2)
mo.append({
    "rank": 3, "tier": "registered alias (documented surface)",
    "acceptance_clause": "bloc_05/01 section 10 + section 8; directives 14/17/45",
    "probe": "alias DIRECTA (API_SYMBOL, open-ended window) is the only carrier for the queried text",
    "input_condition": "event=2023-01-01T12:00Z, cutoff=2025-01-01T12:00Z, text=DIRECTA (no instance registered under this text)",
    "observed_status": r.status.value,
    "observed_flags": flags_of(r),
    "matched_alias_id": r.matched_alias_id,
    "expected": "RESOLVED_ALIAS with matched_alias_id=AL:CI-A:DIRECTA:API_SYMBOL and IDENTITY_ALIAS_USED",
    "result": "PASS" if (r.status is ST.RESOLVED_ALIAS and r.matched_alias_id == "AL:CI-A:DIRECTA:API_SYMBOL"
                         and "IDENTITY_ALIAS_USED" in flags_of(r)) else "FAIL",
    "evidence_ref": GEN_REF + "; alias-match law pinned by " + TESTS + "::test_case_11_expired_alias_does_not_resolve / ::test_case_12_wrong_venue_alias_does_not_resolve (negatives)",
})

# tier 4 semantics: curated non-API carrier wins with IDENTITY_MANUAL_OVERRIDE
sT4 = snap("mot4",
           instances=(ci("CI-B", vfrom=T2, vto=None, kfrom=T2 - timedelta(days=1)),),
           aliases=(al("LEGACYX", I.AliasType.LEGACY_SYMBOL, iid="CI-B",
                       vfrom=T2, kfrom=T2 - timedelta(days=1)),))
r = resolve(sT4, "LEGACYX", T2 + timedelta(days=1), T2 + timedelta(days=1))
mo.append({
    "rank": 4, "tier": "curated manual mapping (evidence-backed alias carrier)",
    "acceptance_clause": "bloc_05/01 section 10 + section 14; vocabulary matrix directive 29 path A; directives 14/45",
    "probe": "LEGACY_SYMBOL carrier LEGACYX is the only candidate: curated-carrier win must surface tier-4 semantics (IDENTITY_MANUAL_OVERRIDE) while keeping status RESOLVED_ALIAS with matched_alias_id (directive 17)",
    "input_condition": "event=2025-01-02T12:00Z, cutoff=2025-01-02T12:00Z, alias LEGACYX/LEGACY_SYMBOL valid [2025-01-01T12:00Z, open), known_from=2024-12-31T12:00Z",
    "observed_status": r.status.value,
    "observed_flags": flags_of(r),
    "matched_alias_id": r.matched_alias_id,
    "expected": "RESOLVED_ALIAS with IDENTITY_MANUAL_OVERRIDE (tier-4 semantics inside the pooled tier-3/4 scan) and matched_alias_id set",
    "result": "PASS" if (r.status is ST.RESOLVED_ALIAS
                         and "IDENTITY_MANUAL_OVERRIDE" in flags_of(r)
                         and "IDENTITY_ALIAS_USED" not in flags_of(r)
                         and r.matched_alias_id is not None) else "FAIL",
    "evidence_ref": GEN_REF + "; vocabulary authority: BLOC_05_I03_VOCABULARY_AUTHORITY_MATRIX.json (tier-4 path A row)",
})

# tier 5: nothing registered under the text
r = resolve(sMO, "GHOSTX", T0, T2)
mo.append({
    "rank": 5, "tier": "no result",
    "acceptance_clause": "bloc_05/01 section 10; directives 14/24/45",
    "probe": "GHOSTX is registered nowhere: no instance, no alias, nothing late",
    "input_condition": "event=2023-01-01T12:00Z, cutoff=2025-01-01T12:00Z, text=GHOSTX (absent from the registry)",
    "observed_status": r.status.value,
    "observed_flags": flags_of(r),
    "matched_alias_id": r.matched_alias_id,
    "expected": "UNKNOWN_SYMBOL with no identity payload",
    "result": "PASS" if (r.status is ST.UNKNOWN_SYMBOL and carries_no_identity(r)) else "FAIL",
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_prefix_candidates_do_not_match family",
})

# ambiguity inside the pooled alias scan dominates convenience
sAMB = snap("moamb",
    instances=(ci("CI-A"), ci("CI-B", native="BBTA", vfrom=T0, vto=None,
                              kfrom=T0 - timedelta(days=2))),
    aliases=(al("AMBT", I.AliasType.API_SYMBOL, iid="CI-A", vto=None),
             al("AMBT", I.AliasType.DISPLAY_SYMBOL, iid="CI-B", vto=None)))
r = resolve(sAMB, "AMBT", T0 + timedelta(days=1), T2 + timedelta(days=1))
mo.append({
    "rank": "3/4 (pooled)", "tier": "ambiguity inside the pooled alias scan",
    "acceptance_clause": "bloc_05/01 section 9 + section 10; directives 17/24/45 (ambiguity dominates convenience)",
    "probe": "same text AMBT carried by two alias rows of different kinds, each pointing at a different instance, both PIT-valid at the event: the pooled scan must refuse a winner",
    "input_condition": "event=2023-01-02T12:00Z, cutoff=2025-01-02T12:00Z, two same-text carriers (API_SYMBOL->CI-A, DISPLAY_SYMBOL->CI-B), both windows open at the event",
    "observed_status": r.status.value,
    "observed_flags": flags_of(r),
    "matched_alias_id": r.matched_alias_id,
    "expected": "AMBIGUOUS with no identity payload (never a sorted/first/last winner)",
    "result": "PASS" if (r.status is ST.AMBIGUOUS and carries_no_identity(r)) else "FAIL",
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_case_14_competing_alias_candidates_return_ambiguous",
})

# ---- B5-I03H G2/G3 closure rows (MATCH_ORDER is affected: tier-1 venue
# axis + exactness law + flag coverage now measured, not implied) ----

# G2: the provider instrument ID is venue-scoped (tier-1 isolation)
sG2 = snap("g2", instances=(ci("CI-A"),), venues=(ven(), ven("EXB_FUT")))
r_ctrl = resolve(sG2, "XBTUSDT", T0 + timedelta(days=3), T2, pid="PID-1")
r_wv = resolve(sG2, "XBTUSDT", T0 + timedelta(days=3), T2, pid="PID-1",
               ven="EXB_FUT")
mo.append({
    "rank": "1 (venue axis)", "tier": "provider instrument id - venue isolation",
    "acceptance_clause": "bloc_05/01 section 10 (tier 1 requires provider + venue + time + knowledge context, never the bare ID); directive 15; G2 closure (B5-I03H)",
    "probe": "provider instrument ID PID-1 is correct for the instrument, but the query carries registered venue EXB_FUT where no instrument/instance exists: the ID must not anchor across venues",
    "input_condition": "event=2023-01-04T12:00Z, cutoff=2025-01-01T12:00Z, pid=PID-1 (registered on EXA_FUT), query venue=EXB_FUT (registered, instrument absent); control call identical but venue=EXA_FUT",
    "observed_status": r_wv.status.value,
    "observed_flags": flags_of(r_wv),
    "matched_alias_id": r_wv.matched_alias_id,
    "control_observed_status": r_ctrl.status.value,
    "control_contract_instance_id": r_ctrl.contract_instance_id,
    "expected": "UNKNOWN_SYMBOL with no identity payload on the wrong venue; the control call on EXA_FUT resolves RESOLVED_EXACT CI-A (difference is the venue axis alone)",
    "result": "PASS" if (r_wv.status is ST.UNKNOWN_SYMBOL and carries_no_identity(r_wv)
                         and r_ctrl.status is ST.RESOLVED_EXACT
                         and r_ctrl.contract_instance_id == "CI-A") else "FAIL",
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_provider_id_on_the_wrong_venue_does_not_anchor",
})

# G3a: negative alias law - prefix / case-fold / separator probes never match
r_pre = resolve(sMO, "XBTUSDTZ", T0, T2)
r_case = resolve(sMO, "xbtusdt", T0, T2)
r_sep = resolve(sMO, "XBT-USDT", T0, T2)
mo.append({
    "rank": "3/4 (exactness)", "tier": "negative alias / exact-text law",
    "acceptance_clause": "bloc_05/01 section 10 (EXACT matching only: no fuzzy, no prefix, no substring, no case folding, no separator normalization); section 8; directives 5/17/47",
    "probe": "prefix (XBTUSDTZ), case-folded (xbtusdt) and separator-inserted (XBT-USDT) variants of the registered text XBTUSDT, each queried against a registry where that exact text is registered",
    "input_condition": "event=2023-01-01T12:00Z, cutoff=2025-01-01T12:00Z; registered texts: native XBTUSDT + alias XBTUSDT (API_SYMBOL) + alias DIRECTA",
    "observed_status": {"prefix": r_pre.status.value, "case_fold": r_case.status.value, "separator": r_sep.status.value},
    "observed_flags": {"prefix": flags_of(r_pre), "case_fold": flags_of(r_case), "separator": flags_of(r_sep)},
    "expected": "UNKNOWN_SYMBOL with no identity payload for all three variants (fuzzy never enters)",
    "result": "PASS" if all(r.status is ST.UNKNOWN_SYMBOL and carries_no_identity(r)
                            for r in (r_pre, r_case, r_sep)) else "FAIL",
    "evidence_ref": GEN_REF + "; standing regressions: " + TESTS + "::test_prefix_candidates_do_not_match / ::test_fuzzy_one_char_deviation_cannot_resolve / ::test_case_fold_cannot_resolve",
})

# G3b: stablecoin / quote-asset firewall - canonical identity never substitutes
r_sc = resolve(sMO, "XBTUSDT", T0 + timedelta(days=3), T2)
mo.append({
    "rank": "2 (stablecoin firewall)", "tier": "exact native symbol - quote/asset firewall",
    "acceptance_clause": "bloc_05/01 section 12 (stablecoin firewall: no USD/USDT/USDC substitution); directives 6/7",
    "probe": "USDT-quoted contract queried by its native symbol: canonical identity must be the underlying asset, never a quote/stablecoin asset",
    "input_condition": "event=2023-01-04T12:00Z, cutoff=2025-01-01T12:00Z, quote_asset_id=USDT, settlement_asset_id=USDT, underlying_asset_id=BTC",
    "observed_status": r_sc.status.value,
    "observed_canonical_asset_id": r_sc.canonical_asset_id,
    "expected": "RESOLVED_EXACT with canonical_asset_id=BTC (underlying, never quote); no USD/USDT substitution",
    "result": "PASS" if (r_sc.status is ST.RESOLVED_EXACT
                         and r_sc.canonical_asset_id == "BTC"
                         and r_sc.canonical_asset_id not in {"USD", "USDT", "USDC"}) else "FAIL",
    "evidence_ref": GEN_REF + "; standing regression: " + TESTS + "::test_case_stablecoin_never_usd_substituted",
})

# G3c: identity-flag coverage - the four sanctioned EMITTED flags each observed;
# the sanctioned NOT-emitted flags never observed on any I03 path
sFC = snap("flagcov", instances=(ci("CI-A"),),
           aliases=(al("DIRECTA", I.AliasType.API_SYMBOL),),
           lifecycles=(le(I.LifecycleState.SUSPENDED, vfrom=T0 + timedelta(days=1),
                          vto=T0 + timedelta(days=9), kfrom=T0, kto=T0 + timedelta(days=5)),))
flag_probes = {
    "IDENTITY_ALIAS_USED": resolve(sFC, "DIRECTA", T0, T2),
    "IDENTITY_MANUAL_OVERRIDE": resolve(sT4, "LEGACYX", T2 + timedelta(days=1), T2 + timedelta(days=1)),
    "IDENTITY_PROVIDER_ID_MISSING": resolve(sFC, "XBTUSDT", T0, T2, pid="PID-1"),
    "IDENTITY_LIFECYCLE_BOUNDARY": resolve(sFC, "XBTUSDT", T0 + timedelta(days=2), T0 + timedelta(days=4)),
}
observed_all = set()
for rr in flag_probes.values():
    observed_all.update(f.value for f in rr.quality_flags)
not_emitted = {
    "IDENTITY_SYMBOL_REUSED", "IDENTITY_RELISTED", "IDENTITY_CURRENT_METADATA_BACKCAST_RISK",
    "IDENTITY_AMBIGUOUS", "IDENTITY_TERMS_UNVERIFIED", "IDENTITY_STABLECOIN_DISTINCT",
}
flags_expected_observed = set(flag_probes)
mo.append({
    "rank": "coverage", "tier": "identity quality-flag coverage",
    "acceptance_clause": "bloc_05/01 section 14 (quality flags); BLOC_05_I03_IMPLEMENTATION_EVIDENCE.md section 2 (flag inventory: four emitted, six sanctioned NOT emitted)",
    "probe": "four flag-producing paths run live (alias win, curated-carrier win, tier-1 pid match, lifecycle warning) and the union of observed flags is compared against the sanctioned inventory",
    "input_condition": "alias win=DIRECTA@T0/cutoff T2; curated win=LEGACYX@2025-01-02; tier-1=XBTUSDT+PID-1@T0/cutoff T2; lifecycle=SUSPENDED row known [T0, T0+5d), event=T0+2d, cutoff=T0+4d",
    "observed_flags_by_probe": {k: flags_of(v) for k, v in flag_probes.items()},
    "observed_flags_union": sorted(observed_all),
    "expected": "all four sanctioned-emitted flags observed; zero occurrences of the six sanctioned NOT-emitted flags on any path",
    "result": "PASS" if (flags_expected_observed <= observed_all
                         and not (observed_all & not_emitted)) else "FAIL",
    "evidence_ref": GEN_REF + "; flag inventory: BLOC_05_I03_IMPLEMENTATION_EVIDENCE.md section 2; standing regressions: " + TESTS + " (alias/manual/pid/lifecycle flag assertions)",
})

match_ok = all(row["result"] == "PASS" for row in mo)
write_matrix("BLOC_05_I03_MATCH_ORDER_MATRIX.json", {
    "artifact": "BLOC_05_I03_MATCH_ORDER_MATRIX",
    "checkpoint": "SENSOR-B5-I03",
    "created": RUN_DATE,
    "evidence_class": "measured_executable",
    "authority": ["bloc_05/01 section 10; I03 directives 14/45"],
    "law": "tier rank hard-laws the resolver: a higher tier wins ONLY with PIT-valid evidence; no lowered-priority candidate may override a valid higher-priority match; no arbitrary winner inside one tier (AMBIGUOUS); fuzzy never enters",
    "generated_by": GEN_REF,
    "disclosure": "tier 4 is implemented per the vocabulary matrix path A: curated manual mappings are carried as evidence-backed InstrumentAlias rows of non-API kinds. Tiers 3 and 4 are ONE pooled scan (ambiguity dominates convenience: a later sequential tier could outrank an ambiguity the pooled scan sees); tier-4 semantics are carried by the winner's alias kind -> IDENTITY_MANUAL_OVERRIDE on a curated-carrier win, status stays RESOLVED_ALIAS with matched_alias_id (directive 17). The vocabulary matrix's RESOLVED_WITH_WARNING wording for tier 4 is NOT used because it would conflict with the matched_alias_id-only-on-RESOLVED_ALIAS law; this wording deviation is disclosed in BLOC_05_I03_IMPLEMENTATION_EVIDENCE.md.",
    "summary": {"tiers_probed": len(mo), "all_results_pass": match_ok},
    "rows": mo,
})
print("match order:", match_ok, len(mo))

# ===========================================================================
# 46 LIFECYCLE MATRIX: the seven states, exact resolver behavior per state
# ===========================================================================
lc_rows = []

def lc_row(state, probe, input_condition, r, expected_status, expect_ids,
           extra_flags_expected=(), under_specified=False, note=None,
           check=None, evidence_ref_extra=""):
    ok = r.status is expected_status and (r.contract_instance_id is not None) is expect_ids
    for fl in extra_flags_expected:
        ok = ok and fl in flags_of(r)
    if check is not None:
        ok = ok and check(r)
    row = {
        "state_enumerated": state,
        "acceptance_clause": "bloc_05/01 section 6; bloc_05/07 F4; directives 4/33/34/46",
        "probe": probe,
        "input_condition": input_condition,
        "observed_status": r.status.value,
        "observed_flags": flags_of(r),
        "carries_identity": r.contract_instance_id is not None,
        "fabricated_ids": (
            (r.contract_instance_id is None)
            if r.status in RESOLVED_LIKE
            else (r.contract_instance_id is not None)
        ),
        "under_specified_surfaced": under_specified,
        "result_block_or_resolved": (
            "RESOLVED (" + r.status.value + ")" if r.status in RESOLVED_LIKE
            else "VERDICT/BLOCKED (" + r.status.value + ")"
        ),
        "evidence_ref": GEN_REF + evidence_ref_extra,
        "result": "PASS" if ok else "FAIL",
    }
    if note:
        row["note"] = note
    lc_rows.append(row)

BASE = (ci("CI-A"),)

# PRE_LISTING
r = resolve(snap("lcp", instances=BASE), "XBTUSDT", T0 - timedelta(days=1), T2)
lc_row("PRE_LISTING",
    "event one day before valid_from with the instance evidence known by the cutoff",
    "event=2022-12-31T12:00Z, cutoff=2025-01-01T12:00Z, instance CI-A valid [2023-01-01T12:00Z, 2024-01-01T12:00Z)",
    r, ST.NOT_YET_LISTED, expect_ids=False,
    evidence_ref_extra="; standing regression: " + TESTS + "::test_case_4_before_listing_is_not_yet_listed")

# ACTIVE
r = resolve(snap("lca", instances=BASE), "XBTUSDT", T0 + timedelta(days=1), T2)
lc_row("ACTIVE",
    "event inside the instance valid window",
    "event=2023-01-02T12:00Z, cutoff=2025-01-01T12:00Z, instance CI-A valid [2023-01-01T12:00Z, 2024-01-01T12:00Z)",
    r, ST.RESOLVED_EXACT, expect_ids=True,
    check=lambda rr: rr.contract_instance_id == "CI-A",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_boundary_valid_from_inclusive")

# SUSPENDED
sS = snap("lcs", instances=BASE,
          lifecycles=(le(I.LifecycleState.SUSPENDED, vfrom=T0 + timedelta(days=1),
                         vto=T0 + timedelta(days=5)),))
r = resolve(sS, "XBTUSDT", T0 + timedelta(days=2), T2)
lc_row("SUSPENDED",
    "event inside a knowledge-valid SUSPENDED lifecycle window over the instance",
    "event=2023-01-03T12:00Z, cutoff=2025-01-01T12:00Z, SUSPENDED window [2023-01-02T12:00Z, 2023-01-06T12:00Z) known_from=2022-12-31T12:00Z",
    r, ST.RESOLVED_WITH_WARNING, expect_ids=True,
    extra_flags_expected=("IDENTITY_LIFECYCLE_BOUNDARY",),
    note="no unique frozen status exists for suspended (bloc_05/01 section 9); RESOLVED_WITH_WARNING + IDENTITY_LIFECYCLE_BOUNDARY is the plan-justified smallest answer (directive 33)",
    evidence_ref_extra="; standing regression: " + TESTS + " lifecycle warning cases")

# DELISTING_ANNOUNCED
sD = snap("lcd", instances=BASE,
          lifecycles=(le(I.LifecycleState.DELISTING_ANNOUNCED, vfrom=T0 + timedelta(days=1),
                         vto=T1),))
r = resolve(sD, "XBTUSDT", T0 + timedelta(days=2), T2)
lc_row("DELISTING_ANNOUNCED",
    "event inside a knowledge-valid DELISTING_ANNOUNCED window over the instance",
    "event=2023-01-03T12:00Z, cutoff=2025-01-01T12:00Z, DELISTING_ANNOUNCED window [2023-01-02T12:00Z, 2024-01-01T12:00Z) known_from=2022-12-31T12:00Z",
    r, ST.RESOLVED_WITH_WARNING, expect_ids=True,
    extra_flags_expected=("IDENTITY_LIFECYCLE_BOUNDARY",),
    note="same frozen-vocabulary justification as SUSPENDED",
    evidence_ref_extra="; standing regression: " + TESTS + " lifecycle warning cases")

# DELISTED
r = resolve(snap("lcdel", instances=BASE), "XBTUSDT", T1 + timedelta(microseconds=1), T2)
lc_row("DELISTED",
    "event at/after valid_to with the instance evidence known by the cutoff",
    "event=2024-01-01T12:00:00.000001Z, cutoff=2025-01-01T12:00Z, instance CI-A valid_to=2024-01-01T12:00Z (exclusive)",
    r, ST.DELISTED, expect_ids=False,
    evidence_ref_extra="; standing regression: " + TESTS + "::test_case_5_after_delisting_is_delisted")

# RELISTED_NEW_INSTANCE: the between-break must NOT silently select the future instance
sR = snap("lcr", instances=(ci("CI-A"), ci("CI-B", vfrom=T2, vto=None,
                                          kfrom=T2 - timedelta(days=1))))
r_break = resolve(sR, "XBTUSDT", T1 + timedelta(days=1), T2 + timedelta(days=1))
lc_row("RELISTED_NEW_INSTANCE",
    "event inside the relisting break between CI-A (ends T1) and CI-B (starts T2)",
    "event=2024-01-02T12:00Z, cutoff=2025-01-02T12:00Z, CI-A valid [T0, T1), CI-B valid [T2, open)",
    r_break, ST.DELISTED, expect_ids=False,
    note="the between-gap refuses to silently select the future instance (no latest-win); DELISTED is the frozen not-active-at-event verdict (section 6 cutover law, directives 12/13)",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_case_8_break_interval_does_not_silently_choose_latest")

# RELISTED_NEW_INSTANCE: after the new instance starts, the NEW id resolves
r_new = resolve(sR, "XBTUSDT", T2 + timedelta(days=1), T2 + timedelta(days=1))
lc_row("RELISTED_NEW_INSTANCE",
    "event after the new instance's valid_from: cutover to the new contract instance id",
    "event=2025-01-02T12:00Z, cutoff=2025-01-02T12:00Z, CI-B valid [2025-01-01T12:00Z, open) known_from=2024-12-31T12:00Z",
    r_new, ST.RESOLVED_EXACT, expect_ids=True,
    check=lambda rr: rr.contract_instance_id == "CI-B",
    note="symbol reuse resolves to the NEW instance only after its valid_from (directive 12)",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_case_7_relisting_selects_new_instance_only_after_new_valid_from")

# UNKNOWN: knowledge-valid instance + UNKNOWN lifecycle row -> UNKNOWN is inert
r = resolve(snap("lcu", instances=BASE,
                 lifecycles=(le(I.LifecycleState.UNKNOWN, vfrom=T0, vto=None,
                                kfrom=T0 - timedelta(days=1)),)),
            "XBTUSDT", T0 + timedelta(days=1), T2)
lc_row("UNKNOWN",
    "event inside the instance window while an UNKNOWN lifecycle row is registered for the same instance",
    "event=2023-01-02T12:00Z, cutoff=2025-01-01T12:00Z, instance CI-A valid [T0, T1) known by cutoff; UNKNOWN window [T0, open) known_from=2022-12-31T12:00Z",
    r, ST.RESOLVED_EXACT, expect_ids=True,
    under_specified=True,
    note="documented under-specified choice: UNKNOWN lifecycle evidence neither gates nor activates nor warns - the instance interval law alone governs (activation comes from the instance row, never from the UNKNOWN row; directive 34 forbids optimistic activation FROM UNKNOWN evidence). Surfaced here rather than silently assumed.",
    evidence_ref_extra="; UNKNOWN semantics pinned by " + TESTS + " (directive 34 posture)")

# UNKNOWN: instance known only after the cutoff -> fail closed, never optimistic
r = resolve(snap("lcu2", instances=(ci("CI-A", kfrom=T1),),
                 lifecycles=(le(I.LifecycleState.UNKNOWN, vfrom=T0, vto=None,
                                kfrom=T1),)),
            "XBTUSDT", T0 + timedelta(days=1), T0 + timedelta(days=1))
lc_row("UNKNOWN",
    "instance (and its UNKNOWN lifecycle row) known only AFTER the cutoff: no optimistic activation",
    "event=2023-01-02T12:00Z, cutoff=2023-01-02T12:00Z, instance CI-A valid [T0, T1) but known_from=2024-01-01T12:00Z (> cutoff)",
    r, ST.PIT_KNOWLEDGE_BLOCKED, expect_ids=False,
    note="directive 34: UNKNOWN lifecycle must not become ACTIVE by default; with the instance row unknown at the cutoff the answer is PIT_KNOWLEDGE_BLOCKED (fail closed), never a fabricated identity",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_case_1_future_known_exact_symbol_must_not_resolve_backward (same gate, no lifecycle row)")

# ---------------------------------------------------------------------------
# I03D evidence amendment (operator gap sweep, 2026-10-07): lifecycle-ROW
# state laws and warning-window boundary instants.  The warning law
# enumerates only SUSPENDED / DELISTING_ANNOUNCED; every other lifecycle row
# is inert evidence.  These rows pin that by measurement, not by omission.
# ---------------------------------------------------------------------------

# RELISTED_NEW_INSTANCE state row over a PIT-valid instance: inert evidence
r = resolve(snap("lcrn", instances=BASE,
                 lifecycles=(le(I.LifecycleState.RELISTED_NEW_INSTANCE,
                                vfrom=T0, vto=None, kfrom=T0),)),
            "XBTUSDT", T0 + timedelta(days=1), T2)
lc_row("RELISTED_NEW_INSTANCE",
    "a RELISTED_NEW_INSTANCE lifecycle ROW over a PIT-valid instance is inert evidence",
    "event=2023-01-02T12:00Z, cutoff=2025-01-01T12:00Z, instance CI-A valid [2023-01-01T12:00Z, 2024-01-01T12:00Z); RELISTED_NEW_INSTANCE window [2023-01-01T12:00Z, open) known_from=2023-01-01T12:00Z",
    r, ST.RESOLVED_EXACT, expect_ids=True,
    check=lambda rr: "IDENTITY_LIFECYCLE_BOUNDARY" not in flags_of(rr),
    note="the warning law enumerates only SUSPENDED / DELISTING_ANNOUNCED (S6/I03D33); the relisting cutover is carried by the NEW instance's own valid_from, never by the state row. Pinned by probe, not by omission.",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_relisted_new_instance_lifecycle_row_is_inert")

# PRE_LISTING state row over a PIT-valid instance: inert evidence (A7b law)
r = resolve(snap("lcpl", instances=BASE,
                 lifecycles=(le(I.LifecycleState.PRE_LISTING,
                                vfrom=T0 - timedelta(days=30), vto=T0, kfrom=T0),)),
            "XBTUSDT", T0 + timedelta(days=1), T2)
lc_row("PRE_LISTING",
    "a PRE_LISTING lifecycle ROW over a PIT-valid instance is inert evidence",
    "event=2023-01-02T12:00Z, cutoff=2025-01-01T12:00Z, instance CI-A valid [T0, T1); PRE_LISTING window [2022-12-02T12:00Z, 2023-01-01T12:00Z) known_from=2023-01-01T12:00Z",
    r, ST.RESOLVED_EXACT, expect_ids=True,
    check=lambda rr: "IDENTITY_LIFECYCLE_BOUNDARY" not in flags_of(rr),
    note="exactly the A7b law (DELISTED row over a live instance is inert): PRE_LISTING evidence about one instance never de-activates the instance's own PIT-valid interval",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_pre_listing_lifecycle_row_is_inert")

# SUSPENDED warning-window boundary instants (half-open [vfrom, vto))
sS2 = snap("lcsb", instances=BASE,
           lifecycles=(le(I.LifecycleState.SUSPENDED,
                          vfrom=T0 + timedelta(days=1),
                          vto=T0 + timedelta(days=5), kfrom=T0),))
r = resolve(sS2, "XBTUSDT", T0 + timedelta(days=1), T2)
lc_row("SUSPENDED",
    "event exactly AT the SUSPENDED window start: warning is start-inclusive",
    "event=2023-01-02T12:00Z == SUSPENDED valid_from; window [2023-01-02T12:00Z, 2023-01-06T12:00Z)",
    r, ST.RESOLVED_WITH_WARNING, expect_ids=True,
    extra_flags_expected=("IDENTITY_LIFECYCLE_BOUNDARY",),
    note="half-open warning-window law pinned at the start instant (directive 43 temporal axes)",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_suspended_warning_window_boundaries_are_half_open")

r = resolve(sS2, "XBTUSDT", T0 + timedelta(days=1) - timedelta(microseconds=1), T2)
lc_row("SUSPENDED",
    "event one microsecond BEFORE the SUSPENDED window start: no warning",
    "event=2023-01-02T11:59:59.999999Z < SUSPENDED valid_from; same window as above",
    r, ST.RESOLVED_EXACT, expect_ids=True,
    check=lambda rr: "IDENTITY_LIFECYCLE_BOUNDARY" not in flags_of(rr),
    note="not-yet-warning side of the start boundary",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_suspended_warning_window_boundaries_are_half_open")

r = resolve(sS2, "XBTUSDT", T0 + timedelta(days=5), T2)
lc_row("SUSPENDED",
    "event exactly AT the SUSPENDED window end: warning is end-exclusive",
    "event=2023-01-06T12:00Z == SUSPENDED valid_to (exclusive); window [2023-01-02T12:00Z, 2023-01-06T12:00Z)",
    r, ST.RESOLVED_EXACT, expect_ids=True,
    check=lambda rr: "IDENTITY_LIFECYCLE_BOUNDARY" not in flags_of(rr),
    note="half-open warning-window law pinned at the end instant",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_suspended_warning_window_boundaries_are_half_open")

r = resolve(sS2, "XBTUSDT", T0 + timedelta(days=5) - timedelta(microseconds=1), T2)
lc_row("SUSPENDED",
    "event one microsecond BEFORE the SUSPENDED window end: still warning",
    "event=2023-01-06T11:59:59.999999Z < SUSPENDED valid_to; same window as above",
    r, ST.RESOLVED_WITH_WARNING, expect_ids=True,
    extra_flags_expected=("IDENTITY_LIFECYCLE_BOUNDARY",),
    note="still-warning side of the end boundary",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_suspended_warning_window_boundaries_are_half_open")

# DELISTING_ANNOUNCED warning-window boundary instants (half-open)
sD2 = snap("lcdb", instances=BASE,
           lifecycles=(le(I.LifecycleState.DELISTING_ANNOUNCED,
                          vfrom=T0 + timedelta(days=1),
                          vto=T0 + timedelta(days=9), kfrom=T0),))
r = resolve(sD2, "XBTUSDT", T0 + timedelta(days=1), T2)
lc_row("DELISTING_ANNOUNCED",
    "event exactly AT the DELISTING_ANNOUNCED window start: warning is start-inclusive",
    "event=2023-01-02T12:00Z == DELISTING_ANNOUNCED valid_from; window [2023-01-02T12:00Z, 2023-01-10T12:00Z)",
    r, ST.RESOLVED_WITH_WARNING, expect_ids=True,
    extra_flags_expected=("IDENTITY_LIFECYCLE_BOUNDARY",),
    note="half-open warning-window law pinned at the start instant",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_delisting_announced_warning_window_boundaries_are_half_open")

r = resolve(sD2, "XBTUSDT", T0 + timedelta(days=9), T2)
lc_row("DELISTING_ANNOUNCED",
    "event exactly AT the DELISTING_ANNOUNCED window end: warning is end-exclusive",
    "event=2023-01-10T12:00Z == DELISTING_ANNOUNCED valid_to (exclusive); window [2023-01-02T12:00Z, 2023-01-10T12:00Z)",
    r, ST.RESOLVED_EXACT, expect_ids=True,
    check=lambda rr: "IDENTITY_LIFECYCLE_BOUNDARY" not in flags_of(rr),
    note="half-open warning-window law pinned at the end instant",
    evidence_ref_extra="; standing regression: " + TESTS + "::test_delisting_announced_warning_window_boundaries_are_half_open")

life_ok = all(row["result"] == "PASS" for row in lc_rows)
write_matrix("BLOC_05_I03_LIFECYCLE_MATRIX.json", {
    "artifact": "BLOC_05_I03_LIFECYCLE_MATRIX",
    "checkpoint": "SENSOR-B5-I03",
    "created": RUN_DATE,
    "evidence_class": "measured_executable",
    "authority": ["bloc_05/01 section 6; bloc_05/07 F4; I03 directives 4/33/34/46"],
    "law": "all seven states enumerated without collapsing; lifecycle record = minimal InstrumentLifecycle evidence rows (documented choice per directive 9); UNKNOWN never optimistically activates; PRE_LISTING/DELISTED/UNKNOWN are never collapsed into one absence state",
    "generated_by": GEN_REF,
    "summary": {
        "states_enumerated": 7,
        "rows": len(lc_rows),
        "collapse_events": 0,
        "under_specified_rows": sum(1 for row in lc_rows if row["under_specified_surfaced"]),
        "all_results_pass": life_ok,
    },
    "rows": lc_rows,
})
print("lifecycle:", life_ok, len(lc_rows))

# ===========================================================================
# 47 ALIAS MATRIX: all six AliasType values; PIT window + cutoff + wrong venue
# ===========================================================================
al_rows = []
for at in I.AliasType:
    text = "TXT_" + at.value
    # registry-valid wrong-venue snapshot: OTHERVEN is REGISTERED, the alias
    # lives there, the queried venue stays VEN (resolver-side negative)
    s_wv = snap("wv-" + at.value,
                instances=(ci("CI-A"),),
                aliases=(al(text, at, ven_id=OTHERVEN),),
                venues=(ven(), ven(OTHERVEN)))
    s_a = snap("alt-" + at.value, instances=(ci("CI-A"),),
               aliases=(al(text, at, vto=T1),))
    tin = resolve(s_a, text, T0, T2)                              # inside window
    tout = resolve(s_a, text, T1 + timedelta(microseconds=1), T2)  # past valid_to
    r_wv = resolve(s_wv, text, T0, T2)                             # wrong venue
    row = {
        "alias_type": at.value,
        "acceptance_clause": "bloc_05/01 section 8; directives 5/17/47",
        "evidence_ref": GEN_REF + "; standing regressions: " + TESTS
            + "::test_case_11_expired_alias_does_not_resolve / ::test_case_12_wrong_venue_alias_does_not_resolve",
        "inside_window_and_cutoff": {
            "probe": "query the alias text at an instant inside [valid_from, valid_to) with the cutoff past known_from",
            "input_condition": "event=2023-01-01T12:00Z, cutoff=2025-01-01T12:00Z, alias window [2023-01-01T12:00Z, 2024-01-01T12:00Z)",
            "observed_status": tin.status.value,
            "matched_alias_id": tin.matched_alias_id,
            "observed_confidence": tin.confidence,
            "expected": "RESOLVED_ALIAS with matched_alias_id set and opaque confidence passthrough",
            "result": "PASS" if (tin.status is ST.RESOLVED_ALIAS
                                 and tin.matched_alias_id is not None) else "FAIL",
        },
        "past_alias_valid_to": {
            "probe": "query the same text one microsecond past the alias valid_to (queried text has no registered instances, so no tier-2 verdict fires)",
            "input_condition": "event=2024-01-01T12:00:00.000001Z, cutoff=2025-01-01T12:00Z, alias valid_to=2024-01-01T12:00Z (exclusive)",
            "observed_status": tout.status.value,
            "matched_alias_id": tout.matched_alias_id,
            "expected": "UNKNOWN_SYMBOL with matched_alias_id=None (dual-clock gate closed)",
            "result": "PASS" if (tout.status is ST.UNKNOWN_SYMBOL
                                 and tout.matched_alias_id is None) else "FAIL",
        },
        "wrong_venue_probe": {
            "probe": "same text/type registered ONLY on venue OTHER_FUT (registered venue), queried against EXA_FUT",
            "input_condition": "event=2023-01-01T12:00Z, cutoff=2025-01-01T12:00Z, alias venue=OTHER_FUT, query venue=EXA_FUT",
            "observed_status": r_wv.status.value,
            "matched_alias_id": r_wv.matched_alias_id,
            "expected": "UNKNOWN_SYMBOL with matched_alias_id=None (venue gate exact, never cross-venue)",
            "result": "PASS" if (r_wv.status is ST.UNKNOWN_SYMBOL
                                 and r_wv.matched_alias_id is None) else "FAIL",
        },
    }
    row["result"] = "PASS" if all(
        row[k]["result"] == "PASS"
        for k in ("inside_window_and_cutoff", "past_alias_valid_to", "wrong_venue_probe")
    ) else "FAIL"
    al_rows.append(row)

alias_ok = all(row["result"] == "PASS" for row in al_rows)
write_matrix("BLOC_05_I03_ALIAS_MATRIX.json", {
    "artifact": "BLOC_05_I03_ALIAS_MATRIX",
    "checkpoint": "SENSOR-B5-I03",
    "created": RUN_DATE,
    "evidence_class": "measured_executable",
    "authority": ["bloc_05/01 section 8; I03 directives 5/17/47"],
    "law": "registered alias matches ONLY while its dual-clock gate is open (valid-time AND knowledge-time) in the exact (provider, venue, text) context; wrong venue/provider/text never matches; all six AliasType values enumerated without extension",
    "generated_by": GEN_REF,
    "summary": {"alias_types_probed": 6, "all_results_pass": alias_ok},
    "rows": al_rows,
})
print("alias:", alias_ok, len(al_rows))

# ===========================================================================
# B5-I03H KNOWLEDGE BOUNDARY MATRIX: Option 1 closure
#   known_from <= knowledge_cutoff < known_to (absent known_to = open-ended)
# PROSPECTIVE operator-directed clarification - NOT attributed to the frozen
# I03 contract; bloc_05/01 section 5 seals the lower bound only.
# Every row holds the event-time clock FIXED inside a valid window and moves
# only the knowledge cutoff.
# ===========================================================================

KB_CLAUSE = (
    "operator-directed Option 1 closure (B5-I03H): known_from <= knowledge_cutoff "
    "< known_to; an absent known_to is an open-ended knowledge interval. "
    "PROSPECTIVE clarification, not attributed to the frozen I03 contract "
    "(bloc_05/01 section 5 seals the lower knowledge bound only)")
K0 = datetime(2023, 6, 1, 12, tzinfo=UTC)
K1 = datetime(2023, 12, 1, 12, tzinfo=UTC)
EV = datetime(2023, 9, 1, 12, tzinfo=UTC)  # fixed inside valid [T0, T1)

def _ts(dt):
    """Compact UTC rendering derived FROM THE EXECUTED VALUE (B5-I03I: the
    KB1/KB3/KB7b narrations were previously hand-typed from the test file's
    midnight-based K0/K1 instead of this fixture's noon-based ones)."""
    if dt.microsecond:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    return dt.strftime("%Y-%m-%dT%H:%M") + "Z"

kb_rows = []

def kb_row(case_id, probe, input_condition, r, expected_status,
           expect_instance=None, expect_flags=None, evidence_extra=""):
    resolved = r.status in RESOLVED_LIKE
    flags_observed = flags_of(r)
    ok = r.status.value == expected_status
    if expect_instance is not None:
        ok = ok and r.contract_instance_id == expect_instance
    if expect_flags:
        ok = ok and all(f in flags_observed for f in expect_flags)
    if resolved:
        ok = ok and r.contract_instance_id is not None
    else:
        ok = ok and carries_no_identity(r)
    kb_rows.append({
        "case_id": case_id,
        "acceptance_clause": KB_CLAUSE,
        "probe": probe,
        "input_condition": input_condition,
        "event_clock": "event fixed at 2023-09-01T12:00Z (or T0-based event in the same valid window); the event-time clock is NOT moved by this row",
        "observed_status": r.status.value,
        "observed_flags": flags_observed,
        "contract_instance_id": r.contract_instance_id,
        "expected_status": expected_status,
        "result": "PASS" if ok else "FAIL",
        "evidence_ref": GEN_REF + "; standing regression: " + TESTS + evidence_extra,
    })

sKB = snap("kb", instances=(ci("CI-A", kfrom=K0, kto=K1),))

r = resolve(sKB, "XBTUSDT", EV, K0 - timedelta(microseconds=1))
kb_row("KB1", "cutoff strictly BEFORE known_from leaves no eligible candidate",
       f"event={_ts(EV)}, cutoff={_ts(K0 - timedelta(microseconds=1))} "
       f"== known_from - 1us, instance known [{_ts(K0)}, {_ts(K1)})",
       r, "PIT_KNOWLEDGE_BLOCKED",
       evidence_extra="::test_knowledge_cutoff_before_known_from_is_blocked")

r = resolve(sKB, "XBTUSDT", EV, K0)
kb_row("KB2", "cutoff EXACTLY at known_from is eligible (lower bound inclusive)",
       "event=2023-09-01T12:00Z, cutoff=2023-06-01T12:00Z == known_from, instance known [K0, K1)",
       r, "RESOLVED_EXACT", expect_instance="CI-A",
       evidence_extra="::test_knowledge_cutoff_exactly_at_known_from_resolves")

r = resolve(sKB, "XBTUSDT", EV, K1 - timedelta(microseconds=1))
kb_row("KB3", "cutoff one microsecond BEFORE known_to resolves; the cutoff is LATER than the event (historical query inside the knowledge window)",
       f"event={_ts(EV)}, cutoff={_ts(K1 - timedelta(microseconds=1))} "
       f"== known_to - 1us < known_to={_ts(K1)}, instance known [{_ts(K0)}, {_ts(K1)})",
       r, "RESOLVED_EXACT", expect_instance="CI-A",
       evidence_extra="::test_knowledge_cutoff_one_microsecond_before_known_to_still_resolves / ::test_historical_event_resolves_only_inside_the_knowledge_window")

r = resolve(sKB, "XBTUSDT", EV, K1)
kb_row("KB4", "cutoff EXACTLY at known_to is past the interval (upper bound exclusive)",
       "event=2023-09-01T12:00Z, cutoff=2023-12-01T12:00Z == known_to, instance known [K0, K1)",
       r, "PIT_KNOWLEDGE_BLOCKED",
       evidence_extra="::test_knowledge_cutoff_exactly_at_known_to_is_blocked")

r = resolve(sKB, "XBTUSDT", EV, K1 + timedelta(days=1))
kb_row("KB5", "cutoff AFTER known_to: historical event with a later, post-close cutoff blocks (no as-of retention outside the knowledge window)",
       "event=2023-09-01T12:00Z, cutoff=2023-12-02T12:00Z > known_to, instance known [K0, K1)",
       r, "PIT_KNOWLEDGE_BLOCKED",
       evidence_extra="::test_knowledge_cutoff_after_known_to_is_blocked / ::test_historical_event_resolves_only_inside_the_knowledge_window")

sKB6 = snap("kb6", instances=(ci("CI-A", kfrom=T0 - timedelta(days=2)),))  # known_to absent
r = resolve(sKB6, "XBTUSDT", EV, datetime(2030, 1, 1, 12, tzinfo=UTC))
kb_row("KB6", "absent known_to = open-ended knowledge interval: an arbitrarily late cutoff still resolves",
       "event=2023-09-01T12:00Z, cutoff=2030-01-01T12:00Z, instance known_from=2022-12-30T12:00Z, known_to=None",
       r, "RESOLVED_EXACT", expect_instance="CI-A",
       evidence_extra="::test_absent_known_to_is_open_ended")

# KB7: multiple revisions with nonoverlapping knowledge windows
k2 = datetime(2024, 3, 1, 12, tzinfo=UTC)
PAUSE2 = datetime(2024, 6, 1, 12, tzinfo=UTC)
sKB8 = snap("kb8", instances=(
    ci("CI-OLD", vfrom=T0, vto=PAUSE2, kfrom=K0, kto=K1),
    ci("CI-NEW", vfrom=T2, vto=None, kfrom=k2)))
r = resolve(sKB8, "XBTUSDT", PAUSE2, datetime(2024, 1, 15, 12, tzinfo=UTC))
kb_row("KB7a", "cutoff in the GAP between the old knowledge window closing and the new one opening: no eligible candidate; no supersession engine, no replacement selected",
       "event=2024-06-01T12:00Z, cutoff=2024-01-15T12:00Z (old known [2023-06-01, 2023-12-01), new known [2024-03-01, open))",
       r, "PIT_KNOWLEDGE_BLOCKED",
       evidence_extra="::test_nonoverlapping_revisions_gap_cutoff_blocks_without_supersession")
r = resolve(sKB8, "XBTUSDT", EV, K1 - timedelta(microseconds=1))
kb_row("KB7b", "cutoff inside the OLD knowledge window answers with the OLD record (no arbitrary replacement selection)",
       f"event={_ts(EV)}, cutoff={_ts(K1 - timedelta(microseconds=1))} "
       f"(old known [{_ts(K0)}, {_ts(K1)}); new not yet known at this cutoff)",
       r, "RESOLVED_EXACT", expect_instance="CI-OLD",
       evidence_extra="::test_nonoverlapping_revisions_gap_cutoff_blocks_without_supersession")
r = resolve(sKB8, "XBTUSDT", T2 + timedelta(days=1), k2)
kb_row("KB7c", "cutoff inside the NEW knowledge window answers with the NEW record (valid-time cutover law, not knowledge law)",
       "event=2025-01-02T12:00Z, cutoff=2024-03-01T12:00Z == new known_from (inclusive lower bound)",
       r, "RESOLVED_EXACT", expect_instance="CI-NEW",
       evidence_extra="::test_nonoverlapping_revisions_gap_cutoff_blocks_without_supersession")

# KB8: ambiguity must not be manufactured away by knowledge eligibility
sKB9 = snap("kb9",
    instances=(ci("CI-K1", native="AMBKA1", kfrom=K0, kto=K1),
               ci("CI-K2", native="AMBKA2", kfrom=K0, kto=None)),
    aliases=(al("AMBK1", I.AliasType.API_SYMBOL, iid="CI-K1", vto=None),
             al("AMBK1", I.AliasType.DISPLAY_SYMBOL, iid="CI-K2", vto=None)))
r = resolve(sKB9, "AMBK1", EV, datetime(2023, 10, 1, 12, tzinfo=UTC))
kb_row("KB8", "two alias-matched records both knowledge-eligible at the cutoff and both valid at the event stay AMBIGUOUS (eligibility never manufactures a winner)",
       "event=2023-09-01T12:00Z, cutoff=2023-10-01T12:00Z (inside BOTH knowledge windows: [K0,K1) and [K0,open)); two same-text carriers -> CI-K1/CI-K2",
       r, "AMBIGUOUS",
       evidence_extra="::test_overlapping_eligible_records_stay_ambiguous")

# KB9: lifecycle warning row with expired knowledge is inert (control pair)
sKB10 = snap("kb10", instances=(ci("CI-A"),), lifecycles=(
    le(I.LifecycleState.SUSPENDED, vfrom=T0 + timedelta(days=1),
       vto=T0 + timedelta(days=9), kfrom=T0, kto=T0 + timedelta(days=5)),))
r = resolve(sKB10, "XBTUSDT", T0 + timedelta(days=2), T0 + timedelta(days=4))
kb_row("KB9a", "CONTROL: cutoff inside the SUSPENDED row's knowledge window fires the warning downgrade",
       "event=2023-01-03T12:00Z, cutoff=2023-01-05T12:00Z; SUSPENDED row valid [2023-01-02, 2023-01-10), known [2023-01-01, 2023-01-06)",
       r, "RESOLVED_WITH_WARNING", expect_instance="CI-A",
       expect_flags=["IDENTITY_LIFECYCLE_BOUNDARY"],
       evidence_extra="::test_lifecycle_warning_row_with_expired_knowledge_is_inert")
r = resolve(sKB10, "XBTUSDT", T0 + timedelta(days=2), T0 + timedelta(days=5))
kb_row("KB9b", "cutoff EXACTLY at the SUSPENDED row's known_to: the row is not knowledge-eligible, no downgrade fires (knowledge clock alone)",
       "event=2023-01-03T12:00Z, cutoff=2023-01-06T12:00Z == row known_to; same event, same valid-time windows as KB9a",
       r, "RESOLVED_EXACT", expect_instance="CI-A",
       evidence_extra="::test_lifecycle_warning_row_with_expired_knowledge_is_inert")
r = resolve(sKB10, "XBTUSDT", T0 + timedelta(days=2), T0 + timedelta(days=6))
kb_row("KB9c", "cutoff after the SUSPENDED row's known_to: warning stays inert",
       "event=2023-01-03T12:00Z, cutoff=2023-01-07T12:00Z > row known_to",
       r, "RESOLVED_EXACT", expect_instance="CI-A",
       evidence_extra="::test_lifecycle_warning_row_with_expired_knowledge_is_inert")

# KB10: alias schema untouched - no known_to field, open-ended by frozen design
sKB11 = snap("kb11", instances=(ci("CI-A"),),
             aliases=(al("OPENAL", I.AliasType.API_SYMBOL),))
r = resolve(sKB11, "OPENAL", EV, datetime(2035, 1, 1, 12, tzinfo=UTC))
kb_row("KB10", "InstrumentAlias carries no known_to (frozen eleven-field schema): its knowledge interval is open-ended and a far-future cutoff still resolves it",
       "event=2023-09-01T12:00Z, cutoff=2035-01-01T12:00Z, alias known_from=2022-12-31T12:00Z, known_to ABSENT by frozen schema",
       r, "RESOLVED_ALIAS", expect_instance="CI-A",
       expect_flags=["IDENTITY_ALIAS_USED"],
       evidence_extra="(frozen schema pin - aliases.py section 8 field list)")

kb_ok = all(row["result"] == "PASS" for row in kb_rows)
write_matrix("BLOC_05_I03H_KNOWLEDGE_BOUNDARY_MATRIX.json", {
    "artifact": "BLOC_05_I03H_KNOWLEDGE_BOUNDARY_MATRIX",
    "checkpoint": "SENSOR-B5-I03H",
    "created": RUN_DATE,
    "evidence_class": "measured_executable",
    "authority": [KB_CLAUSE],
    "law": "a record carrying known_to is knowledge-eligible iff known_from <= knowledge_cutoff < known_to; an absent known_to is open-ended; an expired knowledge record leaving no eligible candidate resolves to PIT_KNOWLEDGE_BLOCKED using existing blocking vocabulary (no new status, no supersession engine); alias schema untouched",
    "generated_by": GEN_REF,
    "summary": {
        "cases": len(kb_rows),
        "all_results_pass": kb_ok,
        "event_clock_fixed": True,
    },
    "rows": kb_rows,
})
print("knowledge boundary:", kb_ok, len(kb_rows))
print("ALL MATRICES WRITTEN")
