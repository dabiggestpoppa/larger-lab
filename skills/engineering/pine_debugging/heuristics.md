# Heuristics — Pine State Machine Debugging

## State Variable Rules

1. `var` variables persist across bars — use for inter-bar state
2. `varip` variables persist within a bar — use for intra-bar state
3. Never reset `var` variables unconditionally (resets every bar)
4. Always use explicit initialization: `var string state = "INIT"`

## Debugging Checklist

- [ ] All `var` variables initialized with defaults
- [ ] No unconditional resets of state variables
- [ ] State transitions are mutually exclusive
- [ ] Entry and exit conditions don't overlap
- [ ] Tested with `calc_on_every_tick = false` (default)
- [ ] Tested with `calc_on_every_tick = true` (real-time)

## Common Error Patterns

| Error | Cause | Fix |
|-------|-------|-----|
| Repeated triggers | State reset every bar | Move reset to conditional block |
| State desync | Multiple state variables out of sync | Consolidate into single state variable |
| Tier mismatch | Tier logic evaluated before state | Reorder: state first, then tier |
| Entry on exit bar | No guard against same-bar entry/exit | Add `barstate.isconfirmed` check |
