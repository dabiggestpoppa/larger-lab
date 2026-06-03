"""Chat agent for Primary Observer — with robust response parsing."""
import os, json, requests, datetime, time
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

    @property
    def current_model(self) -> str:
        return MODEL_CHAIN[self._model_index % len(MODEL_CHAIN)]

    def _build_system_prompt(self, vault_context: str = "", sovereign_context: str = "") -> str:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        ctx = "\n## Vault Context\n" + vault_context if vault_context else ""
        sov = "\n" + sovereign_context if sovereign_context else ""
        return (
            "You are the Primary Observer (PO) — sovereign operational interface for Larger-Lab.\n"
            "- Speaking face of OCE (Observer Core Engine)\n"
            "- You have access to the operational vault, service status, agent orchestration\n"
            f"- Current time: {ts}\n"
            f"{sov}\n\n"
            "## Output Format\n"
            "Use Telegram markdown: **bold**, `code`, • bullets, ✅❌⚠️🔄📊🔍 emoji\n"
            "Show your work: scan → evidence → analysis → conclusion\n"
            "Reference specific files, commits, vault notes by name\n"
            "Be technical and direct — no filler\n"
            f"{ctx}\n\n"
            "Respond like OC2 — structured, informative, with clear visual hierarchy."
        )

    def _get_vault_context(self, message: str) -> str:
        try:
            from core.observer.vault import Vault
            v = Vault()
            words = message.lower().split()
            stop = {"the","a","an","and","or","to","of","in","on","for","is","are","it","i","you","me","my","what","how","why","when","where","do","does","can","could","would","should","this","that","these","those"}
            keywords = [w for w in words if w not in stop and len(w) > 3][:5]
            if not keywords: return ""
            hits = v.search_notes(keywords, max_results=5)
            if not hits: return ""
            return "\n".join([f"- `{h['path']}`: {h['snippet'][:150]}" for h in hits])
        except:
            return ""

    def _call_llm(self, messages: List[Dict[str, str]], model: str):
        """Returns (content, model, error)."""
        try:
            r = requests.post(
                self.base_url,
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json",
                },
                json={"model": model, "messages": messages, "max_tokens": 4096, "temperature": 0.7},
                timeout=120,
            )
            if r.status_code == 429:
                return None, model, "rate_limited"
            if r.status_code >= 400:
                return None, model, "http_" + str(r.status_code) + ": " + r.text[:200]
            data = r.json()
            # Try multiple response formats
            if "choices" in data and len(data["choices"]) > 0:
                c = data["choices"][0]
                if isinstance(c, dict):
                    if "message" in c and isinstance(c["message"], dict):
                        return c["message"].get("content", ""), model, None
                    if "text" in c:
                        return c["text"], model, None
            if "error" in data:
                return None, model, "api_error: " + json.dumps(data["error"])[:200]
            if "output" in data:
                return str(data["output"]), model, None
            return None, model, "unknown_format: " + json.dumps(data)[:200]
        except requests.exceptions.Timeout:
            return None, model, "timeout"
        except Exception as e:
            return None, model, str(e)[:200]

    def chat(self, message: str, sovereign_context: str = "") -> str:
        if not self.api_key:
            return "LLM not configured. Set OPENROUTER_API_KEY."
        vault_context = self._get_vault_context(message)
        system_prompt = self._build_system_prompt(vault_context=vault_context, sovereign_context=sovereign_context)
        messages = [{"role": "system", "content": system_prompt}]
        for h in self._history[-self._max_history:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})
        for attempt in range(len(MODEL_CHAIN)):
            model = MODEL_CHAIN[(self._model_index + attempt) % len(MODEL_CHAIN)]
            resp, used_model, err = self._call_llm(messages, model)
            if resp:
                self._model_index = MODEL_CHAIN.index(used_model)
                self._history.append({"role": "user", "content": message})
                self._history.append({"role": "assistant", "content": resp})
                return resp
            continue
        return "All LLM providers failed."

    def clear_history(self):
        self._history.clear()
