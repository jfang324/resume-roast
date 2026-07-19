"""Evaluate tool: score the full answer cycle across the competency framework."""

import logging
from functools import partial

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.structured import structured_completion
from resume_roast.integrations.types import Message, Usage
from resume_roast.prompts.interview.tools.evaluate.builder import SYSTEM, build_user_message
from resume_roast.prompts.interview.tools.evaluate.parser import parse_output
from resume_roast.prompts.interview.tools.evaluate.schema import EvaluateOutput

logger = logging.getLogger(__name__)


def evaluate_answer(
    client: LlmClient,
    original_question: str,
    answer_history: list[str],
    verify_results: str,
    competency_descriptions: str,
    competency_ids: list[str],
) -> tuple[EvaluateOutput, Usage | None]:
    """Score the answer cycle against every competency, one LLM call.

    Raises:
        ValueError: when a required input is empty.
        ApiError: transport and response failures, including malformed output.
    """
    if not original_question.strip():
        raise ValueError("original_question cannot be empty")
    if not answer_history:
        raise ValueError("answer_history cannot be empty")
    if not competency_descriptions.strip():
        raise ValueError("competency_descriptions cannot be empty")
    if not competency_ids:
        raise ValueError("competency_ids cannot be empty")

    messages = [
        Message(role="system", content=SYSTEM),
        Message(
            role="user",
            content=build_user_message(
                original_question,
                answer_history,
                verify_results,
                competency_descriptions,
            ),
        ),
    ]
    logger.debug("evaluate request messages: %s", messages)

    output, usage = structured_completion(
        client,
        messages,
        partial(parse_output, competency_ids=competency_ids),
        temperature=0.0,
    )
    logger.debug("evaluate result: %s", output)

    return output, usage
