"""ChatSession: outcome dispatch, commit-on-success, error handling, and the drain contract."""

from collections.abc import Iterable, Iterator, Mapping, Sequence
from enum import Enum

import pytest

from resume_roast.integrations.conversation import Conversation
from resume_roast.integrations.errors import TransientError
from resume_roast.integrations.types import Completion, Message, Usage
from resume_roast.services.chat.command_executor import CommandExecutor
from resume_roast.services.chat.enums import ArgPolicy
from resume_roast.services.chat.input_parser import InputParser
from resume_roast.services.chat.session import ChatSession
from resume_roast.services.chat.types import CommandSpec, Outcome, SendTurn

_USAGE = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)


class _FakeStream:
    """A CompletionStream: yields scripted chunks, then reports usage/finish."""

    def __init__(self, chunks: Sequence[str], *, error: Exception | None = None) -> None:
        self._chunks = chunks
        self._error = error
        self.usage: Usage | None = None
        self.finish_reason: str | None = None

    def __iter__(self) -> Iterator[str]:
        yield from self._chunks
        if self._error is not None:
            raise self._error
        self.usage = _USAGE
        self.finish_reason = "stop"


class _FakeClient:
    """Satisfies LlmClient; serves a scripted stream (or raises) per call."""

    model: str = ""

    def __init__(self, streams: Sequence["_FakeStream | Exception"]) -> None:
        self._streams = list(streams)
        self.calls: list[list[Message]] = []

    def prompt(self, messages: Sequence[Message], *, temperature: float = 0.0) -> Completion:
        raise NotImplementedError

    def prompt_stream(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.0,  # noqa: ARG002 — the protocol's signature requires it
    ) -> _FakeStream:
        self.calls.append(list(messages))
        item = self._streams.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _ScriptedInput:
    """Feeds scripted lines; raises EOFError when the script runs out."""

    def __init__(self, lines: Sequence[str]) -> None:
        self._lines = list(lines)

    def get_input(self) -> str:
        if not self._lines:
            raise EOFError
        return self._lines.pop(0)


class _RendererSpy:
    """Records every rendering call; drains replies fully."""

    def __init__(self) -> None:
        self.replies: list[str] = []
        self.metrics: list[tuple[Usage | None, str | None]] = []
        self.errors: list[str] = []
        self.helps: list[str] = []
        self.hints = 0
        self.interrupts = 0

    def show_reply(self, chunks: Iterable[str]) -> None:
        self.replies.append("".join(chunks))

    def show_metrics(
        self,
        usage: Usage | None,
        finish_reason: str | None,
        latency_seconds: float,  # noqa: ARG002 — the protocol's signature requires it
    ) -> None:
        self.metrics.append((usage, finish_reason))

    def show_transient_error(self, error: TransientError) -> None:
        self.errors.append(str(error))

    def show_help(self, text: str) -> None:
        self.helps.append(text)

    def show_usage_hint(self) -> None:
        self.hints += 1

    def show_interrupt(self) -> None:
        self.interrupts += 1


class _LazyRenderer(_RendererSpy):
    """A buggy renderer that stops after the first chunk instead of draining."""

    def show_reply(self, chunks: Iterable[str]) -> None:
        next(iter(chunks))


class _PinCommand(Enum):
    PIN = "pin"


class _PinExecutor(CommandExecutor[_PinCommand]):
    """One required-arg command whose commit closure records the pinned value."""

    def __init__(self) -> None:
        self.pinned: list[str] = []

    @property
    def commands(self) -> Mapping[_PinCommand, CommandSpec]:
        return {_PinCommand.PIN: CommandSpec(ArgPolicy.REQUIRED, "Pin a value", "<value>")}

    def chat(self, text: str) -> Outcome:
        return SendTurn(f"chat:{text}")

    def command(self, command: _PinCommand, arg: str | None) -> Outcome:
        assert command is _PinCommand.PIN
        assert arg is not None  # REQUIRED policy filters bare /pin

        def commit() -> None:
            self.pinned.append(arg)

        return SendTurn(f"pin:{arg}", commit)


def _session(
    lines: Sequence[str], streams: Sequence["_FakeStream | Exception"]
) -> tuple[ChatSession[_PinCommand], _FakeClient, _PinExecutor, _RendererSpy]:
    client = _FakeClient(streams)
    conversation = Conversation(client, "be helpful", temperature=0.5)
    executor = _PinExecutor()
    renderer = _RendererSpy()
    session = ChatSession(conversation, InputParser(), executor, renderer, _ScriptedInput(lines))
    return session, client, executor, renderer


def test_exit_ends_the_session_without_an_api_call() -> None:
    session, client, _, renderer = _session(["/exit"], [])

    session.run()

    assert client.calls == []
    assert renderer.replies == []


def test_help_and_hint_make_no_api_call() -> None:
    session, client, _, renderer = _session(["/bogus", "/help", "/exit"], [])

    session.run()

    assert client.calls == []
    assert renderer.hints == 1
    assert renderer.helps == [_PinExecutor().help_text]


def test_a_chat_turn_streams_the_reply_and_reports_metrics() -> None:
    session, client, _, renderer = _session(["hello", "/exit"], [_FakeStream(["Hi", "!"])])

    session.run()

    assert renderer.replies == ["Hi!"]
    assert renderer.metrics == [(_USAGE, "stop")]
    assert client.calls[0][-1].content == "chat:hello"


def test_the_opening_turn_is_sent_before_the_loop() -> None:
    session, client, _, renderer = _session(["/exit"], [_FakeStream(["welcome"])])

    session.run(opening="the opening turn")

    assert client.calls[0][-1].content == "the opening turn"
    assert renderer.replies == ["welcome"]


def test_a_commit_fires_only_after_the_exchange_lands() -> None:
    session, _, executor, _ = _session(["/pin it", "/exit"], [_FakeStream(["ok"])])

    session.run()

    assert executor.pinned == ["it"]


def test_a_transient_error_reports_and_skips_the_commit() -> None:
    session, client, executor, renderer = _session(
        ["/pin it", "/pin again", "/exit"],
        [TransientError("unavailable"), _FakeStream(["ok"])],
    )

    session.run()

    # First /pin failed at request-open: reported, not committed, session alive.
    assert renderer.errors == ["unavailable"]
    assert executor.pinned == ["again"]
    assert len(client.calls) == 2


def test_a_mid_stream_failure_rolls_back_and_skips_the_commit() -> None:
    error = TransientError("dropped mid-stream")
    session, client, executor, renderer = _session(
        ["/pin it", "/exit"], [_FakeStream(["par"], error=error)]
    )

    session.run()

    assert renderer.errors == ["dropped mid-stream"]
    assert executor.pinned == []
    # The failed turn left no trace in the history.
    assert client.calls[0][-1].content == "pin:it"
    assert [m.role for m in client.calls[0]] == ["system", "user"]


def test_end_of_input_shows_the_interrupt() -> None:
    session, _, _, renderer = _session([], [])

    session.run()

    assert renderer.interrupts == 1


def test_a_renderer_that_does_not_drain_the_reply_fails_loudly() -> None:
    client = _FakeClient([_FakeStream(["one", "two"])])
    conversation = Conversation(client, "be helpful", temperature=0.5)
    session = ChatSession(
        conversation, InputParser(), _PinExecutor(), _LazyRenderer(), _ScriptedInput(["hello"])
    )

    with pytest.raises(RuntimeError, match="drain"):
        session.run()
