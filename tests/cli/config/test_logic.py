"""Tests for apply_entries — the wizard's blank-keeps-existing merge rule."""

from resume_roast.cli.config.logic import apply_entries
from resume_roast.persistence.credentials.types import Credentials

_EXISTING_KEY = "sk-existing-1234"  # pragma: allowlist secret
_NEW_KEY = "sk-new-5678"  # pragma: allowlist secret


def test_blank_entry_keeps_existing_value() -> None:
    existing = Credentials(nvidia_api_key=_EXISTING_KEY)
    assert apply_entries(existing, {"nvidia_api_key": ""}) == existing


def test_whitespace_entry_keeps_existing_value() -> None:
    existing = Credentials(nvidia_api_key=_EXISTING_KEY)
    assert apply_entries(existing, {"nvidia_api_key": "   "}) == existing


def test_missing_entry_keeps_existing_value() -> None:
    existing = Credentials(nvidia_api_key=_EXISTING_KEY)
    assert apply_entries(existing, {}) == existing


def test_non_blank_entry_overwrites() -> None:
    existing = Credentials(nvidia_api_key=_EXISTING_KEY)
    updated = apply_entries(existing, {"nvidia_api_key": _NEW_KEY})
    assert updated == Credentials(nvidia_api_key=_NEW_KEY)


def test_non_blank_entry_is_stripped() -> None:
    updated = apply_entries(Credentials(), {"nvidia_api_key": f"  {_NEW_KEY}  "})
    assert updated == Credentials(nvidia_api_key=_NEW_KEY)


def test_blank_entry_on_unset_field_stays_unset() -> None:
    assert apply_entries(Credentials(), {"nvidia_api_key": ""}) == Credentials()


def test_unrecognized_keys_pass_through_the_merge() -> None:
    existing = Credentials(nvidia_api_key=_EXISTING_KEY, unrecognized={"mystery_key": "keep-me"})
    updated = apply_entries(existing, {"nvidia_api_key": _NEW_KEY})
    assert updated.unrecognized == {"mystery_key": "keep-me"}
