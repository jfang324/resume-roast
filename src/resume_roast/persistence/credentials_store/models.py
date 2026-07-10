"""Dataclasses and secret masking for the credentials domain."""

from __future__ import annotations

from dataclasses import dataclass

_MASK = "****"
_VISIBLE_SUFFIX_LENGTH = 4


@dataclass(frozen=True)
class Credentials:
    anthropic_api_key: str


def mask_secret(value: str) -> str:
    """Return value with all but its last four characters masked."""
    if len(value) <= _VISIBLE_SUFFIX_LENGTH:
        return _MASK
    return _MASK + value[-_VISIBLE_SUFFIX_LENGTH:]
