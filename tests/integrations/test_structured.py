"""structured_completion: parse retries, truncation retries, usage summing."""

from collections.abc import Sequence

import pytest

from resume_roast.integrations.errors import (
    MalformedResponseError,
    TransientError,
    TruncatedResponseError,
)
from resume_roast.integrations.llm_client import CompletionStream, LlmClient
from resume_roast.integrations.structured import structured_completion
from resume_roast.integrations.types import Completion, Message, Usage

_MESSAGES = [Message(role="system", content="be strict"), Message(role="user", content="report")]

_USAGE = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)


def _completion(text: str, usage: Usage | None = _USAGE) -> Completion:
    return Completion(text=text, usage=usage, finish_reason="stop")


class _ScriptedClient:
    """Satisfies LlmClient; answers each prompt() from a script, recording calls."""

    def __init__(self, script: Sequence[Completion | Exception]) -> None:
        self._script = list(script)
        self.calls: list[list[Message]] = []

    def prompt(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.0,  # noqa: ARG002 — the protocol's signature requires it
    ) -> Completion:
        self.calls.append(list(messages))
        step = self._script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step

    def prompt_stream(
        self, messages: Sequence[Message], *, temperature: float = 0.0
    ) -> CompletionStream:
        raise NotImplementedError


def _parse(text: str) -> str:
    if text.startswith("bad"):
        raise MalformedResponseError(f"{text} is unacceptable")
    return f"parsed:{text}"


def test_returns_the_parsed_first_response() -> None:
    client: LlmClient = _ScriptedClient([_completion("fine")])

    result, usage = structured_completion(client, _MESSAGES, _parse)

    assert result == "parsed:fine"
    assert usage == _USAGE


def test_retries_a_malformed_response_with_feedback() -> None:
    client = _ScriptedClient([_completion("bad draft"), _completion("fine")])

    result, _ = structured_completion(client, _MESSAGES, _parse)

    assert result == "parsed:fine"
    retry_conversation = client.calls[1]
    assert retry_conversation[:2] == _MESSAGES
    assert retry_conversation[2] == Message(role="assistant", content="bad draft")
    assert retry_conversation[3].role == "user"
    assert "bad draft is unacceptable" in retry_conversation[3].content
    assert "raw JSON object only" in retry_conversation[3].content


def test_gives_up_after_the_second_malformed_response() -> None:
    client = _ScriptedClient([_completion("bad one"), _completion("bad two")])

    with pytest.raises(MalformedResponseError, match="bad two is unacceptable"):
        structured_completion(client, _MESSAGES, _parse)

    assert len(client.calls) == 2


def test_retries_a_truncated_response_as_sent() -> None:
    client = _ScriptedClient([TruncatedResponseError("hit the limit"), _completion("fine")])

    result, _ = structured_completion(client, _MESSAGES, _parse)

    assert result == "parsed:fine"
    # The retry repeats the request untouched: no feedback, no extra turns.
    assert client.calls[1] == _MESSAGES
    assert len(client.calls) == 2


def test_gives_up_after_the_second_truncation() -> None:
    client = _ScriptedClient(
        [TruncatedResponseError("hit the limit"), TruncatedResponseError("again")]
    )

    with pytest.raises(TruncatedResponseError, match="again"):
        structured_completion(client, _MESSAGES, _parse)

    assert len(client.calls) == 2


def test_truncation_does_not_consume_the_parse_retry() -> None:
    client = _ScriptedClient(
        [TruncatedResponseError("hit the limit"), _completion("bad draft"), _completion("fine")]
    )

    result, _ = structured_completion(client, _MESSAGES, _parse)

    assert result == "parsed:fine"
    assert len(client.calls) == 3


def test_sums_usage_across_attempts() -> None:
    client = _ScriptedClient([_completion("bad draft"), _completion("fine")])

    _, usage = structured_completion(client, _MESSAGES, _parse)

    assert usage == Usage(prompt_tokens=200, completion_tokens=100, total_tokens=300)


def test_usage_is_none_when_no_attempt_reported_it() -> None:
    client = _ScriptedClient([_completion("fine", usage=None)])

    _, usage = structured_completion(client, _MESSAGES, _parse)

    assert usage is None


def test_transport_errors_propagate_untouched() -> None:
    client = _ScriptedClient([TransientError("NVIDIA API is unavailable")])

    with pytest.raises(TransientError):
        structured_completion(client, _MESSAGES, _parse)

    assert len(client.calls) == 1
