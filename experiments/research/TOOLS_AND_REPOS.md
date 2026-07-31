# 🔧 Tools & Repos — Assessment & Integration Plan

> **Date:** 2026-05-18 14:30 EDT
> **Updated by:** Resource Adapter
> **Purpose:** Evaluate and integrate repos into our stack with clear priorities

---

## Priority Assessment Framework

| Priority | Meaning |
|----------|---------|
| **HIGH** | Use NOW — benefits active systems, low integration effort |
| **MEDIUM** | Integrate LATER — valuable but needs dependencies or significant effort |
| **LOW** | Reference ONLY — interesting but not directly applicable right now |

---

## MAD's Recommended Repos

### 1. Open Design (nexu-io/open-design) ⭐ 40k+ stars — **HIGH**

**What:** Local-first, BYOK, agent-native design tool. 19 skills + 71 design systems.

**Benefits:** Content Farm (visual production), Agent Environment (design capabilities)

**Integration type:** Tool + Skill
- Can be used as a skill for content creation agents
- 200+ design templates ready to use
- Exports: HTML, PDF, PPTX, MP4

**Effort:** Medium (needs Node 24 + pnpm install)
**Status:** ✅ Cloned → 🟡 Needs dependency install
**Action:** Install dependencies, test, extract templates for Content Farm

---

### 2. ViMax (HKUDS/ViMax) — **MEDIUM**

**What:** Agentic video generation — Director → Screenwriter → Producer → Video.

**Benefits:** Content Farm (video production for TikTok, YT Shorts, Reels)

**Integration type:** Tool (Python package)
- Multi-agent workflow aligns with our pipeline
- Needs API keys for video providers (not free)

**Effort:** High (needs API keys + Python 3.12 + uv)
**Status:** ✅ Cloned → 🟡 Needs dependency install + API keys
**Action:** Install deps, configure keys when MAD approves video production

---

### 3. Netviz (ShadowArcanist/netviz) — **HIGH**

**What:** Browser-based network architecture visualizer.

**Benefits:** ALL systems (architecture documentation, visualization)

**Integration type:** Tool (static site — zero dependencies)
- No API keys needed
- Exports to PNG/SVG
- Can document SRRA+OCE topology, agent architecture

**Effort:** Low (already installed and ready)
**Status:** ✅ Ready to use NOW
**Action:** Run `npm run dev`, create architecture diagrams

---

### 4. UI-TARS Desktop (bytedance/UI-TARS-desktop) — **MEDIUM**

**What:** Multimodal AI agent for browser/desktop automation.

**Benefits:** Content Farm (platform posting), Agent Environment (computer control)

**Integration type:** Tool + Skill
- Monorepo with agent-tars, ui-tars, omni-tars, tarko
- CLI: `npm install @agent-tars/cli@latest -g`
- Needs vision-language model API key

**Effort:** Medium-High (needs pnpm install + model API key)
**Status:** ✅ Cloned → 🟡 Needs dependency install + API key
**Action:** Install deps, configure model key, test browser automation

---

### 5. Google Accounts Strategy — **HIGH**

**What:** Multiple Google accounts = free storage + NotebookLM + Colab.

**Benefits:** ALL systems (storage, research, backups)

**Integration type:** Infrastructure (credential management + API setup)

**Effort:** Low (MAD creates accounts, RA sets up service accounts)
**Status:** ⏳ Waiting for MAD to assign accounts
**Action:** Documented in `config/google-accounts-strategy.md`

---

## Additional Repos to Evaluate

### 6. 12 Factor Agents — **MEDIUM**

**What:** Principles for building reliable AI agents (analogous to 12-factor app methodology).

**Benefits:** SRRA+OCE (agent design principles), Agent Environment (best practices)

**Integration type:** Reference / Skill
- Not a tool — a methodology
- Should inform how we design and evaluate agents

**Effort:** Low (read and apply principles)
**Status:** 📌 Noted — read and extract principles
**Action:** Review and integrate relevant principles into agent design docs

---

### 7. X Algorithm Wiki — **LOW**

**What:** Documentation/analysis of X (Twitter) algorithm.

**Benefits:** Content Farm (understanding what content gets distribution)

**Integration type:** Reference
- Informational, not a tool
- Helps content strategy but doesn't require integration

**Effort:** Low (read and note insights)
**Status:** 📌 Noted — reference for content strategy
**Action:** Read and extract key insights for Content Farm strategy

---

### 8. Public APIs — **LOW**

**What:** Curated list of free public APIs.

**Benefits:** ALL systems (finding free APIs for various needs)

**Integration type:** Reference
- Useful when we need a new API
- Not something to integrate now

**Effort:** Low (bookmark and reference)
**Status:** 📌 Noted — reference list
**Action:** Bookmark for future use when specific API needs arise

---

### 9. Hello Agents — **MEDIUM**

**What:** Starter template/framework for building AI agents.

**Benefits:** Agent Environment (agent templates), SRRA+OCE (agent patterns)

**Integration type:** Reference + Skill templates
- Could provide templates for new agents
- Compare with our existing agent patterns

**Effort:** Low-Medium (review and extract useful patterns)
**Status:** 📌 Noted — review when building new agents
**Action:** Clone and review when Agent Environment needs new agent templates

---

### 10. Guizang PPT — **LOW**

**What:** AI-powered PPT/presentation generation.

**Benefits:** Content Farm (pitch decks, presentations)

**Integration type:** Tool (when needed)
- Overlaps with Open Design's PPTX export
- Lower priority since Open Design covers this

**Effort:** Low (evaluate when presentation need arises)
**Status:** 📌 Noted — evaluate if Open Design insufficient
**Action:** Defer — Open Design handles presentations

---

### 11. Lonkero — **LOW**

**What:** Link management/shortening tool.

**Benefits:** Content Farm (link tracking for social media)

**Integration type:** Tool (when needed)
- Only useful when we have active social media accounts
- Not needed until content is being published

**Effort:** Low
**Status:** 📌 Noted — evaluate when publishing content
**Action:** Defer until Content Farm is actively posting

---

## Integration Priority Summary

| Priority | Tool | System | Effort | Status |
|----------|------|--------|--------|--------|
| **HIGH** | Netviz | All | Low | ✅ Ready |
| **HIGH** | Google Accounts | All | Low | ⏳ Waiting on MAD |
| **HIGH** | Open Design | Content Farm | Medium | 🟡 Needs install |
| **MEDIUM** | UI-TARS | Content Farm + Agents | Medium-High | 🟡 Needs install |
| **MEDIUM** | ViMax | Content Farm | High | 🟡 Needs install + keys |
| **MEDIUM** | 12 Factor Agents | SRRA+OCE | Low | 📌 Noted |
| **MEDIUM** | Hello Agents | Agent Environment | Low-Medium | 📌 Noted |
| **LOW** | X Algorithm Wiki | Content Farm | Low | 📌 Noted |
| **LOW** | Public APIs | All | Low | 📌 Noted |
| **LOW** | Guizang PPT | Content Farm | Low | 📌 Noted |
| **LOW** | Lonkero | Content Farm | Low | 📌 Noted |

---

## Key Insight

**Focus on HIGH priority items first.** Netviz is ready NOW — use it. Google Accounts strategy is documented — waiting on MAD. Open Design is the next install. Everything else is secondary.

The system has a tendency to track too many repos simultaneously. This list should be pruned to only active integrations. LOW priority items should be archived until needed.

---

*Last updated: 2026-05-18 14:30 EDT — Resource Adapter*
