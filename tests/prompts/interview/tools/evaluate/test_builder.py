"""Guards on the interview evaluate tool's system prompt."""

from resume_roast.persistence.settings.types import LEVELS
from resume_roast.prompts.interview.tools.evaluate.builder import build_system


def test_system_prompt_asks_for_reasoning_before_scores() -> None:
    """The requested JSON must place feedback ahead of the numbers.

    The model is autoregressive, so the field order in the requested schema is
    the generation order: strengths/gaps and each competency's rationale must
    precede the scores, or the numbers are committed before any reasoning.
    """
    system = build_system("mid")

    strengths = system.index('"strengths"')
    gaps = system.index('"gaps"')
    assessment = system.index('"assessment"')
    rationale = system.index('"rationale"')
    score = system.index('"score"')

    assert strengths < gaps < assessment < rationale < score


def test_scoring_is_calibrated_before_the_bands_are_read() -> None:
    """The bands are level-relative, so the level must precede them.

    The competency descriptions describe an established IC; an intern scored
    against them unqualified loses points for seniority never expected.
    """
    system = build_system("intern")

    assert "Internship candidate" in system
    assert system.index("Internship candidate") < system.index("assign a score of 1-10")


def test_every_level_builds_a_calibrated_prompt() -> None:
    for level in LEVELS:
        assert "## Candidate Level" in build_system(level)
