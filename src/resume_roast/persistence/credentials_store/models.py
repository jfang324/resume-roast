"""Dataclasses, the credential registry, and secret masking."""

from __future__ import annotations

from dataclasses import dataclass

_MASK = "****"
_VISIBLE_SUFFIX_LENGTH = 4


@dataclass(frozen=True)
class CredentialSpec:
    """Describes one selectable credential: its storage key and menu label."""

    key: str
    label: str


CREDENTIAL_SPECS: tuple[CredentialSpec, ...] = (
    CredentialSpec(key="nvidia_api_key", label="NVIDIA API key"),
)


@dataclass(frozen=True)
class Credentials:
    nvidia_api_key: str | None = None


def mask_secret(value: str) -> str:
    """Return value with all but its last four characters masked."""
    if len(value) <= _VISIBLE_SUFFIX_LENGTH:
        return _MASK
    return _MASK + value[-_VISIBLE_SUFFIX_LENGTH:]
