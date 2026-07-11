"""Settings dataclass, the setting registry, and allowed-value catalogs."""

from dataclasses import dataclass, field, fields
from typing import Any

_LABEL_METADATA_KEY = "label"
_CHOICES_METADATA_KEY = "choices"

_NEMOTRON = "nvidia/nemotron-3-super-120b-a12b"
_DEEPSEEK_FLASH = "deepseek-ai/deepseek-v4-flash"
_MISTRAL_LARGE = "mistralai/mistral-large-3-675b-instruct-2512"
_LLAMA_MAVERICK = "meta/llama-4-maverick-17b-128e-instruct"

MODELS: tuple[str, ...] = (_NEMOTRON, _DEEPSEEK_FLASH, _MISTRAL_LARGE, _LLAMA_MAVERICK)
PERSONAS: tuple[str, ...] = ("recruiter", "hiring_manager", "senior_engineer")
LEVELS: tuple[str, ...] = ("intern", "junior", "mid", "senior")


@dataclass(frozen=True)
class SettingSpec:
    """Describes one registered setting."""

    field: str
    """Matches a `Settings` field name, e.g. ``"persona"``."""

    label: str
    """Prompt/display text, e.g. ``"Persona"``."""

    choices: tuple[str, ...]
    """Every value the setting may take."""

    many: bool
    """True when the field holds a tuple of choices rather than a single one."""


@dataclass(frozen=True)
class Settings:
    """User-tunable settings, each constrained to its allowed choices.

    A field carrying ``label``/``choices`` metadata is a registered setting;
    adding one is one new field here, nothing else. A tuple default marks a
    multi-valued setting.
    """

    model: str = field(
        default=_NEMOTRON,
        metadata={_LABEL_METADATA_KEY: "Model", _CHOICES_METADATA_KEY: MODELS},
    )

    persona: str = field(
        default="recruiter",
        metadata={_LABEL_METADATA_KEY: "Persona", _CHOICES_METADATA_KEY: PERSONAS},
    )

    level: str = field(
        default="intern",
        metadata={_LABEL_METADATA_KEY: "Level", _CHOICES_METADATA_KEY: LEVELS},
    )

    feedback_model: str = field(
        default=_DEEPSEEK_FLASH,
        metadata={_LABEL_METADATA_KEY: "Feedback model", _CHOICES_METADATA_KEY: MODELS},
    )

    ensemble_models: tuple[str, ...] = field(
        default=(_NEMOTRON, _MISTRAL_LARGE, _LLAMA_MAVERICK),
        metadata={_LABEL_METADATA_KEY: "Ensemble models", _CHOICES_METADATA_KEY: MODELS},
    )

    unrecognized: dict[str, Any] = field(default_factory=dict[str, Any])
    """Keys in settings.json that no `SettingSpec` claims — carried through
    load/save verbatim so saving can never destroy them."""


SETTING_SPECS: tuple[SettingSpec, ...] = tuple(
    SettingSpec(
        field=f.name,
        label=f.metadata[_LABEL_METADATA_KEY],
        choices=f.metadata[_CHOICES_METADATA_KEY],
        many=isinstance(f.default, tuple),
    )
    for f in fields(Settings)
    if _LABEL_METADATA_KEY in f.metadata
)
