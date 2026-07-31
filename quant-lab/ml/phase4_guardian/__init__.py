"""
Phase 4: Guardian Alert Pipeline
==================================
Live scanning engine that:
1. Computes micro + macro features on each M15 candle close
2. Queries XGBoost regime classifier for regime + confidence
3. Checks alignment (confidence >= 85% AND near structural boundary AND safe from rekey)
4. Queries RAG Oracle for manual directive
5. Formats rich Markdown alert
6. Dispatches to Telegram/Discord

Ironclad Safety Rules (hardcoded, non-negotiable):
- 12PM EST Hard Exit: No new activations after 11:00 AM EST
- Wednesday PM: If -25% NOT hit by 16:00 UTC, reduce size 50% or EXIT
- 132% Kill-Switch: If breached, EXIT immediately, wait for 78.6% rekey retest
- No retail indicators: Feature store ONLY contains constraint-system metrics
- Close-only SL: M5 CLOSE beyond OCC Extreme, wicks ignored
"""
