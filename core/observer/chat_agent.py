"""Chat agent for Primary Observer — with tool calling support."""
import os, json, requests, datetime, time
from typing import Dict, Any, List, Optional

MODEL_CHAIN = [
    "openrouter/owl-alpha",
    "moonshotai/kimi-k2.6:free",
    "poolside/laguna-m.1:free",
]

from core.observer.tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS


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
            "You are the Primary Observer (PO) — the operational intelligence layer for Larger-Lab.\n"
            "You have access to tools that let you read files, list directories, run commands, and check git.\n"
            "Use these tools to actually investigate the codebase and provide real answers.\n"
            f"- Current time: {ts}\n"
            f"{sov}\n\n"
            "## Available Tools\n"
            "When you need information, respond with a tool call in this format:\n"
            "```tool\n"
            "{\"tool\": \"tool_name\", \"args\": {\"arg1\": \"value1\"}}\n"
            "```\n"
            "Available tools:\n"
            "- list_directory(path, max_depth, max_items) — explore file tree\n"
            "- read_file(path, start_line, max_lines) — read file contents\n"
            "- run_command(command, timeout, cwd) — execute shell commands\n"
            "- git_status() — check modified/added/deleted files\n"
            "- git_log(count) — recent commits\n"
            "- search_files(pattern, path) — find files by name glob\n"
            "- search_content(query, path, file_pattern) — search text in files\n\n"
            "## Rules\n"
            "1. ALWAYS use tools to get real data before answering questions about the codebase\n"
            "2. Call tools one at a time, wait for results, then decide next step\n"
            "3. After gathering info, provide a natural conversational response\n"
            "4. Don't say 'let me check' without actually calling a tool\n"
            "5. Be concise — don't dump entire file contents unless asked\n\n"
            "## Style\n"
            "Concise. Technical when needed, casual when appropriate. No filler.\n"
            "Reference specific files, commits by name when relevant.\n"
            f"{ctx}\n\n"
            "When asked for status, use git_status() and git_log() to get real data first."
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

    def _call_llm(self, messages: List[Dict[str, str]], model: str, tools: list = None):
        """Returns (content, tool_calls, model, error).
        
        tool_calls is a list of {tool, args} dicts if the LLM requested tool execution,
        or None if the LLM returned a direct response.
        """
        payload = {"model": model, "messages": messages, "max_tokens": 4096, "temperature": 0.7}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            r = requests.post(
                self.base_url,
                headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=120,
            )
            if r.status_code == 429:
                return None, None, model, "rate_limited"
            if r.status_code >= 400:
                return None, None, model, "http_" + str(r.status_code) + ": " + r.text[:200]
            data = r.json()
            if "choices" in data and len(data["choices"]) > 0:
                c = data["choices"][0]
                if isinstance(c, dict):
                    msg = c.get("message", {})
                    if isinstance(msg, dict):
                        content = msg.get("content", "") or ""
                        # Check for native OpenAI tool_calls
                        native_tool_calls = msg.get("tool_calls", None)
                        if native_tool_calls:
                            # Convert to our format
                            parsed_calls = []
                            for tc in native_tool_calls:
                                func = tc.get("function", {})
                                try:
                                    args = json.loads(func.get("arguments", "{}"))
                                except json.JSONDecodeError:
                                    args = {}
                                parsed_calls.append({"tool": func.get("name", ""), "args": args})
                            return content, parsed_calls, model, None
                        return content, None, model, None
                    if "text" in c:
                        return c["text"], None, model, None
            if "error" in data:
                return None, None, model, "api_error: " + json.dumps(data["error"])[:200]
            if "output" in data:
                return str(data["output"]), None, model, None
            return None, None, model, "unknown_format: " + json.dumps(data)[:200]
        except requests.exceptions.Timeout:
            return None, None, model, "timeout"
        except Exception as e:
            return None, None, model, str(e)[:200]

    def _parse_tool_call(self, content: str) -> Optional[Dict]:
        """Parse a tool call from LLM response. Supports multiple formats:
        1. ```tool {"tool": "name", "args": {...}} ```
        2. <tool>{"tool": "name", "args": {...}}</tool>
        3. <function_calls>...</function_calls>
        """
        # Format 1: ```tool ... ``` code blocks
        if "```tool" in content:
            try:
                start = content.index("```tool") + len("```tool")
                end = content.index("```", start)
                tool_json = content[start:end].strip()
                return json.loads(tool_json)
            except (ValueError, json.JSONDecodeError):
                pass

        # Format 2: <tool>...</tool> XML tags
        if "<tool>" in content and "</tool>" in content:
            try:
                start = content.index("<tool>") + len("<tool>")
                end = content.index("</tool>", start)
                tool_json = content[start:end].strip()
                return json.loads(tool_json)
            except (ValueError, json.JSONDecodeError):
                pass

        # Format 3: <function_calls> with <invoke> tags
        if "<function_calls>" in content:
            try:
                import re
                invoke_match = re.search(r'<invoke[^>]*name="([^"]+)"[^>]*>(.*?)</invoke>', content, re.DOTALL)
                if invoke_match:
                    tool_name = invoke_match.group(1)
                    args_str = invoke_match.group(2).strip()
                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {"raw": args_str}
                    return {"tool": tool_name, "args": args}
            except Exception:
                pass

        # Format 4: JSON object at start of response
        content_stripped = content.strip()
        if content_stripped.startswith("{") and '"tool"' in content_stripped:
            try:
                obj = json.loads(content_stripped[:content_stripped.index("}") + 1])
                if "tool" in obj:
                    return obj
            except (json.JSONDecodeError, ValueError):
                pass

        return None

    def _execute_tool(self, tool_call: Dict) -> str:
        """Execute a tool call and return the result."""
        tool_name = tool_call.get("tool", "")
        args = tool_call.get("args", {})
        if tool_name not in TOOL_FUNCTIONS:
            return f"Unknown tool: {tool_name}. Available: {', '.join(TOOL_FUNCTIONS.keys())}"
        try:
            result = TOOL_FUNCTIONS[tool_name](**args)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"

    def chat(self, message: str, sovereign_context: str = "", max_tool_rounds: int = 5,
             progress_callback=None) -> str:
        """Chat with tool-calling support. LLM can request tool executions.

        Args:
            progress_callback: Optional callable(event_type, data) that receives
                progress events during tool execution:
                - ("round", {"round": N, "max": M})
                - ("tool_call", {"tool": name, "args": {...}})
                - ("tool_result", {"tool": name, "result": str})
                - ("final", {"response": str})
        """
        if not self.api_key:
            return "LLM not configured. Set OPENROUTER_API_KEY."

        def _notify(event_type, data=None):
            if progress_callback:
                try:
                    progress_callback(event_type, data or {})
                except Exception:
                    pass

        vault_context = self._get_vault_context(message)
        system_prompt = self._build_system_prompt(vault_context=vault_context, sovereign_context=sovereign_context)

        messages = [{"role": "system", "content": system_prompt}]
        for h in self._history[-self._max_history:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})

        for round_num in range(max_tool_rounds):
            _notify("round", {"round": round_num + 1, "max": max_tool_rounds})

            # Try each model in the chain
            resp, tool_calls, used_model, err = None, None, None, None
            for attempt in range(len(MODEL_CHAIN)):
                model = MODEL_CHAIN[(self._model_index + attempt) % len(MODEL_CHAIN)]
                resp, tool_calls, used_model, err = self._call_llm(messages, model, tools=TOOL_DEFINITIONS)
                if resp or tool_calls:
                    self._model_index = MODEL_CHAIN.index(used_model)
                    break

            if not resp and not tool_calls:
                _notify("error", {"message": "All LLM providers failed"})
                return "All LLM providers failed."

            # Handle native OpenAI tool_calls
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc.get("tool", "unknown")
                    tool_args = tc.get("args", {})
                    _notify("tool_call", {"tool": tool_name, "args": tool_args})

                    tool_result = self._execute_tool(tc)
                    _notify("tool_result", {"tool": tool_name, "result": tool_result[:300]})

                    messages.append({"role": "assistant", "content": resp or "", "tool_calls": [
                        {"id": f"tc_{round_num}", "type": "function", "function": {"name": tool_name, "arguments": json.dumps(tool_args)}}
                    ]})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": f"tc_{round_num}",
                        "content": tool_result[:2000],
                    })
                continue

            # Handle parsed tool calls from content (```tool blocks, XML, etc.)
            parsed_tool_call = self._parse_tool_call(resp) if resp else None
            if parsed_tool_call:
                tool_name = parsed_tool_call.get("tool", "unknown")
                tool_args = parsed_tool_call.get("args", {})
                _notify("tool_call", {"tool": tool_name, "args": tool_args})

                tool_result = self._execute_tool(parsed_tool_call)
                _notify("tool_result", {"tool": tool_name, "result": tool_result[:300]})

                messages.append({"role": "assistant", "content": resp})
                messages.append({
                    "role": "user",
                    "content": f"Tool result for {tool_name}:\n{tool_result}\n\nUse this to respond to the user."
                })
                continue

            # No tool calls — this is the final response
            self._history.append({"role": "user", "content": message})
            self._history.append({"role": "assistant", "content": resp})
            _notify("final", {"response": resp})
            return resp

        # Max rounds — ask for final response
        messages.append({"role": "user", "content": "Max tool calls reached. Provide your final response."})
        for attempt in range(len(MODEL_CHAIN)):
            model = MODEL_CHAIN[(self._model_index + attempt) % len(MODEL_CHAIN)]
            resp, _, used_model, err = self._call_llm(messages, model)
            if resp:
                self._history.append({"role": "user", "content": message})
                self._history.append({"role": "assistant", "content": resp})
                _notify("final", {"response": resp})
                return resp
        return "All LLM providers failed after tool calls."

    def clear_history(self):
        self._history.clear()
