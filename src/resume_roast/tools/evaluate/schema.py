"""Input/output types for the evaluate tool."""

from dataclasses import dataclass, field
from typing import cast


@dataclass(frozen=True)
class EvaluateInput:
    original_question: str
    answer_history: list[str]
    verify_results: str
    competency_descriptions: str
    competency_ids: list[str]


@dataclass(frozen=True)
class EvaluateOutput:
    scores: dict[str, int] = field(default_factory=lambda: cast(dict[str, int], {}))
    critical_failure: bool = False
    strengths: list[str] = field(default_factory=lambda: cast(list[str], []))
    gaps: list[str] = field(default_factory=lambda: cast(list[str], []))
