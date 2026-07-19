"""Output types for the interview feature."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Verdict:
    verdict: str
    overall_rating: float
    summary: str
    strengths: tuple[str, ...] = ()
    growth_areas: tuple[str, ...] = ()
