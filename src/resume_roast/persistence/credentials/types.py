"""Credential dataclass, provider registry, and secret masking."""

from dataclasses import dataclass, field, fields
from typing import Any

_MASK = "****"
_VISIBLE_SUFFIX_LENGTH = 4
_LABEL_METADATA_KEY = "label"


@dataclass(frozen=True)
class CredentialSpec:
    """Describes one registered provider credential."""

    field: str
    """Matches a `Credentials` field name, e.g. ``"nvidia_api_key"``."""

    label: str
    """Prompt/display text, e.g. ``"NVIDIA API key"``."""


@dataclass(frozen=True)
class Credentials:
    """Provider API keys. Every field is optional until the user sets it.

    A field carrying ``label`` metadata is a registered provider credential;
    adding a provider is one new field here, nothing else.
    """

    nvidia_api_key: str | None = field(
        default=None, metadata={_LABEL_METADATA_KEY: "NVIDIA API key"}
    )

    unrecognized: dict[str, Any] = field(default_factory=dict[str, Any])
    """Keys in credentials.json that no `CredentialSpec` claims — carried
    through load/save verbatim so saving can never destroy them."""


CREDENTIAL_SPECS: tuple[CredentialSpec, ...] = tuple(
    CredentialSpec(field=f.name, label=f.metadata[_LABEL_METADATA_KEY])
    for f in fields(Credentials)
    if _LABEL_METADATA_KEY in f.metadata
)


def mask_secret(value: str) -> str:
    """Return `value` fully masked, revealing its last four characters only
    when that suffix is a minority of the secret.
    """
    if len(value) <= _VISIBLE_SUFFIX_LENGTH * 2:
        return _MASK

    return _MASK + value[-_VISIBLE_SUFFIX_LENGTH:]
