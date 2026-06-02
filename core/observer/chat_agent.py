"""Real chat agent for Primary Observer Telegram bot.

Uses OpenRouter API with model failover chain:
1. moonshotai/kimi-k2.6:free (primary)
2. openrouter/owl-alpha (backup 1)
3. poolside/laguna-m.1:free (backup 2)

Features:
- Vault context injection before every response
- Conversation history (last 20 turns)
- Structured system prompt with operational context
- Automatic failover on rate limit (429) or error
- OC2-style markdown formatting for Telegram output
"""
import os
import json
import requests
import datetime
import time
from typing import Dict, Any, List, Optional


MODEL_CHAIN = [
    "moonshotai/kimi-k2.6:free",
    "openrouter/owl-alpha",
    "poolside/laguna-m.1:free",
]


class ChatAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self._history: List[Dict[str, str]] = []
        self._max_history = 20
        self._model_index = 0
        self._rate_limit_count: Dict[str, int] = {}

    @property
    def current_model(self) -> str:
        return MODEL_CHAIN[self._model_index % len(MODEL_CHAIN)]

    def _next_model(self) -> str:
        self._model_index += 1
        return self.current_model

    def _build_system_prompt(self, vault_context: str = "", sovereign_context: str = "") -> str:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        ctx = f"\n## Vault Context\n{vault_context}" if vault_context else ""
        sov = f"\n{sovereign_context}" if sovereign_context else ""
        return f"""You are the Primary Observer (PO) — sovereign operational interface for Larger-Lab.

You are not a chatbot. You are an operational continuity layer — the speaking face of OCE.

## Identity
- Direct interface between the operator and the cognitive field
- You have access to the operational vault, service status, and agent orchestration
- Current time: {ts}
{sov}

## Output Format (CRITICAL)
You are communicating via Telegram. Use rich markdown formatting:
- **Bold** for headers, key terms, service names
- `code` for commands, file paths, port numbers, values
- Bullet lists for multi-item responses
- Numbered lists for steps/sequences
- Emoji indicators: ✅ OK, ❌ Error, ⚠️ Warning, 🔄 In-progress, 📊 Data, 🔍 Analysis
- Section headers: ## Major, ### Minor
- Code blocks for configs, JSON, logs
- Tree diagrams for hierarchical data

## Response Patterns

For status/overview queries, use:
📊 **System Status**
├── Service: ✅/❌ (port)
├── Service: ✅/❌ (port)
└── **Summary:** one-line takeaway

For analysis/research:
🔍 **Topic**
## Finding
## Evidence
## Recommendation

For task execution:
⚡ **Executing:** `command`
## Steps
1. Step one
2. Step two
## Result

## Behavior
- Be concise and direct — no filler phrases
- Reference vault knowledge when relevant
- If you don't know, say so directly
- Use technical language appropriate for the operator
- Show your work — explain what you checked and what you found
- For workspace queries, mention specific files, commits, or vault notes
- Always end with a clear summary or next step

{ctx}

You are the operator's direct line to the entire system. Respond with the same structured, informative style as OC2."""

    def _get_vault_context(self, message: str) -> str:
        try:
            from core.observer.vault import Vault
            v = Vault()
            words = message.lower().split()
            stop = {"the","a","an","and","or","to","of","in","on","for","is","are","it","i","you","me","my","what","how","why","when","where","do","does","can","could","would","should","this","that","these","those"}
            keywords = [w for w in words if w not in stop and len(w) > 3][:5]
            if not keywords: return ""
            hits = v.search_notes(keywords, max_results=3)
            if not hits: return ""
            lines = []
            for h in hits:
                lines.append(f"- {h['path']}: {h['snippet'][:120]}")
            return "\n".join(lines)
        except:
            return ""

    def _call_llm(self, messages: List[Dict[str, str]], model: str) -> tuple:
        try:
            r = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/dabiggestpoppa/larger-lab",
                    "X-Title": "Primary Observer",
                },
                json={"model": model, "messages": messages, "max_tokens": 4096, "temperature": 0.7},
                timeout=120,
            )
            if r.status_code == 429:
                self._rate_limit_count[model] = self._rate_limit_count.get(model, 0) + 1
                return None, model, "rate_limited"
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            return content, model, None
        except requests.exceptions.Timeout:
            return None, model, "timeout"
        except requests.exceptions.HTTPError as e:
            return None, model, f"http_{e.response.status_code}"
        except Exception as e:
            return None, model, str(e)

    def chat(self, message: str, meta: Dict[str, Any] = None, sovereign_context: str = "") -> str:
        if not self.api_key:
            return "LLM not configured. Set OPENROUTER_API_KEY."

        vault_context = self._get_vault_context(message)
        system_prompt = self._build_system_prompt(vault_context=vault_context, sovereign_context=sovereign_context)

        messages = [{"role": "system", "content": system_prompt}]
        for h in self._history[-self._max_history:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})

        start_idx = self._model_index
        for attempt in range(len(MODEL_CHAIN)):
            model = MODEL_CHAIN[(start_idx + attempt) % len(MODEL_CHAIN)]
            response, used_model, error = self._call_llm(messages, model)
            if response:
                self._model_index = MODEL_CHAIN.index(used_model)
                self._history.append({"role": "user", "content": message})
                self._history.append({"role": "assistant", "content": response})
                return response
            continue

        return "All LLM providers failed. Rate limits may have been exceeded. Try again in a minute."

    def clear_history(self):
        self._history.clear()


if __name__ == "__main__":
    agent = ChatAgent()
    print(f"Primary model: {agent.current_model}")
    resp = agent.chat("What is the Primary Observer in one sentence?")
    print(f"\n[{agent.current_model}]")
    print(resp)
