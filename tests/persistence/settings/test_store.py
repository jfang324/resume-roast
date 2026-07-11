"""Tests for SettingsStore."""

import json
from pathlib import Path

from resume_roast.persistence.settings.store import SettingsStore
from resume_roast.persistence.settings.types import LEVELS, MODELS, Settings


def test_save_then_load_roundtrips(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path)
    settings = Settings(model=MODELS[1], level=LEVELS[2], ensemble_models=(MODELS[0], MODELS[3]))
    store.save(settings)
    assert store.load() == settings


def test_load_returns_defaults_when_file_missing(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path)
    assert store.load() == Settings()


def test_save_after_load_preserves_unrecognized_keys(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path)
    store.path.write_text(json.dumps({"persona": "recruiter", "mystery_key": 42}), encoding="utf-8")

    store.save(store.load())

    on_disk = json.loads(store.path.read_text(encoding="utf-8"))
    assert on_disk["mystery_key"] == 42
