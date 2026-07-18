"""Guards against drift between the settings choices and the prompt registries."""

from resume_roast.persistence.settings.types import LEVELS, PERSONAS
from resume_roast.prompts.system_prompt.levels import LEVEL_CONTEXT
from resume_roast.prompts.system_prompt.personas import PERSONA_PROMPTS


def test_every_persona_setting_has_a_prompt() -> None:
    assert set(PERSONA_PROMPTS) == set(PERSONAS)


def test_every_level_setting_has_context() -> None:
    assert set(LEVEL_CONTEXT) == set(LEVELS)
