"""Conversation: turn ordering, usage accumulation, and rollback on failure."""

from collections.abc import Iterator, Sequence

import pytest

from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.errors import TransientError
from resume_roast.integrations.types import Completion, Message, Usage

_USAGE = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)


class _FakeStream:
    """A CompletionStream: yields scripted chunks, then reports usage/finish.

    Mirrors the real contract — ``usage`` and ``finish_reason`` stay None until
    the stream is exhausted. When ``error`` is set it raises after its chunks,
    standing in for a client that fails mid-stream.
    """

    def __init__(
        self,
        chunks: Sequence[str],
        *,
        usage: Usage | None = _USAGE,
        finish_reason: str | None = "stop",
        error: Exception | None = None,
    ) -> None:
        self._chunks = chunks
        self._usage = usage
        self._finish_reason = finish_reason
        self._error = error
        self.usage: Usage | None = None
        self.finish_reason: str | None = None

    def __iter__(self) -> Iterator[str]:
        yield from self._chunks
        if self._error is not None:
            raise self._error
        self.usage = self._usage
        self.finish_reason = self._finish_reason


class _FakeClient:
    """Satisfies LlmClient; serves a scripted stream per prompt_stream call."""

    def __init__(self, streams: Sequence[_FakeStream]) -> None:
        self._streams = list(streams)
        self.calls: list[list[Message]] = []
        self.temperatures: list[float] = []

    def prompt(self, messages: Sequence[Message], *, temperature: float = 0.0) -> Completion:
        raise NotImplementedError

    def prompt_stream(
        self, messages: Sequence[Message], *, temperature: float = 0.0
    ) -> _FakeStream:
        self.calls.append(list(messages))
        self.temperatures.append(temperature)
        return self._streams.pop(0)


def test_start_seeds_only_a_system_message() -> None:
    conversation = Conversation.start(_FakeClient([]), "be helpful", temperature=0.5)

    assert conversation.messages == [Message(role="system", content="be helpful")]


def test_send_stream_yields_chunks_and_records_the_turn() -> None:
    client = _FakeClient([_FakeStream(["Hel", "lo", "!"])])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    chunks = list(conversation.send_stream("hi"))

    assert chunks == ["Hel", "lo", "!"]
    assert conversation.messages == [
        Message(role="system", content="be helpful"),
        Message(role="user", content="hi"),
        Message(role="assistant", content="Hello!"),
    ]


def test_sends_the_full_conversation_and_temperature_to_the_client() -> None:
    client = _FakeClient([_FakeStream(["ok"])])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    list(conversation.send_stream("hi"))

    assert client.calls[0] == [
        Message(role="system", content="be helpful"),
        Message(role="user", content="hi"),
    ]
    assert client.temperatures == [0.5]


def test_later_turns_carry_the_prior_turns() -> None:
    client = _FakeClient([_FakeStream(["one"]), _FakeStream(["two"])])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    list(conversation.send_stream("first"))
    list(conversation.send_stream("second"))

    assert client.calls[1] == [
        Message(role="system", content="be helpful"),
        Message(role="user", content="first"),
        Message(role="assistant", content="one"),
        Message(role="user", content="second"),
    ]


def test_accumulates_usage_across_turns() -> None:
    client = _FakeClient([_FakeStream(["one"]), _FakeStream(["two"])])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    list(conversation.send_stream("first"))
    list(conversation.send_stream("second"))

    assert conversation.total_usage == Usage(
        prompt_tokens=200, completion_tokens=100, total_tokens=300
    )


def test_total_usage_is_none_when_no_turn_reported_it() -> None:
    client = _FakeClient([_FakeStream(["ok"], usage=None)])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    list(conversation.send_stream("hi"))

    assert conversation.total_usage is None


def test_records_the_last_finish_reason() -> None:
    client = _FakeClient([_FakeStream(["cut"], finish_reason="length")])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    list(conversation.send_stream("hi"))

    assert conversation.last_finish_reason == "length"


def test_records_the_last_usage() -> None:
    client = _FakeClient([_FakeStream(["ok"], usage=_USAGE)])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    list(conversation.send_stream("hi"))

    assert conversation.last_usage == _USAGE


def test_last_usage_is_this_turn_not_the_running_total() -> None:
    second = Usage(prompt_tokens=7, completion_tokens=3, total_tokens=10)
    client = _FakeClient([_FakeStream(["one"]), _FakeStream(["two"], usage=second)])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    list(conversation.send_stream("first"))
    list(conversation.send_stream("second"))

    # last_usage tracks only the latest turn, unlike the cumulative total_usage.
    assert conversation.last_usage == second
    assert conversation.total_usage == Usage(
        prompt_tokens=107, completion_tokens=53, total_tokens=160
    )


def test_rolls_back_the_user_turn_when_the_stream_fails() -> None:
    error = TransientError("NVIDIA API is unavailable")
    client = _FakeClient([_FakeStream(["par", "tial"], error=error), _FakeStream(["recovered"])])
    conversation = Conversation.start(client, "be helpful", temperature=0.5)

    with pytest.raises(TransientError):
        list(conversation.send_stream("hi"))

    # The failed turn left no trace: back to just the system message.
    assert conversation.messages == [Message(role="system", content="be helpful")]

    # A retry against the unchanged conversation succeeds cleanly.
    chunks = list(conversation.send_stream("hi"))
    assert chunks == ["recovered"]
    assert conversation.messages == [
        Message(role="system", content="be helpful"),
        Message(role="user", content="hi"),
        Message(role="assistant", content="recovered"),
    ]
