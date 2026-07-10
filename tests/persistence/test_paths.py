"""Tests for storage directory resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_roast.persistence.paths import storage_dir


def test_storage_dir_honors_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RESUME_ROAST_HOME", str(tmp_path))

    assert storage_dir() == tmp_path


def test_storage_dir_defaults_to_home_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RESUME_ROAST_HOME", raising=False)

    assert storage_dir() == Path.home() / ".resume-roast"
