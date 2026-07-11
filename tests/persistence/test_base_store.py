"""Tests for the shared Store ABC's file I/O mechanics.

Exercised through a minimal test-only subclass so this file-I/O behavior
(read, atomic write, error handling, permissions) is covered once at the
base-class level instead of being re-tested per concrete store.
"""

import json
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from resume_roast.persistence.base_store import Store
from resume_roast.persistence.errors import InvalidJsonError, InvalidSchemaError, PersistenceError


@dataclass(frozen=True)
class _Widget:
    name: str | None = None


class _WidgetParser:
    def parse(self, data: dict[str, Any]) -> _Widget:
        name = data.get("name")
        if name is not None and not isinstance(name, str):
            raise InvalidSchemaError("name must be a string")
        return _Widget(name=name)

    def serialize(self, value: _Widget) -> dict[str, Any]:
        return {} if value.name is None else {"name": value.name}


class _WidgetStore(Store[_Widget]):
    def __init__(self, base_dir: Path) -> None:
        super().__init__(base_dir, "widget.json", _WidgetParser())

    def default(self) -> _Widget:
        return _Widget()


def test_load_returns_default_when_file_missing(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path)
    assert store.load() == _Widget()


def test_save_then_load_roundtrips(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path)
    store.save(_Widget(name="gadget"))
    assert store.load() == _Widget(name="gadget")


def test_save_creates_base_dir(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path / "nested" / "dir")
    store.save(_Widget(name="gadget"))
    assert store.path.exists()


def test_save_writes_indented_json(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path)
    store.save(_Widget(name="gadget"))
    assert json.loads(store.path.read_text(encoding="utf-8")) == {"name": "gadget"}


def test_save_leaves_no_temp_artifacts(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path)
    store.save(_Widget(name="gadget"))
    assert {p.name for p in tmp_path.iterdir()} == {"widget.json"}


def test_load_raises_invalid_json_error_on_corrupt_file(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path)
    store.path.write_text("not json{", encoding="utf-8")
    with pytest.raises(InvalidJsonError):
        store.load()


def test_load_raises_invalid_schema_error_on_non_object(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path)
    store.path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(InvalidSchemaError):
        store.load()


def test_load_raises_invalid_schema_error_from_parser(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path)
    store.path.write_text(json.dumps({"name": 5}), encoding="utf-8")
    with pytest.raises(InvalidSchemaError, match=re.escape(str(store.path))):
        store.load()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permissions only")
def test_save_sets_owner_only_permissions(tmp_path: Path) -> None:
    store = _WidgetStore(tmp_path)
    store.save(_Widget(name="gadget"))
    mode = stat.S_IMODE(store.path.stat().st_mode)
    assert mode == 0o600


def test_save_wraps_oserror_in_persistence_error(tmp_path: Path) -> None:
    blocked_dir = tmp_path / "blocked"
    blocked_dir.write_text("not a directory", encoding="utf-8")
    store = _WidgetStore(blocked_dir)
    with pytest.raises(PersistenceError):
        store.save(_Widget(name="gadget"))
