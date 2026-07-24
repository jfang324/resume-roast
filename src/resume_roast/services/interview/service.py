"""Interview's session entry point.

Mirrors the other feature services: the CLI handler wires credentials and
display, `run()` owns the orchestration — the plan phase, the per-question
ReAct cycles, and the closing verdict.
"""

import json
import logging
import time
from pathlib import Path

from resume_roast.integrations.errors import MalformedResponseError, TruncatedResponseError
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.structured import structured_completion
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
from resume_roast.services.interview.types import (
    InterviewResult,
    InterviewSession,
    InterviewState,
)
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
) -> InterviewResult | None:
    """Interview the candidate over the resume at *path*, ending in a verdict.

    Returns the verdict-phase result, or None when the session ended before
    any answer was evaluated — by /exit, EOF, or interrupt alike — or when
    the verdict phase itself was interrupted.

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

    except (EOFError, KeyboardInterrupt):
        renderer.show_interrupt()

    # /exit, EOF, and interrupt land here alike: a verdict needs at least one
    # evaluated answer, whatever way the questions ended.
    if session.state.questions_answered == 0:
        renderer.show_abort()

        return None

    try:
        return _verdict_phase(session, started_at or time.perf_counter())
    except (EOFError, KeyboardInterrupt):
        renderer.show_interrupt()

        return None


def _plan_phase(session: InterviewSession) -> None:
    """Generate base questions from the LLM. The caller's spinner covers this.

    A malformed plan is retried once with feedback before the fallback
    questions take over; transport and auth failures propagate, ending the
    session, since retrying won't help.
    """
    logger.debug("Starting planning phase")
    session.messages.append(Message(role="user", content=build_plan_prompt()))

    fallback = False
    try:
        questions, usage = structured_completion(
            session.client, session.messages, parse_plan, temperature=PLANNING_TEMPERATURE
        )
        if usage is not None:
            session.usages.append(usage)

        # structured_completion hides the raw reply, so record the accepted plan
        # as the canonical JSON the model was asked to emit — the rest of the
        # interview reads the transcript, not the questions list. Only on the
        # success path: synthesizing one on fallback would show the model a
        # valid plan it never sent, right before being told its plan failed.
        session.messages.append(
            Message(role="assistant", content=json.dumps({"questions": questions}))
        )
    except (MalformedResponseError, TruncatedResponseError):
        logger.exception("Failed to parse plan, using fallback questions")
        questions = _FALLBACK_QUESTIONS
        fallback = True

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


def _verdict_phase(session: InterviewSession, started_at: float) -> InterviewResult:
    """Get the final verdict from the LLM and render the report."""
    q_answered = max(1, session.state.questions_answered)
    max_per = MAX_SCORE_PER_QUESTION
    normalized = {cid: round(score / q_answered, 1) for cid, score in session.state.scores.items()}
    prompt = build_verdict_prompt(normalized, max_per, render_competency_text())

    verdict_messages = [*session.messages, Message(role="user", content=prompt)]
    with session.renderer.busy("computing verdict..."):
        try:
            verdict, usage = structured_completion(
                session.client, verdict_messages, parse_verdict, temperature=TURN_TEMPERATURE
            )
            if usage is not None:
                session.usages.append(usage)
        except (MalformedResponseError, TruncatedResponseError):
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

    return InterviewResult(
        verdict=verdict,
        scores=normalized,
        max_score=max_per,
        records=tuple(session.state.records),
        questions_answered=session.state.questions_answered,
        total_questions=session.state.total_questions,
    )
