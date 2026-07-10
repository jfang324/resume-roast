"""Storage directory resolution."""

from __future__ import annotations

import os
from pathlib import Path


def storage_dir() -> Path:
    """Return the resume-roast storage directory.

    Honors the RESUME_ROAST_HOME environment variable when set to a
    non-empty value, read at call time; otherwise defaults to
    ~/.resume-roast.
    """
    override = os.environ.get("RESUME_ROAST_HOME", "")
    if override:
        return Path(override)
    return Path.home() / ".resume-roast"
