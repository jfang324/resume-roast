"""Dataclasses for the config domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SettingSpec:
    """Describes one setting: storage key, display label, allowed choices."""

    key: str
    label: str
    choices: tuple[str, ...]
    multi: bool = False


PERSONAS: tuple[str, ...] = ("recruiter", "hiring-manager")
LEVELS: tuple[str, ...] = ("intern", "entry", "mid", "senior")
MODEL_CATALOG: tuple[str, ...] = (
    "nvidia/nemotron-3-super-120b-a12b",
    "mistralai/mistral-large-3-675b-instruct-2512",
    "meta/llama-4-maverick-17b-128e-instruct",
    "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "deepseek-ai/deepseek-v4-flash",
    "deepseek-ai/deepseek-v4-pro",
    "meta/llama-3.1-8b-instruct",
)

SETTING_SPECS: tuple[SettingSpec, ...] = (
    SettingSpec(key="model", label="Model", choices=MODEL_CATALOG),
    SettingSpec(key="persona", label="Persona", choices=PERSONAS),
    SettingSpec(key="level", label="Level", choices=LEVELS),
    SettingSpec(key="feedback_model", label="Feedback model", choices=MODEL_CATALOG),
    SettingSpec(key="ensemble_models", label="Ensemble models", choices=MODEL_CATALOG, multi=True),
)


@dataclass(frozen=True)
class Config:
    model: str | None = None
    persona: str | None = None
    level: str | None = None
    feedback_model: str | None = None
    ensemble_models: tuple[str, ...] | None = None
