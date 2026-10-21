# Chapter 17.6 — Approving Integrations

## Mission

Define the operator decision point between a proven acquisition recommendation and an authorized integration into protected Quant Lab systems.

## Approval Packet

QCAE should present:

```text
capability/contract
selected acquisition form
proving/quant status
license/security status
integration interface
files/services/dependencies affected
migration/shadow plan
rollback plan
monitoring/revalidation plan
known risks
requested authority scope
```

## Approval Scope

Approval must name the allowed action and scope. Examples:

- generate integration patch;
- merge into protected branch;
- deploy to research environment;
- enable paper simulation;
- enable production service use.

These are distinct decisions.

## Shadow First

Material replacements should prefer shadow/parallel operation and acceptance criteria before canonical cutover where practical.

## Trading Boundary

Approval to integrate research code or paper-trading capability is not live capital authority. Trading authority remains separately governed.

## Invariants

1. Proven recommendation does not equal approval.
2. Approval scope/action is explicit.
3. Migration and rollback accompany material integrations.
4. Shadow validation is preferred for replacements.
5. Research/paper integration never implies live capital authority.

## Exit Criteria

Operators can approve useful integration without granting broader or irreversible authority than intended.
