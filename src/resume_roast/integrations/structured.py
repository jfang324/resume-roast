"""Structured completions: drive any LLM client until its response parses."""

from collections.abc import Callable, Sequence

from resume_roast.integrations.errors import MalformedResponseError, TruncatedResponseError
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.integrations.usage import total_usage

_FEEDBACK_TEMPLATE = """\
Your previous response could not be used: {reason}.
Send the corrected response now — the complete raw JSON object only."""


def structured_completion[T](
    client: LlmClient,
    messages: Sequence[Message],
    parse: Callable[[str], T],
) -> tuple[T, Usage | None]:
    """Prompt until the response parses, retrying each failure mode once.

    A malformed response is retried with the bad reply and the parse error
    appended to the conversation; a truncated response is retried as sent
    (re-asking with feedback just truncates again), on a separate budget so
    truncation never consumes the parse retry. Usage is summed across every
    attempt that returned, so cost reporting stays honest.

    Raises:
        ApiError: transport errors from the client propagate untouched;
            `TruncatedResponseError` or `MalformedResponseError` when the
            retry for that failure mode fails the same way again.
    """
    conversation = list(messages)
    usages: list[Usage] = []
    parse_retries = 1
    truncation_retries = 1
    while True:
        try:
            completion = client.prompt(conversation)
        except TruncatedResponseError:
            if truncation_retries == 0:
                raise
            truncation_retries -= 1
            continue
        if completion.usage is not None:
            usages.append(completion.usage)
        try:
            return parse(completion.text), total_usage(usages)
        except MalformedResponseError as exc:
            if parse_retries == 0:
                raise
            parse_retries -= 1
            conversation.append(Message(role="assistant", content=completion.text))
            conversation.append(Message(role="user", content=_FEEDBACK_TEMPLATE.format(reason=exc)))
