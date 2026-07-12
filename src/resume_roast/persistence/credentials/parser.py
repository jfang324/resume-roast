"""Untyped JSON <-> `Credentials` conversion."""

from typing import Any

from resume_roast.persistence.credentials.types import (
    CREDENTIAL_SPECS,
    Credentials,
    CredentialSpec,
)
from resume_roast.persistence.errors import InvalidSchemaError


def _unrecognized_keys(data: dict[str, Any]) -> dict[str, Any]:
    """Everything in `data` that no `CredentialSpec` claims."""
    registered = {spec.field for spec in CREDENTIAL_SPECS}
    return {key: value for key, value in data.items() if key not in registered}


def _validated_value(spec: CredentialSpec, value: Any) -> str:
    """Require a registered field's value to be a non-blank string."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidSchemaError(f"{spec.field!r} must be a non-blank string")
    return value


class CredentialsParser:
    """Implements `JsonParser[Credentials]`."""

    def parse(self, data: dict[str, Any]) -> Credentials:
        """Convert a loaded JSON object into `Credentials`.

        Unrecognized keys are kept so a later save round-trips them instead
        of destroying them.
        """
        values: dict[str, Any] = {"unrecognized": _unrecognized_keys(data)}
        for spec in CREDENTIAL_SPECS:
            if spec.field in data:
                values[spec.field] = _validated_value(spec, data[spec.field])
        return Credentials(**values)

    def serialize(self, value: Credentials) -> dict[str, Any]:
        """Convert `Credentials` into a JSON object.

        Unset registered fields are omitted (not written as null); unrecognized
        keys are re-emitted verbatim.
        """
        data: dict[str, Any] = dict(value.unrecognized)
        for spec in CREDENTIAL_SPECS:
            field_value = getattr(value, spec.field)
            if field_value is not None:
                data[spec.field] = field_value
        return data
