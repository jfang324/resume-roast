"""Input/output types for the follow_up tool."""

from dataclasses import dataclass, field
from typing import cast


@dataclass(frozen=True)
class FollowUpInput:
    original_question: str
    answer: str
    verify_summary: str
    competency_gaps: str | None = None


@dataclass(frozen=True)
class FollowUpOutput:
    questions: list[str] = field(default_factory=lambda: cast(list[str], []))
    rationale: str = ""
