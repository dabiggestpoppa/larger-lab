# R6 â€” Account Heat Definition Lock (VI)

Seven distinct heat concepts (all measured on the sealed 890-event A/B book;
1R = 24.5 bps, unchanged; account mapping
account_return ~= trade_return_R x assigned_f):

| # | concept | definition |
|---|---|---|
| 1 | PER-EVENT f | the static fraction assigned to one R for an event. With a family allocation (w_A, w_B), the event's requested heat = base_f x w_family. |
| 2 | GROSS HEAT | sum of the assigned f of ALL active events (opposing positions included; they are NOT automatically riskless). |
| 3 | NET DIRECTIONAL HEAT | direction-aware net exposure proxy (signed sum of active assigned f). Reported descriptively; opposing events never cancel economic risk. |
| 4 | FAMILY HEAT | active A heat and active B heat separately (sum of assigned f of active events per family). |
| 5 | EPISODE HEAT | the maximum gross heat reached inside a 12h R1 episode (cluster). |
| 6 | REALIZED EPISODE LOSS | realized portfolio loss within an episode (sum of admitted f x final R of the episode's admitted events). |
| 7 | CAE HEAT | portfolio concurrent adverse excursion (min of the summed net-R path of the active events, in R units, unscaled by f). |

**Cap units:** all caps are multiples of the base per-event f (e.g. at base
f=1%, H1 cap 1.0x = 1.0% gross active heat). At 50/50 allocation each event
requests 0.5% at base f=1%, so a 1.0x gross cap admits up to two concurrent
events.

**Admission invariance:** requested heat and every cap scale linearly with
base_f, so admission decisions are identical at every f level; account PnL
scales linearly with f. The admission ledger is emitted at the reference
base_f = 1.0 and is representative at every level.

**Causality:** admission uses ONLY active heat known at entry time. Never
future outcome, future MAE/DD, or later performance.
