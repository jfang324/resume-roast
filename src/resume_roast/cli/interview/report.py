"""Builds the Markdown document the --report flag writes after an interview."""

from resume_roast.prompts.interview.competencies import COMPETENCIES
from resume_roast.services.interview.types import InterviewResult, QuestionRecord

_VERDICT_LABELS = {"hire": "Hire", "maybe": "Maybe", "dont_hire": "Don't hire"}


def build_report_markdown(result: InterviewResult, model: str) -> str:
    """Render the full interview outcome as a standalone Markdown document."""
    sections = [
        _header(result, model),
        _verdict_section(result),
        _scores_section(result),
    ]
    sections.extend(_question_section(record) for record in result.records)

    return "\n\n".join(sections) + "\n"


def _header(result: InterviewResult, model: str) -> str:
    verdict = result.verdict
    label = _VERDICT_LABELS.get(verdict.verdict, verdict.verdict)

    return f"""\
# Interview Report

- Model: `{model}`
- Verdict: **{label}** — rated {verdict.overall_rating:.1f}/10
- Evaluated {result.questions_answered} of {result.total_questions} questions"""


def _verdict_section(result: InterviewResult) -> str:
    verdict = result.verdict
    lines = ["## Verdict", "", verdict.summary]
    if verdict.strengths:
        lines.append("")
        lines.append("**Strengths:**")
        lines.extend(f"- {s}" for s in verdict.strengths)

    if verdict.growth_areas:
        lines.append("")
        lines.append("**Growth areas:**")
        lines.extend(f"- {g}" for g in verdict.growth_areas)

    return "\n".join(lines)


def _scores_section(result: InterviewResult) -> str:
    lines = [
        "## Competency Scores",
        "",
        "| Competency | Score |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| {c.label} | {result.scores.get(c.id, 0)}/{result.max_score} |" for c in COMPETENCIES
    )

    return "\n".join(lines)


def _question_section(record: QuestionRecord) -> str:
    evaluation = record.evaluation
    lines = [f"## Q{record.index + 1}: {record.question}", "", "**Answers:**"]
    lines.extend(f"{i + 1}. {answer}" for i, answer in enumerate(record.answer_history))

    if record.verify_results:
        lines.append("")
        lines.append("**Fact check:**")
        lines.append("")
        lines.append("```")
        lines.append(record.verify_results)
        lines.append("```")

    lines.append("")
    lines.append("**Assessment:**")
    for c in COMPETENCIES:
        score = evaluation.scores.get(c.id)
        if score is None:
            continue

        rationale = evaluation.rationales.get(c.id, "")
        suffix = f": {rationale}" if rationale else ""
        lines.append(f"- **{c.label}** — {score}/10{suffix}")

    if evaluation.strengths:
        lines.append("")
        lines.append(f"**Strengths:** {'; '.join(evaluation.strengths)}")

    if evaluation.gaps:
        lines.append("")
        lines.append(f"**Gaps:** {'; '.join(evaluation.gaps)}")

    if evaluation.critical_failure:
        lines.append("")
        lines.append("**Critical failure:** yes")

    return "\n".join(lines)
