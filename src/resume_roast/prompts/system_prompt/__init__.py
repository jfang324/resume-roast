"""Reusable prompt content pieces that form the system message of each feature builder."""

from resume_roast.prompts.system_prompt.bullets import BULLET_PRINCIPLES
from resume_roast.prompts.system_prompt.levels import LEVEL_CONTEXT
from resume_roast.prompts.system_prompt.personas import PERSONA_PROMPTS
from resume_roast.prompts.system_prompt.scoring import EVALUATION_PRIORITIES, SCORE_BANDS
from resume_roast.prompts.system_prompt.structure import RESUME_STRUCTURE

__all__ = [
    "BULLET_PRINCIPLES",
    "EVALUATION_PRIORITIES",
    "LEVEL_CONTEXT",
    "PERSONA_PROMPTS",
    "RESUME_STRUCTURE",
    "SCORE_BANDS",
]
