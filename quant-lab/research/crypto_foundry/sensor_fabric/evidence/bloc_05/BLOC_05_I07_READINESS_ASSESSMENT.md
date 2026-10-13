# SENSOR-B5-I07 — READINESS ASSESSMENT (READ-ONLY)

> Reconstructed 2026-10-13 by the operator via the SENSOR-B5-I06R1 directive
> (section 10), after I06 ratification review. **READ-ONLY:** no I07 code, no
> I07 tests, no I07 configuration, no revision-mode semantics, no
> placeholders in `src/`, no implementation authority granted. This document
> is a reconstruction of the *frozen* I07 checkpoint and of what already
> exists upstream of it; producing it grants nothing.
> Verification base: HEAD `06fdcde16ae2194d80d3700adce7ed42263d984c`
> (= required starting HEAD = remote), tracked tree clean, all seven frozen
> `bloc_05/` documents byte-identical to the I06 base
> `32a89743656adb638cdaf688b62be505202f1876`.
> Verdict: **I07_READINESS = MEASURED_AND_REPORTED**;
> `next_checkpoint_authorized` remains **FALSE**; **B5-I07+ = UNAUTHORIZED**.

---

## 1. Frozen checkpoint identity

```text
CHECKPOINT_ID  : SENSOR-B5-I07
FROZEN_TITLE   : "revision policies / AS_KNOWN_THEN handling"
                 (bloc_05/06 §19 lines 467-468 — staged implementation commits)
                 "revision policies / AS_KNOWN_THEN"
                 (bloc_05/07 §10 line 415 — frozen future implementation
                 sequence; same checkpoint, two frozen documents)
PURPOSE (as frozen): own the research-revision-policy surface — which
                 historical revision is selected under a declared mode at an
                 explicit replay cutoff — so that a replay query never
                 silently inherits a later correction (bloc_05/02 §11, §12;
                 07 F11).
SEQUENCE         : immediately after SENSOR-B5-I06, before I08 (06 §19,
                 07 §10 — word-identical sequences).
STATUS_NOTE      : like I06 before it, the plan enumerates NO separate I07
                 module list. 02 §17 freezes `revision_policy.py` and
                 `revision_policies.yaml` into the time package, and both
                 were delivered by I05 (see §3). The actual I07 scope delta
                 must therefore be adjudicated by the operator at directive
                 time — it may not be inferred by an agent from the staged
                 title alone.
```

## 2. Governing clauses (frozen authority, read not assumed)

| clause | obligation bearing on I07 |
|---|---|
| 06 §19 L467 / 07 §10 L415 | the checkpoint's frozen title itself |
| 02 §10 | historical revisions: `source_revision_id`, `normalization_generation`, `supersedes_t1_record_id`, `revision_status` (six frozen statuses); "no in-place overwrite of prior T1 generation" |
| 02 §11 | six research revision modes; prose defined for **two** only (`AS_KNOWN_THEN`, `LATEST_VERIFIED`); every research output must record the mode used |
| 02 §12 | provider-correction leakage: a 2022 replay must not use a 2025 correction under `AS_KNOWN_THEN`; `PIT_REVISION_UNCERTAIN` when the original is unavailable |
| 02 §15(3)/(4) | strict replay requires defensible market availability **and** a revision policy compatible with the replay cutoff |
| 02 §17 | required modules include `revision_policy.py` + `revision_policies.yaml` (both already frozen into I05) |
| 06 §1 G7 | duplicates/revisions: revisions append and stay queryable; `AS_KNOWN_THEN` differs from `LATEST_VERIFIED` where appropriate; hard IDs may collapse, soft only flag |
| 06 §13 | frozen timestamp/replay test scenarios, incl. "late 2025 correction of a 2022 value does not enter 2022 `AS_KNOWN_THEN` replay; latest retrospective mode may select it explicitly" |
| 06 §14 | six frozen duplicate/revision test scenarios (identical REST+archive event, live+archive, soft fingerprint, changed source bytes, provider-corrected event, normalization rebuild) |
| 06 §15 | property invariants touching revision/replay (no cross-venue dedupe; deterministic generation checksums) |
| 07 F11 | revision mode is explicit; future corrections cannot leak into past `AS_KNOWN_THEN` state |
| 07 F28 / F29 | revisions append; T1 generations immutable once published |
| 05 §9 | revision model: `T1RevisionChain` (`original_t1_record_id`, `revised_t1_record_id`, `revision_reason`, `first_known_at`, `source_revision_ref`); revision never deletes original |
| 05 §18 | canonical query modes must require an explicit `revision_mode` (strict default `ERROR_ON_AMBIGUITY` or `AS_KNOWN_THEN` when replaying; "do not silently select latest corrections") |
| 05 §19 / 07 F30 | the query layer — not a notebook — applies identity, generation, revision mode, quality filters and replay eligibility |
| 04 (bloc_04/05 §3) | pre-Bloc-5 handoff: raw-lake revision resolution modes + "Bloc 5 may build a PIT revision resolver from these facts" |

## 3. Existing I05 revision capabilities (accepted, sealed, do not rebuild)

Measured at this HEAD (`git diff 32a897436 -- quant-lab/src` empty):

| capability | state |
|---|---|
| `RevisionMode` vocabulary | six frozen members: `AS_KNOWN_THEN`, `LATEST_VERIFIED`, `FIRST_SEEN`, `EXACT_REVISION`, `ALL_REVISIONS`, `ERROR_ON_AMBIGUITY` |
| `select_revisions(revisions, policy, replay_cutoff)` | pure, cutoff-explicit; **two modes implemented** (AS_KNOWN_THEN, LATEST_VERIFIED); the other four raise typed `UnsupportedRevisionMode` (`revision_policy.py:249`) |
| `revision_policies.yaml` | covers **exactly the six** modes; `definition` is prose for the two defined modes and `null` for the other four, with `source: bloc_05/02 section 11 (named; no frozen definition)`; a missing/unknown/duplicate mode is refused at parse time |
| leakage behavior | `AS_KNOWN_THEN` at a cutoff before the correction's `known_from` excludes it and stays `pit_safe`; `LATEST_VERIFIED` selects the later record with `pit_safe=False` |
| gate coupling | `assess_replay_eligibility` applies 02 §15(4) through the supplied `RevisionSelection` (`pit_uncertain` → `BLOCKED_REVISION`; not-PIT-safe → `RETROSPECTIVE_ONLY`) |
| tests / evidence | `test_b5_i05_revision_policy.py` = 28 tests; evidence `revision_*` rows in `bloc_05_time_validation.json` (6 rows); all green in the sealed 219 I05 suite re-run this session |
| I06 additions | none to revision semantics. I06's RS-08/RS-09 rows and the `BLOC_05_I06D1_DECISION_PACKAGE.md` §5 interface contract only *consume* `select_revisions`; `select_revisions` is not redefined anywhere |

## 4. Remaining I07 obligations (reconstructed)

```text
O1 FROZEN, INCOMPLETE SEMANTICS : four of the six declared modes
   (FIRST_SEEN, EXACT_REVISION, ALL_REVISIONS, ERROR_ON_AMBIGUITY) are named
   in 02 §11 and 07 F11 but carry NO frozen prose. Their executable semantics
   are MISSING AUTHORITY, not a pending coding task.
O2 FROZEN, SATISFIED             : AS_KNOWN_THEN handling itself — leakage
   prevention at an explicit cutoff — already exists and is accepted (I05)
   and was re-executed under I06 (RS-08).
O3 FROZEN, UNDELIVERED SURFACE  : 05 §18 canonical query modes and 05 §19 /
   F30 query-boundary application of `revision_mode`. The query surface does
   not exist yet; its natural owner in the frozen sequence is I19 (canonical
   T1 query + strict research/replay filters), and 06 §19/07 §10 say so.
O4 FROZEN, OUT OF I07           : revision persistence / supersession chain
   (`T1RevisionChain`), duplicate taxonomy and dedupe decisions belong to
   I17 (duplicate/revision engine); row-level T1 writing belongs to I16/I18.
O5 NO MODULE LIST               : the plan freezes no I07 module beyond what
   02 §17 already gave I05; there is nothing new to create by default.
```

**Where I07 differs from I05 and from I17 (explicit partition):**

```text
I05 (accepted)  : revision RECORD model + selection over two modes + gate
                  coupling, at the library boundary (no storage, no query).
I07 (frozen)    : the RESEARCH REVISION-POLICY layer itself — executable
                  semantics for the still-undefined modes (only if the
                  operator supplies definitions) and any AS_KNOWN_THEN
                  handling not already accepted. It is a policy layer, not
                  a store and not a query filter.
I17 (frozen)    : duplicate/revision ENGINE — chains, hard/soft dedupe
                  classes (07 §7), append-only revisions (F28) over durable
                  T1 records.
I19 (frozen)    : canonical T1 query + strict research/replay filters —
                  the place where a chosen revision mode and a replay
                  cutoff are actually APPLIED to rows.
```

Ownership rule applied here: **where a rule belongs to I17, it stays with
I17** (chain persistence, dedupe strength classes, generation immutability at
storage level); **where a rule belongs to I19, it stays with I19** (mode
selection applied at query time, cutoff filtering, and the I06-carried
condition that rows whose `market_available_at` is strictly after the replay
cutoff must be excluded).

## 5. The four undefined modes — explicit report (no definitions invented)

```text
FIRST_SEEN        : named in 02 §11, 07 F11, 05 §18 (default list) — NO frozen prose.
EXACT_REVISION    : named likewise — NO frozen prose.
ALL_REVISIONS     : named likewise — NO frozen prose.
ERROR_ON_AMBIGUITY: named likewise; 05 §18 recommends it as a strict default
                    and bloc_04/05 §3 names it as the raw-lake default — but
                    no Bloc 5 selection semantics are frozen for it either.
```

Consequences recorded rather than resolved:

1. Defining any of them would be **new semantics under a frozen plan**, i.e.
   an operator decision (same class as the I06 confidence vocabulary, M1).
2. The Bloc 4 storage layer carries a *different* frozen resolution vocabulary
   (`ERROR_ON_AMBIGUITY`, `ALL`, `FIRST_SEEN`, `LATEST_SEEN`, `EXACT_REVISION`,
   `PROVIDER_DECLARED_CANONICAL` — `bloc_04/05 §3`, consumed by
   `storage/revisions.py`). Names collide *partially* with Bloc 5's
   `RevisionMode` and mean different things at different layers. Importing
   Bloc 4 prose into Bloc 5's four undefined modes would be a cross-bloc
   semantic transfer and is **not authorized** by anything in `bloc_05/`.
3. Until definitions exist, the accepted behavior stands: the catalog
   refuses a `definition` for those four and `select_revisions` raises
   `UnsupportedRevisionMode` (fail-closed, measured this session).

## 6. Required modules / configurations IF FROZEN

```text
NEW MODULES      : none named by the plan for I07 (02 §17's time modules and
                   both configs were delivered by I05).
EXISTING MODULES : normalization/time/revision_policy.py, replay_gate.py
                   (sealed, I05).
CONFIGURATIONS   : config/crypto_sensor_fabric/revision_policies.yaml (six
                   modes, two defined) — frozen schema from 02 §11/§17.
```

## 7. Test contracts and evidence artifacts

```text
TEST CONTRACTS (frozen):
  06 §14  six duplicate/revision scenarios (two of the six — provider-corrected
          event, normalization rebuild — are revision-policy cases; the rest
          exercise duplicate handling and therefore also I17).
  06 §13  late-correction / AS_KNOWN_THEN + latest-retrospective pair.
  06 §15 property items: no cross-venue dedupe; deterministic generation
          checksums.
  existing: test_b5_i05_revision_policy.py (28) inside the sealed 219.

EVIDENCE ARTIFACTS (06 §17):
  bloc_05_duplicate_revision_validation.json   REQUIRED BY THE PLAN, ABSENT;
          the plan assigns it to NO checkpoint — likely I17, but that
          assignment is not written anywhere, so it is reported as MISSING
          AUTHORITY rather than assumed (see §8, R5).
  bloc_05_replay_safety_validation.json        produced and ratified at I06.
  bloc_05_time_validation.json                 sealed I05 evidence.
  bloc_05_acceptance_summary.md                06 §17/§23 → I22/I23.
```

## 8. Missing-authority register for I07

| ID | missing authority | why | who resolves it | if ignored |
|---|---|---|---|---|
| R1 | executable semantics for `FIRST_SEEN`, `EXACT_REVISION`, `ALL_REVISIONS`, `ERROR_ON_AMBIGUITY` | 02 §11 names them, defines none | operator decision (explicit definitions or an explicit "remain refused" ruling) | inventing them = authoring frozen semantics an agent may not choose |
| R2 | scope-delta confirmation for I07 | 02 §17 froze `revision_policy.py` into I05; the plan has no I07 module list | operator clarification at I07 directive time | risk of editing sealed I05 files |
| R3 | query-time application of `revision_mode` + replay cutoff | 05 §18/§19, F30 assign it to the query layer; that layer is frozen to I19 | I19 (or an explicit reassignment) | duplicating I19, or an ad-hoc filter outside the canonical boundary |
| R4 | persistence of revision chains (`T1RevisionChain`) | 05 §9 model exists as a schema only | I17 | building a second revision store |
| R5 | ownership of `bloc_05_duplicate_revision_validation.json` | named in 06 §17, assigned to no checkpoint | operator | evidence produced under the wrong checkpoint, or double-produced |
| R6 | confidence vocabulary (M1, Option A) and real-provider latency/rows (M3/M4) | carried open from I06D1/I06; unrelated to revision policy but blocking for real data | operator + provider documents (`BLOC_05_I06_PROVIDER_DOCUMENTATION_COLLECTION_BRIEF.md`) | fabricated confidence ranking or provider latency |
| R7 | I19 cutoff precondition from I06 (RS-04) | `BLOC_05_I06_IMPLEMENTATION_EVIDENCE.md` §4 hands it downstream | I19 | a replay answer that silently shows rows unavailable at the cutoff |

## 9. Stop conditions (verbatim scope limits for any future I07 directive)

* `next_checkpoint_authorized = FALSE`; **B5-I07 = UNAUTHORIZED** — this
  document creates no implementation authority.
* Do not invent semantics for the four undefined revision modes (R1).
* Do not build a revision store, supersession chain or duplicate engine (I17).
* Do not apply revision/cutoff filters at query time (I19), and do not
  restate the I06 RS-04 boundary as a working capability.
* Do not modify I01–I06 code, tests, sealed evidence or the frozen plan.
* Do not promote any program gate; `REPLAY_SAFETY_GATE`,
  `DUPLICATE_REVISION_GATE` and all others stay `NOT_YET_EARNED`.
* Do not import Bloc 4's resolution vocabulary as Bloc 5 definitions without
  an explicit operator decision (§5).
* RESEARCH = FROZEN; no real-provider rows, no confidence vocabulary.

## 10. Terminal status and recommendation

```text
B5-I01 .. B5-I06 = OPERATOR_ACCEPTED      (I06 via this directive, §172)
BLOC_05          = INCOMPLETE
I07_READINESS    = MEASURED_AND_REPORTED (this document; grants nothing)
IDENTITY_GATE / TIME_GATE / SEMANTIC_GATE / UNIT_GATE / LINEAGE_GATE /
DUPLICATE_REVISION_GATE / REPLAY_SAFETY_GATE / GOLDEN_T0_T1_GATE
                 = NOT_YET_EARNED
next_checkpoint_authorized = FALSE
B5-I07+          = UNAUTHORIZED
BLOC_06          = UNAUTHORIZED
RESEARCH         = FROZEN
```

recommended_next = **OPERATOR: (1) rule on the four undefined revision modes
(R1) or confirm they remain refused, (2) confirm I07's scope delta (R2) and
the owner of `bloc_05_duplicate_revision_validation.json` (R5), (3) then
issue an I07 implementation directive if — and only if — both are answered
in it. HARD STOP after push and report.**

*End of I07 readiness reconstruction (read-only).*
