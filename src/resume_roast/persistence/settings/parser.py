"""Untyped JSON <-> `Settings` conversion."""

from typing import Any, cast

from resume_roast.persistence.errors import InvalidSchemaError
from resume_roast.persistence.settings.types import SETTING_SPECS, Settings, SettingSpec


def _unrecognized_keys(data: dict[str, Any]) -> dict[str, Any]:
    """Everything in `data` that no `SettingSpec` claims."""
    registered = {spec.field for spec in SETTING_SPECS}
    return {key: value for key, value in data.items() if key not in registered}


def _validated_choice(spec: SettingSpec, value: Any) -> str:
    """Require a value to be one of the setting's allowed choices."""
    if not isinstance(value, str) or value not in spec.choices:
        raise InvalidSchemaError(f"{spec.field!r} must be one of: {', '.join(spec.choices)}")
    return value


def _validated_choice_list(spec: SettingSpec, value: Any) -> tuple[str, ...]:
    """Require a value to be a list drawn from the setting's allowed choices."""
    if not isinstance(value, list):
        raise InvalidSchemaError(f"{spec.field!r} must be a list of allowed choices")
    return tuple(_validated_choice(spec, item) for item in cast(list[Any], value))


class SettingsParser:
    """Implements `JsonParser[Settings]`."""

    def parse(self, data: dict[str, Any]) -> Settings:
        """Convert a loaded JSON object into `Settings`.

        Missing settings take their defaults. Unrecognized keys are kept so a
        later save round-trips them instead of destroying them.
        """
        values: dict[str, Any] = {"unrecognized": _unrecognized_keys(data)}
        for spec in SETTING_SPECS:
            if spec.field in data:
                raw = data[spec.field]
                values[spec.field] = (
                    _validated_choice_list(spec, raw) if spec.many else _validated_choice(spec, raw)
                )
        return Settings(**values)

    def serialize(self, value: Settings) -> dict[str, Any]:
        """Convert `Settings` into a JSON object.

        Every registered setting is written — settings always have a value;
        unrecognized keys are re-emitted verbatim.
        """
        data: dict[str, Any] = dict(value.unrecognized)
        for spec in SETTING_SPECS:
            field_value = getattr(value, spec.field)
            data[spec.field] = list(field_value) if spec.many else field_value
        return data
