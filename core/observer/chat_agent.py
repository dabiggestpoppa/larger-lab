"""Real chat agent for Primary Observer Telegram bot.

Uses OpenRouter API with model failover chain:
1. moonshotai/kimi-k2.6:free (primary — free)
2. openrouter/owl-alpha (backup 1 — free)
3. poolside/laguna-m.1:free (backup 2 — free)

Features:
- Vault context injection before every response
- Conversation history (last 20 turns)
- Structured system prompt with operational context
- Automatic failover on rate limit (429) or error
"""
import os
import json
import requests
import datetime
import time
from typing import Dict, Any, List, Optional


# Model failover chain — all free models
MODEL_CHAIN = [
    "moonshotai/kimi-k2.6:free",
    "openrouter/owl-alpha",
    "poolside/laguna-m.1:free",
]


class ChatAgent:
    """LLM-powered chat agent with vault context, history, and model failover."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self._history: List[Dict[str, str]] = []
        self._max_history = 20
        self._model_index = 0  # current position in MODEL_CHAIN
        self._rate_limit_count: Dict[str, int] = {}  # track rate limits per model

    @property
    def current_model(self) -> str:
        return MODEL_CHAIN[self._model_index % len(MODEL_CHAIN)]

    def _next_model(self) -> str:
        """Advance to next model in chain (on rate limit)."""
        self._model_index += 1
        return self.current_model

    def _build_system_prompt(self, vault_context: str = "", sovereign_context: str = "") -> str:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        ctx = f"\n## Vault Context\n{vault_context}" if vault_context else ""
        sov = f"\n{sovereign_context}" if sovereign_context else ""
        return f"""You are the Primary Observer — sovereign operational interface for Larger-Lab.

You are not a chatbot. You are an operational continuity layer.

## Identity
- Speaking face of OCE (Observer Core Engine)
- Direct interface between the operator and the cognitive field
- You have access to the operational vault, service status, and agent orchestration
- Current time: {ts}
{sov}

## Behavior
- Be concise and direct — no filler, no "Great question!"
- Reference vault knowledge when relevant
- If you don't know, say so directly
- Use technical language appropriate for the operator
- You can execute commands: /status /spawn /memory /graph /report /task /failure

{ctx}

Respond naturally. You are the operator's direct line to the entire system."""

    def _get_vault_context(self, message: str) -> str:
        """Search vault for relevant context."""
        try:
            from core.observer.vault import Vault
            v = Vault()
            words = message.lower().split()
            stop = {"the","a","an","and","or","to","of","in","on","for","is","are","it","i","you","me","my","what","how","why","when","where","do","does","can","could","would","should","this","that","these","those"}
            keywords = [w for w in words if w not in stop and len(w) > 3][:5]
            if not keywords:
                return ""
            hits = v.search_notes(keywords, max_results=3)
            if not hits:
                return ""
            lines = []
            for h in hits:
                lines.append(f"- {h['path']}: {h['snippet'][:120]}")
            return "\n".join(lines)
        except Exception:
            return ""

    def _call_llm(self, messages: List[Dict[str, str]], model: str) -> tuple:
        """Call OpenRouter API. Returns (response_text, model_used, error)."""
        try:
            r = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/dabiggestpoppa/larger-lab",
                    "X-Title": "Primary Observer",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 2048,
                    "temperature": 0.7,
                },
                timeout=60,
            )

            # Rate limited — track and signal failover
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
        """Process a chat message. Tries each model in chain on failure."""
        if not self.api_key:
            return "LLM not configured. Set OPENROUTER_API_KEY."

        vault_context = self._get_vault_context(message)
        system_prompt = self._build_system_prompt(vault_context=vault_context, sovereign_context=sovereign_context)

        messages = [{"role": "system", "content": system_prompt}]
        for h in self._history[-self._max_history:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})

        # Try each model in the chain
        start_idx = self._model_index
        for attempt in range(len(MODEL_CHAIN)):
            model = MODEL_CHAIN[(start_idx + attempt) % len(MODEL_CHAIN)]
            response, used_model, error = self._call_llm(messages, model)

            if response:
                # Success — update history and model index
                self._model_index = MODEL_CHAIN.index(used_model)
                self._history.append({"role": "user", "content": message})
                self._history.append({"role": "assistant", "content": response})
                return response

            # If rate limited or error, try next model
            continue

        # All models failed
        return "All LLM providers failed. Rate limits may have been exceeded. Try again in a minute."

    def clear_history(self):
        self._history.clear()


if __name__ == "__main__":
    agent = ChatAgent()
    print(f"Primary model: {agent.current_model}")
    print("Testing...")
    resp = agent.chat("What is the Primary Observer in one sentence?")
    print(f"\n[{agent.current_model}]")
    print(resp)
