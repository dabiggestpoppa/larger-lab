# QL-EXEC-R5 — Restart Matrix

Crash windows tested against `FakeTradeLocker` broker truth (positions/orders
survive session recreation; the adapter reconstructs from provider truth —
never from memory).

| Window | Behavior | Test |
|---|---|---|
| before POST | nothing sent; broker clean | `test_43` |
| after local write-ahead | intent durable; broker clean | `test_42` (write-ahead gate) |
| after POST before response | ambiguous send; NO blind retry; reconcile | `test_33`, `test_34`, `test_44` |
| after accepted order before position appears | order accepted; position truth decides | `test_26`, `test_45` |
| after position appears before ledger update | position reconstructed from truth | `test_45`, `test_46` |
| during close request | closing order placed; position persists until confirmed | `test_47` |
| after close request before actual flat | position truth governs; never assume flat | `test_29`, `test_47` |

Invariants: no duplicate order submission after restart; broker truth is the
only fill/position authority; a restarted session never auto-resubmits an
ambiguous order.
