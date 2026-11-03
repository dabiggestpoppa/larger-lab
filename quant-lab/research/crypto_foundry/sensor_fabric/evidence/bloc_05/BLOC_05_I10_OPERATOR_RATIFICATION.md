# BLOC 05 / SENSOR-B5-I10 — BOUNDED OPERATOR RATIFICATION

**Repository:** `dabiggestpoppa/larger-lab`
**Branch:** `agent/crypto-sensor-fabric-build`
**Base HEAD:** `cd8208ee4ae9c989689ecabedfffaf3b9fb7c88b`
**Ratified checkpoint:** B5-I10 — provider-neutral trade normalizer + Binance side map
**Issued under:** SENSOR-B5-I10R2 directive, step 6 ("If every mandatory gate is genuinely earned, record bounded `B5-I10 = OPERATOR_ACCEPTED`")
**Companion record:** `BLOC_05_I10R2_CUSTODY_CORRECTION.md` (F1 correction, F2 disclosure)
**Prior record superseded for status only:** `BLOC_05_I10R1_AUDIT_HOLD.md` (retains all findings; its HOLD is discharged by the correction above, not by re-audit)

---

## 1. Decision

```
B5-I10 = OPERATOR_ACCEPTED   (bounded; conditions in §5)

basis       24/24 R10 gates PASS at cd8208ee4a + this commit
scope       normalization/sensors/{__init__,side_maps,trade}.py + tests + fixtures
digest      bloc_05_semantic_validation.json = 2587e373…cf54ff50a (measured, corrected)
regression  4,357 passed / 14 skipped / exit 0  (accepted run, not re-executed)
```

The ratification is **bounded**: it accepts exactly the trade normalizer and the
Binance side map as implemented, and nothing downstream of them. Acceptance of a
checkpoint is not acceptance of a bloc, and it is not authorization to start the
next one.

## 2. What this ratification accepts — and what it refuses to imply

**Accepted.** A provider-neutral `T1TradeRecord` normalizer that (a) preserves
every native provider value verbatim alongside its canonical projection, (b)
keeps canonical `aggressor_side` at `UNKNOWN` unless a provider's own vocabulary
admits an unambiguous mapping, (c) records a provider boolean as *provisional*
`SideEvidence` without ever treating it as canonical aggressor flow, (d) computes
I04B quantity base for linear and inverse contracts with the inverse case using
the **reference** price rather than the trade price, (e) refuses to emit
`quantity_base` or `notional_usd` when conversion or unit semantics are
unresolved and cites `B5_I08_UNITS_V1` instead, and (f) preserves lineage,
instrument identity, contract instance and venue without deduplicating,
collapsing or replaying symbols.

**Refused.** That I10 proves liquidation semantics, funding, positioning or any
I11 surface. That the Binance boolean is a certified aggressor mapping. That
`notional_usd` exists. That the U08-20 `(0,1)` allowance is sound. That the
CRLF encoding of five sealed files is good practice. That a full regression was
re-run under this directive.

## 3. Preconditions discharged by this commit

| Defect | Discharge |
|---|---|
| **F1** — I10 evidence §7 records successor `459568e9…`, which no blob has | Corrected: measured `2587e373f269692bb69ed809c153ce6d6efb354e08b48f6520c22cecf54ff50a`, independently recomputed, corroborated by the pre-existing executable pin. Erroneous cell superseded in place, not deleted. See correction §2. |
| **F2** — five sealed files re-encoded LF→CRLF without disclosure | Disclosed: exact predecessor/successor blobs and sha256 for all five, normalized logical change isolated to +83/−19 lines, all of it the authorized `sensors/` extension. See correction §3. |

Both discharges are **append-only**. No historical artifact was edited, no file
normalized, no hash repinned. The failing statements remain readable in their
original bytes and are marked superseded by a record whose own bytes are sealed
by this commit.

## 4. Gate result

| Gate | Verdict |
|---|---|
| R10-01 … R10-07 | PASS |
| R10-08 recorded successor digest | PASS (corrected, §3) |
| R10-09 … R10-13 scope integrity | PASS, with F2 disclosed |
| R10-14 negative-path custody | PASS |
| R10-15 … R10-20 semantics, economics, lineage, I17 | PASS |
| R10-21 full canonical regression | PASS (accepted run, provenance verified) |
| R10-22 … R10-23 reproducibility, determinism | PASS |
| R10-24 governance binding, fast-forward | PASS |

**24 PASS, 0 FAIL, 0 unearned.** Full basis in the correction record §4.

## 5. Conditions attached to this acceptance

This acceptance is **void** if any of the following is later shown to be false;
it does not lapse merely because the obligations below remain open, but it does
not extend to them either.

1. **F3 — U08-20 `(0,1)` allowance.** The I08 unit probe currently accepts a
   ratio in the open interval `(0,1)`. This is broader than the evidence
   supports and must be narrowed or justified under **B5-I08R2**. Until then no
   consumer may rely on the probe as proof of unit correctness.
2. **F4 — I08 producer not re-runnable at HEAD.** It refuses with
   `non_pass_dispositions` and leaves its artifact unchanged. Fail-closed
   behaviour is correct; reproducibility is not yet restored.
3. **F5 — stale `BLOC_05_I10_READINESS_ASSESSMENT.md`** carries
   `AUTHORITY = NONE`. It is documentation debt, superseded in practice by
   `BLOC_05_I11_READINESS_ASSESSMENT.md`; it must not be cited as authority.
4. **F6 — I09 R09-21 / R09-22** and the twenty-counterexample table are absent
   repo-wide. Evidence-completeness debt at the I09 checkpoint, carried, not
   waived.
5. **I09-b provider certification** remains open and requires provider evidence;
   it cannot be closed offline.
6. **`B5_I08_UNITS_V1`** remains unresolved. `notional_usd` must continue to be
   emitted as `value = null` with the citation; no consumer may infer USD value.
7. **I17 duplicate collapse** remains deliberately unimplemented at this layer.
   Any aggregation built on I10 output must not assume collapsed prints.

## 6. I11 implementation authorization proposal (proposal only — not authorized)

Prepared by reusing `BLOC_05_I11_READINESS_ASSESSMENT.md` (already committed at
`cd8208ee4a`); this section restates its boundary as an authorization request.
**No I11 code, test, fixture or evidence is created by this record.**

**Objective.** Normalize liquidation prints to the same provider-neutral
contract quality I10 achieved for trades — without ever conflating position
side, execution side, aggressor side or maker/taker role.

**Proposed scope (on approval).**
- One module `normalization/sensors/liquidation.py` plus the minimum
  supporting surface inside `normalization/sensors/`.
- A `T1LiquidationRecord` that carries position side, execution side,
  aggressor side and role as **four separate, independently nullable** fields
  (bloc_05/04 §3.1–3.2), never collapsing them into one "side".
- `aggregation_scope` restricted to the five canonical values of bloc_05/04
  §3.3; long/short aggregates map to **position** side, never to aggressor flow
  (bloc_05/04 §3.4).
- A zero-interval rule: a zero bucket is representable only when coverage is
  verified (bloc_05/04 §3.5); otherwise it must be missing, not zero.
- `liquidation_usd` remains blocked on `B5_I08_UNITS_V1`.

**Proposed test families** (ten, mirroring the I10 shape): provider-neutral
field carriage; side-separation invariance under renaming; scope coherence;
zero-interval honesty; unit preservation; role retention; lineage; native value
preservation; negative-path package custody; determinism.

**Needs provider evidence before any claim:** endpoint scope (event stream vs
interval aggregate), provider side naming, market-wide vs venue-wide coverage
claims, interval completeness, and Deribit role fields.

**Explicitly out of scope:** funding, positioning, open interest, book metrics,
USD notional, duplicate collapse, any network call, any change to I08/I09/I10
sealed artifacts.

**Exit criteria.** All ten families green; scope audit pins `sensors/` to an
exact module set including the new module; negative-path proof; H1-style
historical reproducibility where a prior producer exists; no gate promoted
until independently audited.

**Stop conditions.** Missing provider evidence for any claimed semantic blocks
that claim, not the whole checkpoint — the checkpoint ships with the claim
marked unsupported, exactly as I10 shipped `B5_I08_UNITS_V1`.

## 7. Non-claims and governance state

- Ratification covers **B5-I10 only**.
- `BLOC_05` remains **INCOMPLETE** — I11 … I17 are not built.
- No gate in the eight-gate set is promoted by this record; they remain as
  recorded, with `NOT_YET_EARNED` for anything that depends on I11+.
- `B5-I11+` and `BLOC_06` remain **UNAUTHORIZED** until an implementation
  directive is issued.
- `RESEARCH = FROZEN`. No provider call, no network, no config change.
- `next_checkpoint_authorized = FALSE`. The I11 proposal in §6 is a request, not
  a grant.

This record accepts work already performed. It builds nothing, fixes nothing,
and authorizes nothing beyond itself.
