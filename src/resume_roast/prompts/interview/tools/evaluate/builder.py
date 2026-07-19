"""Builds the evaluate tool's prompt text and its model-facing result rendering."""

from resume_roast.prompts.interview.tools.evaluate.schema import EvaluateOutput

SYSTEM = """\
You are an interview evaluator. Score the candidate's answer across the
defined competency framework.

For each competency, assign a score of 1-10:
- 1-3: Poor — the answer does not demonstrate this competency
- 4-6: Adequate — some evidence but lacks depth or clarity
- 7-8: Strong — solid demonstration with specific examples
- 9-10: Exceptional — compelling evidence with measurable impact

Consider the full answer history (including any follow-ups), not just the
initial answer.

Set critical_failure=true ONLY in extreme cases: the answer is completely
off-topic, contains clear dishonesty or factual contradictions with the
resume, or scores 1-2 across ALL competencies. A merely average or slightly
weak answer is NOT a critical_failure.

Return a JSON object with EXACTLY this structure:
{
  "scores": {
    "ownership": <int 1-10>,
    "technical_competence": <int 1-10>,
    "problem_solving": <int 1-10>,
    "collaboration": <int 1-10>
  },
  "critical_failure": <bool>,
  "strengths": ["..."],
  "gaps": ["..."]
}

You MUST provide scores for ALL competencies. Do not omit any."""

EVALUATE_DESCRIPTION = """\
## Tool: evaluate

Score the candidate's full answer cycle (including follow-ups) across all competencies. Call after verify and any follow-ups are complete.

Input JSON schema:
{
  "type": "object",
  "properties": {
    "original_question": {
      "type": "string",
      "description": "The question that was asked"
    },
    "verify_results": {
      "type": "string",
      "description": "Results from the verify tool"
    }
  },
  "required": []
}"""
"""How the interviewer's system prompt advertises this tool."""


def build_user_message(
    original_question: str,
    answer_history: list[str],
    verify_results: str,
    competency_descriptions: str,
) -> str:
    """Lay out the question, the numbered answer history, and the evidence."""
    numbered = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(answer_history))

    return f"""\
Original question: {original_question}

Answer history:
{numbered}

Verify results:
{verify_results}

Competency framework:
{competency_descriptions}"""


def render_evaluation_results(output: EvaluateOutput) -> str:
    """Render the evaluation outcome as the observation text the model reads."""
    lines = [
        "Evaluation complete.",
        f"Scores: {output.scores}",
        f"Critical failure: {output.critical_failure}",
    ]
    if output.strengths:
        lines.append(f"Strengths: {', '.join(output.strengths)}")

    if output.gaps:
        lines.append(f"Gaps: {', '.join(output.gaps)}")

    return "\n".join(lines)
