"""`interview` command: agentic behavioral interview session."""

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from rich.console import Console

from resume_roast.cli.interview.actions import (
    AskAction,
    AskFollowupAction,
    ConcludeAction,
    EvaluateAction,
    FollowUpAction,
    InterviewAction,
    ParseFailure,
    VerifyAction,
    action_from_dict,
)
from resume_roast.cli.interview.input_provider import UserInputProvider, make_input_provider
from resume_roast.cli.utils import USER_PROMPT, build_client, spinner, summary_line
from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.integrations.usage import total_usage
from resume_roast.prompts.interview.builder import (
    build_interview_system_prompt,
    build_progress_message,
    build_verdict_prompt,
)
from resume_roast.prompts.interview.competencies import COMPETENCIES
from resume_roast.prompts.interview.output.parser import parse_plan, parse_verdict
from resume_roast.prompts.interview.output.schema import SessionData, Verdict
from resume_roast.tools.evaluate.schema import EvaluateOutput
from resume_roast.utils.extraction.mappings import get_parser

logger = logging.getLogger(__name__)

# ── Limits ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Limits:
    """Named numeric bounds the FSM checks; all in one place for discoverability."""

    max_cycle_turns: int = 12
    """Total LLM turns per question before force-evaluate.
    After 12 turns the LLM is looping; bail out."""
    max_verify_per_cycle: int = 2
    """After 2 verifies the LLM is hallucinating details;
    force a move to follow_up or evaluate."""
    max_follow_ups_per_cycle: int = 2
    """After 2 follow-ups the question is done; evaluate and move on."""


_LIMITS = Limits()

# ── Layered state model ────────────────────────────────────────────────────


@dataclass(frozen=True)
class InterviewSession:
    """Lifetime = whole interview. Once set, never mutated.

    Mutable references (messages, usages) are shared by mutation, not replaced.
    """

    client: LlmClient
    console: Console
    debug: bool
    input_provider: UserInputProvider
    messages: list[Message]
    usages: list[Usage]
    data: SessionData


@dataclass
class QuestionState:
    """Lifetime = one base question. Reset between questions."""

    index: int
    question: str
    answer_history: list[str] = field(default_factory=lambda: cast(list[str], []))
    verify_results: str = ""
    follow_up_count: int = 0
    verify_count: int = 0


@dataclass
class TurnState:
    """Lifetime = one LLM round-trip inside a question."""

    last_action: dict[str, Any] | None = None


# ── Helpers ─────────────────────────────────────────────────────────────────


def _get_competency_gaps(data: SessionData) -> str | None:
    if data.questions_answered == 0:
        return None
    max_per = data.questions_answered * 10
    gaps = [cid for cid, score in data.scores.items() if score < max_per * 0.4]
    if not gaps:
        return None
    return f"Low coverage: {', '.join(gaps)}"


def _to_competency_text() -> str:
    return "\n".join(f"- {c.id}: {c.label} — {c.description}" for c in COMPETENCIES)


def _run_evaluate(
    session: InterviewSession, qs: QuestionState
) -> tuple[EvaluateOutput | None, str]:
    """Run the evaluate tool, accumulate scores, and inject [INTERNAL STATUS].

    Returns (output_or_None, progress_string).
    """
    from resume_roast.tools import REGISTRY

    action = {
        "original_question": qs.question,
        "verify_results": qs.verify_results,
    }
    with spinner("evaluating answer..."):
        result = REGISTRY.execute(
            "evaluate",
            action,
            client=session.client,
            answer_history=qs.answer_history,
            competency_text=_to_competency_text(),
            competency_ids=[c.id for c in COMPETENCIES],
            current_question=qs.question,
            verify_results=qs.verify_results,
        )
    if not result.success:
        return None, ""

    eval_output = result.metadata["eval_output"]
    usage = result.metadata.get("usage")

    if usage is not None:
        session.usages.append(usage)

    for cid, score in eval_output.scores.items():
        session.data.scores[cid] = session.data.scores.get(cid, 0) + score
    session.data.questions_answered += 1

    if eval_output.critical_failure:
        session.data.critical_failures += 1

    max_per = session.data.questions_answered * 10
    progress = build_progress_message(
        session.data.questions_answered,
        session.data.total_questions,
        session.data.scores,
        max_per,
        session.data.base_questions,
    )
    logger.debug(
        "Evaluation: scores=%s, critical=%d",
        eval_output.scores,
        session.data.critical_failures,
    )

    session.messages.append(Message(role="user", content=result.data))
    qs.verify_results = ""
    session.console.print("[dim]✓ answer evaluated[/dim]")

    return eval_output, progress


def _evaluate_and_decide(session: InterviewSession, qs: QuestionState) -> tuple[bool, str]:
    """Evaluate the answer cycle and decide whether the interview continues.

    Returns (continue?, progress_string).
    """
    eval_output, progress = _run_evaluate(session, qs)
    if eval_output is None:
        logger.error("Evaluate failed for Q%d, advancing", qs.index + 1)
        return True, ""
    return session.data.critical_failures < 2, progress


def _llm_turn(
    session: InterviewSession,
    _qs: QuestionState,
    user_text: str,
    progress: str = "",
) -> InterviewAction:
    """Append a user message, prompt with current progress appended, and return the parsed action."""
    session.messages.append(Message(role="user", content=user_text))
    payload = session.messages
    if progress:
        payload = [*session.messages, Message(role="user", content=progress)]
    with spinner("thinking..."):
        completion = session.client.prompt(payload, temperature=0.0)
    if completion.usage is not None:
        session.usages.append(completion.usage)
    session.messages.append(Message(role="assistant", content=completion.text))
    try:
        import json

        from resume_roast.prompts.response_parser import strip_code_fence as _scf

        cleaned = _scf(completion.text.strip())
        parsed: object = json.loads(cleaned)
        if isinstance(parsed, dict):
            raw = cast("dict[str, Any]", parsed)
            thought: str | None = raw.get("thought")
            if thought and session.debug:
                session.console.print(f"[dim]thought: {thought}[/dim]")
            return action_from_dict(raw)
        return ParseFailure(raw_text=completion.text)
    except Exception as exc:
        logger.warning("Failed to parse action: %s", exc)
        return ParseFailure(raw_text=completion.text)


def _plan_phase(session: InterviewSession) -> None:
    """Generate base questions from the LLM. The caller's spinner covers this."""
    logger.debug("Starting planning phase")
    msg = (
        "Generate 4-6 interview questions tailored to this candidate's resume "
        "and background. These should probe the competency areas."
    )
    session.messages.append(Message(role="user", content=msg))
    completion = session.client.prompt(session.messages, temperature=0.7)
    if completion.usage is not None:
        session.usages.append(completion.usage)
    session.messages.append(Message(role="assistant", content=completion.text))

    fallback = None
    try:
        questions = parse_plan(completion.text)
    except Exception:
        logger.exception("Failed to parse plan, using fallback questions")
        fallback = questions = [
            "Tell me about a time you took ownership of a problem that wasn't assigned to you.",
            "Describe a technical challenge you solved and how you approached it.",
            "Give an example of a time you collaborated with people who had different perspectives.",
            "Tell me about a time you had to evaluate trade-offs between different approaches to solve a problem.",
        ]
    session.data.base_questions = questions
    session.data.total_questions = len(questions)
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
    completion = session.client.prompt(session.messages, temperature=0.0)
    if completion.usage is not None:
        session.usages.append(completion.usage)
    session.messages.append(Message(role="assistant", content=completion.text))
    logger.debug("Post-plan: %d questions planned", len(questions))


def _run_question_cycle(
    session: InterviewSession, question_index: int, carry_progress: str
) -> tuple[bool, str]:
    """Ask one base question and process the full answer cycle.

    Returns:
        (continue?, progress_string).
    """
    question = session.data.base_questions[question_index]
    qs = QuestionState(index=question_index, question=question)
    progress = carry_progress
    competency_text = _to_competency_text()

    session.console.print(f"\n[bold]Q{question_index + 1}:[/bold] {question}")
    user_input = session.input_provider.get_input(USER_PROMPT).strip()
    if user_input.lower() in ("/exit",):
        return False, ""
    qs.answer_history.append(user_input)

    action = _llm_turn(session, qs, f"Q{question_index + 1}: {question}\n\n{user_input}", progress)
    turns = 0

    while True:
        turns += 1
        if turns > _LIMITS.max_cycle_turns:
            logger.error(
                "Q%d exceeded %d turns; forcing evaluation",
                question_index + 1,
                _LIMITS.max_cycle_turns,
            )
            should_continue, progress = _evaluate_and_decide(session, qs)
            return should_continue, progress

        match action:
            case EvaluateAction():
                should_continue, progress = _evaluate_and_decide(session, qs)
                return should_continue, progress

            case VerifyAction(claims=claims):
                qs.verify_count += 1
                if qs.verify_count >= _LIMITS.max_verify_per_cycle:
                    action = _llm_turn(
                        session,
                        qs,
                        "Claims already verified for this answer. Continue with follow_up, evaluate, or conclude.",
                        progress,
                    )
                    continue
                if claims:
                    with spinner("checking claims..."):
                        from resume_roast.tools import REGISTRY

                        result = REGISTRY.execute(
                            "verify",
                            {"action": "verify", "claims": list(claims)},
                            client=session.client,
                            resume_md=session.data.resume_markdown,
                            competency_text=competency_text,
                            answer_history=qs.answer_history,
                        )
                    qs.verify_results = result.data
                    if result.success:
                        session.console.print("[dim]✓ claims checked[/dim]")
                    else:
                        session.console.print("[dim]✗ verification failed[/dim]")
                    action = _llm_turn(session, qs, result.data, progress)
                else:
                    action = _llm_turn(session, qs, "No claims to verify. Continue.", progress)

            case FollowUpAction():
                if qs.follow_up_count >= _LIMITS.max_follow_ups_per_cycle:
                    should_continue, progress = _evaluate_and_decide(session, qs)
                    return should_continue, progress
                action_dict: dict[str, Any] = {"action": "follow_up"}
                action_dict["competency_gaps"] = _get_competency_gaps(session.data)
                action_dict["question"] = qs.question
                action_dict["verify_summary"] = qs.verify_results
                with spinner("preparing follow-up..."):
                    from resume_roast.tools import REGISTRY

                    result = REGISTRY.execute(
                        "follow_up",
                        action_dict,
                        client=session.client,
                        resume_md=session.data.resume_markdown,
                        competency_text=competency_text,
                        answer_history=qs.answer_history,
                    )
                if result.success:
                    questions = result.metadata.get("questions", [])
                    if questions:
                        if len(questions) > 1:
                            logger.warning(
                                "Dropping %d extra follow-up question(s) (max 1 per auto-ask)",
                                len(questions) - 1,
                            )
                        q_text = questions[0]
                        session.console.print(f"\n{q_text}")
                        fb_input = session.input_provider.get_input(USER_PROMPT).strip()
                        if fb_input.lower() in ("/exit",):
                            return False, progress
                        qs.answer_history.append(fb_input)
                        qs.follow_up_count += 1
                        action = _llm_turn(
                            session,
                            qs,
                            f"[INTERNAL STATUS — follow-up automatically presented]\nQuestion: {q_text}\n\nAnswer: {fb_input}",
                            progress,
                        )
                        continue
                else:
                    session.console.print("[dim]✗ follow-up failed[/dim]")
                action = _llm_turn(session, qs, result.data, progress)

            case AskFollowupAction(question=q_text):
                if qs.follow_up_count >= _LIMITS.max_follow_ups_per_cycle:
                    session.messages.append(
                        Message(
                            role="user",
                            content=f"[INTERNAL STATUS — max follow-ups reached ({qs.follow_up_count}), ignoring ask_followup]",
                        )
                    )
                    should_continue, progress = _evaluate_and_decide(session, qs)
                    return should_continue, progress
                if not q_text:
                    action = _llm_turn(session, qs, "No question provided. Continue.", progress)
                    continue
                session.console.print(f"\n{q_text}")
                fb_input = session.input_provider.get_input(USER_PROMPT).strip()
                if fb_input.lower() in ("/exit",):
                    return False, progress
                qs.answer_history.append(fb_input)
                qs.follow_up_count += 1
                action = _llm_turn(
                    session,
                    qs,
                    f"[INTERNAL STATUS — follow-up automatically presented]\nQuestion: {q_text}\n\nAnswer: {fb_input}",
                )

            case AskAction():
                session.messages.append(
                    Message(
                        role="user",
                        content="[INTERNAL STATUS — the question is already active. Proceeding to evaluate.]",
                    )
                )
                should_continue, progress = _evaluate_and_decide(session, qs)
                return should_continue, progress

            case ConcludeAction():
                _, progress = _run_evaluate(session, qs)
                if _ is None:
                    logger.warning("Evaluate failed on conclude for Q%d", question_index + 1)
                session.messages.append(
                    Message(
                        role="user",
                        content="[INTERNAL STATUS — interview concluded by LLM]",
                    )
                )
                return False, progress

            case ParseFailure():
                action = _llm_turn(
                    session,
                    qs,
                    "Invalid response format. Respond with a valid JSON action object.",
                    progress,
                )

            case _:
                action = _llm_turn(
                    session,
                    qs,
                    f"Unknown action '{action.name}'. Valid: verify, follow_up, evaluate, ask_followup, conclude.",
                    progress,
                )


def _question_loop(session: InterviewSession) -> None:
    """Ask each base question and process answers."""
    progress = ""
    for idx in range(session.data.total_questions):
        logger.debug("Starting question %d/%d", idx + 1, session.data.total_questions)
        should_continue, progress = _run_question_cycle(session, idx, progress)
        if not should_continue:
            break


def _verdict_phase(session: InterviewSession, started_at: float) -> None:
    """Get the final verdict from the LLM and print the report."""
    q_answered = max(1, session.data.questions_answered)
    max_per = 10
    normalized = {cid: round(score / q_answered, 1) for cid, score in session.data.scores.items()}
    competency_text = _to_competency_text()
    prompt = build_verdict_prompt(normalized, max_per, competency_text)

    with spinner("computing verdict..."):
        completion = session.client.prompt(
            [*session.messages, Message(role="user", content=prompt)],
            temperature=0.0,
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

    _print_report(session.console, verdict, normalized, max_per)
    total = total_usage(session.usages)
    if total is not None:
        elapsed = time.perf_counter() - (started_at or time.perf_counter())
        session.console.print(
            summary_line(session.client.model, total, elapsed),
            style="dim",
        )


def _print_report(
    console: Console,
    verdict: Verdict,
    scores: Mapping[str, int | float],
    max_per_comp: int,
) -> None:
    """Render the final interview report."""
    verdict_colors = {"hire": "green", "maybe": "yellow", "dont_hire": "red"}

    console.rule("\nINTERVIEW REPORT")
    console.print()

    for c in COMPETENCIES:
        score = scores.get(c.id, 0)
        bar_len = 50
        filled = int(bar_len * score / max_per_comp) if max_per_comp > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        console.print(f"{c.label:30} {score:<4}/{max_per_comp:<2}  {bar}")

    console.print()
    color = verdict_colors.get(verdict.verdict, "white")
    console.print(f"Overall Rating: [bold]{verdict.overall_rating:.1f}/10[/bold]")
    console.print(f"Verdict: [bold {color}]{verdict.verdict.upper()}[/bold {color}]")
    console.print()

    if verdict.strengths:
        console.print("[bold green]Strengths:[/bold green]")
        for s in verdict.strengths:
            console.print(f"  + {s}")

    if verdict.growth_areas:
        console.print()
        console.print("[bold yellow]Growth Areas:[/bold yellow]")
        for g in verdict.growth_areas:
            console.print(f"  - {g}")

    console.print()
    console.print(verdict.summary)


def interview(path: Path) -> None:
    """Run an agentic behavioral interview on a PDF or DOCX resume."""
    client, _ = build_client()
    parsed = get_parser(path).parse(path)
    logger.debug("Parsed resume: %d chars", len(parsed.markdown))

    system_prompt = build_interview_system_prompt(parsed)

    messages: list[Message] = [Message(role="system", content=system_prompt)]
    data = SessionData(
        resume_markdown=parsed.markdown,
        base_questions=[],
        competencies=[c.id for c in COMPETENCIES],
        scores={c.id: 0 for c in COMPETENCIES},
        max_per_competency=10,
    )

    console = Console(highlight=False)
    debug = logging.getLogger().isEnabledFor(logging.DEBUG)
    started_at = 0.0
    session = InterviewSession(
        client=client,
        console=console,
        debug=debug,
        input_provider=make_input_provider(),
        messages=messages,
        usages=[],
        data=data,
    )

    try:
        with spinner("preparing interview questions..."):
            _plan_phase(session)

        console.print(
            f"\n[bold]Interview started — {session.data.total_questions} questions planned[/bold]"
        )
        console.print("Type your answers when prompted. Enter /exit to end early.\n")

        started_at = time.perf_counter()
        _question_loop(session)
        _verdict_phase(session, started_at)

    except (EOFError, KeyboardInterrupt):
        console.print()
        if session.data.questions_answered > 0:
            _verdict_phase(session, started_at or time.perf_counter())
        else:
            console.print("Interview aborted before any questions were answered.")
