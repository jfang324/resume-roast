"""Guards against drift between the interview prompt and the loop's dispatch."""

import re

from resume_roast.prompts.interview.builder import (
    build_interview_system_prompt,
    build_plan_prompt,
    build_verdict_prompt,
)
from resume_roast.utils.extraction.types import DocumentMetadata, ParsedResume

_LOOP_TOOLS = {"verify", "ask_followup", "evaluate", "conclude"}
"""Names `parse_tool_call` dispatches; every other name becomes UnknownTool."""


def _parsed() -> ParsedResume:
    metadata = DocumentMetadata(
        page_count=1,
        creator=None,
        producer=None,
        created=None,
        modified=None,
        links=(),
        pages=(),
    )

    return ParsedResume(markdown="Jane Doe — Engineer at Acme Corp", metadata=metadata)


def test_system_prompt_advertises_exactly_the_loop_vocabulary() -> None:
    """A tool the prompt offers but dispatch rejects wastes a turn on UnknownTool."""
    prompt = build_interview_system_prompt(_parsed())

    advertised = set(re.findall(r'"tool":\s*"(\w+)"', prompt))

    assert advertised == _LOOP_TOOLS


def test_plan_prompt_carries_the_output_shape() -> None:
    """Planning parses through parse_plan, so its shape must live in its own prompt."""
    assert "questions" in build_plan_prompt()


def test_verdict_prompt_asks_for_the_decision_after_the_assessment() -> None:
    """The verdict and rating must be generated after the summary that supports them.

    Field order in the requested JSON is the model's generation order, so the
    hire decision and numeric rating must trail the summary/strengths/growth
    areas — otherwise the conclusion is fixed before any reasoning is written.
    """
    prompt = build_verdict_prompt({"ownership": 7}, max_per_comp=10, competencies="")

    summary = prompt.index('"summary"')
    strengths = prompt.index('"strengths"')
    growth_areas = prompt.index('"growth_areas"')
    verdict = prompt.index('"verdict"')
    rating = prompt.index('"overall_rating"')

    assert summary < strengths < growth_areas < verdict < rating
