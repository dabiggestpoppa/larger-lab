# Skill: Pine State Machine Debugging

> **Category:** engineering
> **Version:** 1.0.0
> **Purpose:** Debug Pine Script state machine issues in TradingView indicators/strategies.

## Detection

Symptoms of Pine state machine bugs:
- Repeated trigger execution on same bar
- State desync between expected and actual
- Tier mismatch in multi-tier strategies
- Entry/exit logic firing at wrong times
- Variables resetting unexpectedly

## Fix Flow

1. **Isolate state mutation** — Identify all `var` and `varip` variables
2. **Snapshot variables** — Add debug labels to track variable values bar-by-bar
3. **Prevent reset before execution** — Ensure state persistence across bars
4. **Enforce transition order** — Validate state machine transitions are sequential
5. **Test with `calc_on_every_tick`** — Verify behavior under real-time conditions

## Heuristics

- Use `var` for state that should persist across bars
- Use `varip` only for intra-bar state that must update on every tick
- Never reset state variables inside conditional blocks that may not fire
- Always initialize state variables with explicit default values

## Common Patterns

### State Machine Template
```pinescript
var string current_state = "SEARCH"

if current_state == "SEARCH" and entry_condition
    current_state := "IN_TRADE"
else if current_state == "IN_TRADE" and exit_condition
    current_state := "SEARCH"
```

### Anti-Pattern (NEVER DO)
```pinescript
// BAD: Resetting state before checking it
current_state := "SEARCH"  // This resets EVERY bar!
if current_state == "SEARCH" and entry_condition
    // This will always fire because state was just reset
```
