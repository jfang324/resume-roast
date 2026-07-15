"""Output types for the interview feature."""

from dataclasses import dataclass


@dataclass
class SessionData:
    resume_markdown: str
    base_questions: list[str]
    competencies: list[str]
    scores: dict[str, int]
    max_per_competency: int
    questions_answered: int = 0
    total_questions: int = 0
    critical_failures: int = 0
    finished: bool = False


@dataclass(frozen=True)
class Verdict:
    verdict: str
    overall_rating: float
    summary: str
    strengths: tuple[str, ...] = ()
    growth_areas: tuple[str, ...] = ()
