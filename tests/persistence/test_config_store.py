"""Tests for the config store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from resume_roast.persistence.config_store import Config, ConfigStore
from resume_roast.persistence.errors import InvalidJsonError, InvalidSchemaError


def test_save_then_load_roundtrips_empty_config(store_dir: Path) -> None:
    store = ConfigStore(store_dir)

    store.save(Config())

    assert json.loads(store.path.read_text(encoding="utf-8")) == {}
    assert store.load() == Config()


def test_load_returns_default_config_when_file_missing(store_dir: Path) -> None:
    store = ConfigStore(store_dir)

    assert store.load() == Config()


def test_load_raises_invalid_json_error_on_corrupt_file(store_dir: Path) -> None:
    store = ConfigStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text("not json{", encoding="utf-8")

    with pytest.raises(InvalidJsonError) as exc_info:
        store.load()

    assert str(store.path) in str(exc_info.value)


def test_load_raises_invalid_schema_error_on_non_object(store_dir: Path) -> None:
    store = ConfigStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text("[1, 2]", encoding="utf-8")

    with pytest.raises(InvalidSchemaError):
        store.load()


def test_load_tolerates_unknown_keys(store_dir: Path) -> None:
    store = ConfigStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text(json.dumps({"future_setting": 1}), encoding="utf-8")

    assert store.load() == Config()
