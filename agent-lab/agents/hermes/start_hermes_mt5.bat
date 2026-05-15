@echo off
REM Start Hermes MT5 Strategy Agent
REM Uses only free OpenRouter models

echo Starting Hermes MT5 Agent...
echo Goal: Develop profitable MT5 strategy from CEREBUS manual

REM Set API key (replace with your actual key)
set OPENROUTER_API_KEY=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

REM Activate virtual environment and run
cd /d C:\Users\wifik\Desktop\projects\larger-lab
call .venv\Scripts\activate.bat
python agent-lab\agents\hermes\hermes_mt5_agent.py

pause