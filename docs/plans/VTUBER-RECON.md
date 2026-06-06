# VTuber Recon — Open-LLM-VTuber Architecture Map

> **Author:** PM (Polymorph)
> **Date:** 2026-06-05
> **Source:** `vtuber_integration/Open-LLM-VTuber/` (cloned from `Open-LLM-VTuber/Open-LLM-VTuber`)
> **Purpose:** Map provider architecture, streaming protocol, and integration points for PO injection.

---

## 1. High-Level Architecture

```
Browser (frontend)
  ↕ WebSocket (/client-ws)
FastAPI Server (run_server.py → WebSocketServer)
  ├── WebSocketHandler (message routing)
  ├── ConversationHandler (chat orchestration)
  ├── AgentFactory → AgentInterface (LLM abstraction)
  ├── ASRFactory → ASRInterface (speech-to-text)
  ├── TTSFactory → TTSInterface (text-to-speech)
  ├── VADFactory → VADInterface (voice activity detection)
  ├── ChatHistoryManager (JSON file persistence)
  └── ServiceContext (per-client state container)
```

**Key insight:** The entire system is **WebSocket-based** — NOT REST/SSE. The frontend talks to the backend over a single persistent WebSocket connection at `/client-ws`. There is no HTTP chat endpoint. This changes our PO injection strategy.

---

## 2. Provider Directory Structure

```
src/open_llm_vtuber/
├── agent/
│   ├── agents/
│   │   ├── agent_interface.py      ← ABC: chat(), handle_interrupt(), set_memory_from_history()
│   │   ├── basic_memory_agent.py   ← Default agent: wraps StatelessLLM + memory + tool calling
│   │   ├── hume_ai.py             ← Hume AI agent (voice-native)
│   │   ├── letta_agent.py         ← Letta/MemGPT agent
│   │   └── mem0_llm.py            ← Mem0 memory agent
│   ├── stateless_llm/
│   │   ├── stateless_llm_interface.py  ← ABC: chat_completion(messages, system, tools) → AsyncIterator[str]
│   │   ├── openai_compatible_llm.py    ← OpenAI-compatible (also: gemini, zhipu, deepseek, groq, mistral, lmstudio)
│   │   ├── ollama_llm.py               ← Ollama provider
│   │   ├── claude_llm.py               ← Anthropic Claude provider
│   │   ├── llama_cpp_llm.py            ← Local llama.cpp
│   │   └── stateless_llm_with_template.py  ← Template-wrapped LLM
│   ├── agent_factory.py            ← Factory: create_agent(choice, settings, llm_configs, ...)
│   ├── stateless_llm_factory.py    ← Factory: create_llm(provider, **kwargs)
│   ├── input_types.py              ← BatchInput, TextData, ImageData
│   └── output_types.py             ← SentenceOutput, AudioOutput, DisplayText, Actions
├── asr/                            ← Speech-to-text (Whisper, Azure, FunASR, Sherpa, Groq)
├── tts/                            ← Text-to-speech (Edge, Azure, Bark, ElevenLabs, OpenAI, 15+ providers)
├── vad/                            ← Voice activity detection (Silero)
├── conversations/
│   ├── conversation_handler.py     ← Routes mic/text/ai-speak triggers to single or group conversation
│   ├── single_conversation.py      ← Single user conversation pipeline
│   └── group_conversation.py       ← Multi-user group conversation
├── chat_history_manager.py         ← JSON file-based chat history (per conf_uid/history_uid)
├── websocket_handler.py            ← WebSocket message routing (MessageType enum)
├── service_context.py              ← Per-client state: agent, asr, tts, vad, config, history
├── routes.py                       ← FastAPI router: /client-ws, /proxy-ws, webtool routes
├── server.py                       ← WebSocketServer class (FastAPI app setup)
├── message_handler.py              ← Async request/response matching for WebSocket messages
├── config_manager/                 ← Pydantic config models + YAML loader
└── mcpp/                           ← MCP tool calling (tool_manager, tool_executor, server_registry)
```

---

## 3. Provider Registration Mechanism

### How providers are registered

**LLM providers** are registered via `LLMFactory.create_llm()` in `agent/stateless_llm_factory.py`:

```python
if llm_provider == "openai_compatible_llm" or llm_provider == "openai_llm" or ...:
    return OpenAICompatibleLLM(model=..., base_url=..., llm_api_key=..., ...)
elif llm_provider == "ollama_llm":
    return OllamaLLM(...)
elif llm_provider == "claude_llm":
    return ClaudeLLM(...)
# else: raise ValueError
```

**Agents** are registered via `AgentFactory.create_agent()` in `agent/agent_factory.py`:

```python
if conversation_agent_choice == "basic_memory_agent":
    llm = StatelessLLMFactory.create_llm(llm_provider=..., **llm_config)
    return BasicMemoryAgent(llm=llm, ...)
elif conversation_agent_choice == "mem0_agent":
    ...
elif conversation_agent_choice == "letta_agent":
    ...
```

### Configuration format

YAML-based (`config_templates/conf.default.yaml`):

```yaml
character_config:
  agent_config:
    conversation_agent_choice: 'basic_memory_agent'
    agent_settings:
      basic_memory_agent:
        llm_provider: 'ollama_llm'    # ← This selects the LLM
        faster_first_response: True
        segment_method: 'pysbd'
        use_mcpp: True
    llm_configs:
      openai_compatible_llm:
        base_url: 'http://localhost:11434/v1'
        llm_api_key: 'somethingelse'
        model: 'qwen2.5:latest'
        temperature: 1.0
        interrupt_method: 'user'
      ollama_llm:
        base_url: 'http://localhost:11434/v1'
        ...
      claude_llm:
        ...
```

### PO Insertion Strategy

**Option A (Recommended): Add `po_llm` as a new StatelessLLM provider**

1. Create `po_llm.py` in `src/open_llm_vtuber/agent/stateless_llm/`
2. Implement `StatelessLLMInterface.chat_completion()` → yields text chunks
3. Internally, `po_llm` calls OCE `/api/po/chat` (HTTP POST, SSE stream)
4. Add `"po_llm"` case to `LLMFactory.create_llm()`
5. Add `po_llm` config section to `llm_configs` in YAML
6. Set `llm_provider: 'po_llm'` in agent settings

**Why this works:**
- `StatelessLLMInterface` is the exact abstraction layer we need
- `chat_completion()` returns `AsyncIterator[str]` — perfect for streaming
- `BasicMemoryAgent` already handles memory, tool calling, sentence segmentation, TTS handoff
- We get ALL the VTuber features (Live2D expressions, TTS, VAD, chat history) for free
- Zero frontend changes — the WebSocket protocol is untouched

**Option B (Alternative): Add `po_agent` as a new Agent type**

- More invasive — would bypass BasicMemoryAgent's memory/tool infrastructure
- Only needed if PO needs to control the conversation loop differently
- **Not recommended for Phase 1**

---

## 4. Streaming Response Handler

### Current flow (OpenAI-compatible)

```python
# openai_compatible_llm.py — AsyncLLM.chat_completion()
stream = await self.client.chat.completions.create(
    messages=messages_with_system,
    model=self.model,
    stream=True,           # ← Always streaming
    temperature=self.temperature,
    tools=available_tools,
)

async for chunk in stream:
    if chunk.choices:
        # Yield text content or tool calls
        yield chunk.choices[0].delta.content
```

### How chunks flow to the frontend

```
StatelessLLM.chat_completion()  →  yields str chunks
    ↓
BasicMemoryAgent.chat()  →  yields SentenceOutput/AudioOutput
    ↓ (sentence_divider segments chunks into sentences)
    ↓ (actions_extractor extracts Live2D expressions)
    ↓ (tts_filter cleans text for TTS)
single_conversation.process_single_conversation()
    ↓
process_agent_output()  →  sends WebSocket messages:
    - {"type": "full-text", "text": "..."}        (display text)
    - {"type": "expression", "data": [...]}       (Live2D expression)
    - {"type": "audio", "audio": [...], "text": "..."}  (TTS audio)
```

### PO Streaming Strategy

Our `po_llm.py` will:
1. POST to OCE `/api/po/chat` with `stream: true`
2. Read the SSE response stream
3. Parse each `data: {...}` line
4. Extract `choices[0].delta.content` from each chunk (OpenAI-shape)
5. Yield the content string — matching the `AsyncIterator[str]` contract

The rest of the pipeline (BasicMemoryAgent → sentence segmentation → TTS → WebSocket) **remains completely unchanged**.

---

## 5. WebSocket / Event Bus

### Protocol

Single WebSocket connection at `/client-ws`. Messages are JSON with a `type` field:

**Client → Server (user actions):**
| Type | Trigger | Data |
|------|---------|------|
| `mic-audio-data` | Streaming mic audio | `audio: float[]` |
| `mic-audio-end` | Mic stopped | — |
| `text-input` | Text chat | `text: string` |
| `ai-speak-signal` | Proactive speak | — |
| `interrupt-signal` | User interrupted | — |
| `fetch-history-list` | Load history sidebar | — |
| `fetch-and-set-history` | Switch conversation | `history_uid` |
| `create-new-history` | New conversation | — |
| `delete-history` | Delete conversation | `history_uid` |
| `fetch-configs` | Get character configs | — |
| `switch-config` | Switch character | `conf_uid` |
| `heartbeat` | Keepalive | — |

**Server → Client (responses):**
| Type | Content |
|------|---------|
| `full-text` | Display text (markdown) |
| `expression` | Live2D expression data |
| `audio` | TTS audio payload + lip sync |
| `set-conf` | Configuration update |
| `history-list` | Chat history metadata |
| `tool_call_status` | MCP tool execution status |

### Key insight for PO

We do **NOT** touch the WebSocket protocol. PO operates at the LLM layer only. The WebSocket handler, conversation handler, and all frontend communication remain 100% unchanged.

---

## 6. Chat Session State

### ServiceContext (per-client)

```python
class ServiceContext:
    config: Config
    system_config: SystemConfig
    character_config: CharacterConfig
    live2d_model: Live2dModel
    asr_engine: ASRInterface
    tts_engine: TTSInterface
    agent_engine: AgentInterface      # ← This is where our PO agent lives
    vad_engine: VADInterface
    translate_engine: TranslateInterface
    system_prompt: str
    history_uid: str                  # ← Current conversation ID
    mcp_server_registery: ServerRegistry
    tool_manager: ToolManager
    tool_executor: ToolExecutor
```

### Chat History

- Stored as JSON files in `chat_history/{conf_uid}/{history_uid}.json`
- Each message: `{"role": "human"|"ai", "timestamp": "...", "content": "...", "name": "...", "avatar": "..."}`
- Managed by `chat_history_manager.py` (create, get, store, delete, list)
- `BasicMemoryAgent` loads history via `set_memory_from_history()` into `self._memory`

### PO Session Mapping

- VTuber `history_uid` → OCE `po_session` key
- VTuber `conf_uid` → PO character/identity context
- We can map `history_uid` to our session store for cross-interface continuity (Phase 3)

---

## 7. Voice Pipeline (TTS Handoff)

### Flow

```
User speaks → mic-audio-data (WebSocket)
    ↓
VAD (Silero) detects speech start/end
    ↓
ASR (Whisper/etc) transcribes audio → text
    ↓
Agent.chat(text) → yields SentenceOutput(display_text, tts_text, actions)
    ↓
Sentence divider segments into speakable chunks
    ↓
TTS engine generates audio for each chunk
    ↓
WebSocket sends {"type": "audio", "audio": [...], "text": "..."}
    ↓
Frontend plays audio + animates Live2D model
```

### TTS Factory

`tts/tts_factory.py` — 15+ TTS providers (Edge, Azure, Bark, ElevenLabs, OpenAI, Piper, etc.)

### PO Integration Point

PO does **NOT** touch the voice pipeline. The voice pipeline operates entirely downstream of the LLM:
- ASR → text → **PO (LLM layer)** → text → TTS → audio
- We only replace what's between ASR output and TTS input.

---

## 8. MCP / Tool Calling

### Architecture

```
mcp_servers.json          ← MCP server definitions
mcpp/server_registry.py   ← Discovers and connects to MCP servers
mcpp/tool_manager.py      ← Formats tools for OpenAI/Claude API
mcpp/tool_executor.py     ← Executes tool calls
mcpp/tool_adapter.py      ← Adapts between MCP and agent
mcpp/json_detector.py     ← Detects JSON tool calls in streaming output
```

### PO + Tools

For Phase 1, PO's tool calling is handled by OCE internally (workspace scan, vault retrieval, agent coordination). The VTuber's MCP system is independent and can remain enabled or disabled via config.

For Phase 2+, we could bridge PO's tool results back through the VTuber MCP system, but this is **out of scope for Phase 1**.

---

## 9. Insertion Points Summary

| # | What | Where | How | Phase |
|---|------|-------|-----|-------|
| 1 | **PO LLM Provider** | `agent/stateless_llm/po_llm.py` | New file implementing `StatelessLLMInterface` | P1 |
| 2 | **Factory registration** | `agent/stateless_llm_factory.py` | Add `"po_llm"` case to `create_llm()` | P1 |
| 3 | **Config schema** | `config_manager/stateless_llm.py` | Add `POProviderConfig` Pydantic model | P1 |
| 4 | **YAML config** | `config_templates/conf.default.yaml` | Add `po_llm:` section under `llm_configs` | P1 |
| 5 | **OCE PO API** | `oce/backend/po_api.py` | New FastAPI endpoints `/api/po/chat`, `/api/po/status` | P1 |
| 6 | **OCE main.py wiring** | `oce/backend/main.py` | Import + register `po_api` router | P1 |

---

## 10. Wire Format — PO LLM ↔ OCE

### Request (po_llm → OCE)

```http
POST /api/po/chat
Content-Type: application/json
Authorization: Bearer <OCE_TOKEN>

{
  "model": "po",
  "messages": [
    {"role": "system", "content": "You are PO..."},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": true,
  "temperature": 0.7,
  "session_id": "<vtuber-history-uid>"
}
```

### Response (OCE → po_llm, SSE stream)

```
data: {"id":"po-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hey"}}]}

data: {"id":"po-xxx","object":"chat.completion.chunk","choices":[{"delta":{"content":" there"}}]}

data: [DONE]
```

This is **exactly** the OpenAI streaming format. Our `po_llm.py` will parse this identically to `openai_compatible_llm.py`.

---

## 11. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| VTuber uses WebSocket, not REST — PO must work through LLM layer, not add HTTP endpoints to VTuber | Certain | Low | We already planned LLM-layer injection. No conflict. |
| `StatelessLLMInterface.chat_completion()` expects `AsyncIterator[str]` — PO must yield strings, not dicts | Certain | Low | Our SSE parser yields content strings. Matches contract. |
| Tool calling format differs between OpenAI and PO | Medium | Medium | Phase 1: disable MCP in PO config. Phase 2: bridge PO tools. |
| VTuber's `BasicMemoryAgent` manages its own memory — PO also has memory | Medium | Low | Let BasicMemoryAgent handle VTuber-side memory. PO handles cognitive field memory independently. Dual memory is fine — they serve different purposes. |
| Config hot-reload may not pick up new provider | Low | Medium | Test config reload after adding po_llm. May need server restart. |

---

## 12. Phase 1 Implementation Checklist

Based on this recon, Phase 1 requires:

1. ✅ **Create `po_llm.py`** — implements `StatelessLLMInterface`, calls OCE `/api/po/chat`, parses SSE, yields text chunks
2. ✅ **Register in `stateless_llm_factory.py`** — add `"po_llm"` case
3. ✅ **Add config model** — `POProviderConfig` in `config_manager/stateless_llm.py`
4. ✅ **Add YAML config** — `po_llm:` section with `base_url`, `llm_api_key`, `model`, `temperature`
5. ✅ **Create OCE PO API** — `/api/po/chat` (SSE stream), `/api/po/status` (health)
6. ✅ **Wire into OCE main.py** — import + register router
7. ✅ **Test: po_llm unit tests** — mock OCE response, verify streaming
8. ✅ **Test: OCE PO API tests** — verify endpoint shape, SSE format
9. ✅ **Test: e2e smoke** — VTuber with `llm_provider: 'po_llm'` → talk → response

---

## 13. File Map (Quick Reference)

| File | Purpose | Lines |
|------|---------|-------|
| `run_server.py` | Entry point, starts uvicorn + WebSocketServer | ~120 |
| `src/open_llm_vtuber/server.py` | FastAPI app, CORS, routes, static files | ~120 |
| `src/open_llm_vtuber/routes.py` | WebSocket endpoint `/client-ws`, webtool routes | ~80 |
| `src/open_llm_vtuber/websocket_handler.py` | Message routing, connection management | ~300 |
| `src/open_llm_vtuber/service_context.py` | Per-client state container | ~200 |
| `src/open_llm_vtuber/message_handler.py` | Async request/response matching | ~80 |
| `src/open_llm_vtuber/chat_history_manager.py` | JSON file chat history | ~200 |
| `src/open_llm_vtuber/conversations/conversation_handler.py` | Routes triggers to conversations | ~100 |
| `src/open_llm_vtuber/conversations/single_conversation.py` | Single user conversation pipeline | ~150 |
| `src/open_llm_vtuber/agent/agent_factory.py` | Agent factory (basic_memory, mem0, letta, hume) | ~120 |
| `src/open_llm_vtuber/agent/stateless_llm_factory.py` | LLM factory (openai, ollama, claude, llama_cpp) | ~60 |
| `src/open_llm_vtuber/agent/stateless_llm/stateless_llm_interface.py` | ABC for LLM providers | ~40 |
| `src/open_llm_vtuber/agent/stateless_llm/openai_compatible_llm.py` | OpenAI-compatible streaming LLM | ~150 |
| `src/open_llm_vtuber/agent/agents/agent_interface.py` | ABC for agents | ~40 |
| `src/open_llm_vtuber/agent/agents/basic_memory_agent.py` | Default agent with memory + tools | ~300 |
| `src/open_llm_vtuber/agent/input_types.py` | BatchInput, TextData, ImageData | ~60 |
| `src/open_llm_vtuber/agent/output_types.py` | SentenceOutput, AudioOutput, DisplayText | ~60 |
| `src/open_llm_vtuber/tts/tts_interface.py` | ABC for TTS | ~60 |
| `src/open_llm_vtuber/asr/asr_interface.py` | ABC for ASR | ~40 |
| `config_templates/conf.default.yaml` | Default configuration | ~120 |

---

**RECON COMPLETE. Phase 0 blocker resolved. Phase 1 is unblocked.**
