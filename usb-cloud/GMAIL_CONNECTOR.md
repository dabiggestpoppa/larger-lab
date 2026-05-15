# Gmail Connector Setup for OpenClaw

> Connect OpenClaw to Gmail so it can read/send emails, find trading-related info, and automate tasks.

---

## Option 1: Gmail MCP Server (Recommended)

### Setup
1. Go to https://console.cloud.google.com/
2. Create a new project: `larger-lab-agents`
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json`
6. Run the Gmail MCP server on the cloud VM

### Install Gmail MCP
```bash
# On the cloud VM
npm install -g @modelcontextprotocol/server-gmail
```

### Configure in OpenClaw
Add to `~/.openclaw/openclaw.json`:
```json
{
  "mcp": {
    "servers": {
      "gmail": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-gmail"],
        "env": {
          "GOOGLE_APPLICATION_CREDENTIALS": "/root/larger-lab/credentials.json"
        }
      }
    }
  }
}
```

### First Run
```bash
# This will open a browser for OAuth auth
npx @modelcontextprotocol/server-gmail
```

---

## Option 2: rclone Gmail Backend

### Setup
```bash
# On the cloud VM
rclone config
# Select "Google Drive" → follow OAuth flow
# This gives access to Gmail labels via Drive API
```

---

## Option 3: Direct Gmail API with Python

### Install
```bash
pip install google-api-python-auth google-auth-httplib2 google-api-python-client
```

### Quick Test Script
```python
# gmail_test.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

service = get_gmail_service()
results = service.users().messages().list(userId='me', maxResults=10).execute()
messages = results.get('messages', [])
for msg in messages:
    print(msg['id'])
```

---

## Gmail Search Queries for Trading

Once connected, OpenClaw can search for:
- `from:metatrader subject:signal` — MT4/MT5 signal emails
- `subject:Cerebus` — Cerebus strategy emails
- `from:oanda.com` — Oanda trading notifications
- `subject:backtest` — Backtest results
- `has:attachment filename:.mq5` — MQL5 file attachments
- `from:tradingview.com` — TradingView alerts

---

## Security Notes
- Use a dedicated Gmail account (kemettrucking@gmail.com)
- Enable 2FA on the Google account
- Use OAuth 2.0, never store passwords in plain text
- Restrict API scopes to read-only unless sending is needed
- Store credentials.json and token.json outside the repo
