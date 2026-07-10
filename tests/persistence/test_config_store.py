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


def test_save_then_load_roundtrips_full_settings(store_dir: Path) -> None:
    store = ConfigStore(store_dir)
    config = Config(
        model="nvidia/nemotron-3-super-120b-a12b",
        persona="recruiter",
        level="entry",
        feedback_model="meta/llama-3.1-8b-instruct",
        ensemble_models=(
            "nvidia/nemotron-3-super-120b-a12b",
            "meta/llama-4-maverick-17b-128e-instruct",
        ),
    )

    store.save(config)

    assert json.loads(store.path.read_text(encoding="utf-8")) == {
        "model": "nvidia/nemotron-3-super-120b-a12b",
        "persona": "recruiter",
        "level": "entry",
        "feedback_model": "meta/llama-3.1-8b-instruct",
        "ensemble_models": [
            "nvidia/nemotron-3-super-120b-a12b",
            "meta/llama-4-maverick-17b-128e-instruct",
        ],
    }
    assert store.load() == config


def test_save_preserves_fields_not_included_in_update(store_dir: Path) -> None:
    store = ConfigStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text(
        json.dumps(
            {
                "model": "nvidia/nemotron-3-super-120b-a12b",
                "persona": "recruiter",
                "level": "senior",
                "feedback_model": "meta/llama-3.1-8b-instruct",
                "ensemble_models": ["nvidia/nemotron-3-super-120b-a12b"],
                "future_setting": 1,
            }
        ),
        encoding="utf-8",
    )

    store.save(Config(persona="hiring-manager"))

    assert store.load() == Config(
        model="nvidia/nemotron-3-super-120b-a12b",
        persona="hiring-manager",
        level="senior",
        feedback_model="meta/llama-3.1-8b-instruct",
        ensemble_models=("nvidia/nemotron-3-super-120b-a12b",),
    )
    on_disk = json.loads(store.path.read_text(encoding="utf-8"))
    assert on_disk["future_setting"] == 1
    assert on_disk["persona"] == "hiring-manager"


def test_save_settings_never_touches_credentials_file(store_dir: Path) -> None:
    store_dir.mkdir(parents=True)
    credentials_path = store_dir / "credentials.json"
    credentials_path.write_text('{"marker": true}', encoding="utf-8")
    original_bytes = credentials_path.read_bytes()

    ConfigStore(store_dir).save(Config(persona="recruiter"))

    assert credentials_path.read_bytes() == original_bytes


@pytest.mark.parametrize(
    "key,bad_value",
    [
        ("model", 3),
        ("model", "invalid"),
        ("persona", 3),
        ("persona", "invalid"),
        ("level", 3),
        ("level", "invalid"),
        ("feedback_model", 3),
        ("feedback_model", "invalid"),
    ],
)
def test_load_rejects_unregistered_scalar_value(
    store_dir: Path, key: str, bad_value: object
) -> None:
    store = ConfigStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text(json.dumps({key: bad_value}), encoding="utf-8")

    with pytest.raises(InvalidSchemaError) as exc_info:
        store.load()

    assert str(store.path) in str(exc_info.value)


@pytest.mark.parametrize(
    "bad_value",
    [
        "x",
        [],
        ["not-a-catalog-model"],
        ["nvidia/nemotron-3-super-120b-a12b", "nvidia/nemotron-3-super-120b-a12b"],
        [3],
    ],
    ids=["not_a_list", "empty_list", "non_catalog_string", "duplicate", "non_string_item"],
)
def test_load_rejects_malformed_ensemble(store_dir: Path, bad_value: object) -> None:
    store = ConfigStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text(json.dumps({"ensemble_models": bad_value}), encoding="utf-8")

    with pytest.raises(InvalidSchemaError) as exc_info:
        store.load()

    assert str(store.path) in str(exc_info.value)


def test_load_tolerates_unknown_keys_alongside_known_ones(store_dir: Path) -> None:
    store = ConfigStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text(
        json.dumps({"persona": "recruiter", "future_setting": 1}), encoding="utf-8"
    )

    assert store.load() == Config(persona="recruiter")


def test_load_treats_explicit_null_as_absent(store_dir: Path) -> None:
    store = ConfigStore(store_dir)
    store_dir.mkdir(parents=True)
    store.path.write_text(json.dumps({"persona": None}), encoding="utf-8")

    assert store.load() == Config(persona=None)


def test_save_ignores_empty_ensemble_tuple(store_dir: Path) -> None:
    store = ConfigStore(store_dir)
    store.save(Config(ensemble_models=("nvidia/nemotron-3-super-120b-a12b",)))

    store.save(Config(ensemble_models=()))

    assert store.load().ensemble_models == ("nvidia/nemotron-3-super-120b-a12b",)
