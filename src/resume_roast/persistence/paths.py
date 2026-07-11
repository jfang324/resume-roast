"""Storage directory resolution."""

from pathlib import Path


def storage_dir() -> Path:
    """Return the directory resume-roast persists its data to."""
    return Path.home() / ".resume-roast"
