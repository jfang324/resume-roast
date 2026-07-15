"""Service layer for the evaluate tool."""

import logging

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.tools.evaluate.parser import parse_input, parse_output
from resume_roast.tools.evaluate.schema import EvaluateInput, EvaluateOutput

logger = logging.getLogger(__name__)

_SYSTEM = """\
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


def execute(
    client: LlmClient,
    original_question: str,
    answer_history: list[str],
    verify_results: str,
    competency_descriptions: str,
    competency_ids: list[str],
) -> tuple[EvaluateOutput, Usage | None]:
    run_input = EvaluateInput(
        original_question=original_question,
        answer_history=answer_history,
        verify_results=verify_results,
        competency_descriptions=competency_descriptions,
        competency_ids=competency_ids,
    )
    parsed_input = parse_input(run_input)

    user = f"""\
Original question: {parsed_input.original_question}

Answer history:
{_numbered(parsed_input.answer_history)}

Verify results:
{parsed_input.verify_results}

Competency framework:
{parsed_input.competency_descriptions}"""

    messages = [
        Message(role="system", content=_SYSTEM),
        Message(role="user", content=user),
    ]
    logger.debug("evaluate request messages: %s", messages)

    completion = client.prompt(messages, temperature=0.0)
    output = parse_output(completion.text, parsed_input.competency_ids)
    logger.debug("evaluate result: %s", output)
    return output, completion.usage


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
