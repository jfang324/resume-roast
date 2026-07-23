"""The per-question ReAct cycle: ask, then verify/follow up/evaluate until decided."""

import logging

from resume_roast.integrations.errors import AuthenticationError, MalformedResponseError
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
from resume_roast.services.interview.types import (
    Exchange,
    InterviewSession,
    QuestionRecord,
    QuestionState,
)

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

    qs.exchanges.append(Exchange(question=question, answer=user_input))

    call = _llm_turn(session, qs, f"Q{question_index + 1}: {question}\n\n{user_input}", progress)

    while True:
        match call:
            case EvaluateCall():
                return _evaluate_and_decide(session, qs, progress)

            case VerifyCall(claims=claims):
                if qs.verify_count >= LIMITS.max_verify_per_cycle:
                    call = _steering_turn(
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
                                qs.exchanges[-1].answer,
                                session.state.resume_markdown,
                            )
                        except AuthenticationError:
                            # A rejected key fails every later call the same
                            # way; end the session at the error boundary.
                            raise
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
                    call = _steering_turn(session, qs, "No claims to verify. Continue.", progress)

            case AskFollowupCall(question=q_text):
                if qs.follow_up_count >= LIMITS.max_follow_ups_per_cycle:
                    session.messages.append(
                        Message(
                            role="user",
                            content=f"[INTERNAL STATUS — max follow-ups reached ({qs.follow_up_count}), ignoring ask_followup]",
                        )
                    )

                    return _evaluate_and_decide(session, qs, progress)

                if not q_text:
                    call = _steering_turn(session, qs, "No question provided. Continue.", progress)
                    continue

                fb_input = ask_followup(session.renderer, session.input_provider, q_text)
                if fb_input.lower() in ("/exit",):
                    return False, progress

                qs.exchanges.append(Exchange(question=q_text, answer=fb_input))
                qs.follow_up_count += 1
                call = _llm_turn(
                    session,
                    qs,
                    f"[INTERNAL STATUS — follow-up automatically presented]\nQuestion: {q_text}\n\nAnswer: {fb_input}",
                    progress,
                )

            case UnknownTool(name=name):
                call = _steering_turn(
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
                call = _steering_turn(
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
                [e.answer for e in qs.exchanges],
                qs.verify_results,
                render_competency_text(),
                session.state.competencies,
            )
        except AuthenticationError:
            # A rejected key fails every later call the same way; end the
            # session at the error boundary.
            raise
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

    logger.debug(
        "Evaluation: scores=%s, critical=%d",
        eval_output.scores,
        session.state.critical_failures,
    )

    session.messages.append(
        Message(role="user", content=render_evaluation_results(eval_output)),
    )
    session.state.records.append(
        QuestionRecord(
            index=qs.index,
            question=qs.question,
            exchanges=tuple(qs.exchanges),
            verify_results=qs.verify_results,
            evaluation=eval_output,
            thoughts=tuple(qs.thoughts),
        )
    )
    qs.verify_results = ""

    max_per = session.state.questions_answered * MAX_SCORE_PER_QUESTION
    progress = build_progress_message(
        session.state.questions_answered,
        session.state.total_questions,
        session.state.scores,
        max_per,
        [record.index for record in session.state.records],
    )
    session.renderer.show_status("answer evaluated", ok=True)

    return eval_output, progress


def _evaluate_and_decide(
    session: InterviewSession, qs: QuestionState, carry_progress: str
) -> tuple[bool, str]:
    """Evaluate the answer cycle and decide whether the interview continues.

    Returns (continue?, progress_string). A failed evaluation changes no
    state, so the carried progress is still accurate and rides on.
    """
    eval_output, progress = _run_evaluate(session, qs)
    if eval_output is None:
        logger.error("Evaluate failed for Q%d, advancing", qs.index + 1)

        return True, carry_progress

    return session.state.critical_failures < 2, progress


def _llm_turn(
    session: InterviewSession,
    qs: QuestionState,
    user_text: str,
    progress: str,
) -> ToolCall:
    """Advance the cycle with a message the transcript keeps.

    For the interview itself — the candidate's words and the observations
    tools produce. Use `_steering_turn` for anything that only corrects the
    model.

    Reaching here means the loop accepted the previous answer, which is what
    retires any pending correction. Acceptance is the right trigger rather
    than a clean parse: `{"tool": "dance"}` parses fine and is still refused,
    so clearing on parse would forget a refusal the model is busy repeating.
    """
    if _budget_spent(qs):
        return EvaluateCall()

    qs.pending.clear()
    session.messages.append(Message(role="user", content=user_text))

    return _prompt_and_parse(session, qs, progress)


def _steering_turn(
    session: InterviewSession,
    qs: QuestionState,
    correction: str,
    progress: str,
) -> ToolCall:
    """Advance the cycle with a correction, leaving no trace once it lands.

    The refused call comes back out of the transcript and joins the
    correction in `qs.pending`, which rides along in the next payload until
    the model answers with something the loop accepts. Neither is ever
    written to the history the verdict reads: steering text is written to be
    read once, and read ten turns later it is an imperative with no visible
    referent.
    """
    if _budget_spent(qs):
        return EvaluateCall()

    qs.pending.append(session.messages.pop())
    qs.pending.append(Message(role="user", content=correction))

    return _prompt_and_parse(session, qs, progress)


def _budget_spent(qs: QuestionState) -> bool:
    """Report whether the question has spent its turn budget, logging when it has."""
    if qs.turns < LIMITS.max_cycle_turns:
        return False

    logger.error(
        "Q%d exceeded %d turns; forcing evaluation",
        qs.index + 1,
        LIMITS.max_cycle_turns,
    )

    return True


def _prompt_and_parse(
    session: InterviewSession,
    qs: QuestionState,
    progress: str,
) -> ToolCall:
    """Spend one turn on the next decision, replaying any unresolved correction.

    The cycle's only prompt site. Both turn helpers check the budget and land
    here, so the bound cannot be sidestepped, and both take `qs`, so the type
    checker rejects a call site that forgets it.
    """
    qs.turns += 1

    payload = [*session.messages, *qs.pending]
    if progress:
        payload = [*payload, Message(role="user", content=progress)]

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
        qs.thoughts.append(call.thought)
        session.renderer.show_thought(call.thought)

    return call
