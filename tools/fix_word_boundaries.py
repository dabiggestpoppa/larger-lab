"""Fix word boundary matching in greeting and capabilities patterns."""
import pathlib

p = pathlib.Path(r"C:\Users\wifik\Desktop\projects\larger-lab\core\spawn\agent_spawner.py")
content = p.read_text(encoding="utf-8")

# Fix greeting pattern
old_greeting = '        if any(w in lower for w in ["hello", "hi", "hey", "howdy", "greetings"]):'
new_greeting = '        if any(re.search(r"\\b" + re.escape(w) + r"\\b", lower) for w in ["hello", "hi", "hey", "howdy", "greetings"]):'
content = content.replace(old_greeting, new_greeting)

# Fix capabilities pattern
old_caps = '        if any(w in lower for w in ["what can you do", "what do you do", "help", "capabilities"]):'
new_caps = '        if any(re.search(r"\\b" + re.escape(w) + r"\\b", lower) for w in ["what can you do", "what do you do", "help", "capabilities"]):'
content = content.replace(old_caps, new_caps)

# Also fix the thanks and goodbye patterns
old_thanks = '        if any(w in lower for w in ["thanks", "thank you", "thx", "ty", "appreciate"]):'
new_thanks = '        if any(re.search(r"\\b" + re.escape(w) + r"\\b", lower) for w in ["thanks", "thank you", "thx", "ty", "appreciate"]):'
content = content.replace(old_thanks, new_thanks)

old_bye = '        if any(w in lower for w in ["bye", "goodbye", "see you", "later", "take care"]):'
new_bye = '        if any(re.search(r"\\b" + re.escape(w) + r"\\b", lower) for w in ["bye", "goodbye", "see you", "later", "take care"]):'
content = content.replace(old_bye, new_bye)

# Fix status pattern
old_status = '        if any(w in lower for w in ["how are you", "how\'s it going", "what\'s up", "status", "how do you do", "how are you doing", "how\'s everything"]):'
new_status = '        if any(re.search(r"\\b" + re.escape(w) + r"\\b", lower) for w in ["how are you", "how\'s it going", "what\'s up", "status", "how do you do", "how are you doing", "how\'s everything"]):'
content = content.replace(old_status, new_status)

# Fix identity pattern
old_id = '        if any(w in lower for w in ["tell me about yourself", "who are you", "what are you", "tell me about you", "what type of system", "what kind of system", "who built you", "who made you", "who created you"]):'
new_id = '        if any(re.search(r"\\b" + re.escape(w) + r"\\b", lower) for w in ["tell me about yourself", "who are you", "what are you", "tell me about you", "what type of system", "what kind of system", "who built you", "who made you", "who created you"]):'
content = content.replace(old_id, new_id)

# Fix system knowledge pattern
old_sys = '        if any(w in lower for w in ["what is srra", "what is oce", "what is oph", "how does the field work", "how does the observer work", "tell me about the field", "tell me about the system"]):'
new_sys = '        if any(re.search(r"\\b" + re.escape(w) + r"\\b", lower) for w in ["what is srra", "what is oce", "what is oph", "how does the field work", "how does the observer work", "tell me about the field", "tell me about the system"]):'
content = content.replace(old_sys, new_sys)

# Fix observer/field/entropy pattern
old_obs = '        if any(w in lower for w in ["observer", "field", "topology", "entropy"]):'
new_obs = '        if any(re.search(r"\\b" + re.escape(w) + r"\\b", lower) for w in ["observer", "field", "topology", "entropy"]):'
content = content.replace(old_obs, new_obs)

# Make sure re is imported at the top of the method
# Check if re is already imported
if "import re" not in content[:content.find("def _build_dynamic_response")]:
    # Add import at module level
    content = "import re\n" + content

p.write_text(content, encoding="utf-8")
print("DONE - fixed word boundary matching for all patterns")
