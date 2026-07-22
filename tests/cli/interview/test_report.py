"""Tests for the interview Markdown report builder."""

from resume_roast.cli.interview.report import build_report_markdown
from resume_roast.prompts.interview.competencies import COMPETENCIES
from resume_roast.prompts.interview.output.schema import Verdict
from resume_roast.prompts.interview.tools.evaluate.schema import EvaluateOutput
from resume_roast.services.interview.types import Exchange, InterviewResult, QuestionRecord

_MODEL = "nvidia/nemotron-3-super-120b-a12b"


def _evaluation(critical_failure: bool = False) -> EvaluateOutput:
    return EvaluateOutput(
        scores={c.id: 7 for c in COMPETENCIES},
        rationales={c.id: f"{c.id} evidence" for c in COMPETENCIES},
        critical_failure=critical_failure,
        strengths=["Concrete metrics"],
        gaps=["No trade-offs"],
    )


def _record(critical_failure: bool = False) -> QuestionRecord:
    return QuestionRecord(
        index=0,
        question="Tell me about ownership.",
        exchanges=(
            Exchange(question="Tell me about ownership.", answer="I owned the migration."),
            Exchange(question="What exactly did you own?", answer="Specifically the rollout."),
        ),
        verify_results='Verify results:\n  - "claim" probability=90.0% (evidence found)',
        evaluation=_evaluation(critical_failure),
        thoughts=("The claim needs checking.", "Solid answer, evaluate now."),
    )


def _result(records: tuple[QuestionRecord, ...]) -> InterviewResult:
    return InterviewResult(
        verdict=Verdict(
            verdict="dont_hire",
            overall_rating=3.5,
            summary="Not convincing overall.",
            strengths=("Communicates clearly",),
            growth_areas=("Needs deeper technical grounding",),
        ),
        scores={c.id: 6.5 for c in COMPETENCIES},
        max_score=10,
        records=records,
        questions_answered=len(records),
        total_questions=4,
    )


def test_header_carries_model_verdict_and_progress() -> None:
    text = build_report_markdown(_result((_record(),)), _MODEL)

    assert "# Interview Report" in text
    assert f"- Model: `{_MODEL}`" in text
    assert "**Don't hire** — rated 3.5/10" in text
    assert "Evaluated 1 of 4 questions" in text


def test_verdict_section_lists_strengths_and_growth_areas() -> None:
    text = build_report_markdown(_result(()), _MODEL)

    assert "Not convincing overall." in text
    assert "- Communicates clearly" in text
    assert "- Needs deeper technical grounding" in text


def test_scores_table_uses_competency_labels() -> None:
    text = build_report_markdown(_result(()), _MODEL)

    for c in COMPETENCIES:
        assert f"| {c.label} | 6.5/10 |" in text


def test_question_section_surfaces_answers_fact_check_and_rationales() -> None:
    text = build_report_markdown(_result((_record(),)), _MODEL)

    assert "## Q1: Tell me about ownership." in text
    assert "1. I owned the migration." in text
    assert "2. *What exactly did you own?* — Specifically the rollout." in text
    assert "probability=90.0%" in text
    for c in COMPETENCIES:
        assert f"- **{c.label}** — 7/10: {c.id} evidence" in text

    assert "**Strengths:** Concrete metrics" in text
    assert "**Gaps:** No trade-offs" in text
    assert "Critical failure" not in text


def test_thoughts_render_as_a_bulleted_section() -> None:
    text = build_report_markdown(_result((_record(),)), _MODEL)

    assert "**Interviewer thoughts:**" in text
    assert "- The claim needs checking." in text
    assert "- Solid answer, evaluate now." in text


def test_critical_failure_line_appears_only_when_set() -> None:
    text = build_report_markdown(_result((_record(critical_failure=True),)), _MODEL)

    assert "**Critical failure:** yes" in text


def test_empty_fact_check_and_feedback_are_omitted() -> None:
    record = QuestionRecord(
        index=1,
        question="A second question.",
        exchanges=(Exchange(question="A second question.", answer="Short answer."),),
        verify_results="",
        evaluation=EvaluateOutput(
            scores={c.id: 5 for c in COMPETENCIES},
            rationales={},
        ),
    )

    text = build_report_markdown(_result((record,)), _MODEL)

    assert "## Q2: A second question." in text
    assert "Fact check" not in text
    assert "Interviewer thoughts" not in text
    assert "**Strengths:** " not in text
    assert "**Gaps:** " not in text
    # No rationale parsed: the score line stands alone.
    assert f"- **{COMPETENCIES[0].label}** — 5/10\n" in text
