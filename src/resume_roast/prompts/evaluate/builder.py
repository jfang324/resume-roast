"""Builds the evaluate feature's roast prompt from a parsed resume."""

from resume_roast.prompts.evaluate.levels import LEVEL_CONTEXT
from resume_roast.prompts.evaluate.output.format import (
    JSON_ROAST_FORMAT,
    JSON_ROAST_REMINDER,
    RULES,
)
from resume_roast.prompts.evaluate.personas import PERSONA_PROMPTS
from resume_roast.prompts.evaluate.resume_input import RESUME_INPUT, render_resume_input
from resume_roast.prompts.evaluate.scoring import EVALUATION_PRIORITIES, SCORE_BANDS
from resume_roast.prompts.evaluate.structure import RESUME_STRUCTURE
from resume_roast.prompts.evaluate.types import Prompt
from resume_roast.prompts.system_prompt.bullets import BULLET_PRINCIPLES
from resume_roast.utils.extraction.types import ParsedResume


def build_evaluate_prompt(parsed: ParsedResume, persona: str, level: str) -> Prompt:
    """Assemble the roast prompt for one parsed resume.

    ``persona`` and ``level`` arrive pre-validated as `Settings` choices;
    registry completeness is enforced by tests, not re-checked here.
    """
    selected = PERSONA_PROMPTS[persona]
    system = "\n\n".join(
        [
            f"## Persona: {selected.label}\n\n{selected.prompt}",
            f"## Role Level\n\n{LEVEL_CONTEXT[level]}",
            EVALUATION_PRIORITIES,
            SCORE_BANDS,
            BULLET_PRINCIPLES,
            RESUME_STRUCTURE,
            RESUME_INPUT,
            JSON_ROAST_FORMAT,
            RULES,
        ]
    )
    # The task restatement closes the user message so the output contract is
    # the last thing the model reads — a long real resume otherwise pulls it
    # into its generic review-shaped prior.
    user = "\n\n".join([render_resume_input(parsed), JSON_ROAST_REMINDER])
    return Prompt(system=system, user=user)
