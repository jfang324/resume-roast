"""Loaded JSON to Config."""

from __future__ import annotations

from typing import Any

from resume_roast.persistence.config_store.models import Config


def parse_config(data: dict[str, Any]) -> Config:  # noqa: ARG001
    """Parse a loaded JSON object into Config, ignoring unknown keys."""
    return Config()
