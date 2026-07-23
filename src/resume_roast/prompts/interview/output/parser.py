"""JSON parsing for interview outputs: base questions plan, verdict."""

from typing import cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.interview.output.schema import Verdict
from resume_roast.prompts.response_parser import parse_first_json_object, string_list


def parse_plan(text: str) -> list[str]:
    data = parse_first_json_object(text)
    raw = data.get("questions")
    if not isinstance(raw, list) or not raw:
        raise MalformedResponseError("plan output must contain a non-empty 'questions' array")

    questions = string_list(cast("list[object]", raw))
    if len(questions) < 4:
        raise MalformedResponseError(f"plan must have at least 4 questions, got {len(questions)}")

    if len(questions) > 6:
        questions = questions[:6]

    return questions


def parse_verdict(text: str) -> Verdict:
    data = parse_first_json_object(text)

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

    strengths = tuple(string_list(data.get("strengths")))
    growth_areas = tuple(string_list(data.get("growth_areas")))

    return Verdict(
        verdict=verdict,
        overall_rating=float(rating),
        summary=summary.strip(),
        strengths=strengths,
        growth_areas=growth_areas,
    )
