"""Tests for storage_dir()."""

from pathlib import Path

import pytest

from resume_roast.persistence.paths import storage_dir


def test_storage_dir_is_dot_resume_roast_under_home(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_home = Path("/fake/home")
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    assert storage_dir() == fake_home / ".resume-roast"
