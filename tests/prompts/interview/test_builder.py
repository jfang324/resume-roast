"""Guards against drift between the interview prompt and the loop's dispatch."""

import re

from resume_roast.prompts.interview.builder import (
    build_interview_system_prompt,
    build_plan_prompt,
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
