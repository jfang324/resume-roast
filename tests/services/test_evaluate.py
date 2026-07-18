"""services.evaluate: prompt construction, structured_completion dispatch, result shaping."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from resume_roast.integrations.errors import (
    MalformedResponseError,
    TransientError,
    TruncatedResponseError,
)
from resume_roast.integrations.llm_client import CompletionStream
from resume_roast.integrations.types import Completion, Message, Usage
from resume_roast.prompts.evaluate.output.schema import CATEGORY_NAMES
from resume_roast.services.evaluate.service import run
from resume_roast.services.evaluate.types import EvaluateResult
from resume_roast.utils.extraction.types import DocumentMetadata, ParsedResume

_USAGE = Usage(prompt_tokens=100, completion_tokens=50, total_tokens=150)


def _metadata() -> DocumentMetadata:
    return DocumentMetadata(
        page_count=0,
        creator=None,
        producer=None,
        created=None,
        modified=None,
        links=(),
        pages=(),
    )


_PARSED = ParsedResume(markdown="", metadata=_metadata())

_PATH = Path("resume.pdf")


class _StubDocParser:
    """Stands in for extraction; returns the canned ParsedResume."""

    def parse(
        self,
        path: Path,  # noqa: ARG002 — the extraction signature requires it
    ) -> ParsedResume:
        return _PARSED


def _fake_get_parser(_: Path) -> _StubDocParser:
    return _StubDocParser()


@pytest.fixture(autouse=True)
def _stub_extraction(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    monkeypatch.setattr("resume_roast.services.evaluate.service.get_parser", _fake_get_parser)


def _suggestion() -> dict[str, Any]:
    return {
        "recommendation": "Quantify your impact",
        "examples": [
            {"quote": "Used Python", "rewrite": "Built a Python ETL pipeline"},
        ],
    }


def _category() -> dict[str, Any]:
    return {"score": 5, "findings": "Needs work.", "suggestions": [_suggestion()]}


def _valid_payload() -> dict[str, Any]:
    return {
        "overall": "A promising draft undermined by vague bullets.",
        "overall_score": 6,
        "categories": {name: _category() for name in CATEGORY_NAMES},
        "strengths": ["Concise single page"],
        "weaknesses": ["No metrics anywhere"],
    }


def _completion(text: str, usage: Usage | None = _USAGE) -> Completion:
    return Completion(text=text, usage=usage, finish_reason="stop")


class _ScriptedClient:
    """Satisfies LlmClient; serves a scripted sequence of completions or exceptions."""

    model: str = ""

    def __init__(self, script: Sequence[Completion | Exception]) -> None:
        self._script = list(script)
        self.calls: list[list[Message]] = []

    def prompt(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.0,  # noqa: ARG002 — protocol signature
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


def test_returns_a_complete_evaluate_result() -> None:
    client = _ScriptedClient([_completion(json.dumps(_valid_payload()))])

    result = run(client, _PATH, "recruiter", "mid")

    assert isinstance(result, EvaluateResult)
    assert result.report.overall_score == 6
    assert result.report.strengths == ("Concise single page",)
    assert result.usage == _USAGE
    assert result.latency_seconds >= 0.0


def test_sends_system_then_user_messages() -> None:
    client = _ScriptedClient([_completion(json.dumps(_valid_payload()))])

    run(client, _PATH, "recruiter", "mid")

    assert len(client.calls) == 1
    messages = client.calls[0]
    assert messages[0].role == "system"
    assert messages[1].role == "user"


def test_propagates_truncation_after_retry_exhaustion() -> None:
    client = _ScriptedClient(
        [TruncatedResponseError("hit the limit"), TruncatedResponseError("again")]
    )

    with pytest.raises(TruncatedResponseError, match="again"):
        run(client, _PATH, "recruiter", "mid")


def test_propagates_malformed_after_retry_exhaustion() -> None:
    client = _ScriptedClient([_completion("not json"), _completion("also not json")])

    with pytest.raises(MalformedResponseError):
        run(client, _PATH, "recruiter", "mid")


def test_propagates_transport_errors_untouched() -> None:
    client = _ScriptedClient([TransientError("API is down")])

    with pytest.raises(TransientError):
        run(client, _PATH, "recruiter", "mid")


def test_retries_a_malformed_response_with_feedback() -> None:
    """Confirms the structured_completion wiring: a first malformed answer feeds a second prompt."""
    client = _ScriptedClient([_completion("not json"), _completion(json.dumps(_valid_payload()))])

    result = run(client, _PATH, "recruiter", "mid")

    assert result.report.overall_score == 6
    assert len(client.calls) == 2
    retry_conversation = client.calls[1]
    assert retry_conversation[0] == client.calls[0][0]
    assert retry_conversation[1] == client.calls[0][1]
    assert retry_conversation[2].role == "assistant"
    assert retry_conversation[2].content == "not json"
    assert retry_conversation[3].role == "user"
    assert "not valid JSON" in retry_conversation[3].content
