"""Builds the evaluate feature's roast prompt from a parsed resume."""

from resume_roast.prompts.bullets import BULLET_PRINCIPLES
from resume_roast.prompts.input.resume import RESUME_INPUT, render_resume_input
from resume_roast.prompts.levels import LEVEL_CONTEXT
from resume_roast.prompts.output.markdown_roast import MARKDOWN_ROAST_FORMAT
from resume_roast.prompts.personas import PERSONA_PROMPTS
from resume_roast.prompts.scoring import SCORE_BANDS
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
            SCORE_BANDS,
            BULLET_PRINCIPLES,
            RESUME_STRUCTURE,
            RESUME_INPUT,
            MARKDOWN_ROAST_FORMAT,
        ]
    )
    return Prompt(system=system, user=render_resume_input(parsed))
