"""Tests for CredentialsStore.

Only the parts specific to this store live here — the default it falls back
to and its wiring to CredentialsParser. The shared file-I/O mechanics (atomic
write, directory creation, corrupt-file errors, permissions) are covered once
in `tests/persistence/test_base_store.py`.
"""

import json
from pathlib import Path

from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import Credentials

_TEST_KEY = "sk-test-9876"  # pragma: allowlist secret


def test_save_then_load_roundtrips_key(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    store.save(Credentials(nvidia_api_key=_TEST_KEY))
    assert store.load() == Credentials(nvidia_api_key=_TEST_KEY)


def test_load_returns_default_credentials_when_file_missing(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    assert store.load() == Credentials()


def test_save_after_load_preserves_unrecognized_keys(tmp_path: Path) -> None:
    store = CredentialsStore(tmp_path)
    store.path.write_text(
        json.dumps({"nvidia_api_key": _TEST_KEY, "mystery_key": "keep-me"}), encoding="utf-8"
    )

    store.save(store.load())

    on_disk = json.loads(store.path.read_text(encoding="utf-8"))
    assert on_disk == {"nvidia_api_key": _TEST_KEY, "mystery_key": "keep-me"}
