# Chapter 17.5 — Reading Capability Receipts

## Mission

Teach operators how to interpret a Capability Receipt as the canonical evidence-backed explanation of what QCAE learned, what it approved/rejected/recommended, and what remains conditional.

## Receipt Sections

Operators should expect:

```text
capability/contract identity
candidate/source revision
acquisition form
verified behavior
failed/unproven behavior
license/security state
proving evidence
quant evidence if relevant
integration scope
known assumptions/limitations
authority state
rollback/exit path
revalidation triggers
current lifecycle status
```

## Reading Priority

Read in this order:

1. capability/contract scope;
2. current lifecycle/authority state;
3. hard failures/limitations;
4. verified evidence;
5. acquisition rationale;
6. monitoring/revalidation conditions.

Do not begin with headline recommendation alone.

## Scope Discipline

A receipt proves only the reviewed revision, contract, environment, and evidence scope. It does not imply all later upstream versions or adjacent capabilities are approved.

## Rejection Receipts

Rejected candidates are equally valuable. Their receipts explain why the path failed and when re-evaluation might become rational.

## Invariants

1. Receipts summarize canonical evidence, not chat opinion.
2. Scope/revision/authority are read before recommendation.
3. Known limitations remain first-class.
4. Rejected receipts are durable knowledge.
5. A receipt never silently generalizes beyond its contract/revision.

## Exit Criteria

An operator can tell exactly what QCAE knows, what it does not know, and what permission actually exists from the receipt alone.
