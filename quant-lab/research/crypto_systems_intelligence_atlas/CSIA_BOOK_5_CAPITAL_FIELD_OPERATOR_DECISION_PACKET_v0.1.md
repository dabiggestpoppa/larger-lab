# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL FIELD OPERATOR DECISION PACKET (D7)

**Document ID:** CSIA-B5-D7-PACKET-001
**Version:** 0.1
**Status:** OPERATOR DECISION PACKET — NO DECISION MADE OR RECOMMENDED
**Gate:** Constitution v0.2 §4.3; D7 OPEN. This packet exists to receive an operator decision; it selects nothing.

**Companion artifacts:**

- `CSIA_BOOK_5_CAPITAL_FIELD_RECONCILIATION_v0.1.md` — historical meanings M-1..M-10; principles P1–P18; stock/flow; transformations; ownership; route/flow
- `CSIA_BOOK_5_ECONOMIC_PRIMITIVE_CANDIDATE_MATRIX_v0.1.md` — candidate primitives and identity gaps
- `CSIA_BOOK_5_DOUBLE_COUNTING_STRESS_MATRIX_v0.1.md` — 10 mandatory scenarios and counting rules
- `CSIA_BOOK_5_BOUNDARY_REVIEW_v0.1.md` — Book 4/5, 5/6, 5/8 fences; amendment candidates

---

# 0. The operator question, verbatim scope

Constitution v0.2 §4.3: Book 5 planning **must begin** with an operator decision, recorded in the Operator Decision Log, on whether existing Capital Field planning artifacts are **absorbed, referenced, or superseded** by CSIA Book 5. The D7 directive additionally asks the operator to determine the *relationship* between Book 5 and the historically deferred Capital Field concept — i.e., which object the name denotes and which authority assignment follows.

**The historical record constrains but does not force any answer.** Attested meanings (reconciliation doc M-1..M-10): a queued content domain ≈ capital plumbing (IACER §C2/R3); a subsystem/lens inside CSIA (IACER, Constitution v0.1 §4.3); the reconciliation-gate subject (Constitution v0.2 §4.3); Bloc 5G "Capital Field synthesis" + exit gate `PASS_CSIA_B5_CAPITAL_FIELD_V1` (roadmap); the Book 5 content that must not leak into Book 4 (frozen `book4_boundary.py`); a forbidden-until-authorized work category (session guard language). No canonical Capital Field schema, plan, or implementation exists.

**Decision required (operator supplies selections):**

```text
D7-SELECT-OPTION:        A | B | C | D | E | (operator's own formulation)
D7-ARTIFACT-DISPOSITION: ABSORBED | REFERENCED | SUPERSEDED   [for historical Capital Field planning text]
D7-5G-NAMING:            KEEP "Capital Field synthesis" as 5G name | RENAME (operator supplies)
D7-EXIT-SEMANTICS:       CONFIRM "exit" = economic-topology state only (descriptive)  [guard, P17]
```

Recommended recording form (per §5.4): a `D7` entry block in `CSIA_OPERATOR_DECISION_LOG.md` citing this packet, the selected option, the artifact disposition, and the exit-semantics confirmation.

---

# 1. OPTION A — CAPITAL FIELD = BOOK 5 ITSELF

**Exact meaning.** "Capital Field" is the canonical name for the entire Book 5 domain (Capital Plumbing and Economic Topology). Historical usage M-1/M-2/M-4/M-6/M-9 all resolve to this. Bloc 5G keeps its roadmap name as a bloc within the domain (or the operator renames it — D7-5G-NAMING).

**Authority:** canonical data authority = Book 5 (blocs 5A–5G) under Books 0–2 doctrine; "Capital Field" becomes a synonym, not an authority holder.

**Canonical vs derived:** Book 5 records are canonical; nothing is added above them.

**Write authority:** Book 5 canonical writes only, evidence-backed per Book 2 (P1).

**Provenance model:** unchanged — Book 2 claim-evidence pairs, §13 provenance fields.

**Temporal semantics:** unchanged — bitemporal per §12; stocks temporally versioned; flows append-only events (P13/P14).

**Double-counting risk:** none added. The stress matrix's counting rules (rule set 1–7) become canonical Book 5 schema requirements.

**Cross-book impact:** Book 4 boundary unchanged (its `book4_boundary.py` wording already calls Book 5 content "capital-field"); Book 1 extension candidates unchanged; Books 6/8 boundaries unchanged.

**Implementation complexity:** lowest of all options — no extra layer, no extra governance object.

**Failure modes:** (i) name ambiguity persists informally (people saying "the Capital Field subsystem" when they mean Book 5 outputs); mitigate by one line in the Book 5 plan defining the synonym; (ii) temptation to treat the domain name as a runtime component — guarded by §35 bloc isolation.

**Migration impact:** none. **Roadmap change:** none. **Constitution amendment:** none. **Books 1–4 amendments:** none.

**Principle stresses:** no P15 risk (no new layer). All of P3–P12 must be enforced by Book 5 schemas themselves (they would otherwise be enforced by a synthesis layer).

---

# 2. OPTION B — CAPITAL FIELD = BLOC 5G SYNTHESIS LAYER

**Exact meaning.** Blocs 5A–5F own canonical economic records; 5G composes them into the derived capital topology — "the Capital Field." Matches roadmap M-5 naming exactly and gives the 5G exit gate (`PASS_CSIA_B5_CAPITAL_FIELD_V1`) its literal referent.

**Authority:** canonical records = 5A–5F; 5G is a **derived composition with no independent canonical authority** (P15). The operator decision would explicitly state: 5G creates no capital facts, only typed compositions of 5A–5F records.

**Canonical vs derived:** 5G = derived, pointer-linked to source records, methodology-carrying.

**Write authority:** 5A–5F write canonical records; 5G writes only derived synthesis records referencing them.

**Provenance model:** synthesis records must carry full pointer lineage to constituent records + composition methodology (§13 "a derived state must point to the facts that produced it").

**Temporal semantics:** synthesis must be replayable at any valid time — composition results are functions of temporally versioned inputs (P13/P14); no "current snapshot" collapse.

**Double-counting risk:** the decisive constraint — if 5A–5F record unclassified balances, 5G inherits every stress-matrix failure. Requires the counting rules to bind blocs 5A–5F *and* the composition layer.

**Cross-book impact:** none on Books 1–4. Book 6 seam sharpens: 5G-derived topology vs Book 6 derived metrics must be delineated (both derived; different purposes — topology composition vs measurement normalization). Book 8 consumes 5G only as derived context.

**Implementation complexity:** moderate — one extra derived layer with lineage obligations.

**Failure modes:** (i) 5G accretes facts "just this once" — hidden authority (P15); mitigation is the operator decision explicitly forbidding 5G canonical writes; (ii) double-counting if composition sums before classifying; (iii) name collision with Option A intuition ("isn't the whole book the Capital Field?") — must be answered in the plan's glossary.

**Migration impact:** none (5G already exists as a bloc). **Roadmap change:** none. **Constitution amendment:** none. **Books 1–4 amendments:** none.

**Principle stresses:** P15 (derived must not become hidden authority) is the central risk; P3–P12 enforced at bloc level; P17/P18 guard 5G outputs.

---

# 3. OPTION C — CAPITAL FIELD = DERIVED READ MODEL ABOVE BOOK 5

**Exact meaning.** Book 5 is canonical economic truth; "Capital Field" names a separate derived projection/read model (a governed view layer) computed from Book 5 records, with no independent authority — a consumer-grade projection (query/aggregate/render surface), distinct from Book 5 itself and from Bloc 5G.

**Authority:** Book 5 holds all canonical authority; the read model holds **zero** write authority over canonical records (P15); its outputs are always marked derived with methodology + lineage.

**Canonical vs derived:** read model = derived, by construction.

**Write authority:** none over canonical data; it may persist its own projections only as reproducible derived artifacts (§29 reproducibility).

**Provenance model:** every projected value traces to canonical record IDs + transformation spec + output version (mirrors Book 4's derived transitive-dependency pattern: derived records point to their ordered derivation inputs).

**Temporal semantics:** projections are parameterized by valid time; replay is mandatory (P13/P14).

**Double-counting risk:** concentrated exactly where summation happens — the read model must enforce stress-matrix rules 1–7 in its aggregation methodology; a read model that aggregates before classifying fails the corpus.

**Cross-book impact:** none on Books 1–4. Book 6 boundary must be restated carefully: Book 6 owns *measurement methods*; a Book 5 read model may not acquire measurement authority — it re-projects canonical facts. Book 8 consumes the read model as a derived surface.

**Implementation complexity:** moderate-high — a new governed artifact class (projections) with reproducibility obligations, introduced during Book 5 or deferred to a later book.

**Failure modes:** (i) two names for near-identical things (read model vs 5G synthesis) — the operator decision must state the relationship (e.g., read model supersedes/contains 5G composition outputs, or 5G is the canonical composition and the read model is its publishable projection); (ii) scope creep into dashboards (Book 9 territory); (iii) hidden authority drift (P15).

**Migration impact:** none for Books 1–5 canonical planning; adds a projection contract to Book 5 planning scope. **Roadmap change:** none strictly; a naming/convention note. **Constitution amendment:** none (§13/§29/§4.4 patterns suffice). **Books 1–4 amendments:** none.

**Principle stresses:** P15 central; P13/P14 (replayable projections); P17/P18 guard projection outputs.

---

# 4. OPTION D — CAPITAL FIELD = SEPARATE FIRST-CLASS SUBSYSTEM

**Exact meaning.** "Capital Field" becomes an independently governed subsystem that Book 5 feeds — its own ontology, records, and authority, parallel to Book 5 rather than inside it. This is the historical IACER-adjacent reading ("a queued, separately planned program").

**Authority:** split — Book 5 canonical records vs Capital Field subsystem authority. **This is the option the anti-absorption rule ("No component silently gains authority over another") was written to police:** the split must be explicit, or one side silently absorbs the other.

**Canonical vs derived:** Capital Field would hold canonical capital semantics *beside* Book 5 — creating two canonical capital truths unless subordinated by decision.

**Write authority:** ambiguous by construction; the operator decision would have to define who writes capital truth (Book 5 or the subsystem) — the packet records that this is unresolved under Option D and cannot be resolved by planning alone.

**Provenance model:** duplicated or bridged; either way an extra reconciliation layer.

**Temporal semantics:** must re-declare Book 1/§12 semantics or inherit them — added surface.

**Double-counting risk:** highest — two capital models with different counting rules can produce conflicting totals; the stress corpus would need to pass twice and reconcile.

**Cross-book impact:** roadmap change required (5G's meaning plus possibly a new book/bloc); Constitution §4.3 wording tension ("CSIA-internal… subsystem" vs an independently governed subsystem outside Book 5) — likely needs a §4.3-adjacent amendment or a recorded boundary assignment; Book 4 boundary consumers (`book4_boundary.py` comments naming Book 5 content "capital-field") change meaning textually without code change; Books 6/8 must choose which capital truth they consume.

**Implementation complexity:** highest; defers Book 5 planning further (the subsystem needs its own plan before Book 5 blocs can finalize their synthesis obligations).

**Failure modes:** parallel authority; duplicate evidence pipelines; conflicting capital-routing semantics — precisely the collision Constitution review CR-04/SG-F predicted ("duplicated evidence pipelines, conflicting capital-routing semantics, or a hostile absorption of one by the other").

**Migration impact:** significant; roadmap v0.1 change required. **Constitution amendment:** possibly (recorded as an operator question, not decided here). **Books 1–4 amendments:** none required, but Book 4 boundary semantics change interpretively.

**Principle stresses:** P15 structurally at risk; P1 risk if the subsystem ever accepts capital claims outside Book 2 doctrine; P3–P12 must be implemented twice or explicitly delegated.

---

# 5. OPTION E (INFORMATIONAL) — FUTURE OPERATOR SURFACE RATHER THAN A DATA MODEL

The directive's Phase 4 lists a fifth reading: "Capital Field as a future operator surface rather than a canonical data model." Recorded for completeness: under this reading the name belongs to a Book 9-style interaction lens (the operator-facing way to *see* capital state), with the data model living entirely in Book 5. This is not a D7 authority assignment — it mostly renames a presentation concern and leaves §4.3's artifact disposition to be answered as in A/B/C. It is listed so the operator can select it or fold it into A/B; the packet makes no comparison ranking between E and the others. Book 9 blocs already include investor surfaces; a "Capital Field" surface would be a Book 9 naming question.

---

# 6. OPTION MATRIX (comparison table — not a recommendation)

| Dimension | A: = Book 5 | B: = 5G synthesis | C: = derived read model | D: = independent subsystem | E: = operator surface |
|---|---|---|---|---|---|
| Canonical capital authority | Book 5 | 5A–5F | Book 5 | split (must be defined) | Book 5 |
| New governance object | none | 5G as derived composition | projection artifact class | full subsystem | none (Book 9 concern) |
| Write authority above canonical | none | none (5G derived-only) | none | ambiguous — must be defined | none |
| P15 hidden-authority risk | none | must be guarded | must be guarded | structural | none |
| Double-counting risk surface | Book 5 schemas | blocs + composition | read-model aggregation | two models to reconcile | Book 5 schemas |
| Roadmap v0.1 change | none | none | naming note | required | none |
| Constitution amendment | none | none | none | possibly §4.3-adjacent | none |
| Books 1–4 amendments | none | none | none | none (interpretive shift) | none |
| Historical-text fit (M-1..M-6) | M-1, M-2, M-4, M-6, M-9 | M-5 (+M-1 lens reading) | M-1 lens reading | IACER queued-program reading | M-1 "lens" reading |
| Migration/deferred-planning cost | none | none | projection contract in Book 5 scope | Book 5 planning delayed | none |
| D8/Book 8 impact | none | consumes 5G | consumes projection | must pick capital truth source | consumes surfaces |
| Failure concentration | schema discipline | composition discipline | aggregation discipline | authority split | presentation |

**Amendment flags, restated:** no option except D raises a possible constitutional amendment; no option requires Books 1–4 amendments; the boundary review's four BOOK_1_EXTENSION_CANDIDATES are orthogonal to the option choice (they are needed under every option).

---

# 7. Structural findings (directive Phase 21 — STRUCTURAL_FINDING)

- SF-1: The program's ratified doctrine already contains everything needed to answer D7's *consequences*: the §4.3 gate supplies the artifact dispositions (absorbed/referenced/superseded), and §19/§19.1 supply the capability/capacity/flow law that any option must implement. What D7 actually decides is **where the name's authority lands** and **how much derived-layer machinery Book 5 planning must carry**.
- SF-2: Historical Capital Field text contains **no schemas, no plans, no implementation** — only scope lists. Therefore ABSORB vs REFERENCED vs SUPERSEDED carries near-zero technical cost under any option; the disposition is a record-keeping act, not a migration.
- SF-3: The only option introducing structural risk is D (parallel authority). A, B, C, and E are compatible with the frozen boundaries without amendment.
- SF-4: The 5G "exit" term requires the descriptive-only guard under every option (P17/P18); the guard is a constraint, not a selection criterion.
- SF-5: Four Book 1 extension candidates (boundary review §6) are required under every option; they are not differentiators and require no amendment now.
- SF-6: The stress matrix's counting rules (rules 1–7) bind Book 5 planning under every option; they are not differentiators either.
- SF-7: No silent winner is embedded in these findings; SF-3 states a *risk asymmetry*, not a selection.

---

# 8. TRADEOFFS summary

- **A** trades naming fidelity (M-5's 5G-specific usage) for maximal simplicity; the 5G bloc name becomes slightly overloaded unless renamed.
- **B** trades a strict derivation discipline at 5G for giving the roadmap's most distinctive bloc its literal name; the program carries one derived layer with lineage obligations.
- **C** trades planning scope growth (a governed projection contract) for a clean canonical/derived split that most literally matches the "lens" language; risks duplication-of-names with 5G.
- **D** trades deferred Book 5 planning and possible constitutional amendment for an independent subsystem; carries the only structural authority risk.
- **E** defers the question into Book 9 naming, but §4.3 still requires the artifact disposition — E does not fully close D7 by itself.

---

# 9. OPERATOR_DECISION_REQUIRED (record decision per §5.4)

The operator is asked to supply, explicitly and verbatim:

```text
D7-SELECT-OPTION:        A | B | C | D | E | operator's own formulation
D7-ARTIFACT-DISPOSITION: ABSORBED | REFERENCED | SUPERSEDED
D7-5G-NAMING:            KEEP | RENAME (operator supplies name)
D7-EXIT-SEMANTICS:       CONFIRM descriptive-only guard
OPTIONAL:                conditions, annotations, or a composite instruction
```

Until that entry exists in `CSIA_OPERATOR_DECISION_LOG.md`:

```text
D7 = OPEN
BOOK_5_PLAN = NOT_STARTED_PENDING_D7
BOOK_5_IMPLEMENTATION = UNAUTHORIZED
LIVE_ACQUISITION = UNAUTHORIZED
```

This packet makes no selection, embeds no default, and grants no authority. No decision is inferred from silence (Operator Decision Log session-integrity rule).
