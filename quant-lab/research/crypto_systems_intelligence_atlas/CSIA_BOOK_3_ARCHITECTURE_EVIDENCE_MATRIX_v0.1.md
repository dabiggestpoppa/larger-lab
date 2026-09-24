# CSIA Book 3 — Architecture Evidence Matrix v0.1

**MODE = PLANNING ONLY**
**RULE = no Book 3 fact bypasses Book 2**

Every architecture dossier field is populated only from a canonical Book 2 claim
with evidence refs, claim family, authority resolution, valid time, and observed
time. A source, vendor page, RPC result, or chain name without a Book 2 claim is not
an architecture fact.

## Claim-family matrix

| Architecture claim family | Preferred evidence | Book 2 binding | Required corroboration posture | Known planning gap |
|---|---|---|---|---|
| NETWORK IDENTITY | Genesis/config, deployed chain state, official technical specification, deployment manifest | `CHAIN_ARCHITECTURE` or evidence-specific family; source × family × valid time | Independent official specification plus deployed state or genesis evidence; identity ambiguity remains explicit | No universal anchor priority until D3-5 |
| CONSENSUS | Implementation source, protocol specification, deployed validator/client behavior, activation state | `CHAIN_ARCHITECTURE`, `SECURITY_EVENT`, or `GOVERNANCE_EXECUTION` as appropriate | Specification and deployed behavior must agree; implementation and observation cannot be conflated | Finality remains separate from consensus |
| EXECUTION MODEL | Runtime/VM implementation, official technical specification, deployed state, transaction execution evidence | `CHAIN_ARCHITECTURE` | Runtime and deployed behavior; no EVM assumption | Family-native runtime taxonomy needs admission |
| STATE MODEL | Ledger schema, state transition specification, deployed state, migration/upgrade state | `CHAIN_ARCHITECTURE` | Specification plus observed deployed state; historical state remains queryable | Book 1 object coverage may need family extension |
| FINALITY MODEL | Protocol finality specification, validator/client evidence, confirmation/finality state | `CHAIN_ARCHITECTURE` or `SECURITY_EVENT` | Must identify the exact semantic claim; consensus alone is insufficient | No common finality enum |
| DATA AVAILABILITY | DA specification, availability proof/state, provider deployment, storage/retention evidence | `CHAIN_ARCHITECTURE`, `SECURITY_EVENT` | Separate DA from execution and settlement | Provider identity and guarantees vary by family |
| SETTLEMENT MODEL | Settlement specification, bridge/rollup state, finality/settlement evidence | `CHAIN_ARCHITECTURE` | Settlement relation is explicit and independently evidenced | Settlement and security may be distinct |
| VALIDATOR/PARTICIPANT | Validator set, participant registry, staking/delegation state, node configuration | `CHAIN_ARCHITECTURE` or `GOVERNANCE_EXECUTION` | Participant role is not consensus proof by itself | Permissioned and non-validator systems need native values |
| GOVERNANCE | Governance proposal, vote, execution, multisig/authority state, upgrade activation | `GOVERNANCE_EXECUTION` or `GOVERNANCE_PROPOSAL` | Proposal, decision, and execution are separate claims | Governance entities differ by family |
| UPGRADE | Release specification, governance execution, runtime/protocol activation, deployed version state | `GOVERNANCE_EXECUTION`, `CHAIN_ARCHITECTURE` | Planned upgrade is not active upgrade; activation and deployment evidence required | Historical transitions need temporal registry |
| INTEROPERABILITY | Protocol state, channel/route state, bridge/messaging deployment, transaction evidence | `INTEGRATION` or `CHAIN_ARCHITECTURE` | Messaging does not imply shared security or shared identity | Cross-chain representation is often multi-hop |
| NATIVE ASSET | Native issuance/genesis state, chain specification, ledger state, asset contract/module/account state | `MARKET_DATA` or `CHAIN_ARCHITECTURE` | Economic asset identity and realization are separate claims; no ticker-only inference | Custodian and migration history |
| SECURITY MODEL | Validator/committee configuration, consensus evidence, fraud/validity proof or shared-security relationship | `SECURITY_EVENT` or `CHAIN_ARCHITECTURE` | Security provider and execution domain remain distinct | Security terminology differs by family |
| NETWORK CHANGE | Fork/upgrade/migration/genesis/restart record, governance action, deployed state | `CHAIN_ARCHITECTURE` and `GOVERNANCE_EXECUTION` | Old truth is retained; new current state is separately evidenced | Identity doctrine requires operator decisions |

## Evidence custody rules

- Every field records `source_claim_refs`, valid time, and observed time.
- Evidence is bound to the architecture claim, not merely to a network name.
- Conflicting sources create a contested claim; they do not silently merge.
- Unknown architecture values remain `UNKNOWN` until a Book 2 claim reaches the required
  authority and corroboration state.
- A Book 3 planning document is not itself runtime evidence.

## Gate result

```text
ARCHITECTURE_EVIDENCE_MATRIX = COMPLETE_FOR_REVIEW
BOOK_3_FACTS_BYPASSING_BOOK_2 = 0
LIVE_ACQUISITION_AUTHORITY = FALSE
```
