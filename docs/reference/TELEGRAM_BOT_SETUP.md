# Telegram Bot Registration Guide

## Step 1: Create a Bot with BotFather

1. Open Telegram and search for **@BotFather** (the official Telegram bot)
2. Start a chat and send: `/newbot`
3. BotFather will ask for a **name** — enter: `PrimaryObserver` (or whatever you like)
4. BotFather will ask for a **username** — must end in `bot`, e.g.: `primary_observer_bot`
5. BotFather will give you a **token** like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
6. **Save this token** — you'll need it to run the gateway

## Step 2: Configure the Bot (Optional but Recommended)

Send these commands to @BotFather:

```
/setdescription — Set bot description: "Primary Observer — sovereign operational interface for Larger-Lab"
/setabouttext — Set about text: "Operational continuity layer. Not a chatbot."
/setuserpic — Upload a profile picture
/setcommands — Set command menu:
  status — Check all service ports
  spawn — Spawn an agent
  report — Operational summary
  memory — Search vault notes
  graph — Knowledge graph summary
  research — Research a topic
  sync — Sync vault state
  task — Create/list tasks
  trace — Trace execution
  failure — Log structured failure
  help — Show all commands
```

## Step 3: Get Your Chat ID

1. Start a chat with your new bot (tap the username, send any message)
2. Open this URL in a browser (replace `<TOKEN>`):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Look for `"chat":{"id":123456789` — that number is your **Chat ID**
4. Save it for access control (optional)

## Step 4: Run the Gateway

```powershell
# In the larger-lab workspace:
$env:TELEGRAM_TOKEN = '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
python scripts\start_telegram_gateway.py
```

## Step 5: Test

Send these messages to your bot:
- `/help` — see all commands
- `/status` — check service ports
- `/memory observer` — search vault
- `/spawn research analyze something` — spawn an agent

## Security Notes

- **Never commit the token** to git — use environment variables
- The gateway validates messages come from Telegram's API
- For production: add chat_id whitelist in `telegram_gateway.py`
- BotFather token format: `<numeric_id>:<alphanumeric_string>`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Set TELEGRAM_TOKEN" error | Export the env var before running |
| No response | Check bot token, ensure you messaged the bot first |
| Port conflicts | Gateway doesn't use a port — it polls Telegram's API |
| SSL errors | Update Python/certifi: `pip install --upgrade certifi` |
