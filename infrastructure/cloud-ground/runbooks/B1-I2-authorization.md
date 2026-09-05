# B1-I2 Authorization Runbook

## When to Authorize B1-I2

B1-I2 (Clean Host Baseline) should only be authorized after:

1. ✅ B1-I1 evidence has been reviewed
2. ✅ Static validation passes
3. ✅ You understand what B1-I2 will do
4. ✅ You have a server to deploy to (B1-I0 purchase completed)

## What B1-I2 Will Do

1. Apply the Ansible host baseline to a fresh Ubuntu 24.04 server
2. Install and configure Tailscale private network
3. Set up firewall rules (deny all inbound except SSH via Tailscale)
4. Install Docker Engine and Compose
5. Create the storage directory layout
6. Verify operator access and negative access tests

## What B1-I2 Requires

- A provisioned server (from B1-I0 purchase)
- Tailscale account and auth key
- SSH key pair for operator access
- Operator approval to modify the remote host

## Authorization Command

```
AUTHORIZED_STAGE=B1-I2
```

This must be explicitly set. Possession of this prompt does NOT authorize B1-I2.

## How to Stop B1-I2

- Interrupt the Ansible playbook
- The host can be rebuilt from scratch (that's the point)
- No irreversible changes are made without the playbook completing
