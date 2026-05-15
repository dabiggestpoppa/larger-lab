# Shared Overlap Channel — SRRS+OPH

> This directory contains the shared observation channel for the
> SRRS+OPH cognitive architecture. Each agent patch writes here
> so other patches can reconcile overlapping observations.

## Files

| File | Purpose |
|------|---------|
| `overlap-log.jsonl` | Append-only log of all agent observations |
| `consensus-state.json` | Current consensus across patches |
| `error-signatures.json` | Compressed error patterns |

## Format

Each line in `overlap-log.jsonl` is a JSON object:

```json
{
  "channel": "twitter-research | github-discovery | ...",
  "timestamp": "2026-05-15T12:00:00Z",
  "overlap_hash": "sha256-partial",
  "observer_patch": "agent-name",
  "data": { ... agent-specific observation ... }
}
```

## Reconciliation Protocol

1. Agent writes observation to overlap-log.jsonl
2. Other agents periodically read the log
3. Matching overlap_hashes = confirmed observation
4. Conflicting observations → reconciliation via priority rules:
   - Data > Inference > Speculation
   - Recent > Stale
   - Higher relevance_score wins

## Usage

No manual editing. Agents write to this channel automatically.
To read: use `reconcile.py` (coming soon) or query directly.