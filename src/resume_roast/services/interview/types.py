"""State types for the interview service, layered by lifetime."""

from dataclasses import dataclass, field
from typing import cast

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.prompts.interview.output.schema import Verdict
from resume_roast.prompts.interview.tools.evaluate.schema import EvaluateOutput
from resume_roast.services.chat.input_provider import InputProvider
from resume_roast.services.interview.renderer import InterviewRenderer


@dataclass(frozen=True)
class Limits:
    """Named numeric bounds the FSM checks; all in one place for discoverability."""

    max_cycle_turns: int = 12
    """Interviewer LLM calls allowed per question, counting the first one made
    after the candidate's answer. Spending the budget forces evaluation, and
    the check runs before each call so an exhausted cycle never pays for a
    completion it would discard. After 12 turns the LLM is looping; bail out."""
    max_verify_per_cycle: int = 1
    """Verify executions allowed per question; further requests are rebuffed
    without running the tool. One call fact-checks every claim in an answer,
    so a second would only ever cover a later answer in the same cycle —
    and follow-ups probe past what a highlights-style resume can corroborate,
    where the checks mostly come back as absent evidence rather than support.

    Raising this needs `QuestionState.verify_results` to accumulate first: it
    holds one rendered block today, so a second result would overwrite the
    first and the evaluator would score every answer against the last
    answer's fact-check."""
    max_follow_ups_per_cycle: int = 2
    """After 2 follow-ups the question is done; evaluate and move on."""
    max_critical_failures: int = 2
    """Critical-failure evaluations that end the interview early. Two strikes:
    one may be an off day, a second is a pattern not worth spending the
    remaining questions on."""


@dataclass(frozen=True)
class Exchange:
    """One question put to the candidate and the answer it drew.

    The first exchange of a cycle carries the base question; later ones
    carry the interviewer's follow-ups."""

    question: str
    answer: str


@dataclass(frozen=True)
class QuestionRecord:
    """Lifetime = whole interview: one answered question's evaluation evidence.

    Captured when evaluate succeeds — a question whose evaluation failed
    leaves no record, so an interview can hold fewer records than questions
    asked."""

    index: int
    question: str
    exchanges: tuple[Exchange, ...]
    verify_results: str
    evaluation: EvaluateOutput
    thoughts: tuple[str, ...] = ()


@dataclass
class InterviewState:
    """Lifetime = whole interview: the accumulated scores and question plan."""

    resume_markdown: str
    base_questions: list[str]
    competencies: list[str]
    scores: dict[str, int]
    questions_answered: int = 0
    total_questions: int = 0
    critical_failures: int = 0
    records: list[QuestionRecord] = field(default_factory=lambda: cast(list[QuestionRecord], []))


@dataclass(frozen=True)
class InterviewSession:
    """Lifetime = whole interview. Once set, never mutated.

    Mutable references (messages, usages) are shared by mutation, not replaced.
    """

    client: LlmClient
    renderer: InterviewRenderer
    input_provider: InputProvider
    messages: list[Message]
    usages: list[Usage]
    state: InterviewState


@dataclass(frozen=True)
class InterviewResult:
    """Lifetime = after the interview: everything the verdict phase produced.

    `scores` are per-question averages out of `max_score`. Records number
    `questions_answered`, which can trail `total_questions` when the interview
    ends early or an evaluation fails."""

    verdict: Verdict
    scores: dict[str, float]
    max_score: int
    records: tuple[QuestionRecord, ...]
    questions_answered: int
    total_questions: int


@dataclass
class QuestionState:
    """Lifetime = one base question. Reset between questions."""

    index: int
    question: str
    exchanges: list[Exchange] = field(default_factory=lambda: cast(list[Exchange], []))
    thoughts: list[str] = field(default_factory=lambda: cast(list[str], []))
    """Every thought the model attached to a call this cycle, accepted or not."""
    verify_results: str = ""
    follow_up_count: int = 0
    verify_count: int = 0
    turns: int = 0

    pending: list[Message] = field(default_factory=lambda: cast(list[Message], []))
    """Refused calls and the corrections sent for them, held out of the transcript.

    Replayed in the next payload so the model can see what it got wrong —
    without it the retry would re-send an identical prompt and, at this
    cycle's temperature, draw the same refused answer. Accumulates while
    refusals repeat and empties once the loop accepts a call, so a recovered
    mistake costs one turn instead of riding every later prompt through to
    the verdict."""
