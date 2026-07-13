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
def test_refine_opens_with_a_single_system_message_then_the_bullet() -> None:
    runner.invoke(app, ["refine", "Managed a team"], input="/exit\n")

    client = _FakeClient.last
    assert client is not None
    assert client.api_key == "nv-key"  # pragma: allowlist secret
    assert client.model == _MODEL  # default settings

    # calls[0] is exactly: one leading system message, then the user turn.
    messages = client.calls[0]
    assert [m.role for m in messages] == ["system", "user"]
    # The single system message carries the builder's sections.
    assert "## Context" in messages[0].content
    assert "## Principles" in messages[0].content
    assert "## Rules" in messages[0].content
    # The opening user turn carries the bullet, tagged for the header.
    assert messages[-1].role == "user"
    assert "Managed a team" in messages[-1].content
    assert "<current bullet point>" in messages[-1].content


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

    # Exactly one system message throughout — per-turn context rides in user turns.
    messages = client.calls[1]
    assert sum(m.role == "system" for m in messages) == 1

    # The /replace user turn carries the new bullet and asks for a re-rating.
    replace_turn = messages[-1]
    assert replace_turn.role == "user"
    assert "Led a team of 10 engineers" in replace_turn.content
    assert "re-rate" in replace_turn.content.lower()


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
    assert sum(m.role == "system" for m in messages) == 1

    # The /generate user turn carries the current bullet and the note.
    generate_turn = messages[-1]
    assert generate_turn.role == "user"
    assert "Managed a team" in generate_turn.content
    assert "add metrics" in generate_turn.content


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

    generate_turn = client.calls[1][-1]
    assert generate_turn.role == "user"
    assert "Managed a team" in generate_turn.content
    assert "<note>" not in generate_turn.content


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

    # The chat turn carries both the current bullet and the user's question.
    chat_turn = client.calls[1][-1]
    assert chat_turn.role == "user"
    assert "Initial bullet" in chat_turn.content
    assert "what about the verb?" in chat_turn.content


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


@pytest.mark.usefixtures("saved_key")
def test_failed_replace_does_not_commit_the_new_bullet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_FakeClient, "fail_on_call", 2)  # the /replace call fails

    result = runner.invoke(
        app,
        ["refine", "Original bullet"],
        input="/replace New bullet that fails\nwhat next?\n/exit\n",
    )

    assert result.exit_code == 0
    assert "try again" in result.output
    client = _FakeClient.last
    assert client is not None
    # Three API calls: initial (ok) + replace (fails) + chat (ok).
    assert len(client.calls) == 3

    # The failed /replace was never committed: the chat turn still references
    # the original bullet, and no trace of the failed replace remains.
    chat_turn = client.calls[2][-1]
    assert chat_turn.role == "user"
    assert "Original bullet" in chat_turn.content
    # No trace of the failed replace anywhere in the conversation.
    assert not any("New bullet that fails" in m.content for m in client.calls[2])
