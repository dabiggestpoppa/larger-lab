"""Fix the default handler in _build_dynamic_response."""
import pathlib

p = pathlib.Path(r"C:\Users\wifik\Desktop\projects\larger-lab\core\spawn\agent_spawner.py")
content = p.read_text(encoding="utf-8")

# Find the start marker
start_marker = "# ── Default: substantive conversational response ──"
start_idx = content.find(start_marker)
assert start_idx > 0, f"Could not find start marker"

# Find the end - the return statement for this block
end_marker = '        return "\n".join(lines)'
end_idx = content.find(end_marker, start_idx + len(start_marker))
assert end_idx > 0, f"Could not find end marker after position {start_idx}"
end_idx += len(end_marker)

# The new default handler
new_handler = '''        # ── Default: analyze message content and respond dynamically ──
        # Check if this sounds like they want to DO something
        action_words = ["let's", "can you", "could you", "would you", "please",
                        "i want", "i need", "should we", "show me", "tell me",
                        "give me", "i'd like", "help me"]
        if any(w in lower for w in action_words):
            lines.append("I can definitely help with that.")
            lines.append("")
            truncated = text[:150] + ('...' if len(text) > 150 else '')
            lines.append("Here's what I'm thinking: **" + truncated + "**")
            lines.append("")
            tt = consensus.task_type.replace('_', ' ')
            lines.append("The consensus engine routes this as **" + tt + "** at **" + consensus.complexity + "** complexity.")
            lines.append("")
            if consensus.agreement_score > 0.7:
                lines.append("The observers are in strong agreement. Want me to proceed, or do you want to adjust the approach?")
            elif consensus.agreement_score > 0.4:
                lines.append("Moderate consensus among observers. I can proceed, or we can refine first.")
            else:
                lines.append("The observers don't fully agree on the best path. Can you give me more details?")
            return "\\n".join(lines)

        # Check if this is a factual question we can answer directly
        factual = self._try_factual_answer(lower)
        if factual:
            lines.append(factual)
            lines.append("")
            lines.append("Anything else you'd like to know?")
            return "\\n".join(lines)

        # Truly open-ended: ask a clarifying question specific to what was said
        truncated = text[:120] + ('...' if len(text) > 120 else '')
        lines.append('Interesting — "' + truncated + '"')
        lines.append("")

        # Use conversation history for continuity
        history = context.get("conversation_history", [])
        if history and len(history) > 1:
            last_topic = context.get("last_domain", "")
            if last_topic and last_topic not in ["general", "conversation"]:
                lines.append("We were just discussing " + last_topic.replace('_', ' ') + ". Want to continue that thread, or is this something new?")
                lines.append("")

        # Reference the consensus analysis
        tt = consensus.task_type.replace('_', ' ')
        pct = str(int(consensus.agreement_score * 100))
        lines.append("My analysis: this reads as **" + tt + "** complexity. Observer mesh agreement: **" + pct + "%**.")
        lines.append("")
        lines.append("What would you like to do with this? I can dive deeper, take action, or keep chatting.")

        return "\\n".join(lines)'''

content = content[:start_idx] + new_handler + content[end_idx:]
p.write_text(content, encoding="utf-8")
print("DONE - default handler replaced successfully")
print(f"Replaced {end_idx - start_idx} chars with {len(new_handler)} chars")
