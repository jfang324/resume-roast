"""Builds the Markdown document the --report flag writes after an interview."""

import re
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from resume_roast.prompts.interview.competencies import COMPETENCIES
from resume_roast.services.interview.types import InterviewResult, QuestionRecord

REPORTS_DIRNAME = "interview-reports"
"""Subdirectory of the storage dir where --report drops its files."""

_VERDICT_LABELS = {"hire": "Hire", "maybe": "Maybe", "dont_hire": "Don't hire"}


def report_filename(resume_path: Path, when: datetime) -> str:
    """Name a report file from the timestamp and source resume.

    Timestamp-first (e.g. ``20260723-142530-resume.md``) so a directory of
    reports sorts chronologically; the resume stem tells overlapping runs
    apart. Falls back to ``resume`` when the path carries no usable stem.
    """
    stem = resume_path.stem or "resume"

    return f"{when:%Y%m%d-%H%M%S}-{stem}.md"


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
    lines.extend(_bulleted("Strengths", verdict.strengths))
    lines.extend(_bulleted("Growth areas", verdict.growth_areas))

    return "\n".join(lines)


def _bulleted(title: str, items: Sequence[str]) -> list[str]:
    """Render a titled bullet list as report lines; nothing when there are no items."""
    if not items:
        return []

    return ["", f"**{title}:**", *(f"- {item}" for item in items)]


def _scores_section(result: InterviewResult) -> str:
    lines = [
        "## Competency Scores",
        "",
        "| Competency | Score |",
        "| --- | --- |",
    ]
    for c in COMPETENCIES:
        score = result.scores.get(c.id)
        # A missing competency is an upstream bug; "n/a" surfaces it where a
        # defaulted 0 would pass for a genuine bottom score.
        cell = f"{score}/{result.max_score}" if score is not None else "n/a"
        lines.append(f"| {c.label} | {cell} |")

    return "\n".join(lines)


def _fence_for(text: str) -> str:
    """Pick a code fence longer than any backtick run inside *text*.

    Verify results quote claim text drawn from candidate answers, which can
    itself contain ``` and would otherwise terminate the block early."""
    runs = re.findall(r"`+", text)
    longest = max((len(run) for run in runs), default=0)

    return "`" * max(3, longest + 1)


def _question_section(record: QuestionRecord) -> str:
    evaluation = record.evaluation
    lines = [f"## Q{record.index + 1}: {record.question}", "", "**Answers:**"]
    for i, exchange in enumerate(record.exchanges):
        # The heading already shows the base question; only a differing
        # (follow-up) question earns an inline repeat.
        if exchange.question == record.question:
            lines.append(f"{i + 1}. {exchange.answer}")
        else:
            lines.append(f"{i + 1}. *{exchange.question}* — {exchange.answer}")

    if record.verify_results:
        fence = _fence_for(record.verify_results)
        lines.append("")
        lines.append("**Fact check:**")
        lines.append("")
        lines.append(fence)
        lines.append(record.verify_results)
        lines.append(fence)

    lines.extend(_bulleted("Interviewer thoughts", record.thoughts))

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
