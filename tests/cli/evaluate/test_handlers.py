"""Tests for `resume-roast evaluate`."""

# The fixture drives PyMuPDF's partially annotated document-building API.
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false

import re
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import ClassVar

import pymupdf
import pytest
from typer.testing import CliRunner

from resume_roast.cli.registry import build_subcommand_registry
from resume_roast.integrations.nvidia.errors import TransientError
from resume_roast.integrations.nvidia.types import Message, Usage
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import Credentials

app = build_subcommand_registry()
runner = CliRunner()

_MODEL = "nvidia/nemotron-3-super-120b-a12b"


class _FakeStream:
    def __init__(self, chunks: list[str], usage: Usage | None, finish_reason: str | None) -> None:
        self._chunks = chunks
        self.usage = usage
        self.finish_reason = finish_reason

    def __iter__(self) -> Iterator[str]:
        yield from self._chunks


class _FakeClient:
    """Stands in for NvidiaClient; records what the handler sends."""

    chunks: ClassVar[list[str]] = ["It's ", "a roast."]
    usage: ClassVar[Usage | None] = Usage(
        prompt_tokens=2_000, completion_tokens=1_214, total_tokens=3_214
    )
    finish_reason: ClassVar[str | None] = "stop"
    error: ClassVar[Exception | None] = None
    last: ClassVar["_FakeClient | None"] = None

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.messages: Sequence[Message] | None = None
        type(self).last = self

    def prompt_stream(self, messages: Sequence[Message]) -> _FakeStream:
        self.messages = messages
        error = type(self).error
        if error is not None:
            raise error
        return _FakeStream(type(self).chunks, type(self).usage, type(self).finish_reason)


@pytest.fixture(autouse=True)
def _isolated_storage_dir(  # pyright: ignore[reportUnusedFunction]
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.setattr("resume_roast.cli.evaluate.handlers.storage_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    monkeypatch.setattr("resume_roast.cli.evaluate.handlers.NvidiaClient", _FakeClient)
    monkeypatch.setattr(_FakeClient, "chunks", ["It's ", "a roast."])
    monkeypatch.setattr(
        _FakeClient,
        "usage",
        Usage(prompt_tokens=2_000, completion_tokens=1_214, total_tokens=3_214),
    )
    monkeypatch.setattr(_FakeClient, "finish_reason", "stop")
    monkeypatch.setattr(_FakeClient, "error", None)
    monkeypatch.setattr(_FakeClient, "last", None)


@pytest.fixture
def saved_key(tmp_path: Path) -> None:
    credentials = Credentials(nvidia_api_key="nv-key")  # pragma: allowlist secret
    CredentialsStore(tmp_path).save(credentials)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "sample.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 80), "Jane Doe", fontsize=20)
        page.insert_text((72, 120), "Roasted resumes at Acme Corp", fontsize=11)
        doc.save(path)
    return path


@pytest.mark.usefixtures("saved_key")
def test_evaluate_streams_the_roast(sample_pdf: Path) -> None:
    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    assert result.exit_code == 0
    assert "It's a roast." in result.output


@pytest.mark.usefixtures("saved_key")
def test_evaluate_sends_system_and_user_messages(sample_pdf: Path) -> None:
    runner.invoke(app, ["evaluate", str(sample_pdf)])

    client = _FakeClient.last
    assert client is not None
    assert client.api_key == "nv-key"  # pragma: allowlist secret
    assert client.model == _MODEL  # default settings
    assert client.messages is not None
    system, user = client.messages
    assert system.role == "system"
    assert "## Persona: Recruiter" in system.content
    assert user.role == "user"
    assert "Jane Doe" in user.content


@pytest.mark.usefixtures("saved_key")
def test_evaluate_prints_summary_line(sample_pdf: Path) -> None:
    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    # 2000/1M * $0.09 + 1214/1M * $0.45 = $0.00072...
    assert "2,000 in · 1,214 out · ~$0.0007 · " in result.output
    assert _MODEL not in result.output
    assert re.search(r"· \d+\.\ds", result.output)


@pytest.mark.usefixtures("saved_key")
def test_evaluate_summary_omits_tokens_and_cost_without_usage(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_FakeClient, "usage", None)

    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    assert result.exit_code == 0
    assert " in ·" not in result.output
    assert "$" not in result.output
    assert re.search(r"^\d+\.\ds", result.output, re.MULTILINE)


@pytest.mark.usefixtures("saved_key")
def test_evaluate_warns_on_truncation(sample_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_FakeClient, "finish_reason", "length")

    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    assert result.exit_code == 0
    assert "completion-token limit" in result.output


def test_evaluate_requires_an_api_key(sample_pdf: Path) -> None:
    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    assert result.exit_code == 1
    assert "No NVIDIA API key configured" in result.output
    assert "resume-roast config credentials" in result.output
    assert "Traceback" not in result.output


@pytest.mark.usefixtures("saved_key")
def test_evaluate_reports_client_errors(sample_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_FakeClient, "error", TransientError("NVIDIA API is unavailable."))

    result = runner.invoke(app, ["evaluate", str(sample_pdf)])

    assert result.exit_code == 1
    assert "NVIDIA API is unavailable" in result.output
    assert "Traceback" not in result.output


@pytest.mark.usefixtures("saved_key")
def test_evaluate_reports_unreadable_file(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"this is not a pdf")

    result = runner.invoke(app, ["evaluate", str(path)])

    assert result.exit_code == 1
    assert "Error" in result.output
    assert "Traceback" not in result.output


@pytest.mark.usefixtures("saved_key")
def test_evaluate_reports_missing_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["evaluate", str(tmp_path / "missing.pdf")])

    assert result.exit_code == 1
    assert "Error" in result.output
    assert "Traceback" not in result.output
