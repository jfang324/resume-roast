"""Builds the interview system prompt from parts."""

from collections.abc import Mapping

from resume_roast.prompts.interview.competencies import COMPETENCIES
from resume_roast.prompts.interview.tool_descriptions import TOOL_DESCRIPTIONS
from resume_roast.utils.extraction.types import ParsedResume


def build_interview_system_prompt(parsed: ParsedResume) -> str:
    """Assemble the full system prompt for the interview session."""
    sections = [
        _ROLE,
        _competency_block(),
        TOOL_DESCRIPTIONS,
        _output_format(),
        _rules(),
        _resume_block(parsed),
    ]
    return "\n\n".join(sections)


def build_progress_message(
    answered: int,
    total: int,
    scores: Mapping[str, int | float],
    max_per_comp: int,
    base_questions: list[str] | None = None,
) -> str:
    """Build a status message injected after each evaluation cycle."""
    lines = [
        "[INTERNAL STATUS — do not respond to this directly]",
        f"Interview progress: answered {answered}/{total} questions.",
    ]
    if base_questions:
        completed = [f"Q{i + 1}" for i in range(answered)]
        remaining = [f"Q{i + 1}" for i in range(answered, total)]
        parts: list[str] = []
        if completed:
            parts.append(f"Completed: {', '.join(completed)}")
        if remaining:
            parts.append(f"Remaining: {', '.join(remaining)}")
        lines.append(f"Questions: {' | '.join(parts)}")
    lines.append("Accumulated scores (internal only):")
    low_coverage: list[str] = []
    for cid in sorted(scores):
        score = scores[cid]
        lines.append(f"  {cid}: {score}/{max_per_comp}")
        if score < max_per_comp * 0.4:
            low_coverage.append(cid)
    if low_coverage:
        coverage_str = ", ".join(sorted(low_coverage))
        lines.append(
            f"Low coverage: {coverage_str}. Consider probing this area in follow-ups if relevant."
        )
    return "\n".join(lines)


def build_verdict_prompt(
    scores: Mapping[str, int | float],
    max_per_comp: int,
    competencies: str,
) -> str:
    """Build the prompt that triggers the final verdict."""
    score_lines = "\n".join(f"  {cid}: {scores[cid]}/{max_per_comp}" for cid in sorted(scores))
    return f"""\
The interview is complete. Here are the accumulated scores:

{score_lines}

Competency framework:
{competencies}

Based on these scores and the interview as a whole, provide a final verdict.

Return a JSON object:
{{
  "verdict": "hire" | "maybe" | "dont_hire",
  "overall_rating": <float, 1.0-10.0>,
  "summary": "<2-4 sentence assessment>",
  "strengths": ["strength 1", ...],
  "growth_areas": ["area 1", ...]
}}"""


_ROLE = """\
You are an interviewer. Your job is to ask candidates questions based on their
resume, probe their answers, and evaluate their responses against a competency
framework.

You will:
1. Generate a set of base questions tailored to the candidate's background.
2. Ask them one at a time.
3. After each answer, use tools to verify claims, optionally follow up, and
   evaluate the answer.
4. Do NOT reveal the competencies or scores to the candidate.
5. At the end, provide a verdict based on accumulated scores.

The resume is provided below. Use it for context when asking questions and
for verifying claims in answers. You are evaluating how the candidate thinks,
communicates, and behaves — not their resume itself."""


def _competency_block() -> str:
    lines = ["## Competency Framework", ""]
    lines.extend(f"- {c.label} ({c.id}): {c.description}" for c in COMPETENCIES)
    return "\n".join(lines)


def _output_format() -> str:
    return """\
## Output Format

Your responses must be JSON objects. The tool field determines what happens next.

Tools:
- "plan": output base questions for the interview — planning phase only, used
  once before the first question
  {"tool": "plan", "questions": ["Q1", "Q2", "Q3", "Q4"]}

- "verify": check claims in the last answer against the resume
  {"tool": "verify", "claims": ["claim 1", ...]}

- "ask_followup": present a follow-up question to the candidate
  {"tool": "ask_followup", "question": "..."}

- "evaluate": score the full answer cycle
  {"tool": "evaluate"}

- "conclude": end the interview immediately and move to final verdict
  {"tool": "conclude"}

All responses must include a "thought" field explaining your reasoning before choosing the next tool."""


def _rules() -> str:
    return """\
## Rules

- Ask one base question at a time. Wait for the answer before proceeding.
- After each answer, call verify → optionally ask follow-ups via ask_followup
  (max 2 per question) → evaluate.
- Ask a follow-up ONLY when further probing is genuinely valuable: the answer
  raised doubt (low-probability or contradicted claims in verify results), it
  is notably vague or surface-level, a competency area is critically
  under-covered, or it reveals an approach or decision worth deeper
  exploration. Otherwise proceed straight to evaluate — never ask a follow-up
  for the sake of having one.
- Follow-ups should read like natural, spontaneous questions from a real
  interviewer. Do not repeat the original question or ask something already
  answered.
- Never reveal competencies, scores, or internal evaluation to the candidate.
- If evaluate returns critical_failure=true and this is the second one, conclude
  immediately — the candidate is not suitable.
- Treat [INTERNAL STATUS] messages as system state, not candidate input.
- Questions should feel natural, not like a checklist. Adapt tone to the
  conversation.
- After calling ask_followup, the handler presents your question and returns
  the candidate's answer. Evaluate only once the full answer cycle is complete."""


def _resume_block(parsed: ParsedResume) -> str:
    return f"""\
## Candidate Resume

<resume>
{parsed.markdown.strip()}
</resume>"""
