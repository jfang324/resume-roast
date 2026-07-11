"""Tests for the config wizards' pure merge and selection logic."""

import pytest

from resume_roast.cli.config.logic import (
    InvalidSelectionError,
    apply_entries,
    apply_selections,
    parse_selection,
)
from resume_roast.persistence.credentials.types import Credentials
from resume_roast.persistence.settings.types import PERSONAS, SETTING_SPECS, Settings

_EXISTING_KEY = "sk-existing-1234"  # pragma: allowlist secret
_NEW_KEY = "sk-new-5678"  # pragma: allowlist secret

_SCALAR_SPEC = next(spec for spec in SETTING_SPECS if not spec.many)
_MANY_SPEC = next(spec for spec in SETTING_SPECS if spec.many)


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


def test_parse_selection_resolves_a_single_number() -> None:
    assert parse_selection(_SCALAR_SPEC, "2") == _SCALAR_SPEC.choices[1]


def test_parse_selection_resolves_comma_separated_numbers() -> None:
    expected = (_MANY_SPEC.choices[0], _MANY_SPEC.choices[2])
    assert parse_selection(_MANY_SPEC, "1, 3") == expected


def test_parse_selection_deduplicates_in_entry_order() -> None:
    assert parse_selection(_MANY_SPEC, "2,1,2") == (_MANY_SPEC.choices[1], _MANY_SPEC.choices[0])


@pytest.mark.parametrize("entry", ["0", "abc", "99", "-1", "1.5"])
def test_parse_selection_rejects_out_of_range_entries(entry: str) -> None:
    with pytest.raises(InvalidSelectionError):
        parse_selection(_SCALAR_SPEC, entry)


def test_parse_selection_rejects_multiple_numbers_for_single_valued_setting() -> None:
    with pytest.raises(InvalidSelectionError):
        parse_selection(_SCALAR_SPEC, "1,2")


def test_apply_selections_overwrites_only_selected_fields() -> None:
    updated = apply_selections(Settings(), {"persona": PERSONAS[1]})
    assert updated == Settings(persona=PERSONAS[1])
