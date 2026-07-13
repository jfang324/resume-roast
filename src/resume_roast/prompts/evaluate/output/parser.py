"""Validates the model's JSON roast report against the schema."""

from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.response_parser import ApiResponseParser

from .schema import CATEGORY_NAMES, CategoryReview, Example, RoastReport, Suggestion

_MAX_EXAMPLES = 3


class RoastReportParser(ApiResponseParser[RoastReport]):
    """Checks the decoded report field by field.

    Error messages name the offending field with its dotted path so the
    retry feedback tells the model exactly what to fix.
    """

    def _parse_object(self, data: dict[str, Any]) -> RoastReport:
        return RoastReport(
            overall=_text(data.get("overall"), "overall"),
            overall_score=_score(data.get("overall_score"), "overall_score"),
            categories=_categories(data),
            strengths=_string_list(data.get("strengths"), "strengths"),
            weaknesses=_string_list(data.get("weaknesses"), "weaknesses"),
        )


def _text(value: Any, label: str) -> str:
    """Require a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise MalformedResponseError(f"{label} must be a non-empty string")
    return value


def _optional_text(value: Any) -> str:
    """Accept a string or nothing; a blank or absent value becomes empty.

    Used for an example's quote: additive suggestions have no resume text
    to target, so an empty quote is valid rather than a failure.
    """
    return value if isinstance(value, str) and value.strip() else ""


def _score(value: Any, label: str) -> int:
    """Require an integer score in 0-10 (bool is an int in Python; reject it)."""
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10:
        raise MalformedResponseError(f"{label} is {value!r}; every score is an integer 0-10")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    """Require a JSON object."""
    if not isinstance(value, dict):
        raise MalformedResponseError(f"{label} is missing or not a JSON object")
    return cast(dict[str, Any], value)


def _categories(data: dict[str, Any]) -> dict[str, CategoryReview]:
    """Require every category from CATEGORY_NAMES, each fully formed."""
    raw = _object(data.get("categories"), "categories")
    reviews: dict[str, CategoryReview] = {}
    for name in CATEGORY_NAMES:
        path = f"categories.{name}"
        entry = _object(raw.get(name), path)
        reviews[name] = CategoryReview(
            score=_score(entry.get("score"), f"{path}.score"),
            findings=_text(entry.get("findings"), f"{path}.findings"),
            suggestions=_suggestions(entry.get("suggestions"), f"{path}.suggestions"),
        )
    return reviews


def _string_list(value: Any, label: str) -> tuple[str, ...]:
    """Require a non-empty array of non-empty strings."""
    if not isinstance(value, list) or not value:
        raise MalformedResponseError(f"{label} must be a non-empty array of strings")
    return tuple(
        _text(item, f"{label}[{index}]") for index, item in enumerate(cast(list[Any], value))
    )


def _suggestions(value: Any, label: str) -> tuple[Suggestion, ...]:
    """Require an array of recommendation+examples objects; empty is allowed.

    An empty array is how the model reports a category with no real
    criticism — the contract would rather have that than invented advice.
    """
    if not isinstance(value, list):
        raise MalformedResponseError(f"{label} must be an array (empty if there is nothing to fix)")
    suggestions: list[Suggestion] = []
    for index, item in enumerate(cast(list[Any], value)):
        path = f"{label}[{index}]"
        entry = _object(item, path)
        suggestions.append(
            Suggestion(
                recommendation=_text(entry.get("recommendation"), f"{path}.recommendation"),
                examples=_examples(entry.get("examples"), f"{path}.examples"),
            )
        )
    return tuple(suggestions)


def _examples(value: Any, label: str) -> tuple[Example, ...]:
    """Parse zero to three quote+rewrite objects backing a recommendation.

    Empty or absent is allowed: a self-evident recommendation adds nothing
    by carrying an example, and the contract asks it to omit one.
    """
    if value is None:
        return ()
    if not isinstance(value, list):
        raise MalformedResponseError(f"{label} must be an array")
    items = cast(list[Any], value)
    if len(items) > _MAX_EXAMPLES:
        raise MalformedResponseError(f"{label} has {len(items)} items; keep it to at most 3")
    examples: list[Example] = []
    for index, item in enumerate(items):
        path = f"{label}[{index}]"
        entry = _object(item, path)
        examples.append(
            Example(
                quote=_optional_text(entry.get("quote")),
                rewrite=_text(entry.get("rewrite"), f"{path}.rewrite"),
            )
        )
    return tuple(examples)
