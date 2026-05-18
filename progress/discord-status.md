# Discord Integration Status

> **Last Updated:** 2026-05-17 14:16 EDT
> **Monitor:** OWL (OC2) Sub-Agent

## Connection Status

| Metric | Value |
|--------|-------|
| **Gateway** | ✅ Running (pid 1612) |
| **Port** | 18790 (loopback) |
| **Gateway Version** | 2026.5.12 |
| **Connectivity Probe** | ✅ OK (114ms) |
| **Capability** | read-only |
| **Discord Config** | ✅ Token configured in `~/.openclaw/openclaw.json` |
| **Guild ID** | 1486771735729537085 |
| **User Allowlist** | 8258195396 |

## Uptime Info

- **Gateway Start Method:** Scheduled Task (Startup-folder login item)
- **Listener:** 127.0.0.1:18790
- **Dashboard:** http://127.0.0.1:18790/

## Available Discord Features

Based on the Discord skill configuration, the following actions are available:

| Feature | Status | Notes |
|---------|--------|-------|
| Send Messages | ✅ Available | `channel: "discord"`, target by channel/user ID |
| Send with Media | ✅ Available | File attachments via `media` parameter |
| Components v2 | ✅ Available | Rich UI (Container, TextDisplay, etc.) |
| Legacy Embeds | ⚠️ Available (not recommended) | Ignored when v2 components present |
| React to Messages | ✅ Available | Emoji reactions on messages |
| Read Messages | ✅ Available | Fetch message history with `limit` |
| Edit Messages | ✅ Available | Modify sent messages |
| Delete Messages | ✅ Available | Remove messages |
| Polls | ✅ Available | Create polls with options and duration |
| Pin Messages | ✅ Available | Pin/unpin messages |
| Thread Management | ✅ Available | Create threads from messages |
| Search | ✅ Available | Search guild messages by query |
| Presence | ⚠️ Gated | May be disabled by `channels.discord.actions.presence` |
| Roles | ⚠️ Gated | May be disabled by `channels.discord.actions.roles` |
| Moderation | ⚠️ Gated | May be disabled by `channels.discord.actions.moderation` |

## Error Log

| Timestamp | Error | Resolution |
|-----------|-------|------------|
| — | No errors detected | — |

## Cron Job Setup

- **Status:** ⚠️ Pending — requires gateway scope approval
- **Error:** `scope upgrade pending approval` — the OpenClaw CLI needs device pairing approval to create cron jobs
- **Action Required:** MAD needs to approve the scope upgrade request on the gateway host (blrrr)
- **Request ID:** `634ca408-3075-4401-95c2-5e149c2d16e5`
- **Intended Schedule:** Every 15 minutes
- **Intended Payload:** System event to check Discord connectivity and write status to this file

## Notes

- Gateway is loopback-only; only local clients can connect
- Discord bot token is configured but actual bot online status should be verified via Discord client
- Some features (roles, moderation, presence) may be gated by config
- Writing style for Discord: short, conversational, no markdown tables, mention users as `<@USER_ID>`
