"""Tests for SettingsParser."""

from typing import Any

import pytest

from resume_roast.persistence.errors import InvalidSchemaError
from resume_roast.persistence.settings.parser import SettingsParser
from resume_roast.persistence.settings.types import Settings

_EXAMPLE = {
    "model": "nvidia/nemotron-3-super-120b-a12b",
    "persona": "recruiter",
    "level": "intern",
    "feedback_model": "deepseek-ai/deepseek-v4-flash",
    "ensemble_models": [
        "nvidia/nemotron-3-super-120b-a12b",
        "mistralai/mistral-large-3-675b-instruct-2512",
        "meta/llama-4-maverick-17b-128e-instruct",
    ],
}


def test_parse_reads_the_documented_shape() -> None:
    parser = SettingsParser()
    settings = parser.parse(dict(_EXAMPLE))
    assert settings.model == "nvidia/nemotron-3-super-120b-a12b"
    assert settings.persona == "recruiter"
    assert settings.level == "intern"
    assert settings.feedback_model == "deepseek-ai/deepseek-v4-flash"
    assert settings.ensemble_models == tuple(_EXAMPLE["ensemble_models"])


def test_parse_empty_object_yields_defaults() -> None:
    parser = SettingsParser()
    assert parser.parse({}) == Settings()


def test_serialize_writes_every_registered_setting() -> None:
    parser = SettingsParser()
    assert parser.serialize(Settings()) == {
        "model": "nvidia/nemotron-3-super-120b-a12b",
        "persona": "recruiter",
        "level": "intern",
        "feedback_model": "deepseek-ai/deepseek-v4-flash",
        "ensemble_models": [
            "nvidia/nemotron-3-super-120b-a12b",
            "mistralai/mistral-large-3-675b-instruct-2512",
            "meta/llama-4-maverick-17b-128e-instruct",
        ],
    }


def test_parse_serialize_roundtrips() -> None:
    parser = SettingsParser()
    assert parser.serialize(parser.parse(dict(_EXAMPLE))) == _EXAMPLE


def test_unknown_keys_survive_a_parse_serialize_roundtrip() -> None:
    parser = SettingsParser()
    data = {**_EXAMPLE, "future_setting": 42}
    assert parser.serialize(parser.parse(data)) == data


@pytest.mark.parametrize(
    "data",
    [
        {"model": "gpt-4"},
        {"persona": 5},
        {"level": "principal"},
        {"ensemble_models": "not-a-list"},
        {"ensemble_models": ["nvidia/nemotron-3-super-120b-a12b", "bad-model"]},
    ],
)
def test_parse_rejects_values_outside_the_allowed_choices(data: dict[str, Any]) -> None:
    parser = SettingsParser()
    with pytest.raises(InvalidSchemaError):
        parser.parse(data)
