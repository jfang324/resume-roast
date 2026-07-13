"""Tests for `resume-roast refine`."""

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import ClassVar

import pytest
from typer.testing import CliRunner

from resume_roast.cli.registry import build_subcommand_registry
from resume_roast.integrations.errors import ApiError
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

    reply: ClassVar[str] = "Lead with the metric."
    usage: ClassVar[Usage | None] = None
    last: ClassVar["_FakeClient | None"] = None
    fail_on_call: ClassVar[int | None] = None
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
            raise ApiError("Simulated transient error")
        return _FakeStream(type(self).reply, type(self).usage)


@pytest.fixture(autouse=True)
def _isolated_storage_dir(  # pyright: ignore[reportUnusedFunction]
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.setattr("resume_roast.cli.refine.handlers.storage_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    monkeypatch.setattr("resume_roast.cli.refine.handlers.NvidiaClient", _FakeClient)
    monkeypatch.setattr(_FakeClient, "reply", "Lead with the metric.")
    monkeypatch.setattr(_FakeClient, "usage", None)
    monkeypatch.setattr(_FakeClient, "last", None)
    monkeypatch.setattr(_FakeClient, "fail_on_call", None)
    monkeypatch.setattr(_FakeClient, "_call_count", 0)


@pytest.fixture
def saved_key(tmp_path: Path) -> None:
    credentials = Credentials(nvidia_api_key="nv-key")  # pragma: allowlist secret
    CredentialsStore(tmp_path).save(credentials)


# -- existing tests (adapted for new architecture) ---------------------------


@pytest.mark.usefixtures("saved_key")
def test_refine_streams_a_reply_to_the_bullet() -> None:
    result = runner.invoke(app, ["refine", "Managed a team"], input="/exit\n")

    assert result.exit_code == 0
    assert "> Managed a team" in result.output
    # The reply is tagged with the model's name, not a generic "AI".
    assert "nemotron-3-super" in result.output
    assert "Lead with the metric." in result.output


@pytest.mark.usefixtures("saved_key")
def test_refine_opens_with_the_bullet_as_the_first_user_turn() -> None:
    runner.invoke(app, ["refine", "Managed a team"], input="/exit\n")

    client = _FakeClient.last
    assert client is not None
    assert client.api_key == "nv-key"  # pragma: allowlist secret
    assert client.model == _MODEL  # default settings

    # calls[0] has: system, initial-block system, user = bullet
    messages = client.calls[0]
    # Last message is the user bullet
    assert messages[-1] == Message(role="user", content="Managed a team")
    # Some system messages are present
    assert any(m.role == "system" for m in messages)
    # System content includes the builder's sections
    system_contents = [m.content for m in messages if m.role == "system"]
    assert any("## Context" in c for c in system_contents)
    assert any("## Principles" in c for c in system_contents)
    assert any("## Rules" in c for c in system_contents)


@pytest.mark.usefixtures("saved_key")
def test_refine_prints_the_summary_line(monkeypatch: pytest.MonkeyPatch) -> None:
    usage = Usage(prompt_tokens=1_000, completion_tokens=200, total_tokens=1_200)
    monkeypatch.setattr(_FakeClient, "usage", usage)

    result = runner.invoke(app, ["refine", "Managed a team"], input="/exit\n")

    assert "1,000 input tokens · 200 output tokens" in result.output
    assert _MODEL not in result.output


def test_refine_requires_an_api_key() -> None:
    result = runner.invoke(app, ["refine", "Managed a team"], input="/exit\n")

    assert result.exit_code == 1
    assert "No NVIDIA API key configured" in result.output
    assert "Traceback" not in result.output


# -- new tests for /replace and /generate ------------------------------------


@pytest.mark.usefixtures("saved_key")
def test_replace_updates_current_bullet_and_triggers_re_rating() -> None:
    result = runner.invoke(
        app,
        ["refine", "Managed a team"],
        input="/replace Led a team of 10 engineers\n/exit\n",
    )

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None

    # Two API calls: initial bullet + /replace
    assert len(client.calls) == 2

    # Second call: system + initial-block + replace-block + user
    messages = client.calls[1]
    system_contents = [m.content for m in messages if m.role == "system"]

    # A system block mentions the new bullet
    assert any("Led a team of 10 engineers" in c for c in system_contents)
    # User message is the synthetic replace text
    assert messages[-1] == Message(role="user", content="I've updated my bullet.")


@pytest.mark.usefixtures("saved_key")
def test_generate_produces_candidate_without_changing_state() -> None:
    result = runner.invoke(
        app,
        ["refine", "Managed a team"],
        input="/generate add metrics\n/exit\n",
    )

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None

    # Two API calls: initial + /generate
    assert len(client.calls) == 2

    messages = client.calls[1]
    system_contents = [m.content for m in messages if m.role == "system"]

    # Generate block mentions the current bullet
    assert any("Managed a team" in c for c in system_contents)
    # Generate block has <note> with the note text
    assert any("add metrics" in c for c in system_contents)
    # User message is the synthetic generate text
    assert messages[-1] == Message(role="user", content="Generate a candidate.")


@pytest.mark.usefixtures("saved_key")
def test_generate_without_notes_omits_note_tag() -> None:
    result = runner.invoke(
        app,
        ["refine", "Managed a team"],
        input="/generate\n/exit\n",
    )

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None
    assert len(client.calls) == 2

    system_contents = [m.content for m in client.calls[1] if m.role == "system"]
    assert any("Managed a team" in c for c in system_contents)
    assert not any("<note>" in c for c in system_contents)


@pytest.mark.usefixtures("saved_key")
def test_unrecognised_command_prints_hint() -> None:
    result = runner.invoke(
        app,
        ["refine", "Managed a team"],
        input="/bogus\n/exit\n",
    )

    assert result.exit_code == 0
    assert "(unrecognised command)" in result.output


@pytest.mark.usefixtures("saved_key")
def test_conversation_chat_does_not_change_current_bullet() -> None:
    result = runner.invoke(
        app,
        ["refine", "Initial bullet"],
        input="what about the verb?\n/exit\n",
    )

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None

    messages = client.calls[1]
    system_contents = [m.content for m in messages if m.role == "system"]

    # Current bullet remains the initial one
    assert any("Initial bullet" in c for c in system_contents)
    # User text is the chat message
    assert messages[-1] == Message(role="user", content="what about the verb?")


@pytest.mark.usefixtures("saved_key")
def test_transient_error_is_reported_and_session_survives(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_FakeClient, "fail_on_call", 2)  # second call fails

    result = runner.invoke(
        app,
        ["refine", "Managed a team"],
        input="what about the verb?\nwhat about the verb?\n/exit\n",
    )

    assert result.exit_code == 0
    assert "try again" in result.output  # error message printed
    client = _FakeClient.last
    assert client is not None
    # Three API calls: initial + failed chat + retry chat
    assert len(client.calls) == 3
