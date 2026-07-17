"""Tests for `resume-roast generate-block`."""

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import ClassVar

import pytest
from typer.testing import CliRunner

from resume_roast.cli.registry import build_subcommand_registry
from resume_roast.integrations.errors import AuthenticationError, TransientError
from resume_roast.integrations.types import Completion, Message, Usage
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import Credentials

app = build_subcommand_registry()
runner = CliRunner()

_MODEL = "nvidia/nemotron-3-super-120b-a12b"


class _FakeStream:
    """A CompletionStream that yields one reply, then reports usage/finish."""

    def __init__(self, reply: str, usage: Usage | None) -> None:
        self._reply = reply
        self._usage = usage
        self.usage: Usage | None = None
        self.finish_reason: str | None = None

    def __iter__(self) -> Iterator[str]:
        yield self._reply
        self.usage = self._usage
        self.finish_reason = "stop"


class _FakeClient:
    """Stands in for NvidiaClient; streams a fixed reply per turn."""

    reply: ClassVar[str] = "Tell me more about your role."
    usage: ClassVar[Usage | None] = None
    last: ClassVar["_FakeClient | None"] = None
    fail_on_call: ClassVar[int | None] = None
    fail_error: ClassVar[type[Exception]] = TransientError
    _call_count: ClassVar[int] = 0

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.calls: list[list[Message]] = []
        type(self).last = self

    def prompt(self, messages: Sequence[Message], *, temperature: float = 0.0) -> Completion:
        raise NotImplementedError

    def prompt_stream(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.0,  # noqa: ARG002 — the protocol's signature requires it
    ) -> _FakeStream:
        self.calls.append(list(messages))
        type(self)._call_count += 1
        if (
            type(self).fail_on_call is not None
            and type(self)._call_count == type(self).fail_on_call
        ):
            raise type(self).fail_error("Simulated API error")
        return _FakeStream(type(self).reply, type(self).usage)


@pytest.fixture(autouse=True)
def _isolated_storage_dir(  # pyright: ignore[reportUnusedFunction]
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.setattr("resume_roast.cli.utils.storage_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    monkeypatch.setattr("resume_roast.cli.utils.NvidiaClient", _FakeClient)
    monkeypatch.setattr(_FakeClient, "reply", "Tell me more about your role.")
    monkeypatch.setattr(_FakeClient, "usage", None)
    monkeypatch.setattr(_FakeClient, "last", None)
    monkeypatch.setattr(_FakeClient, "fail_on_call", None)
    monkeypatch.setattr(_FakeClient, "fail_error", TransientError)
    monkeypatch.setattr(_FakeClient, "_call_count", 0)


@pytest.fixture
def saved_key(tmp_path: Path) -> None:
    credentials = Credentials(nvidia_api_key="nv-key")  # pragma: allowlist secret
    CredentialsStore(tmp_path).save(credentials)


# -- tests -------------------------------------------------------------------


@pytest.mark.usefixtures("saved_key")
def test_generate_block_shows_welcome_message() -> None:
    result = runner.invoke(app, ["generate-block"], input="/exit\n")

    assert result.exit_code == 0
    assert "Tell me about a role or project" in result.output
    assert "/help" in result.output


@pytest.mark.usefixtures("saved_key")
def test_generate_block_streams_a_reply() -> None:
    result = runner.invoke(
        app, ["generate-block"], input="Tell me about my role at Google\n/exit\n"
    )

    assert result.exit_code == 0
    assert "Tell me about a role or project" in result.output
    assert "Tell me more about your role." in result.output


@pytest.mark.usefixtures("saved_key")
def test_opens_with_a_single_system_message_then_first_user_turn() -> None:
    runner.invoke(app, ["generate-block"], input="I was a backend engineer at Stripe\n/exit\n")

    client = _FakeClient.last
    assert client is not None
    assert client.api_key == "nv-key"  # pragma: allowlist secret
    assert client.model == _MODEL  # default settings

    messages = client.calls[0]
    assert [m.role for m in messages] == ["system", "user"]
    assert "## Context" in messages[0].content
    assert "## Process" in messages[0].content
    assert "## Principles" in messages[0].content
    assert "## Rules" in messages[0].content
    assert messages[-1].role == "user"
    assert messages[-1].content == "I was a backend engineer at Stripe"


@pytest.mark.usefixtures("saved_key")
def test_prints_the_summary_line(monkeypatch: pytest.MonkeyPatch) -> None:
    usage = Usage(prompt_tokens=1_000, completion_tokens=200, total_tokens=1_200)
    monkeypatch.setattr(_FakeClient, "usage", usage)

    result = runner.invoke(app, ["generate-block"], input="I worked at Google\n/exit\n")

    assert "1,000 input tokens · 200 output tokens" in result.output
    assert "nemotron-3-super" in result.output
    assert "Tell me about a role or project" in result.output


def test_requires_an_api_key() -> None:
    result = runner.invoke(app, ["generate-block"], input="I worked at Google\n/exit\n")

    assert result.exit_code == 1
    assert "No NVIDIA API key configured" in result.output
    assert "Traceback" not in result.output
    assert "Tell me about a role" not in result.output  # never gets past setup


@pytest.mark.usefixtures("saved_key")
def test_generate_triggers_block_creation() -> None:
    result = runner.invoke(
        app,
        ["generate-block"],
        input="I was a backend engineer at Stripe\n/generate\n/exit\n",
    )

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None
    assert len(client.calls) == 2

    messages = client.calls[1]
    assert sum(m.role == "system" for m in messages) == 1

    generate_turn = messages[-1]
    assert generate_turn.role == "user"
    assert "generate a complete resume entry" in generate_turn.content.lower()


@pytest.mark.usefixtures("saved_key")
def test_generate_with_notes_includes_notes() -> None:
    result = runner.invoke(
        app,
        ["generate-block"],
        input="I was a backend engineer at Stripe\n/generate Focus on payment processing\n/exit\n",
    )

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None

    generate_turn = client.calls[1][-1]
    assert generate_turn.role == "user"
    assert "generate a complete resume entry" in generate_turn.content.lower()
    assert "payment processing" in generate_turn.content


@pytest.mark.usefixtures("saved_key")
def test_exit_ends_the_session() -> None:
    result = runner.invoke(app, ["generate-block"], input="/exit\n")

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None
    assert len(client.calls) == 0  # no API calls were made
    assert "Tell me about a role" in result.output


@pytest.mark.usefixtures("saved_key")
def test_help_prints_available_commands() -> None:
    result = runner.invoke(app, ["generate-block"], input="/help\n/exit\n")

    assert result.exit_code == 0
    assert "/generate" in result.output
    assert "/exit" in result.output
    assert "/help" in result.output
    client = _FakeClient.last
    assert client is not None
    assert len(client.calls) == 0  # no API calls for /help


@pytest.mark.usefixtures("saved_key")
def test_unrecognised_command_prints_hint() -> None:
    result = runner.invoke(
        app,
        ["generate-block"],
        input="/bogus\n/exit\n",
    )

    assert result.exit_code == 0
    assert "(unrecognised command)" in result.output


@pytest.mark.usefixtures("saved_key")
def test_chat_passes_through_raw_text() -> None:
    result = runner.invoke(
        app,
        ["generate-block"],
        input="I was a backend engineer at Stripe\n/exit\n",
    )

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None

    chat_turn = client.calls[0][-1]
    assert chat_turn.role == "user"
    assert chat_turn.content == "I was a backend engineer at Stripe"


@pytest.mark.usefixtures("saved_key")
def test_transient_error_is_reported_and_session_survives(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_FakeClient, "fail_on_call", 2)  # second call fails

    result = runner.invoke(
        app,
        ["generate-block"],
        input="I worked at Google\nwhat about Stripe?\n/exit\n",
    )

    assert result.exit_code == 0
    assert "try again" in result.output
    client = _FakeClient.last
    assert client is not None
    # Two API calls: first chat succeeds, second chat fails (no retry since /exit follows)
    assert len(client.calls) == 2


@pytest.mark.usefixtures("saved_key")
def test_non_transient_error_ends_the_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_FakeClient, "fail_on_call", 1)  # first call fails
    monkeypatch.setattr(_FakeClient, "fail_error", AuthenticationError)

    result = runner.invoke(
        app,
        ["generate-block"],
        input="I worked at Google\nwhat about Stripe?\n/exit\n",
    )

    assert result.exit_code == 1
    assert "try again" not in result.output  # a rejected key is not retryable
    client = _FakeClient.last
    assert client is not None
    # The session ends on the first (failing) turn — the later turns never run.
    assert len(client.calls) == 1
