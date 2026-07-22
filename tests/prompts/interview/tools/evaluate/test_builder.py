"""Guards on the interview evaluate tool's system prompt."""

from resume_roast.prompts.interview.tools.evaluate.builder import SYSTEM


def test_system_prompt_asks_for_reasoning_before_scores() -> None:
    """The requested JSON must place feedback ahead of the numbers.

    The model is autoregressive, so the field order in the requested schema is
    the generation order: strengths/gaps and each competency's rationale must
    precede the scores, or the numbers are committed before any reasoning.
    """
    strengths = SYSTEM.index('"strengths"')
    gaps = SYSTEM.index('"gaps"')
    assessment = SYSTEM.index('"assessment"')
    rationale = SYSTEM.index('"rationale"')
    score = SYSTEM.index('"score"')

    assert strengths < gaps < assessment < rationale < score
