# G8 — prior-pass red evidence (STRESS-G8ARCH5)

Transcript of the defects fixed by the passes AFTER the first closure
matrix, reproduced against the code that carried them. Regenerate with:

```
cd stress-suite && PYTHONIOENCODING=utf-8 python scenarios/g8_arch_red_transcript.py
```

The harness extracts each named commit read-only into a temporary directory,
copies the working tree into another, and runs the SAME probes against both
in a subprocess. It never moves HEAD, never writes to the working tree, and
never overwrites a committed artifact. Each probe line ends in
`verdict=RED` (the defect was present) or `verdict=GREEN` (the property
holds), so every row of the closure matrix that cites this annex resolves to
a rerunnable line here.

pre-pass commits:

- STRESS-G8ARCH2/3: `d859e26e2c7320dda517c623dcb4aaf8afd7060f` — STRESS-G8ARCH2-R2: re-archive at the corrected tested tree 4d80828f
- STRESS-G8ARCH4: `36a84563ccaa0d132c56cda2802ed7996098ae05` — STRESS-G8ARCH3-R: re-archive at the derived tree 30d4ff4f

## Probes against `d859e26e2c7320dda517c623dcb4aaf8afd7060f` (STRESS-G8ARCH2/3)

```
ARCH-A: check_baseline(record, tested_sha='')['verified']=True | verdict=RED
ARCH-B: verify_citation(..., expected_tested_sha='')['verified']=True (signature default '') | verdict=RED
ARCH-C: the citation publishes exit_status=0 | verdict=RED
ARCH-D: decide_gate declares citation_check=True | verdict=RED
ARCH-E: the tree declares no lag rule at all | verdict=RED
ARCH-F: the tree declares no lag rule at all | verdict=RED
ARCH-G: published rule 'JUNIT_XML_MINUS_TIME_TIMESTAMP_HOSTNAME' : resolvable definition=False fingerprint=None | verdict=RED
CONTROL: derived tested tree: no derivation available: the tree rule this pass introduces does not exist in this tree
reviewer command exit=1 accepted=False
engine.g8_test_evidence.UnverifiableTestEvidence: baseline/tree mismatch: artifact was produced against aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, this evidence is being archived for
```

## Probes against `36a84563ccaa0d132c56cda2802ed7996098ae05` (STRESS-G8ARCH4)

```
ARCH-A: check_baseline(record, tested_sha='')['verified']=True | verdict=RED
ARCH-B: verify_citation(..., expected_tested_sha='')['verified']=True (signature default '') | verdict=RED
ARCH-C: the citation publishes exit_status=0 | verdict=RED
ARCH-D: decide_gate declares citation_check=True | verdict=RED
ARCH-E: rule(package=aaaaaaaa.., code=bbbbbbbb..) -> 'lagging tested tree: the committed package names aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa but the code/test tree is now bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb. Re-produce the artifact at the new tree and re-emit.' | verdict=GREEN
ARCH-F: rule(package=aaaaaaaa.., code='') -> '' | verdict=RED
ARCH-G: published rule 'JUNIT_XML_MINUS_TIME_TIMESTAMP_HOSTNAME' : resolvable definition=False fingerprint=None | verdict=RED
CONTROL: derived tested tree: ''
reviewer command exit=1 accepted=False
engine.g8_test_evidence.UnverifiableTestEvidence: baseline/tree mismatch: artifact was produced against aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, this evidence is being archived for
```

## Probes against the working tree

```
ARCH-A: check_baseline(record, tested_sha='')['verified']=False | verdict=GREEN
ARCH-B: verify_citation(..., expected_tested_sha='')['verified']=False (signature default <class 'inspect._empty'>) | verdict=GREEN
ARCH-C: the citation publishes exit_status='<absent>' | verdict=GREEN
ARCH-D: decide_gate declares citation_check=False | verdict=GREEN
ARCH-E: rule(package=aaaaaaaa.., code=bbbbbbbb..) -> 'lagging tested tree: the committed package names aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa but the code/test tree is now bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb. Re-produce the artifact at the new tree and re-emit.' | verdict=GREEN
ARCH-F: rule(package=aaaaaaaa.., code='') -> 'unverifiable tested tree: the code/test tree could not be derived, so the committed package cannot be shown to describe this checkout. A tree that cannot be derived is not a tree that matches.' | verdict=GREEN
ARCH-G: published rule 'JUNIT_XML_MINUS_VOLATILE_ATTRS_V1' : resolvable definition=True fingerprint='eae28317d14ded9a' | verdict=GREEN
CONTROL: derived tested tree: ''
reviewer command exit=1 accepted=False
engine.g8_test_evidence.UnverifiableTestEvidence: baseline/tree mismatch: artifact was produced against aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa, this evidence is being archived for
```
