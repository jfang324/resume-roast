"""Tests for CredentialsParser and mask_secret."""

import pytest

from resume_roast.persistence.credentials.parser import CredentialsParser
from resume_roast.persistence.credentials.types import Credentials, mask_secret
from resume_roast.persistence.errors import InvalidSchemaError


def test_parse_serialize_roundtrips() -> None:
    parser = CredentialsParser()
    creds = Credentials(nvidia_api_key="sk-test-9876")
    assert parser.parse(parser.serialize(creds)) == creds


def test_serialize_omits_unset_fields() -> None:
    parser = CredentialsParser()
    assert parser.serialize(Credentials()) == {}


def test_parse_keeps_unknown_keys_as_unrecognized() -> None:
    parser = CredentialsParser()
    creds = parser.parse({"nvidia_api_key": "sk-test-9876", "future_provider_key": "x"})
    assert creds.nvidia_api_key == "sk-test-9876"  # pragma: allowlist secret
    assert creds.unrecognized == {"future_provider_key": "x"}


def test_unknown_keys_survive_a_parse_serialize_roundtrip() -> None:
    parser = CredentialsParser()
    data = {
        "nvidia_api_key": "sk-test-9876",  # pragma: allowlist secret
        "future_provider_key": "x",
    }
    assert parser.serialize(parser.parse(data)) == data


def test_parse_missing_field_is_none() -> None:
    parser = CredentialsParser()
    assert parser.parse({}) == Credentials()


@pytest.mark.parametrize("value", ["   ", 5, ""])
def test_parse_rejects_invalid_value(value: object) -> None:
    parser = CredentialsParser()
    with pytest.raises(InvalidSchemaError):
        parser.parse({"nvidia_api_key": value})


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("sk-ant-key-9876", "****9876"),
        ("abc", "****"),
        ("abcd", "****"),
        ("abcdefgh", "****"),  # suffix would be half the secret — stay fully masked
        ("abcdefghi", "****fghi"),
    ],
)
def test_mask_secret(value: str, expected: str) -> None:
    assert mask_secret(value) == expected
