"""Loaded JSON to Config."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

from resume_roast.persistence.config_store.models import SETTING_SPECS, Config
from resume_roast.persistence.errors import InvalidSchemaError


def parse_config(data: dict[str, Any]) -> Config:
    """Parse a loaded JSON object into Config, ignoring unknown keys.

    Every setting is optional: an absent key or an explicit JSON null leaves
    the field None. A present, non-null value must match its spec's
    registered choices, else InvalidSchemaError is raised.
    """
    config = Config()
    for spec in SETTING_SPECS:
        raw = data.get(spec.key)
        if raw is None:
            continue
        value = (
            _parse_multi(spec.key, raw, spec.choices)
            if spec.multi
            else _parse_scalar(spec.key, raw, spec.choices)
        )
        config = replace(config, **{spec.key: value})

    return config


def _parse_scalar(key: str, raw: Any, choices: tuple[str, ...]) -> str:
    if not isinstance(raw, str) or raw not in choices:
        raise InvalidSchemaError(f"{key} must be one of: {', '.join(choices)}")
    return raw


def _parse_multi(key: str, raw: Any, choices: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise InvalidSchemaError(f"{key} must be a non-empty list of: {', '.join(choices)}")
    items = cast("list[Any]", raw)
    if len(items) == 0:
        raise InvalidSchemaError(f"{key} must be a non-empty list of: {', '.join(choices)}")

    validated: list[str] = []
    for item in items:
        if not isinstance(item, str) or item not in choices:
            raise InvalidSchemaError(f"{key} must only contain values from: {', '.join(choices)}")
        if item in validated:
            raise InvalidSchemaError(f"{key} must not contain duplicate values")
        validated.append(item)
    return tuple(validated)
