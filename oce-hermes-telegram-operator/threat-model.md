# Threat Model — OCE Hermes Telegram Operator

> Version: 0.1.0  
> Date: 2026-08-23

## Scope

This document identifies threats to the OCE Hermes Telegram Operator and the mitigations implemented in Phase 0 (Observer Mode).

## Assets

| Asset | Description | Criticality |
|-------|-------------|-------------|
| OCE Backend Data | System status, jobs, events, evidence, costs | HIGH |
| Operator Telegram Identity | User ID, chat context | MEDIUM |
| Hermes LLM Credentials | API keys for model inference | HIGH |
| OCE Service Token | Facade→backend auth | HIGH |
| BotFather Token | Telegram bot authentication | CRITICAL |
| Audit Logs | Interaction history | MEDIUM |
| System Integrity | No unauthorized modifications | HIGH |

## Threat Actors

| Actor | Capability | Motivation |
|-------|-----------|------------|
| Unauthorized Telegram User | Send messages to bot | Access OCE data, cause disruption |
| Prompt Injection via Telegram | Craft messages to bypass restrictions | Execute unauthorized actions |
| Compromised Hermes | Access underlying system | Lateral movement, data exfiltration |
| Network Eavesdropper | Observe traffic | Credential theft, data leakage |
| Malicious MCP Response | Forge OCE responses | Mislead operator, hide issues |

## Threat Catalog

### T1: Unauthorized Telegram Access
- **Description:** Non-allowed user interacts with bot
- **Impact:** Data exposure, unauthorized observation
- **Mitigation:** TELEGRAM_ALLOWED_USERS allowlist, fail-closed
- **Test:** T-SEC-02 (Unauthorized user denied)

### T2: Missing Allowlist Bypass
- **Description:** Bot starts without TELEGRAM_ALLOWED_USERS configured
- **Impact:** No access control possible
- **Mitigation:** Gateway refuses startup when allowlist is empty/missing
- **Test:** T-SEC-03 (Missing allowlist prevents startup)

### T3: Allow-All Bypass
- **Description:** TELEGRAM_ALLOW_ALL_USERS=true in production
- **Impact:** Any Telegram user can interact
- **Mitigation:** Production config rejects allow-all setting
- **Test:** T-SEC-04 (Allow-all rejected in production)

### T4: Token Leakage
- **Description:** Bot token appears in logs, git, evidence
- **Impact:** Complete bot compromise
- **Mitigation:** Token never in logs, git, test fixtures; env-only loading
- **Test:** T-SEC-05 (Token never in output)

### T5: Unauthorized MCP Tool Exposure
- **Description:** Hermes exposes non-observer tools (terminal, filesystem, etc.)
- **Impact:** Arbitrary code execution, data access
- **Mitigation:** Explicit tool include list in MCP config
- **Test:** T-SEC-06 through T-SEC-11

### T6: Prompt Injection — Shell Execution
- **Description:** User crafts message to make Hermes execute shell commands
- **Impact:** Full system compromise
- **Mitigation:** Terminal tool disabled, MCP tools filtered
- **Test:** T-SEC-07

### T7: Prompt Injection — Database Access
- **Description:** User crafts message to query PostgreSQL directly
- **Impact:** Data exfiltration, modification
- **Mitigation:** No database tools exposed, OCE is sole data boundary
- **Test:** T-SEC-08

### T8: Prompt Injection — Docker Access
- **Description:** User crafts message to control Docker containers
- **Impact:** Container escape, lateral movement
- **Mitigation:** Docker socket not mounted, Docker tools disabled
- **Test:** T-SEC-09

### T9: Prompt Injection — Deployment
- **Description:** User crafts message to trigger deployment
- **Impact:** Production modification
- **Mitigation:** No deployment tools exposed
- **Test:** T-SEC-10

### T10: Prompt Injection — Trade Execution
- **Description:** User crafts message to execute trades
- **Impact:** Financial loss
- **Mitigation:** No trading tools exposed
- **Test:** T-SEC-11

### T11: OCE Offline Masking
- **Description:** OCE backend down but facade reports success
- **Impact:** Operator believes system is healthy when it's not
- **Mitigation:** Explicit OFFLINE state, never fabricated success
- **Test:** T-SEC-12

### T12: OCE Timeout
- **Description:** OCE backend slow, facade hangs or errors
- **Impact:** Denial of service
- **Mitigation:** 30s timeout, DEGRADED/ERROR state
- **Test:** T-SEC-13

### T13: Malformed Backend Response
- **Description:** OCE returns unexpected data format
- **Impact:** Crash, data corruption
- **Mitigation:** Schema validation, fail-closed
- **Test:** T-SEC-14

### T14: MCP Authentication Failure
- **Description:** Facade cannot authenticate to OCE
- **Impact:** Data access denied
- **Mitigation:** Explicit denial, no fallback to unprotected endpoints
- **Test:** T-SEC-15

### T15: Rate Limit Abuse
- **Description:** Excessive requests from Telegram
- **Impact:** OCE backend overload
- **Mitigation:** 60 req/min rate limit per tool
- **Test:** T-SEC-16

### T16: Inbound Port Exposure
- **Description:** Service listens on public port
- **Impact:** External access to internal systems
- **Mitigation:** Long polling only, no inbound ports
- **Test:** T-SEC-19

### T17: Lateral Movement via Hermes
- **Description:** Compromised Hermes accesses OCE internals
- **Impact:** Full system compromise
- **Mitigation:** Container isolation, no Docker socket, no SSH keys, resource limits
- **Test:** T-SEC-01, container config

## Residual Risks

| Risk | Status | Mitigation Plan |
|------|--------|-----------------|
| LLM hallucination | Accepted | Response validation, explicit states |
| Telegram API compromise | Accepted | Low probability, out of scope |
| Hermes upstream vulnerability | Monitored | Pin version, update regularly |
| Physical access to host | Accepted | Physical security outside scope |
