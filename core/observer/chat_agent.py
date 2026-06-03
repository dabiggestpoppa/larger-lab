"""Chat agent for Primary Observer — OC2-style verbose output with error handling."""
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
        ctx = f"\n## Vault Context\n{vault_context}" if vault_context else ""
        sov = f"\n{sovereign_context}" if sovereign_context else ""
        return f"""You are the Primary Observer (PO) — sovereign operational interface for Larger-Lab.

## Identity
- Speaking face of OCE (Observer Core Engine)
- Direct interface between the operator and the cognitive field
- You have access to the operational vault, service status, agent orchestration
- Current time: {ts}
{sov}

## CRITICAL: Show Your Work (OC2 Style)
ALWAYS show your reasoning process:
1. **Scan/Search** — mention what you're checking
2. **Evidence** — quote specific findings
3. **Analysis** — explain what it means
4. **Conclusion** — clear answer with next steps

## Output Format (Telegram Markdown)
- **Bold** for headers, key terms
- `code` for commands, paths, ports, values
- • Bullet lists for items
- 1. 2. 3. Numbered steps
- ✅ ❌ ⚠️ 🔄 📊 🔍 emoji indicators
- ## Section headers
- ```code blocks``` for data/configs

## Response Templates

For workspace/progress queries:
📊 **Workspace Scan**
🔍 **Sources Checked:**
• `file/path.md` — finding
• vault search "keyword" — N results
**Summary:** [what you found]
**Status:** ✅/❌/⚠️

For status queries:
📊 **System Status**
├── Service: ✅/❌ (detail)
└── **Overall:** [summary]

## Behavior
- NEVER give one-line answers — always show work
- Reference specific files, commits, vault notes by name
- Be technical and direct — no filler
- End with clear next steps

{ctx}

You are the operator's direct line to the entire system. Always show your work like OC2."""

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

    def _call_llm(self, messages: List[Dict[str, str]], model: str) -> tuple:
        """Call OpenRouter. Returns (content_or_None, model, error_or_None)."""
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
                return None, model, "rate_limited"
            if r.status_code >= 400:
                return None, model, f"http_{r.status_code}: {r.text[:200]}"
            data = r.json()
            # Handle different response formats safely
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if isinstance(choice, dict):
                    if "message" in choice and isinstance(choice["message"], dict) and "content" in choice["message"]:
                        return choice["message"]["content"], model, None
                    if "text" in choice:
                        return choice["text"], model, None
            # Check for error in response
            if "error" in data:
                return None, model, f"api_error: {json.dumps(data['error'])[:200]}"
            return None, model, f"unexpected_format: {json.dumps(data)[:200]}"
        except requests.exceptions.Timeout:
            return None, model, "timeout"
        except Exception as e:
            return None, model, str(e)[:200]

    def chat(self, message: str, sovereign_context: str = "") -> str:
        if not self.api_key:
            return "❌ LLM not configured. Set OPENROUTER_API_KEY."

        vault_context = self._get_vault_context(message)
        system_prompt = self._build_system_prompt(vault_context=vault_context, sovereign_context=sovereign_context)

        messages = [{"role": "system", "content": system_prompt}]
        for h in self._history[-self._max_history:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})

        errors = []
        for attempt in range(len(MODEL_CHAIN)):
            model = MODEL_CHAIN[(self._model_index + attempt) % len(MODEL_CHAIN)]
            response, used_model, error = self._call_llm(messages, model)
            if response:
                self._model_index = MODEL_CHAIN.index(used_model)
                self._history.append({"role": "user", "content": message})
                self._history.append({"role": "assistant", "content": response})
                return response
            errors.append(f"{model}: {error}")
            continue

        return f"❌ All LLM providers failed:\n" + "\n".join(errors)

    def clear_history(self):
        self._history.clear()
