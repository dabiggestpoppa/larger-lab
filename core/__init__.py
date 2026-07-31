"""
OCE Core — Cognition Substrate

Phase 1 implementation:
- parser/orchestration: multimodal document ingestion (1.2)
- semantic/chunking: semantic text segmentation (1.3.1)
- semantic/embeddings: vector embedding engine (1.3.2)
- semantic/vector/turbovec: vector search index (1.3.3)
- knowledge/graph: entity-relationship topology (1.5)
- knowledge/ontology: concept hierarchies (1.5.3)
- cognition/procedural: skill-based workflows (1.6)
- research/distiller: research compression (2)
- research/signal_engine: gap detection + autonomous research (3)

GitHub integrations:
- microsoft/markitdown     → core/parser/markitdown (universal parser)
- opendataloader-project   → core/parser/odl-pdf (research PDF extraction)
- run-llama/liteparse      → core/parser/liteparse (orchestration)
- datalab-to/chandra       → core/parser/chandra (OCR/vision)
- RyanCodrai/turbovec      → core/semantic/vector/turbovec (vector search)
- colbymchenry/codegraph   → tools/codegraph (code knowledge graph)
- virgiliojr94/book-to-skill → core/cognition/procedural/book-to-skill
- maipianworni/SkillTree   → core/cognition/router/skilltree
- mattpocock/skills        → skills/ (engineering best practices)
- teng-lin/notebooklm-py   → content-farm/github-repos/notebooklm-py
- Thysrael/Horizon         → core/research/horizon (news radar)
- dograh-hq/dograh         → vtuber_integration/dograh (voice AI)
- LottieFiles/dotlottie-web → vtuber_integration/dotlottie-web (animations)
- terrastruct/d2            → tools/d2 (diagram scripting)
- averygan/reclip          → content-farm/sites/reclip (video downloader)
- nexu-io/open-design      → content-farm/design/open-design (design assets)
"""

__version__ = "0.1.0"