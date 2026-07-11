"""CREDENTIAL_SPECS derivation from Credentials field metadata."""

from resume_roast.persistence.credentials.types import CREDENTIAL_SPECS


def test_at_least_one_provider_is_registered() -> None:
    assert CREDENTIAL_SPECS


def test_specs_exclude_bookkeeping_fields() -> None:
    assert "unrecognized" not in {spec.field for spec in CREDENTIAL_SPECS}


def test_every_spec_has_a_non_blank_label() -> None:
    for spec in CREDENTIAL_SPECS:
        assert spec.label.strip()
