# 🔴 Polymorph (PM) — PO × VTuber Recon Task

> **Agent:** Polymorph (PM)
> **Task:** Phase 0 Recon for PO × Open-LLM-VTuber Integration
> **Plan:** `docs/plans/PO-VTUBER-INTEGRATION.md`
> **Start:** 2026-06-05 15:00 UTC
> **Status:** 🟡 START NOW — this is the BLOCKER for all Phase 1 work

---

## Mission

Clone [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) and map the actual provider architecture, streaming protocol, and integration points. **Nothing else starts until this is done.**

## Deliverables

### 1. Clone the repo
```bash
cd "C:\Users\wifik\Desktop\projects\larger-lab"
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git vtuber_integration/Open-LLM-VTuber
```

### 2. Map the provider architecture
Identify and document:

- [ ] Provider directory location (`backend/`, `src/llm/`, `providers/`, `services/`, etc.)
- [ ] OpenAI provider file (we'll emulate this)
- [ ] Ollama provider file
- [ ] Claude provider file
- [ ] Provider base class / protocol
- [ ] Streaming response handler (SSE / WebSocket / generator)
- [ ] WebSocket / event bus between frontend and backend
- [ ] Chat session state module
- [ ] Voice pipeline trigger point (TTS handoff)
- [ ] Provider registration mechanism (factory / config / registry / decorator)

### 3. Capture wire format
- [ ] Exact request shape from frontend to LLM provider
- [ ] Exact response shape (full and streaming chunks)
- [ ] SSE event names / data prefixes
- [ ] Error response format
- [ ] Auth/header conventions

### 4. Document integration points
- [ ] Where to add `po_provider.py` (file path)
- [ ] Where to register PO in the provider list
- [ ] Where the chat controller hands off to the LLM provider
- [ ] Where voice/TTS gets the response text
- [ ] Where the frontend reads provider selection from

### 5. Write the recon output
File: `docs/plans/VTUBER-RECON.md`

Must include:
- Directory tree (relevant sections only, ≤3 levels deep)
- File map (path → purpose → 1-line description)
- Wire format examples (request + response JSON)
- Integration points (where we inject PO)
- Dependencies (`requirements.txt` or `pyproject.toml`)
- Any surprises or deviations from the plan's assumptions

## Posting to Team Chat

When done, post a summary:
```
[PM] 2026-06-05 HH:MM UTC — VTuber Recon Complete

Repo cloned to: vtuber_integration/Open-LLM-VTuber/
Provider dir: <path>
Base class: <path>
Streaming: SSE via <module>
Provider registration: <method>
Wire format: OpenAI-compatible (confirmed) / different (see recon doc)

Recon doc: docs/plans/VTUBER-RECON.md

✅ CC: cleared to start Phase 1
```

## Do NOT

- ❌ Start writing PO Provider code
- ❌ Modify any files in the cloned repo
- ❌ Create the OCE `/api/po/chat` endpoint
- ❌ Run the VTuber app

## Once Phase 0 Done → Phase 2/3 Tasks

| Phase | Task | File | Tests |
|-------|------|------|-------|
| P2.1 | Workspace scanner | `oce/backend/po_workspace.py` | 4 |
| P3.3 | Interrupt/cancel handler | `oce/backend/po_interrupt.py` | 2 |

Total: 6 tests across 2 components.

## Commit Prefix

`[PO-VTUBER P0]` for recon work
`[PO-VTUBER P2]` for P2.1
`[PO-VTUBER P3]` for P3.3
