"""State types for the interview service, layered by lifetime."""

from dataclasses import dataclass, field
from typing import cast

from resume_roast.integrations.llm_client import LlmClient
from resume_roast.integrations.types import Message, Usage
from resume_roast.services.chat.input_provider import InputProvider
from resume_roast.services.interview.renderer import InterviewRenderer


@dataclass(frozen=True)
class Limits:
    """Named numeric bounds the FSM checks; all in one place for discoverability."""

    max_cycle_turns: int = 12
    """Total LLM turns per question before force-evaluate.
    After 12 turns the LLM is looping; bail out."""
    max_verify_per_cycle: int = 1
    """Verify executions allowed per question; further requests are rebuffed
    without running the tool. One fact-check covers the answer — asking again
    means the LLM is hallucinating details instead of reading the results, so
    force a move to ask_followup or evaluate."""
    max_follow_ups_per_cycle: int = 2
    """After 2 follow-ups the question is done; evaluate and move on."""


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


@dataclass
class QuestionState:
    """Lifetime = one base question. Reset between questions."""

    index: int
    question: str
    answer_history: list[str] = field(default_factory=lambda: cast(list[str], []))
    verify_results: str = ""
    follow_up_count: int = 0
    verify_count: int = 0
