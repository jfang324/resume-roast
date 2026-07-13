"""The roast report: what the model's JSON response must contain."""

from dataclasses import dataclass

CATEGORY_NAMES = ("Content", "Clarity", "Polish")
"""Category keys in display order; the output contract and parser both use this."""


@dataclass(frozen=True)
class Example:
    """One concrete rewrite, targeting quoted resume text when there is any.

    ``quote`` is empty for additive suggestions — recommending a section or
    detail the resume lacks has no existing text to target.
    """

    quote: str
    rewrite: str


@dataclass(frozen=True)
class Suggestion:
    """One high-level improvement, with up to three concrete examples.

    ``examples`` is empty when the recommendation is self-evident and a
    before/after would only restate it.
    """

    recommendation: str
    examples: tuple[Example, ...]


@dataclass(frozen=True)
class CategoryReview:
    """One category's score, findings, and the improvements the findings imply.

    ``suggestions`` is empty when the findings hold no real criticism —
    the contract forbids inventing suggestions to fill space.
    """

    score: int
    findings: str
    suggestions: tuple[Suggestion, ...]


@dataclass(frozen=True)
class RoastReport:
    """The full structured evaluation of one resume.

    ``categories`` is keyed by `CATEGORY_NAMES`, all present. ``strengths``
    and ``weaknesses`` are short bullet statements, rendered as the What's
    Good and What's Bad sections.
    """

    overall: str
    overall_score: int
    categories: dict[str, CategoryReview]
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
