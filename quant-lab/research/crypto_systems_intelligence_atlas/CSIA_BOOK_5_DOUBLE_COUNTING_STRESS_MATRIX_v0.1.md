# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — DOUBLE-COUNTING STRESS MATRIX (D7 RECONNAISSANCE)

**Document ID:** CSIA-B5-D7-DCM-001
**Version:** 0.1
**Status:** MANDATORY STRESS ANALYSIS — NOT A DECISION — NOT A BOOK 5 PLAN
**Gate:** D7 OPEN. This matrix constrains whichever reconciliation option the operator selects; it approves no model.

---

# 0. Purpose and theorem

Directive Phase 9 mandates ten double-counting stress scenarios. The finding, stated once and then applied per scenario:

**D7 must not approve a model that structurally assumes every balance is additive.**
Any "Capital Field" semantics that sums balances across representations, claims, and liabilities counts the same economic principal multiple times. Gross exposure ≠ economic principal ≠ net exposure. The ten scenarios below are the accepted corpus for adversarial testing of Book 5 models later; they are recorded now so the D7 options can be evaluated against the counting failure modes.

Definitions used (candidate semantics, consistent with §6 of the reconciliation document):

- **economic principal** — the underlying asset value originally at stake (the thing that must be counted once);
- **representation** — a chain-local or wrapper form of a claim (realization or claim token);
- **claim / liability** — who is owed what by whom;
- **gross exposure** — the sum of positions that gain/lose from a risk, regardless of offset;
- **net exposure** — gross minus offsetting positions;
- **naive TVL-style summation** — adding balances without claim/liability classification.

---

# 1. The ten mandatory scenarios

## 1.1 USDC deposited into Aave

- Economic principal: 1,000 USDC held by Alice.
- Representations: aUSDC (deposit receipt claim).
- Claim/liability: Alice holds a supply claim; the market owes withdrawal; borrowers owe the market.
- Gross exposure: Alice = 1,000 (supply claim); market gross = deposits + loans.
- Net exposure: net of debt, the market's net position is ~0 plus reserves.
- **Where naive summation double-counts:** counting "USDC in Aave" (Alice's balance) *and* Alice's aUSDC as value, or counting supplied capital and outstanding loans as two pools of capital. Supplied 1,000 + borrowed 800 = 1,800 is false principal; it is 1,000 principal + 800 redeployed with 800 liability.

## 1.2 USDC borrowed and deposited elsewhere

- Economic principal: the original 1,000 USDC.
- Representations: Alice's deposit claim; Bob's borrowed ETH; Bob's new deposit of borrowed USDC in market B.
- Claim/liability: Bob owes market A; market B owes Bob.
- Gross exposure: Alice 1,000; Bob's positions on both sides; market B shows 800 "TVL" that traces to the same principal.
- **Double-counts:** chain-aggregated TVL counts the same USDC principal in market A *and* market B. Without a transformation/re-deposit ledger, "total capital across DeFi" is inflated by every recursive deposit loop.

## 1.3 ETH → stETH

- Economic principal: 10 ETH.
- Representations: stETH (liquid staking claim).
- Claim/liability: protocol owes stETH redemption; validator set holds the ETH as bonded stake.
- Gross exposure: Alice 10 ETH-equivalent via stETH; protocol redemption liability 10.
- **Double-counts:** counting ETH staked (validator side) + stETH supply (holder side) as 20 ETH of "capital in staking." Principal is 10; the second leg is a liability, not capital.

## 1.4 stETH → restaking layer

- Economic principal: still the original 10 ETH.
- Representations: stETH → restaked receipt (strategy/LST claim on the stETH claim).
- Claim/liability: restaking layer owes the receipt; AVS slashing liabilities stack on top.
- **Double-counts:** the canonical error — summing ETH (consensus stake) + stETH (LST supply) + restaked receipt (restaking TVL) across protocol dashboards. Three representations, one principal. Second-order collateral (§19.2) multiplies this error class.

## 1.5 LP tokens collateralized in a lending market

- Economic principal: the pool reserves backing the LP token (say 1,000 USDC-equivalent).
- Representations: LP token; its use as loan collateral; borrow against it.
- Claim/liability: pool owes LP; borrower owes lending market; LP token is encumbered.
- **Double-counts:** pool TVL + lending-market collateral value both report the same principal; the borrowed amount against it creates a third sighting. Encumbrance (collateralization) must be a typed relation, not an additive balance.

## 1.6 Bridged stablecoin with canonical + wrapped representations

- Economic principal: 1,000 canonical stablecoins locked in canonical-bridge escrow.
- Representations: escrow balance (canonical chain) + wrapped realization (destination chain).
- Claim/liability: bridge owes redemption of wrapped to canonical holders.
- **Double-counts:** canonical supply + wrapped supply summed as "total stablecoin supply" counts 1,000 twice. Stablecoin supply records (primitive #13) must be canonical-side vs realization-side with explicit liability links; cross-realization aggregation is derived-only (INV-1C-7 pattern).

## 1.7 Vault token representing underlying assets

- Economic principal: 500 USDC deposited into a yield vault.
- Representations: vault share token.
- Claim/liability: vault owes share redemption; strategy may itself deposit into lending (→ scenario 1.2 recursion).
- **Double-counts:** vault AUM + underlying strategy deposits; or user net-worth summing wallet USDC-less-but-share-holding as both "in vault" and the strategy's "TVL" simultaneously.

## 1.8 Perp collateral supporting notional exposure

- Economic principal: 100 USDC margin.
- Representations: margin balance; open notional 1,000.
- Claim/liability: trader owes/owns PnL; venue/counterparty pool absorbs the other side.
- **Double-counts:** adding open interest or notional (1,000) to spot capital (100) as if both were principal. Notional is exposure, not capital (P12). Also: both sides of a trade counted as capital (trader's margin + counterparty pool backing the same position set).

## 1.9 RWA token representing an off-chain treasury claim

- Economic principal: off-chain treasury bill held by SPV.
- Representations: on-chain RWA token.
- Claim/liability: token holders hold claim on SPV; SPV holds the T-bill; custodian holds custody.
- **Double-counts:** counting on-chain token "market cap" and the off-chain asset value as separate capital; or counting the T-bill inside the issuer's treasury *and* the token supply. On-chain token supply ≠ off-chain asset value without redemption evidence (P9-adjacent; directive Phase 17 rule).

## 1.10 Rehypothecated collateral

- Economic principal: collateral posted by Alice, re-used as collateral by venue/protocol.
- Representations: Alice's original margin; venue's re-pledge of the same asset to a third party.
- Claim/liability: venue owes Alice; third party has a claim on the re-pledged asset.
- **Double-counts:** every re-pledge hop adds another sighting of the same principal in "total collateral" statistics. CEX attestation gaps make the true encumbrance chain frequently UNKNOWN — must stay UNKNOWN (P16), not assumed unencumbered.

---

# 2. Structural rules the stress corpus forces (recorded for D7 consequence analysis)

1. **No model may present a scalar "total capital" without a claim/liability classification and a methodology ID.** Naive TVL-style summation fails scenarios 1.1, 1.2, 1.4, 1.6, 1.7, 1.8, 1.10 outright.
2. **Representations must be linked, not summed.** Canonical asset ↔ realization ↔ claim token edges must exist (primitives #13, #20) so consumers can collapse to principal as a *derived* view.
3. **Liabilities are records, not negative capital.** Debt (1.1, 1.2), bridge liability (1.6), protocol liability (1.3, 1.4, 1.7), rehypothecation claims (1.10) are typed records; netting is derived.
4. **Exposure quantities (notional, OI) never enter principal sums** (1.8, P12).
5. **Off-chain claims require redemption-path evidence before value equivalence** (1.9); absent evidence → UNKNOWN equivalence, not assumed equality.
6. **Recursion loops must be traceable** (1.2, 1.7): a re-deposit is a transformation referencing its input claim; aggregation over a traced cycle must either de-duplicate or report UNKNOWN, never silently multiply.
7. **Encumbrance is a typed state** (1.5, 1.10): the same asset can back multiple claims; "available" vs "pledged" are different stocks.

---

# 3. Per-option consequence (summary; full option analysis in the decision packet)

- **Option A (Capital Field = Book 5):** counting discipline is a Book 5 schema requirement from day one; the stress corpus becomes canonical Book 5 adversarial tests. Risk: none specific.
- **Option B (Capital Field = 5G synthesis):** synthesis must consume the classified records; if blocs 5A–5F record unclassified balances, 5G inherits the double-counting. Risk: correctness of the whole depends on the strictest bloc discipline.
- **Option C (derived read model):** the read model is where summation would happen; rules 1–7 above must be enforced in the read model's methodology, with pointer lineage to canonical records. Risk: a derived layer that aggregates before classifying.
- **Option D (independent subsystem):** worst case — two capital models with different counting rules producing conflicting totals; requires reconciliation authority that D7 would have to define.

---

# 4. Directive alignment

Answers Phase 9 (all 10 scenarios with economic principal / representation / claim-liability / gross / net / double-count location) and Phase 7's aggregation rule. Feeds the pre-decision review checks #3, #4, #5, #6, #7, #8. No winner selected anywhere in this document.
