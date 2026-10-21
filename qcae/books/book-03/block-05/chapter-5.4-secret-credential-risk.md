# Chapter 5.4 — Secret & Credential Risk

## Mission

Prevent candidate code from gaining credentials, tokens, signing material, production identities, brokerage access, private datasets, or other authority merely because execution requires configuration.

## 5.4.1 Default Rule

Unknown code receives **no real secrets by default**.

## 5.4.2 Secret Classes

```text
API token
Git credential
cloud credential
broker/exchange credential
database credential
signing key
SSH key
webhook secret
private dataset credential
OCE/service identity
```

## 5.4.3 Proving Credentials

When a capability genuinely requires authentication, use the least-privileged disposable test identity possible with:

- minimal scope;
- isolated account/resource;
- no production authority;
- short lifetime;
- explicit egress destination;
- revocation after test.

## 5.4.4 Environment Leakage

Sandbox environments must not inherit host environment variables, credential files, SSH agents, cloud metadata, browser sessions, mounted home directories, or socket access unless explicitly whitelisted.

## 5.4.5 Secret Discovery

Static inspection should identify code paths that read likely credentials or secret stores. This informs runtime policy; it does not authorize access.

## 5.4.6 Logging

Tests must avoid placing secrets in logs/evidence receipts. Evidence should record secret class/scope and test identity reference, not raw secret values.

## 5.4.7 Quant Execution Boundary

No proving candidate receives live brokerage/exchange trading credentials. Paper/simulated environments are separate from trading authority.

## 5.4.8 Credential Request Record

```text
candidate
requested secret class
purpose
scope
resource
duration
egress targets
approved policy
revocation plan
```

## Invariants

1. Unknown code gets no production secrets.
2. Test credentials are disposable and least-privileged.
3. Host credential inheritance is denied by default.
4. Evidence never stores raw secrets.
5. Trading credentials are outside proving authority.
6. Credential need is not credential permission.

## Exit Criteria

Every candidate can be executed or rejected without accidentally inheriting Quant Lab authority through credentials.
