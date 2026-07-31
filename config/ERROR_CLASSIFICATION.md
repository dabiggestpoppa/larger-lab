# Error Classification Reference
> Used by all agents to classify and route errors.

## Levels

| Level | Code | Description | Auto-Action |
|-------|------|-------------|-------------|
| INFO | I | Expected variation, not a real problem | Log, continue |
| WARN | W | Suboptimal result, needs review | Log, flag for next review |
| ERROR | E | Execution failure, retryable | Retry (max 3x with backoff), then escalate |
| FATAL | F | Systemic failure, halt required | Stop, escalate to overseer immediately |

## Common Error Catalog

| Error ID | Level | Description | Fix |
|----------|-------|-------------|-----|
| ERR-001 | E | CSV parse failure — unexpected format | Try alternate separator, check encoding |
| ERR-002 | E | Missing data file | Run step1_prep_data.py, verify Downloads/ |
| ERR-003 | W | Low trade count (<10) | Expand date range or reduce filters |
| ERR-004 | W | Win rate below threshold | Adjust parameters, check data quality |
| ERR-005 | F | Nautilus engine crash | Check data integrity, verify parquet format |
| ERR-006 | I | No trades generated (valid no-trade day) | Log, mark as no-go day |
| ERR-007 | W | Max drawdown exceeded | Reduce position size, check tier classification |
| ERR-008 | E | Oanda API unavailable | Retry with backoff, fallback to cached CSV |