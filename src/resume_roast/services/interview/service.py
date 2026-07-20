"""Interview's session entry point.

Mirrors the other feature services: the CLI handler wires credentials and
display, `run()` owns the orchestration — the plan phase, the per-question
ReAct cycles, and the closing verdict.
"""

import logging
import time
from pathlib import Path

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message
from resume_roast.integrations.usage import total_usage
from resume_roast.prompts.interview.builder import (
    build_interview_system_prompt,
    build_plan_prompt,
    build_verdict_prompt,
    render_competency_text,
)
from resume_roast.prompts.interview.competencies import COMPETENCIES
from resume_roast.prompts.interview.output.parser import parse_plan, parse_verdict
from resume_roast.prompts.interview.output.schema import Verdict
from resume_roast.services.chat.input_provider import InputProvider
from resume_roast.services.interview.constants import (
    MAX_SCORE_PER_QUESTION,
    PLANNING_TEMPERATURE,
    TURN_TEMPERATURE,
)
from resume_roast.services.interview.cycle import run_question_cycle
from resume_roast.services.interview.renderer import InterviewRenderer
from resume_roast.services.interview.types import InterviewSession, InterviewState
from resume_roast.utils.extraction.mappings import get_parser

logger = logging.getLogger(__name__)

_FALLBACK_QUESTIONS = [
    "Tell me about a time you took ownership of a problem that wasn't assigned to you.",
    "Describe a technical challenge you solved and how you approached it.",
    "Give an example of a time you collaborated with people who had different perspectives.",
    "Tell me about a time you had to evaluate trade-offs between different approaches to solve a problem.",
]
"""Asked verbatim when the model's question plan cannot be parsed."""


def run(
    client: LlmClient,
    path: Path,
    renderer: InterviewRenderer,
    input_provider: InputProvider,
) -> None:
    """Interview the candidate over the resume at *path*, ending in a verdict.

    Raises:
        ExtractionError: when the document cannot be parsed.
        ApiError: non-transient transport failures, which end the session.
    """
    parsed = get_parser(path).parse(path)
    logger.debug("Parsed resume: %d chars", len(parsed.markdown))

    session = InterviewSession(
        client=client,
        renderer=renderer,
        input_provider=input_provider,
        messages=[Message(role="system", content=build_interview_system_prompt(parsed))],
        usages=[],
        state=InterviewState(
            resume_markdown=parsed.markdown,
            base_questions=[],
            competencies=[c.id for c in COMPETENCIES],
            scores={c.id: 0 for c in COMPETENCIES},
        ),
    )
    started_at = 0.0

    try:
        with renderer.busy("preparing interview questions..."):
            _plan_phase(session)

        renderer.show_start(session.state.total_questions)

        started_at = time.perf_counter()
        _question_loop(session)
        _verdict_phase(session, started_at)

    except (EOFError, KeyboardInterrupt):
        renderer.show_interrupt()
        if session.state.questions_answered > 0:
            _verdict_phase(session, started_at or time.perf_counter())
        else:
            renderer.show_abort()


def _plan_phase(session: InterviewSession) -> None:
    """Generate base questions from the LLM. The caller's spinner covers this."""
    logger.debug("Starting planning phase")
    session.messages.append(Message(role="user", content=build_plan_prompt()))
    completion = session.client.prompt(session.messages, temperature=PLANNING_TEMPERATURE)
    if completion.usage is not None:
        session.usages.append(completion.usage)

    session.messages.append(Message(role="assistant", content=completion.text))

    fallback = None
    try:
        questions = parse_plan(completion.text)
    except Exception:
        logger.exception("Failed to parse plan, using fallback questions")
        fallback = questions = _FALLBACK_QUESTIONS

    session.state.base_questions = questions
    session.state.total_questions = len(questions)
    logger.debug("Planned %d questions: %s", len(questions), questions)

    if fallback:
        begin_msg = (
            "Plan parsing failed. Using these fallback questions:\n"
            + "\n".join(f"- {q}" for q in questions)
            + "\n\nPlan received. Begin the interview."
        )
    else:
        begin_msg = "Plan received. Begin the interview."

    session.messages.append(Message(role="user", content=begin_msg))
    logger.debug("Post-plan: %d questions planned", len(questions))


def _question_loop(session: InterviewSession) -> None:
    """Ask each base question and process answers."""
    progress = ""
    for idx in range(session.state.total_questions):
        logger.debug("Starting question %d/%d", idx + 1, session.state.total_questions)
        should_continue, progress = run_question_cycle(session, idx, progress)
        if not should_continue:
            break


def _verdict_phase(session: InterviewSession, started_at: float) -> None:
    """Get the final verdict from the LLM and render the report."""
    q_answered = max(1, session.state.questions_answered)
    max_per = MAX_SCORE_PER_QUESTION
    normalized = {cid: round(score / q_answered, 1) for cid, score in session.state.scores.items()}
    prompt = build_verdict_prompt(normalized, max_per, render_competency_text())

    with session.renderer.busy("computing verdict..."):
        completion = session.client.prompt(
            [*session.messages, Message(role="user", content=prompt)],
            temperature=TURN_TEMPERATURE,
        )
        if completion.usage is not None:
            session.usages.append(completion.usage)

        try:
            verdict = parse_verdict(completion.text)
        except Exception:
            logger.exception("Failed to parse verdict, using fallback")
            verdict = Verdict(
                verdict="maybe",
                overall_rating=5.0,
                summary="Unable to generate a verdict due to a parsing error. Review the per-category scores above for a manual assessment.",
                strengths=(),
                growth_areas=(),
            )

    session.renderer.show_report(verdict, normalized, max_per)
    total = total_usage(session.usages)
    if total is not None:
        elapsed = time.perf_counter() - (started_at or time.perf_counter())
        session.renderer.show_metrics(total, elapsed)
