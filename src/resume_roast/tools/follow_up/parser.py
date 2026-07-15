"""Input validation and output normalization for follow_up."""

import json
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.tools.follow_up.schema import FollowUpInput, FollowUpOutput

_MAX_FOLLOW_UPS = 2


def parse_input(data: FollowUpInput) -> FollowUpInput:
    if not data.original_question.strip():
        raise ValueError("original_question cannot be empty")
    if not data.answer.strip():
        raise ValueError("answer cannot be empty")
    if not data.verify_summary.strip():
        raise ValueError("verify_summary cannot be empty")
    return data


def parse_output(text: str) -> FollowUpOutput:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(cleaned)
    except json.JSONDecodeError as exc:
        raise MalformedResponseError(f"follow_up output is not valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise MalformedResponseError("follow_up output must be a JSON object")
    data = cast(dict[str, Any], data)
    raw_questions = data.get("questions")
    if not isinstance(raw_questions, list):
        raise MalformedResponseError("follow_up output must contain a 'questions' array")
    raw_list = cast(list[object], raw_questions)
    questions = [item.strip() for item in raw_list if isinstance(item, str) and item.strip()]
    questions = questions[:_MAX_FOLLOW_UPS]
    rationale = data.get("rationale", "")
    if not isinstance(rationale, str):
        rationale = ""
    return FollowUpOutput(questions=questions, rationale=rationale)
