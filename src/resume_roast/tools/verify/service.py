"""Service layer for the verify tool."""

import logging

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.tools.verify.parser import parse_input, parse_output
from resume_roast.tools.verify.schema import VerifyInput, VerifyOutput

logger = logging.getLogger(__name__)

_SYSTEM = """\
You are a fact-checking assistant. Given a candidate's answer to an interview
question and their resume, evaluate each factual claim in the answer.

For each claim:
- Search the resume for supporting evidence.
- If the resume supports the claim, assign a high probability (0.8-1.0).
- If the resume contradicts the claim, assign a low probability (0.0-0.2)
  and note the contradiction.
- If the resume neither supports nor contradicts (information not present in
  the resume), assign a moderate probability (0.3-0.7) — the lack of evidence
  does not mean the claim is false.
- If the claim is a vague or soft statement that cannot be verified (e.g.
  "I think", "in my opinion"), flag it as unverifiable.

Return ONLY a JSON object with a "claims" array. Each claim object MUST have
a non-empty "text" field. Example:
{"claims": [{"text": "...", "probability": 0.9, "evidence": "...", "contradiction": false}]}"""


def execute(
    client: LlmClient,
    claims: list[str],
    answer: str,
    resume_markdown: str,
) -> tuple[VerifyOutput, Usage | None]:
    run_input = VerifyInput(claims=claims, answer=answer, resume_markdown=resume_markdown)
    parsed_input = parse_input(run_input)

    user = f"""\
<resume>
{parsed_input.resume_markdown}
</resume>

Candidate answer: {parsed_input.answer}

Claims to verify:
{_numbered(parsed_input.claims)}"""

    messages = [
        Message(role="system", content=_SYSTEM),
        Message(role="user", content=user),
    ]
    logger.debug("verify request messages: %s", messages)

    completion = client.prompt(messages, temperature=0.0)
    output = parse_output(completion.text)
    logger.debug("verify result: %s", output)
    return output, completion.usage


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{i + 1}. {c}" for i, c in enumerate(items))
