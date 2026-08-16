"""TB Forward Engine package (TB-R0 scaffold).

This package will host the deployment layers of the Triangular Basis (TB)
forward execution engine built in checkpoints TB-R1 through TB-R10:

  market_data.py / snapshot.py   -- synchronized 3-leg TriangleSnapshot (R2)
  strategy.py / state.py / signals.py -- canonical strategy port (R3)
  sizing.py / exposure.py        -- exact-neutral notional/lot translation (R4)
  basket.py / coordinator.py / order_plan.py -- atomic basket (R5)
  persistence.py / reconciliation.py -- crash recovery + reconcile (R6)
  runner.py                      -- shadow/demo runner + operational CLI (R7/R10)

TB-R0 deliberately contains NO live logic. Do not add strategy or broker
execution code until the corresponding checkpoint authorizes it.
"""

__all__: list = []
