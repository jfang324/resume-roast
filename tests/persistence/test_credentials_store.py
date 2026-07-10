"""Tests for the credentials store."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from resume_roast.persistence.credentials_store import (
    Credentials,
    CredentialsStore,
    mask_secret,
)
from resume_roast.persistence.errors import InvalidJsonError, InvalidSchemaError

TEST_KEY = "sk-ant-key-9876"  # pragma: allowlist secret


def test_save_then_load_roundtrips_key(store_dir: Path) -> None:
    store = CredentialsStore(store_dir)

    store.save(Credentials(anthropic_api_key=TEST_KEY))

    assert store.load() == Credentials(anthropic_api_key=TEST_KEY)


def test_load_returns_none_when_file_missing(store_dir: Path) -> None:
    store = CredentialsStore(store_dir)

    assert store.load() is None


def test_save_creates_store_dir(store_dir: Path) -> None:
    store = CredentialsStore(store_dir)
    assert not store_dir.exists()

    store.save(Credentials(anthropic_api_key=TEST_KEY))

    assert store_dir.is_dir()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file mode not applicable on Windows")
def test_credentials_file_is_owner_only_on_posix(store_dir: Path) -> None:
    store = CredentialsStore(store_dir)

    store.save(Credentials(anthropic_api_key=TEST_KEY))

    mode = store.path.stat().st_mode & 0o777
    assert mode == 0o600


def test_load_raises_invalid_json_error_on_corrupt_file(store_dir: Path) -> None:
    store = CredentialsStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text("not json{", encoding="utf-8")

    with pytest.raises(InvalidJsonError) as exc_info:
        store.load()

    assert str(store.path) in str(exc_info.value)
    assert "not json{" not in str(exc_info.value)


@pytest.mark.parametrize(
    "raw_contents",
    [
        pytest.param('{"other_key": "value"}', id="missing_key"),
        pytest.param('{"anthropic_api_key": "   "}', id="blank_key"),
        pytest.param("[1, 2, 3]", id="non_object_top_level"),
    ],
)
def test_load_raises_invalid_schema_error(store_dir: Path, raw_contents: str) -> None:
    store = CredentialsStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text(raw_contents, encoding="utf-8")

    with pytest.raises(InvalidSchemaError) as exc_info:
        store.load()

    assert str(store.path) in str(exc_info.value)
    assert raw_contents not in str(exc_info.value)


def test_saving_credentials_never_touches_config_file(store_dir: Path) -> None:
    store_dir.mkdir(parents=True)
    config_path = store_dir / "config.json"
    config_path.write_text('{"marker": true}', encoding="utf-8")
    original_bytes = config_path.read_bytes()

    CredentialsStore(store_dir).save(Credentials(anthropic_api_key=TEST_KEY))

    assert config_path.read_bytes() == original_bytes


def test_save_leaves_no_temp_artifacts(store_dir: Path) -> None:
    store = CredentialsStore(store_dir)

    store.save(Credentials(anthropic_api_key=TEST_KEY))

    assert {p.name for p in store_dir.iterdir()} == {"credentials.json"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("sk-ant-key-9876", "****9876", id="long_key"),
        pytest.param("abc", "****", id="short_key"),
    ],
)
def test_mask_secret_shows_at_most_last_four(value: str, expected: str) -> None:
    assert mask_secret(value) == expected
