# CR-BLOCK4-D1.2 IMPLEMENTATION SEQUENCE

| id | name | gate |
|---|---|---|
| D1.2A | PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL | ingest actual observed / documented USDJPY account + instrument specs from the intended venue(s); freeze profiles |
| D1.2B | QUANTITY-REPRESENTABILITY-SURFACE | execute the sealed Lane-B study on frozen profiles |
| D1.3 | MARGIN-CONTRACT-FEASIBILITY | Lane C; actual margin semantics else BLOCKED_PENDING_MARGIN_TRUTH |
| D1.4 | CONCURRENT-ACCOUNT-RESOURCE-REPLAY | causal overlap replay |
| D1.5 | PHYSICAL-BOOK-DISTORTION-SEAL | ideal vs physical book |
| D1.6 | BROKER-QUANTITY-TRANSLATION-CONTRACT | broker-native quantity handoff |

D1.2A must precede D1.2B so physical assumptions cannot silently enter the
empirical engine.  Each later checkpoint requires its own authorization.
