"""Service layer for the follow_up tool."""

import logging

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.tools.follow_up.parser import parse_input, parse_output
from resume_roast.tools.follow_up.schema import FollowUpInput, FollowUpOutput

logger = logging.getLogger(__name__)

_SYSTEM = """\
You are an interview assistant. Given:
1. The original interview question
2. The candidate's answer
3. Fact-check results from verify
4. Current competency coverage gaps (which areas need more probing)

Generate 0-2 follow-up questions ONLY when further probing is genuinely valuable.
Valid reasons include:

- The answer raised genuine doubt (low-probability or contradictory claims in verify results)
- The answer is notably vague or surface-level and probing would reveal meaningful signal
- A competency area is critically under-covered (no data yet for that slot)
- The answer reveals an interesting approach, technical decision, or experience that
  warrants deeper exploration — even if well-supported and well-articulated

Otherwise return an empty questions array. Do NOT generate questions for the
sake of having questions — only when further probing is genuinely valuable.

Do NOT repeat the original question or ask something already answered.
Avoid repetitive phrasing — each follow-up should read like a natural,
spontaneous question from a real interviewer, not a template.

Return a JSON object with a "questions" array and a "rationale" string.
If no follow-up is needed, return an empty questions array."""


def execute(
    client: LlmClient,
    original_question: str,
    answer: str,
    verify_summary: str,
    competency_gaps: str | None,
) -> tuple[FollowUpOutput, Usage | None]:
    run_input = FollowUpInput(
        original_question=original_question,
        answer=answer,
        verify_summary=verify_summary,
        competency_gaps=competency_gaps,
    )
    parsed_input = parse_input(run_input)

    parts = [
        f"Original question: {parsed_input.original_question}",
        f"Candidate answer: {parsed_input.answer}",
        f"Verify results: {parsed_input.verify_summary}",
    ]
    if parsed_input.competency_gaps:
        parts.append(f"Competency gaps to probe: {parsed_input.competency_gaps}")

    messages = [
        Message(role="system", content=_SYSTEM),
        Message(role="user", content="\n\n".join(parts)),
    ]
    logger.debug("follow_up request messages: %s", messages)

    completion = client.prompt(messages, temperature=0.0)
    output = parse_output(completion.text)
    logger.debug("follow_up result: %s", output)
    return output, completion.usage
