"""Guards on the interview verify tool's system prompt."""

from resume_roast.prompts.interview.tools.verify.builder import SYSTEM


def test_system_prompt_asks_for_probability_after_evidence() -> None:
    """The per-claim `probability` must be generated after its evidence.

    Generation is autoregressive, so the field order in the example schema is
    the order the model produces: evidence and the contradiction flag must
    precede the probability, or the rating is committed before the reasoning
    that supports it.
    """
    evidence = SYSTEM.index('"evidence"')
    contradiction = SYSTEM.index('"contradiction"')
    probability = SYSTEM.index('"probability"')

    assert evidence < contradiction < probability
