"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def store_dir(tmp_path: Path) -> Path:
    """Return a store directory path that does not yet exist on disk."""
    return tmp_path / "store"
