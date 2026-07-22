"""Tests for `resume-roast interview`."""

# The fixture drives PyMuPDF's partially annotated document-building API.
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportGeneralTypeIssues=false

import json
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import pymupdf
import pytest
from typer.testing import CliRunner

from resume_roast.cli.registry import build_subcommand_registry
from resume_roast.integrations.types import Completion, Message, Usage
from resume_roast.persistence.credentials.store import CredentialsStore
from resume_roast.persistence.credentials.types import Credentials
from resume_roast.prompts.interview.competencies import COMPETENCIES

app = build_subcommand_registry()
runner = CliRunner()

_MODEL = "nvidia/nemotron-3-super-120b-a12b"


def _plan_json() -> str:
    return json.dumps(
        {
            "questions": [
                "Q one?",
                "Q two?",
                "Q three?",
                "Q four?",
            ]
        }
    )


def _scores_json(critical_failure: bool = False) -> str:
    return json.dumps(
        {
            "strengths": [],
            "gaps": [],
            "assessment": {c.id: {"rationale": "solid", "score": 7} for c in COMPETENCIES},
            "critical_failure": critical_failure,
        }
    )


def _verdict_json() -> str:
    return json.dumps(
        {
            "verdict": "maybe",
            "overall_rating": 5.0,
            "summary": "Some summary.",
            "strengths": [],
            "growth_areas": [],
        }
    )


def _verify_json() -> str:
    return json.dumps(
        {
            "claims": [
                {
                    "text": "claim 1",
                    "probability": 0.9,
                    "evidence": "Match from resume",
                    "contradiction": False,
                }
            ]
        }
    )


class _FakeClient:
    """Stands in for NvidiaClient; answers prompt() from a queue of texts."""

    texts: ClassVar[list[str]] = []
    usage: ClassVar[Usage | None] = None
    error: ClassVar[Exception | None] = None
    last: ClassVar["_FakeClient | None"] = None

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.calls: list[list[Message]] = []
        type(self).last = self

    def prompt(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.0,  # noqa: ARG002
    ) -> Completion:
        self.calls.append(list(messages))
        error = type(self).error
        if error is not None:
            raise error
        queue = type(self).texts
        if not queue:
            raise AssertionError("Unexpected extra LLM call")
        text = queue.pop(0)
        return Completion(text=text, usage=type(self).usage, finish_reason="stop")


@pytest.fixture(autouse=True)
def _isolated_storage_dir(  # pyright: ignore[reportUnusedFunction]
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.setattr("resume_roast.cli.utils.storage_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def _fake_client(  # pyright: ignore[reportUnusedFunction]
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("resume_roast.cli.utils.NvidiaClient", _FakeClient)
    monkeypatch.setattr(_FakeClient, "texts", [])
    monkeypatch.setattr(
        _FakeClient,
        "usage",
        Usage(prompt_tokens=2_000, completion_tokens=1_214, total_tokens=3_214),
    )
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
        page.insert_text((72, 120), "Engineer at Acme Corp", fontsize=11)
        doc.save(path)
    return path


@pytest.mark.usefixtures("saved_key")
def test_interview_advances_after_evaluate(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Q1 evaluate -> advance to Q2 (Blocker 1 regression guard)."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="answer one\n/exit\n")
    assert result.exit_code == 0
    assert "Q2:" in result.output


@pytest.mark.usefixtures("saved_key")
def test_interview_verify_then_evaluate(sample_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """verify -> evaluate path advances to Q2."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "verify", "claims": ["claim 1"]}),
            _verify_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="some answer\n/exit\n")
    assert result.exit_code == 0
    assert "Q2:" in result.output


@pytest.mark.usefixtures("saved_key")
def test_ask_followup_presents_the_interviewers_question(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The model's own follow-up question reaches the candidate, then the cycle evaluates."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "ask_followup", "question": "What was your specific role?"}),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )

    result = runner.invoke(
        app, ["interview", str(sample_pdf)], input="vague answer\nfollow-up answer\n/exit\n"
    )

    assert result.exit_code == 0
    assert "What was your specific role?" in result.output


@pytest.mark.usefixtures("saved_key")
def test_unknown_action_gets_named_feedback_not_forced_evaluation(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stray 'ask' mid-cycle is answered with guidance; the cycle continues."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "ask"}),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )

    result = runner.invoke(app, ["interview", str(sample_pdf)], input="answer one\n/exit\n")

    assert result.exit_code == 0
    assert "Q2:" in result.output
    client = _FakeClient.last
    assert client is not None
    feedback = [
        m.content for call in client.calls for m in call if "Unknown tool 'ask'" in m.content
    ]
    assert feedback  # the runtime corrected the model instead of force-evaluating


@pytest.mark.usefixtures("saved_key")
def test_interview_early_exit_on_two_critical_failures(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two critical_failure evaluations end the interview early."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(critical_failure=True),
            json.dumps({"tool": "evaluate"}),
            _scores_json(critical_failure=True),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="bad answer\nworse answer\n")
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output
    assert "Q3:" not in result.output


@pytest.mark.usefixtures("saved_key")
def test_interview_exhaustion_reaches_verdict(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """All base questions answered -> verdict phase reached."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(
        app,
        ["interview", str(sample_pdf)],
        input="\n".join(["a1", "a2", "a3", "a4"]) + "\n",
    )
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output
    assert "Overall Rating:" in result.output
    assert "Verdict:" in result.output


@pytest.mark.usefixtures("saved_key")
def test_interview_conclude_ends_and_scores(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """conclude action evaluates current question then ends."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "conclude"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="only answer\n")
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output
    assert "7.0 /10" in result.output


@pytest.mark.usefixtures("saved_key")
def test_interview_turn_cap_prevents_hang(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prose that never produces a valid action hits the turn cap instead of hanging."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            *([json.dumps({"tool": "proceed"})] * 14),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(
        app,
        ["interview", str(sample_pdf)],
        input="some answer\n/exit\n",
    )
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output


@pytest.mark.usefixtures("saved_key")
def test_progress_block_never_accumulates(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each LLM payload contains at most one progress block."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(
        app,
        ["interview", str(sample_pdf)],
        input="\n".join(["a1", "a2", "a3", "a4"]) + "\n",
    )
    assert result.exit_code == 0

    client = _FakeClient.last
    assert client is not None
    for messages in client.calls:
        blocks = [m for m in messages if "Interview progress:" in m.content]
        assert len(blocks) <= 1, f"Found {len(blocks)} progress blocks in one payload"


@pytest.mark.usefixtures("saved_key")
def test_corrections_replay_during_retry_then_leave_no_trace(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A refused call and its correction ride the retry, then vanish from the history.

    Two rejections back to back: malformed JSON, then an unknown tool. The
    retry payloads must carry both the refused text and the steering, or the
    model has no signal to answer differently. Every later payload must be
    clean of them.
    """
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            "not valid json",
            json.dumps({"tool": "dance"}),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )

    result = runner.invoke(app, ["interview", str(sample_pdf)], input="my answer\n/exit\n")

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None

    def carries(messages: list[Message], needle: str) -> bool:
        return any(needle in m.content for m in messages)

    replayed = [c for c in client.calls if carries(c, "Invalid response format")]
    assert replayed, "the correction never reached the model"
    assert carries(replayed[0], "not valid json"), "retry dropped the text being corrected"

    unknown = [c for c in client.calls if carries(c, "Unknown tool 'dance'")]
    assert unknown, "the unknown-tool correction never reached the model"

    settled = client.calls[-1]
    for residue in ("not valid json", "Invalid response format", '"dance"', "Unknown tool"):
        assert not carries(settled, residue), f"{residue!r} persisted into the transcript"


@pytest.mark.usefixtures("saved_key")
def test_repeated_refusals_accumulate_in_the_replay(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A model repeating a refused call sees every prior attempt, not just the last.

    `{"tool": "dance"}` parses cleanly and is still refused, so retiring the
    replay on a successful parse would hide the repetition from the model.
    """
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "dance"}),
            json.dumps({"tool": "dance"}),
            json.dumps({"tool": "dance"}),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )

    result = runner.invoke(app, ["interview", str(sample_pdf)], input="my answer\n/exit\n")

    assert result.exit_code == 0
    client = _FakeClient.last
    assert client is not None

    corrections = [sum("Unknown tool 'dance'" in m.content for m in call) for call in client.calls]
    assert max(corrections) >= 2, "the third attempt did not see the earlier refusals"
    assert corrections[-1] == 0, "refusals persisted into the verdict payload"


@pytest.mark.usefixtures("saved_key")
def test_immediate_exit(sample_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """/exit on the first question aborts before any LLM turn."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [_plan_json(), _verdict_json()],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="/exit\n")
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output

    client = _FakeClient.last
    assert client is not None
    # Planning costs exactly one call, and the verdict one more — the plan is
    # never acknowledged by a round-trip whose reply nobody reads.
    assert len(client.calls) == 2


@pytest.mark.usefixtures("saved_key")
def test_verify_runs_once_then_further_requests_are_rebuffed(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The cap counts executions: one verify runs, the next request is refused.

    The queue holds a single verify result — a second execution would drain it
    and trip the fake's unexpected-call assertion.
    """
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "verify", "claims": ["c1"]}),
            _verify_json(),
            json.dumps({"tool": "verify", "claims": ["c2"]}),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="my answer\n")
    assert result.exit_code == 0
    assert result.output.count("claims checked") == 1
    assert "INTERVIEW REPORT" in result.output


@pytest.mark.usefixtures("saved_key")
def test_max_cycle_turns_forced_evaluate(sample_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """12 unknown actions spend the turn budget and force evaluate.

    The queue holds exactly the budget: a 13th interviewer call would drain it
    and trip the fake's unexpected-call assertion, which is what pins the
    guard to running before the call rather than after.
    """
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            *([json.dumps({"tool": "dance"})] * 12),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="my answer\n")
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output


@pytest.mark.usefixtures("saved_key")
def test_parse_failure_retry_then_evaluate(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid JSON response triggers retry, then valid action succeeds."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            "not valid json",
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="my answer\n")
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output


@pytest.mark.usefixtures("saved_key")
def test_unknown_action_retry(sample_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown tool name triggers retry with feedback."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "unknown_action_name"}),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="my answer\n")
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output


@pytest.mark.usefixtures("saved_key")
def test_long_answer(sample_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A very long answer (10k+ chars) is accepted without error."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    long_answer = "word " * 2_500
    result = runner.invoke(app, ["interview", str(sample_pdf)], input=f"{long_answer}\n")
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output


@pytest.mark.usefixtures("saved_key")
def test_empty_answer(sample_pdf: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty answer (blank line) is accepted."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(app, ["interview", str(sample_pdf)], input="\n")
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output


@pytest.mark.usefixtures("saved_key")
def test_multiple_questions_score_accumulation(
    sample_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scores from multiple questions accumulate."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "verify", "claims": ["c1"]}),
            _verify_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            json.dumps({"tool": "evaluate"}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    result = runner.invoke(
        app,
        ["interview", str(sample_pdf)],
        input="\n".join(["a1", "a2"]) + "\n",
    )
    assert result.exit_code == 0
    assert "INTERVIEW REPORT" in result.output
    assert "14" in result.output or "7.0" in result.output


@pytest.mark.usefixtures("saved_key")
def test_report_flag_writes_the_markdown_report(
    sample_pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--report writes a file carrying the verdict and per-question evidence."""
    monkeypatch.setattr(
        _FakeClient,
        "texts",
        [
            _plan_json(),
            json.dumps({"tool": "verify", "claims": ["claim 1"]}),
            _verify_json(),
            json.dumps({"tool": "ask_followup", "question": "What was your role?"}),
            json.dumps({"tool": "evaluate", "thought": "Answer cycle complete, scoring."}),
            _scores_json(),
            _verdict_json(),
        ],
    )
    report_path = tmp_path / "report.md"

    result = runner.invoke(
        app,
        ["interview", str(sample_pdf), "--report", str(report_path)],
        input="some answer\nfollow-up answer\n/exit\n",
    )

    assert result.exit_code == 0
    text = report_path.read_text(encoding="utf-8")
    assert "# Interview Report" in text
    assert "Evaluated 1 of 4 questions" in text
    assert "## Q1: Q one?" in text
    assert "1. some answer" in text
    assert "2. *What was your role?* — follow-up answer" in text
    assert "- Answer cycle complete, scoring." in text
    assert "claim 1" in text
    assert ": solid" in text
    assert "Some summary." in text


@pytest.mark.usefixtures("saved_key")
def test_report_flag_aborted_interview_writes_nothing(
    sample_pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An abort before any evaluated answer produces no report file."""
    monkeypatch.setattr(_FakeClient, "texts", [_plan_json()])
    report_path = tmp_path / "report.md"

    result = runner.invoke(
        app,
        ["interview", str(sample_pdf), "--report", str(report_path)],
        input="",
    )

    assert result.exit_code == 0
    assert not report_path.exists()
    assert "report not written" in result.output
