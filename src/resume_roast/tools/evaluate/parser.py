"""Input validation and output normalization for evaluate."""

import json
import logging
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.tools.evaluate.schema import EvaluateInput, EvaluateOutput

logger = logging.getLogger(__name__)


def parse_input(data: EvaluateInput) -> EvaluateInput:
    if not data.original_question.strip():
        raise ValueError("original_question cannot be empty")
    if not data.answer_history:
        raise ValueError("answer_history cannot be empty")
    if not data.competency_descriptions.strip():
        raise ValueError("competency_descriptions cannot be empty")
    if not data.competency_ids:
        raise ValueError("competency_ids cannot be empty")
    return data


def parse_output(text: str, competency_ids: list[str]) -> EvaluateOutput:
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
        raise MalformedResponseError(f"evaluate output is not valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise MalformedResponseError("evaluate output must be a JSON object")
    data = cast(dict[str, Any], data)

    raw_scores = data.get("scores")
    if not isinstance(raw_scores, dict):
        raise MalformedResponseError("evaluate output must contain a 'scores' object")
    raw_scores = cast(dict[str, Any], raw_scores)

    scores: dict[str, int] = {}
    for cid in competency_ids:
        val = raw_scores.get(cid)
        if not isinstance(val, int) or isinstance(val, bool) or not 1 <= val <= 10:
            logger.warning("evaluate: missing/invalid score for %s (%s), defaulting to 5", cid, val)
            scores[cid] = 5
        else:
            scores[cid] = val

    critical_failure = bool(data.get("critical_failure", False))
    strengths = _string_list(data.get("strengths"))
    gaps = _string_list(data.get("gaps"))

    return EvaluateOutput(
        scores=scores,
        critical_failure=critical_failure,
        strengths=strengths,
        gaps=gaps,
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        item.strip() for item in cast(list[object], value) if isinstance(item, str) and item.strip()
    ]
