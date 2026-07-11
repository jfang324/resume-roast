"""Tests for CredentialsStore."""

import json
import stat
import sys
from pathlib import Path

import pytest

from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import Credentials
from resume_roast.persistence.errors import InvalidJsonError, InvalidSchemaError

_TEST_KEY = "sk-test-9876"  # pragma: allowlist secret


def test_save_then_load_roundtrips_key(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    store.save(Credentials(nvidia_api_key=_TEST_KEY))
    assert store.load() == Credentials(nvidia_api_key=_TEST_KEY)


def test_load_returns_default_credentials_when_file_missing(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    assert store.load() == Credentials()


def test_save_creates_store_dir(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path / "nested")
    store.save(Credentials(nvidia_api_key=_TEST_KEY))
    assert store.path.exists()


def test_save_leaves_no_temp_artifacts(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    store.save(Credentials(nvidia_api_key=_TEST_KEY))
    assert {p.name for p in tmp_path.iterdir()} == {"credentials.json"}


def test_save_after_load_preserves_unrecognized_keys(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    store.path.write_text(
        json.dumps({"nvidia_api_key": _TEST_KEY, "mystery_key": "keep-me"}), encoding="utf-8"
    )

    store.save(store.load())

    on_disk = json.loads(store.path.read_text(encoding="utf-8"))
    assert on_disk == {"nvidia_api_key": _TEST_KEY, "mystery_key": "keep-me"}


def test_load_raises_invalid_json_error_on_corrupt_file(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    store.path.write_text("not json{", encoding="utf-8")
    with pytest.raises(InvalidJsonError):
        store.load()


@pytest.mark.parametrize(
    "contents",
    [
        json.dumps({"nvidia_api_key": "   "}),
        json.dumps({"nvidia_api_key": 5}),
        json.dumps([1, 2]),
    ],
)
def test_load_raises_invalid_schema_error(tmp_path: Path, contents: str) -> None:
    store = CredentialsStore(tmp_path)
    store.path.write_text(contents, encoding="utf-8")
    with pytest.raises(InvalidSchemaError):
        store.load()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
def test_credentials_file_is_owner_only_on_posix(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    store.save(Credentials(nvidia_api_key=_TEST_KEY))
    mode = stat.S_IMODE(store.path.stat().st_mode)
    assert mode == 0o600
