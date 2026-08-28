# LOWER-FIELD-6 SUMMARY

**TRUE-vs-FALSE loner geometry, multi-sigma recovery ladders, peer rejoin vs
peer catchdown, rank-patch anatomy, health-state harmonization, local
sequences and propagation structure.**

PARENTS: LF5 `8bd8cfbd` · MECH-10 `decf75bc` · POST-MECH10 `805461c9`
VERDICT: see 29_LOWER_FIELD_6_DECISION.md

## 1. Consensus loner classification

Loner events classified by consensus across 5 true peer families
(BEHAVIORAL_10, CORR_60_10, CORR_120_10, STATE, HYBRID_10):

| Class | n | pct |
|-------|---|-----|
| TRUE_MULTI_PEER_LONER (>=3/5 families) | 1957 | 0.795 |
| FALSE_LONER (dominant false family) | 495 | 0.201 |
| AMBIGUOUS | 10 | 0.004 |

The consensus view refines the LF5 single-family estimate (~1 in 5 false):
a meaningful share of isolated-down events is NOT isolated relative to its
historically relevant peers under multiple independent definitions.

## 2. Multi-sigma recovery ladder

Recovery from the shock anchor is a graduated ladder, not a single 1σ gate:
P(reach 0.5σ by 1D) = 0.279; P(reach 1σ by 7D) = 0.344; higher
checkpoints (2σ/3σ) are progressively rarer and later.

## 3. Peer rejoin vs peer catchdown (PRIMARY)

| Path | n | pct |
|------|---|-----|
| ASSET_REJOINS_PEERS | 262 | 0.106 |
| LOCAL_CONTAGION | 348 | 0.141 |
| PERSISTENT_DECOUPLING | 492 | 0.200 |

Both resolution modes exist. The split between rejoin and contagion is the
central descriptive output of LF6; each named class >= 50 events was required.

## 4. PRD harmonization

Canonical PRD (1σ price rule, rank-down at 7D, LF5 PIT universe, bands
26-2000) n = 59 at 7D. Legacy Agent-1 (MECH-8/10, 0.5σ rule, health
universe) and Agent-2 (LF5) counts differ by universe + threshold; resolved
by documentation + canonical universe (14_PRD_DEFINITION_HARMONIZATION.md).

## 5. Reversal primitives

Reversal primitive audit across rank patches (19): see verdicts —
GLOBAL / CONDITIONAL / LOCAL / NULL per coordinate.

## 6. False-loner composition

False loners are structurally different assets: BEHAVIORAL_FALSE events have
median vol_63d ~0.17% and median |ret_1d| ~0.5% vs TRUE_MULTI_PEER_LONER
median vol_63d ~5.4% and median |ret_1d| ~14%. A "2σ event" for a false
loner is a tiny absolute move that its peers matched — isolation is a
low-volatility artifact, not a genuine shock. True loners are genuinely
idiosyncratic high-amplitude events.

## 7. Key caveats

Descriptive only. Peer maps are outcome-free but correlation peers use
reconstructed same-date returns for isolation scoring. Sequence families
require purged FDR validation before promotion. new-low is defined as
signed_fwd{h} < 0 (no intraday low in the PIT panel), so p_new_low equals
p_reversal by construction; treat both as "still below t0 close".
