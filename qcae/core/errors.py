"""QCAE base error taxonomy (canon Book V 15.2; master prompt P0 item 7).

All QCAE errors derive from QcaeError. Domain validation failures derive from
QcaeValidationError so callers can distinguish malformed domain objects from
infrastructure failures. Deserialization contract failures (schema version,
object type) are their own classes because they indicate contract drift rather
than malformed content.
"""

from __future__ import annotations


class QcaeError(Exception):
    """Base class for all QCAE errors."""


class QcaeValidationError(QcaeError):
    """A domain object or transition failed constitutional/canon validation."""


class QcaeSchemaVersionError(QcaeError):
    """A serialized record declares a schema version or type the reader cannot interpret.

    This is a contract failure, not a content failure: the payload itself may be
    fine, but this reader does not understand its shape. Fail closed.
    """


class QcaeSerializationError(QcaeError):
    """A record could not be converted to or from its serialized form."""


class QcaeStateTransitionError(QcaeValidationError):
    """An illegal lifecycle transition was requested."""


class QcaeTransitionWaiverError(QcaeStateTransitionError):
    """A waivable evidence gate was skipped without a recorded policy justification."""


class QcaeUnknownTypeError(QcaeSchemaVersionError):
    """A serialized record declares an object type this reader does not know."""
