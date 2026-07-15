"""JSON parsing for interview outputs: base questions plan, verdict."""

import json
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.interview.output.schema import Verdict
from resume_roast.prompts.response_parser import strip_code_fence


def _parse_first_json(text: str) -> dict[str, Any]:
    """Parse the first JSON object from text, ignoring any trailing data."""
    cleaned = strip_code_fence(text.strip())
    try:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(cleaned)
    except json.JSONDecodeError as exc:
        raise MalformedResponseError(f"output is not valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise MalformedResponseError("output must be a JSON object")
    return cast(dict[str, Any], data)


def parse_plan(text: str) -> list[str]:
    data = _parse_first_json(text)
    raw = data.get("questions")
    if not isinstance(raw, list) or not raw:
        raise MalformedResponseError("plan output must contain a non-empty 'questions' array")
    raw_list = cast(list[object], raw)
    questions: list[str] = [
        item.strip() for item in raw_list if isinstance(item, str) and item.strip()
    ]
    if len(questions) < 4:
        raise MalformedResponseError(f"plan must have at least 4 questions, got {len(questions)}")
    if len(questions) > 6:
        questions = questions[:6]
    return questions


def parse_verdict(text: str) -> Verdict:
    data = _parse_first_json(text)

    verdict = data.get("verdict")
    if verdict not in ("hire", "maybe", "dont_hire"):
        raise MalformedResponseError(
            f"verdict must be 'hire', 'maybe', or 'dont_hire', got {verdict!r}"
        )

    rating = data.get("overall_rating")
    if not isinstance(rating, (int, float)) or not 1.0 <= rating <= 10.0:
        raise MalformedResponseError(f"overall_rating must be a number 1.0-10.0, got {rating!r}")

    summary = data.get("summary", "")
    if not isinstance(summary, str) or not summary.strip():
        raise MalformedResponseError("summary must be a non-empty string")

    strengths = _string_tuple(data.get("strengths"))
    growth_areas = _string_tuple(data.get("growth_areas"))

    return Verdict(
        verdict=verdict,
        overall_rating=float(rating),
        summary=summary.strip(),
        strengths=strengths,
        growth_areas=growth_areas,
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    raw_list = cast(list[object], value)
    return tuple(item.strip() for item in raw_list if isinstance(item, str) and item.strip())
