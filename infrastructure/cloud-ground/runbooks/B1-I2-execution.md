# B1-I2 Execution Runbook - Clean Host Baseline

## Scope

B1-I2 provisions the first durable Cloud Ground host and proves a clean,
repeatable, local-first baseline: clean OS, secure bootstrap, private network,
firewall, Docker Engine + Compose, deterministic storage layout, time sync,
automated security updates, hardening, rollback/rebuild, and a fail-closed gate.

It does not deploy PostgreSQL, Redis, observability, the OCE runtime, workers,
a dashboard, or any live-trading service. B1-I2 deploys no public service and
exposes no public port.

## Local-first boundary

- Development, tests, simulations, strategy research, and validation all run
  locally without the cloud host.
- CI provides authoritative clean-environment verification.
- The cloud host is for durable deployment, remote availability, persistence,
  backups, observability, and later heavy compute.
- This runbook's checks must not require a reachable cloud host to pass.
- Local tools presenting as BLOCKED are reported honestly, never converted to PASS.

## Status: PURCHASE HOLD - do not provision yet

The operator has authorized B1-I2 with:

    AUTHORIZED_STAGE=B1-I2
    APPROVED_PROVIDER=netcup
    APPROVED_PRODUCT=RS 4000 G12
    APPROVED_MAX_FIRST_MONTH_USD=100
    APPROVED_MAX_MONTHLY_USD=60
    APPROVED_CONTRACT_TERM=MONTHLY

The host has not yet been purchased. Until the operator completes the purchase
and supplies the sanitized host identity below, the agent must stop at the
purchase hold and return these verified checkout requirements.

## Verified checkout requirements (operator action required)

Before any provisioning runs, the operator must complete the purchase manually
and provide only these non-secret facts:

1. provider name (must be netcup);
2. product name (must be RS 4000 G12);
3. selected region;
4. invoice/order total without card numbers (must be <= $100 first month);
5. contract term (must be MONTHLY, not yearly);
6. renewal price (must be <= $60/month recurring);
7. server identifier;
8. public IP or hostname;
9. confirmation that account MFA is enabled;
10. confirmation that an operator-controlled SSH public key is registered or
    available for the target.

The operator has separately confirmed the requested non-secret host identity
(the placeholder shape; real values are provided only by the operator after
purchase):

    provider: netcup
    product: "RS 4000 G12"
    region: <operator-selected>
    term: MONTHLY
    server_id: <operator-provided>
    ip_or_host: <operator-provided>
    ssh_public_key_registered: true
    mfa_enabled: true

Do not send the agent: payment-card details, account passwords, MFA codes,
recovery codes, private SSH keys, Tailscale reusable keys, or cloud API secrets.

## Checkout guard checks (before buying)

Independent confirmation at the provider checkout that ALL hold:

- [ ] exact product is netcup RS 4000 G12
- [ ] monthly contract, no yearly commitment
- [ ] first-month total <= $100
- [ ] recurring monthly total <= $60
- [ ] no unapproved add-ons (no extra IPs, load balancers, storage, snapshots,
      backup products, domains, support plans)
- [ ] no automatic fallback purchase
- [ ] cancellation/refund terms documented
- [ ] region and IPv4/IPv6 terms documented

If any fails, return BLOCKED_AT_PURCHASE_HOLD.

## Post-purchase provisioning sequence (B1-I2 execution)

After the operator confirms the purchase and supplies the sanitized identity:

1. target identity confirmation;
2. preflight host facts;
3. source cleanliness check;
4. bootstrap access (provider console + operator SSH key, per the contract's
   safest-path order);
5. private-network enrollment (Tailscale, ephemeral/one-time key, no reusable
   key stored anywhere);
6. private SSH verification in a separate session;
7. firewall transition;
8. public bootstrap closure;
9. OS baseline (Ubuntu 24.04 LTS confirmed);
10. hardening;
11. Docker Engine + Compose installation (pinned sources);
12. storage layout (deterministic paths, no DB init);
13. first provisioning run (Ansible);
14. second provisioning run (idempotence proof);
15. adversarial verification;
16. external exposure scan;
17. final source cleanliness;
18. cleanup;
19. independent gate.

Each phase produces evidence into the single external OCE_RUN_ID evidence
directory. No phase is skipped. A failed phase stops provisioning.

## Evidence produced (when execution is authorized)

purchase-verification.json, requirements-matrix.json, local-validation-results.json,
target-identity.json, preflight-host-facts.json, postflight-host-facts.json,
package-versions.json, network-exposure-before.json, network-exposure-after.json,
private-network-verification.json, ssh-hardening-results.json, firewall-results.json,
docker-baseline-results.json, storage-layout-results.json, ansible-first-run.json,
ansible-second-run.json, idempotence-results.json, adversarial-results.json,
regression-output.txt, stage-status.json, stage-log.txt, cleanup-results.json,
rollback-readiness.json, static-validation-summary.md, evidence-manifest.json.

No evidence contains passwords, private keys, Tailscale auth keys, API tokens,
payment data, or recovery codes.

## Lockout-safe network transition

Before removing any access path:

1. verify provider-console recovery access;
2. verify the authorized SSH key;
3. establish the new administrative account;
4. open a second verified session;
5. establish private-network access;
6. verify private SSH in a separate session;
7. apply firewall changes;
8. verify private access again;
9. remove temporary public bootstrap access;
10. verify public access is closed;
11. preserve provider-console recovery instructions.

If any verification fails, preserve the last confirmed working access path,
record the failure, and stop.

## Stop conditions

Return BLOCKED and stop if: the starting SHA/branch/repo is wrong; the worktree
is dirty; a mandatory local test fails; the approved product or monthly contract
is unavailable; price exceeds either ceiling; provider/product identity cannot
be verified; the operator has not completed the purchase; required target
details are missing; provider-console recovery is unavailable; secure SSH cannot
be established; the OS is unsupported; an unexpected public port remains open;
private access fails after firewall changes; public bootstrap access cannot be
closed; provisioning is not idempotent; a real remote dependency is introduced;
required evidence is missing; hashes disagree; cleanup fails; rollback readiness
cannot be verified; or any B1-I3 service is accidentally deployed.
