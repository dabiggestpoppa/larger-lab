# MECH-3 OBSERVATION LIMITS (WORKSTREAM N)

**Branch:** `agent/crypto-quant-foundry` · **Checkpoint:** CRYPTO-ALT-MECH-3
**Doctrine:** Observe → Compress → Perturb → Reconstruct → Localize → Formalize.
No gap in this document is filled with narrative. Each claim class is labeled with
its observation layer.

## 1. Observation layers available in DATA-1.1

| Layer | Directly observed | Source |
|---|---|---|
| Global market | total mcap, top500 breadth, dispersion, BTC/ETH returns, dominance, alt share | MARKET_TERRAIN_V2 + computed |
| Chain / ecosystem | per-chain TVL (level, share, 1D/7D/30D change) | CHAIN_FLOW (DefiLlama) |
| Sector | membership, sector mcap, breadth, median returns | SECTOR_MEMBERSHIP/FEATURES (PIT) |
| Rank band | median return/velocity/breadth/mcap-share per band | RANK_BAND_FEATURES |
| Asset | return, rank velocity, mcap share, volume share, vol 30D, is_stablecoin | ASSET_MULTISCALE_FEATURES_V2 |
| Flow (global) | stablecoin total mcap + changes, total DEX volume, fees, revenue | GLOBAL_FLOW (DefiLlama) |
| Perp | perp eligibility flag only (no OI, no funding history) | PERP_ELIGIBILITY |
| Meteora | aggregate asset-level daily TVL proxy only | METEORA_ASSET_DAILY |

## 2. Per-finding observation classification

### CHAIN-LIQUIDITY DECOMPOSITION (WS A)
- Per-chain TVL level / share / changes — **DIRECTLY_OBSERVED** (DefiLlama, AVAILABLE_NEXT_DAY-shifted).
- Native improving-share / velocity / mcap-share / return-breadth — **DIRECTLY_OBSERVED** (computed from PIT feat × chain mapping).
- Global stablecoin / DEX / fees changes — **DIRECTLY_OBSERVED** (global flow).
- Per-chain stablecoin supply — **UNOBSERVED** (only global stablecoin total is available; per-chain split is NOT synthesized).
- Bridge inflows/outflows — **UNOBSERVED** (no bridge dataset in canonical inputs).
- Perp OI / funding — **UNOBSERVED** (perp eligibility flag only).
- Lending TVL, staking flows — **UNOBSERVED**.
- Active addresses / tx activity — **UNOBSERVED**.
- Exchange in/outflows — **UNOBSERVED**.
- Wallet identities / holder cohorts — **UNOBSERVED**.

### PERTURBATION (WS B)
- Ablation deltas on observed series — **DIRECTLY_OBSERVED** (trailing-window residualization is a transform of observed data).
- Whether a link "would survive" under an unobserved substitute — **INDIRECTLY_INFERRED** (only tested substitutes are observed).

### MULTI-VIEW RECONSTRUCTION (WS C)
- Agreement among global/chain/sector/native/rank views — **DIRECTLY_OBSERVED**.
- Sector view for a chain (dominant sector median return) — **INDIRECTLY_INFERRED** (dominance is a same-day cross-sectional argmax; membership is PIT).
- Whether disagreement implies a hidden state vs measurement lag — **UNOBSERVED** (documented as candidate interpretations, not claims).

### REGIME ROUTING FLIP (WS D)
- Conditional correlations under 16 single-condition states — **DIRECTLY_OBSERVED**.
- Two-state interactions — **PARTIALLY_OBSERVED** (preregistered single-state only; interactions deferred).

### CONCENTRATION PIVOT (WS E/F/G)
- Entry/exit event dates from PIT routing states — **DIRECTLY_OBSERVED**.
- Precursor geometry (windows 1-30D) — **DIRECTLY_OBSERVED**.
- "First changed observable" — **INDIRECTLY_INFERRED** (max |z| over the observed precursor set; unobserved channels may move first).
- Route selection mechanism (why a given route is taken) — **UNOBSERVED**; only route-frequency and first-changed-observable statistics are reported.

### PLATEAUS (WS H/I)
- Information plateau (incremental R²) — **DIRECTLY_OBSERVED**.
- Field plateau episodes (P1/P2/P3) — **DIRECTLY_OBSERVED**.
- "What constraint became binding" — **INDIRECTLY_INFERRED** (release-trigger statistics over observed variables only).

### PRIMITIVE AUDIT (WS J)
- Redundancy, materiality, substitution, recurrence statistics — **DIRECTLY_OBSERVED**.
- Primitive "status" as an economic primitive — **INDIRECTLY_INFERRED** (earned only via the fixed classification rule; philosophical claims avoided).

### TOPOLOGY / DYNAMICS / MORPHISM (WS K/L/M)
- Graph density, components, articulation points — **DIRECTLY_OBSERVED**.
- Transition-matrix stability, basin persistence, hysteresis chi-square — **DIRECTLY_OBSERVED**.
- "Attractor-like" language — **INDIRECTLY_INFERRED** (descriptive; no mechanism claim).
- Morphism recurrence across cycles — **DIRECTLY_OBSERVED** (counts); why some morphisms recur — **UNOBSERVED**.

## 3. Global observation gaps (permanently or temporarily unavailable)

- Private OTC flows, hidden market-maker inventory, incomplete wallet identity,
  private treasury decisions, untracked off-chain capital, unpublished
  institutional positioning — **UNOBSERVED** in every workstream.
- Any statement about these is speculation and is excluded from findings.

## 4. Data-quality caveats (carried from MECH-1/2)

- DefiLlama flows follow `AVAILABLE_NEXT_DAY` timing; all flow features are shifted
  before use. No same-day look-ahead.
- Chain-name bridge (CMC platform → DefiLlama display) is a fixed engineering alias;
  chains absent from either source are excluded per-coverage rules, never inferred.
- Meteora pool-level history remains DEFERRED; only the aggregate asset-level proxy
  is used (and it failed to support relationships in MECH-1 — carried forward).
- Source-gap dates (79) are excluded by the truth lock; no silent bridging.
- Cross-sectional rows are never treated as IID; block bootstrap / permutation
  surrogates / cluster counts are used throughout.

## 5. What this checkpoint can and cannot say

- CAN: which observed chain-liquidity coordinates are redundant vs distinct;
  which observed links survive controlled removal; where routing flips under
  observed states; the observed precursor geometry of concentration entry/exit;
  observed release-route frequencies; information/field plateaus on observed
  variables; graph/dynamical/morphism readiness statistics.
- CANNOT: any claim about unobserved channels (bridges, perp OI, wallets, OTC);
  any causal claim beyond the assigned ladder level (max L3, per prereg §20);
  any strategy implication.
