"""Verify tool: fact-check the candidate's claims against the resume."""

import logging

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.prompts.interview.tools.verify.builder import SYSTEM, build_user_message
from resume_roast.prompts.interview.tools.verify.parser import parse_output
from resume_roast.prompts.interview.tools.verify.schema import VerifyOutput

logger = logging.getLogger(__name__)


def verify_claims(
    client: LlmClient,
    claims: list[str],
    answer: str,
    resume_markdown: str,
) -> tuple[VerifyOutput, Usage | None]:
    """Check each claim from *answer* against the resume, one LLM call.

    Raises:
        ValueError: when a required input is empty.
        ApiError: transport and response failures, including malformed output.
    """
    if not claims:
        raise ValueError("claims list cannot be empty")
    if not answer.strip():
        raise ValueError("answer cannot be empty")
    if not resume_markdown.strip():
        raise ValueError("resume_markdown cannot be empty")

    messages = [
        Message(role="system", content=SYSTEM),
        Message(role="user", content=build_user_message(claims, answer, resume_markdown)),
    ]
    logger.debug("verify request messages: %s", messages)

    completion = client.prompt(messages, temperature=0.0)
    output = parse_output(completion.text)
    logger.debug("verify result: %s", output)

    return output, completion.usage
