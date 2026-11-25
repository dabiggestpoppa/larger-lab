# 03 - Remaining integration contracts

Two contracts are unresolved. Neither is implemented in this mission; this is
an actionable requirements note, not a design package.

---

## A. `REPLAY_EVIDENCE_RECORD_BINDING_V1`

**Existing schema limitation.** The frozen I05 `ReplayEvidence` record carries a
revision selection (`selected` / `excluded` rows keyed by `source_revision_id`)
and a declared market-availability instant. It carries **no record identity,
provider, record kind or artifact identity**. The I05 gate is a law about
*evidence*, not about *whose* evidence: the same eligible row passes whether it
was derived from this record or from an unrelated one.

**Bound today** (`TrustConsumerPolicy._bind_replay`): the record's own
`source_revision_id` must appear in the selection; no selected revision may have
become known after the cutoff; the availability instant may not be after the
cutoff and must agree with the record's declared instant when it declares one.
The unbound state is explicit (`replay_status = "NOT_BOUND"`), never an implicit
pass.

**Missing identity dimensions.** `record_id`, `provider`, `record_kind`,
`artifact_id` (plus the artifact evidence digest that would tie the replay row
to the record's own verified artifact).

**Required future source authority.** The I05 replay producer must be the
authority for those fields: a versioned schema that carries them, minted by the
producer that already owns replay evidence, admitted by operator approval of the
schema version. The consumer must not infer them from the record under test.

**Affected production interfaces.** `ConsumerRequest.replay_evidence`; the I05
replay gate result consumed by `TrustConsumerPolicy`; `_bind_replay` and its
refusal mapping (`PIT_INADMISSIBLE` for *when*, `REPLAY_BLOCKED` for *which*);
`UNRESOLVED_REPLAY_BINDING` and the `NOT_BOUND` status become obsolete; the I06
audit's admitted-field set.

**Acceptance controls required.**
Positive: evidence minted for this record, provider, kind and artifact is
accepted at a cutoff where all of it is known.
Negative (each must refuse with a named code): a replay row copied from another
record of the same provider; the same record under a different provider; the
same artifact under a different record kind; a row from another artifact; a
selection whose record id matches but whose artifact digest does not; evidence
missing any of the new fields.

---

## B. `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1`

**Existing schema limitation.** The reviewed `ApprovalManifest` can approve a
**registry artifact** and its evidence, and the consumer derives custody
authority from that pinned root. It has **no record type that names a custody
source** (store, operator, record kinds, providers) as operator-authorized.
Artifact approval is not source authorization.

**Bound today.** `CustodyAuthorityIdentity` is a complete, frozen identity -
`manifest_sha256`, `artifact_id`, `approval_id`, `registry_digest`,
`record_kind`, `provider`, `knowledge_cutoff`. `derive_custody_authority`
returns one of three bases; `AUTHORIZED` requires a matching
`identity_sha256`; the policy additionally requires the artifact to be listed in
the pinned manifest's approvals. With `artifacts = {}` no authorization can be
composed at all.

**Missing identity dimensions.** The *source* itself: a source identifier, the
store it reads, the operating entity, the record kinds and providers it is
authorized for, the validity window, and the manifest root it was granted under.
Without a source dimension, an approval proves a file is reviewed, not that this
operator may treat this store as a custody source.

**Required future source authority.** A separate operator-signed record type,
held at the same authority level as the manifest and bound to it by
`manifest_sha256`. It must be created by the operator; no configuration flag,
environment variable or test seam may synthesize it (the production enum
deliberately has no `SYNTHETIC_TEST_ONLY`).

**Affected production interfaces.** `custody_authority.derive_custody_authority`,
the `CustodySourceAuthoritySource` protocol, `ManifestCustodyAuthority`,
`CustodyAuthorityDerivation` (`basis`, `unresolved_contract`, `identity_sha256`),
the policy's composition step, and the refusal code
`UNAUTHORIZED_CUSTODY_SOURCE`. The empty-manifest path stays as the default.

**Acceptance controls required.**
Positive: a record from an authorized source, authorized kind and provider, inside
its validity window, with an approved artifact and matching identity digest,
yields `AUTHORIZED`.
Negative (each must refuse, never downgrade silently): an unlisted source; a
listed source used for a record kind it was not granted; a provider outside its
grant; a revoked or expired source record; an artifact that is approved but the
source is not; a matching source whose `manifest_sha256` names another root; an
`AUTHORIZED` derivation whose `identity_sha256` disagrees with the identity the
policy just built.
