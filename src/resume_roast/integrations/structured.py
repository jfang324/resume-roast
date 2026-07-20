"""Structured completions: drive any LLM client until its response parses."""

import logging
from collections.abc import Callable, Sequence

from resume_roast.integrations.errors import MalformedResponseError, TruncatedResponseError
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.integrations.usage import total_usage

logger = logging.getLogger(__name__)

_MAX_RETRIES: int = 1
"""Retries allowed per failure mode, on top of the initial attempt."""

_FEEDBACK_TEMPLATE = """\
Your previous response could not be used: {reason}.
Send the corrected response now — the complete raw JSON object only."""


def structured_completion[T](
    client: LlmClient,
    messages: Sequence[Message],
    parse: Callable[[str], T],
    *,
    temperature: float,
) -> tuple[T, Usage | None]:
    """Prompt until the response parses, retrying each failure mode within budget.

    ``temperature`` has no default so every caller states its sampling
    choice; it is forwarded unchanged on every attempt.

    A malformed response is retried with the bad reply and the parse error
    appended to the conversation; a truncated response is retried as sent
    (re-asking with feedback just truncates again), on a separate budget so
    truncation never consumes the parse retry. Usage is summed across every
    attempt that returned, so cost reporting stays honest.

    Raises:
        ApiError: transport errors from the client propagate untouched;
            `TruncatedResponseError` or `MalformedResponseError` once the
            retry budget for that failure mode is exhausted.
    """
    conversation = list(messages)
    usages: list[Usage] = []

    parse_attempts = 0
    truncation_attempts = 0

    while True:
        try:
            completion = client.prompt(conversation, temperature=temperature)

        except TruncatedResponseError:
            truncation_attempts += 1
            if truncation_attempts > _MAX_RETRIES:
                raise

            continue

        if completion.usage is not None:
            usages.append(completion.usage)

        try:
            return parse(completion.text), total_usage(usages)

        except MalformedResponseError as exc:
            parse_attempts += 1
            _log_malformed(exc, completion.text)
            if parse_attempts > _MAX_RETRIES:
                raise

            _append_feedback(conversation, completion.text, exc)


def _log_malformed(exc: MalformedResponseError, body: str) -> None:
    logger.error("Malformed response: %s", exc)
    logger.debug("Malformed raw response: %s", body)


def _append_feedback(
    conversation: list[Message], response_text: str, reason: MalformedResponseError
) -> None:
    conversation.append(Message(role="assistant", content=response_text))
    conversation.append(
        Message(role="user", content=_FEEDBACK_TEMPLATE.format(reason=reason)),
    )
