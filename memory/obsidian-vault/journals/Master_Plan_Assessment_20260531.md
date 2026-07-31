# 22:35 EDT — MAD's Master Plan Document + Assessment

## Document: lab_expansion_two_parts_in_order.txt
MAD sent comprehensive 2-part master plan covering Track A (Tradovate/NT8) and Track B (Crypto) with detailed phases, mermaid diagrams, and code snippets.

## Key Findings from Master Plan

### Track A — NT8 Corrections Needed
1. **Tier thresholds**: Current .cs uses EURUSD-specific <20/30/45p. Plan requires per-asset thresholds via UserDefinedInput
2. **Gear shift logic**: Plan specifies T1→T2 at 50pts, T1/T2→T3 at 62pts (not trigger-based)
3. **Risk gate**: Completely missing from current .cs files. Need: daily loss 0.40%, correlation cap, position sizing
4. **12PM hard exit**: Must be API-level enforced, not just strategy-level

### Track B — Crypto Phase 6 Missing
- **Structural Validity Firewall**: Must validate assets BEFORE ingestion (age >30d, vol >$10M, book depth >0.5%, funding <0.1%)
- **Structural Decay Monitor**: Live monitoring with auto-blacklist when metrics degrade

## MAD's Questions/Directives Pending
1. Asset tier thresholds for ES/NQ/GC/CL for NT8
2. Tradovate API credentials for Python REST/WS client build

## Files Needing Updates
- `tradovate/CEREBUS_ST_NT8.cs` — add risk gate, gear shift, per-asset tiers
- `tradovate/CEREBUS_P90_NT8.cs` — add risk gate, session enforcement
- `tradovate/CEREBUS_AssetPresets.cs` — add futures asset presets
- `crypto/CryptoAssetScanner.py` — add structural validity firewall (Phase 6)

## What I Did NOT Do
- Did NOT start implementing any changes (awaiting MAD confirmation)
- Did NOT spawn any subagents
- Did NOT touch NT8 files without confirmation

---
*Logged: 2026-05-31 22:35 EDT — Awaiting MAD confirmation on asset thresholds and path forward*
