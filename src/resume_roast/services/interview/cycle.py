"""The per-question ReAct cycle: ask, then verify/follow up/evaluate until decided."""

import logging

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.integrations.types import Message
from resume_roast.prompts.interview.builder import build_progress_message, render_competency_text
from resume_roast.prompts.interview.tools.evaluate.builder import render_evaluation_results
from resume_roast.prompts.interview.tools.evaluate.schema import EvaluateOutput
from resume_roast.prompts.interview.tools.verify.builder import render_verify_results
from resume_roast.services.interview.constants import (
    LIMITS,
    MAX_SCORE_PER_QUESTION,
    TURN_TEMPERATURE,
)
from resume_roast.services.interview.tool_calls import (
    AskFollowupCall,
    ConcludeCall,
    EvaluateCall,
    ParseFailure,
    ToolCall,
    UnknownTool,
    VerifyCall,
    parse_tool_call,
)
from resume_roast.services.interview.tools.ask_followup import ask_followup
from resume_roast.services.interview.tools.evaluate import evaluate_answer
from resume_roast.services.interview.tools.verify import verify_claims
from resume_roast.services.interview.types import InterviewSession, QuestionState

logger = logging.getLogger(__name__)


def run_question_cycle(
    session: InterviewSession, question_index: int, carry_progress: str
) -> tuple[bool, str]:
    """Ask one base question and process the full answer cycle.

    Returns:
        (continue?, progress_string).
    """
    question = session.state.base_questions[question_index]
    qs = QuestionState(index=question_index, question=question)
    progress = carry_progress

    session.renderer.show_question(question_index, question)
    user_input = session.input_provider.get_input().strip()
    if user_input.lower() in ("/exit",):
        return False, ""

    qs.answer_history.append(user_input)

    call = _llm_turn(session, qs, f"Q{question_index + 1}: {question}\n\n{user_input}", progress)

    while True:
        match call:
            case EvaluateCall():
                return _evaluate_and_decide(session, qs)

            case VerifyCall(claims=claims):
                if qs.verify_count >= LIMITS.max_verify_per_cycle:
                    call = _llm_turn(
                        session,
                        qs,
                        "Claims already verified for this answer. Continue with ask_followup, evaluate, or conclude.",
                        progress,
                    )
                    continue

                if claims:
                    with session.renderer.busy("checking claims..."):
                        try:
                            output, usage = verify_claims(
                                session.client,
                                list(claims),
                                qs.answer_history[-1],
                                session.state.resume_markdown,
                            )
                        except Exception:
                            logger.exception("verify tool failed")
                            output, usage = None, None

                    qs.verify_count += 1

                    if usage is not None:
                        session.usages.append(usage)

                    if output is not None:
                        text = render_verify_results(output)
                        session.renderer.show_status("claims checked", ok=True)
                    else:
                        text = "Verification encountered an error."
                        session.renderer.show_status("verification failed", ok=False)

                    qs.verify_results = text
                    call = _llm_turn(session, qs, text, progress)
                else:
                    call = _llm_turn(session, qs, "No claims to verify. Continue.", progress)

            case AskFollowupCall(question=q_text):
                if qs.follow_up_count >= LIMITS.max_follow_ups_per_cycle:
                    session.messages.append(
                        Message(
                            role="user",
                            content=f"[INTERNAL STATUS — max follow-ups reached ({qs.follow_up_count}), ignoring ask_followup]",
                        )
                    )

                    return _evaluate_and_decide(session, qs)

                if not q_text:
                    call = _llm_turn(session, qs, "No question provided. Continue.", progress)
                    continue

                fb_input = ask_followup(session.renderer, session.input_provider, q_text)
                if fb_input.lower() in ("/exit",):
                    return False, progress

                qs.answer_history.append(fb_input)
                qs.follow_up_count += 1
                call = _llm_turn(
                    session,
                    qs,
                    f"[INTERNAL STATUS — follow-up automatically presented]\nQuestion: {q_text}\n\nAnswer: {fb_input}",
                    progress,
                )

            case UnknownTool(name=name):
                call = _llm_turn(
                    session,
                    qs,
                    f"Unknown tool '{name}'. Valid: verify, ask_followup, evaluate, conclude.",
                    progress,
                )

            case ConcludeCall():
                eval_output, progress = _run_evaluate(session, qs)
                if eval_output is None:
                    logger.warning("Evaluate failed on conclude for Q%d", question_index + 1)

                session.messages.append(
                    Message(
                        role="user",
                        content="[INTERNAL STATUS — interview concluded by LLM]",
                    )
                )

                return False, progress

            case ParseFailure():
                call = _llm_turn(
                    session,
                    qs,
                    "Invalid response format. Respond with a valid JSON tool call.",
                    progress,
                )


def _run_evaluate(
    session: InterviewSession, qs: QuestionState
) -> tuple[EvaluateOutput | None, str]:
    """Run the evaluate tool, accumulate scores, and inject [INTERNAL STATUS].

    Returns (output_or_None, progress_string).
    """
    with session.renderer.busy("evaluating answer..."):
        try:
            eval_output, usage = evaluate_answer(
                session.client,
                qs.question,
                qs.answer_history,
                qs.verify_results,
                render_competency_text(),
                session.state.competencies,
            )
        except Exception:
            logger.exception("evaluate tool failed")

            return None, ""

    if usage is not None:
        session.usages.append(usage)

    for cid, score in eval_output.scores.items():
        session.state.scores[cid] = session.state.scores.get(cid, 0) + score

    session.state.questions_answered += 1

    if eval_output.critical_failure:
        session.state.critical_failures += 1

    max_per = session.state.questions_answered * MAX_SCORE_PER_QUESTION
    progress = build_progress_message(
        session.state.questions_answered,
        session.state.total_questions,
        session.state.scores,
        max_per,
        session.state.base_questions,
    )
    logger.debug(
        "Evaluation: scores=%s, critical=%d",
        eval_output.scores,
        session.state.critical_failures,
    )

    session.messages.append(
        Message(role="user", content=render_evaluation_results(eval_output)),
    )
    qs.verify_results = ""
    session.renderer.show_status("answer evaluated", ok=True)

    return eval_output, progress


def _evaluate_and_decide(session: InterviewSession, qs: QuestionState) -> tuple[bool, str]:
    """Evaluate the answer cycle and decide whether the interview continues.

    Returns (continue?, progress_string).
    """
    eval_output, progress = _run_evaluate(session, qs)
    if eval_output is None:
        logger.error("Evaluate failed for Q%d, advancing", qs.index + 1)

        return True, ""

    return session.state.critical_failures < 2, progress


def _llm_turn(
    session: InterviewSession,
    qs: QuestionState,
    user_text: str,
    progress: str,
) -> ToolCall:
    """Append a user message, prompt with current progress appended, and return the parsed tool call.

    Spends one of the question's turns. Once the budget is gone this forces
    evaluation instead, checked before the call so an exhausted cycle never
    pays for a completion it would only discard. Taking `qs` is what makes
    the budget unskippable: every path that advances the cycle comes through
    here, and the type checker rejects a call site that forgets it.
    """
    if qs.turns >= LIMITS.max_cycle_turns:
        logger.error(
            "Q%d exceeded %d turns; forcing evaluation",
            qs.index + 1,
            LIMITS.max_cycle_turns,
        )

        return EvaluateCall()

    qs.turns += 1
    session.messages.append(Message(role="user", content=user_text))

    payload = session.messages
    if progress:
        payload = [*session.messages, Message(role="user", content=progress)]

    with session.renderer.busy("thinking..."):
        completion = session.client.prompt(payload, temperature=TURN_TEMPERATURE)

    if completion.usage is not None:
        session.usages.append(completion.usage)

    session.messages.append(Message(role="assistant", content=completion.text))

    try:
        call = parse_tool_call(completion.text)
    except MalformedResponseError as exc:
        logger.warning("Failed to parse tool call: %s", exc)

        return ParseFailure(raw_text=completion.text)

    if call.thought:
        session.renderer.show_thought(call.thought)

    return call
