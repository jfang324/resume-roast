"""Builds the evaluate feature's roast prompt from a parsed resume."""

from resume_roast.prompts.bullets import BULLET_PRINCIPLES
from resume_roast.prompts.evaluate.input import RESUME_INPUT, render_resume_input
from resume_roast.prompts.evaluate.output import (
    MARKDOWN_ROAST_FORMAT,
    MARKDOWN_ROAST_REMINDER,
)
from resume_roast.prompts.levels import LEVEL_CONTEXT
from resume_roast.prompts.personas import PERSONA_PROMPTS
from resume_roast.prompts.scoring import EVALUATION_PRIORITIES, SCORE_BANDS
from resume_roast.prompts.structure import RESUME_STRUCTURE
from resume_roast.prompts.types import Prompt
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
            MARKDOWN_ROAST_FORMAT,
        ]
    )
    # The task restatement closes the user message so the output contract is
    # the last thing the model reads — a long real resume otherwise pulls it
    # into its generic review-shaped prior.
    user = "\n\n".join([render_resume_input(parsed), MARKDOWN_ROAST_REMINDER])
    return Prompt(system=system, user=user)
