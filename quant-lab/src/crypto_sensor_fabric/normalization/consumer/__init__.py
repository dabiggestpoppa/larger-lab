"""SENSOR-B5-P3 - the production trust consumer (``normalization.consumer``).

A real package with a docstring and **no eager imports**.  That is deliberate on
both counts:

* a regular package cannot be shadowed by an unrelated ``consumer`` module on
  ``sys.path``, which is what an implicit namespace directory allows;
* importing ``consumer.models`` must not drag in the verifier, so the Rung 1
  contract cannot quietly become a second source of truth for verification.
  A re-export here would load ``policy`` -> ``sensors.verification`` on any
  ``import`` of the models module, so the package exposes no symbols and each
  module is imported by name.  ``tests/.../test_b5_p3_consumer_contracts.py``
  measures that in a clean subprocess rather than assuming it.

What lives here:

``models``
    Rung 1 -- request, verdict and the three closed vocabularies.  Data only.
``policy``
    Rungs 2 and 4 -- ``TrustConsumerPolicy``, which derives verification,
    adjudicates replay and PIT, rebinds evidence and derives authority.
``custody_authority``
    Rung 3 -- the bounded custody-source authority *derivation*.  No
    capability object exists, and under the shipped empty manifest no input can
    reach ``AUTHORIZED``.

Hard stop, restated where the code lives: none of this grants provider
authority, approves a custody source, promotes trust or advances a program gate.
``INTEGRATION_REQUIRED`` is the integration state, not a bug.
"""
