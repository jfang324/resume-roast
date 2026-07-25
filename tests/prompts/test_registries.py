"""Guards against drift between the settings choices and the prompt registries."""

from resume_roast.persistence.settings.types import LEVELS, PERSONAS
from resume_roast.prompts.evaluate.levels import LEVEL_CONTEXT
from resume_roast.prompts.evaluate.personas import PERSONA_PROMPTS
from resume_roast.prompts.interview.levels import LEVEL_CONTEXT as INTERVIEW_LEVEL_CONTEXT


def test_every_persona_setting_has_a_prompt() -> None:
    assert set(PERSONA_PROMPTS) == set(PERSONAS)


def test_every_level_setting_has_context() -> None:
    assert set(LEVEL_CONTEXT) == set(LEVELS)


def test_every_level_setting_has_interview_context() -> None:
    """The interview keys its own level blocks off the same setting."""
    assert set(INTERVIEW_LEVEL_CONTEXT) == set(LEVELS)
