#!/usr/bin/env python3
"""Wire PO provider into VTuber factory and create conf.yaml."""
import os
import shutil

factory_path = r"c:\Users\wifik\Desktop\projects\larger-lab\vtuber_integration\Open-LLM-VTuber\src\open_llm_vtuber\agent\stateless_llm_factory.py"

with open(factory_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
old_import = "from .stateless_llm.claude_llm import AsyncLLM as ClaudeLLM\n\n\nclass LLMFactory:"
new_import = "from .stateless_llm.claude_llm import AsyncLLM as ClaudeLLM\nfrom .stateless_llm.po_llm import POProvider\n\n\nclass LLMFactory:"
content = content.replace(old_import, new_import)

# Add po_llm case before else
old_claude = ('        elif llm_provider == "claude_llm":\n'
              '            return ClaudeLLM(\n'
              '                system=kwargs.get("system_prompt"),\n'
              '                base_url=kwargs.get("base_url"),\n'
              '                model=kwargs.get("model"),\n'
              '                llm_api_key=kwargs.get("llm_api_key"),\n'
              '            )\n'
              '        else:')

new_claude = ('        elif llm_provider == "claude_llm":\n'
              '            return ClaudeLLM(\n'
              '                system=kwargs.get("system_prompt"),\n'
              '                base_url=kwargs.get("base_url"),\n'
              '                model=kwargs.get("model"),\n'
              '                llm_api_key=kwargs.get("llm_api_key"),\n'
              '            )\n'
              '        elif llm_provider == "po_llm":\n'
              '            return POProvider(\n'
              '                model=kwargs.get("model", "po"),\n'
              '                base_url=kwargs.get("base_url", "http://localhost:8000"),\n'
              '                llm_api_key=kwargs.get("llm_api_key", ""),\n'
              '                temperature=kwargs.get("temperature", 0.7),\n'
              '            )\n'
              '        else:')

content = content.replace(old_claude, new_claude)

with open(factory_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Factory updated successfully")

# Create conf.yaml
conf_path = r"c:\Users\wifik\Desktop\projects\larger-lab\vtuber_integration\Open-LLM-VTuber\conf.yaml"
default_conf = r"c:\Users\wifik\Desktop\projects\larger-lab\vtuber_integration\Open-LLM-VTuber\config_templates\conf.default.yaml"
shutil.copy2(default_conf, conf_path)

with open(conf_path, 'r', encoding='utf-8') as f:
    conf = f.read()

conf = conf.replace("llm_provider: 'ollama_llm'", "llm_provider: 'po_llm'")

old_ollama = ("      ollama_llm:\n"
              "        base_url: 'http://localhost:11434/v1'\n"
              "        model: 'qwen2.5:latest'\n"
              "        temperature: 1.0\n"
              "        keep_alive: -1\n"
              "        unload_at_exit: True")

new_ollama = ("      ollama_llm:\n"
              "        base_url: 'http://localhost:11434/v1'\n"
              "        model: 'qwen2.5:latest'\n"
              "        temperature: 1.0\n"
              "        keep_alive: -1\n"
              "        unload_at_exit: True\n"
              "\n"
              "      po_llm:\n"
              "        base_url: 'http://localhost:8000'\n"
              "        model: 'po'\n"
              "        llm_api_key: ''\n"
              "        temperature: 0.7")

conf = conf.replace(old_ollama, new_ollama)

with open(conf_path, 'w', encoding='utf-8') as f:
    f.write(conf)

print("conf.yaml created successfully")
print("Done!")