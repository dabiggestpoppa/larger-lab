# Discord Bot Setup Guide — Separate Bots for Hermes & OpenClaw

## Step 1: Create Two Discord Bot Applications

### Bot 1: Hermes
1. Go to https://discord.com/developers/applications
2. Click **"New Application"** → Name it **"Hermes"**
3. Go to **Bot** tab → Click **"Add Bot"**
4. Under **Privileged Gateway Intents** → Enable **"Message Content Intent"**
5. Click **"Reset Token"** → Copy the token
6. Go to **OAuth2** → **URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Read Messages`, `Send Messages`, `Read Message History`, `Use Slash Commands`, `Manage Webhooks`
7. Copy the generated URL and open it in your browser to invite Hermes to your server

### Bot 2: OpenClaw
1. Go to https://discord.com/developers/applications
2. Click **"New Application"** → Name it **"OpenClaw"**
3. Go to **Bot** tab → Click **"Add Bot"**
4. Under **Privileged Gateway Intents** → Enable **"Message Content Intent"**
5. Click **"Reset Token"** → Copy the token
6. Go to **OAuth2** → **URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Read Messages`, `Send Messages`, `Read Message History`, `Use Slash Commands`, `Manage Webhooks`
7. Copy the generated URL and open it in your browser to invite OpenClaw to your server

## Step 2: Add Tokens to .env

Edit `C:\Users\wifik\Desktop\projects\larger-lab\.env`:

```bash
DISCORD_HERMES_TOKEN=your_hermes_token_here
DISCORD_OPENCLAW_TOKEN=your_openclaw_token_here
```

## Step 3: Run the Bots

```bash
cd discord-agent-hq

# Option A: Run both at once
python run_both.py

# Option B: Run separately (two terminals)
python hermes_bot.py
python openclaw_bot.py
```

## Step 4: Test in Discord

- `@Hermes status` → reads project progress
- `@Hermes workspace` → lists workspace files
- `@Hermes plan: add new feature` → logs a plan
- `@OpenClaw status` → checks progress
- `@OpenClaw edit progress: tested discord bot` → adds to progress
- `@OpenClaw run backtest_cerebus.py` → runs a script
- `@OpenClaw create file: test.txt | hello` → creates a file

## Bot Commands (Slash)

- `/hermes <message>` — talk to Hermes
- `/openclaw <message>` — talk to OpenClaw
- `/status` — get project status
