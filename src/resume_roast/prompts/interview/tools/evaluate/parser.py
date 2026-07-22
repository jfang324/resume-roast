"""Output parsing for the evaluate tool."""

import json
import logging
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.interview.tools.evaluate.schema import EvaluateOutput
from resume_roast.prompts.response_parser import strip_code_fence

logger = logging.getLogger(__name__)


def parse_output(text: str, competency_ids: list[str]) -> EvaluateOutput:
    """Parse the model's per-competency assessment, defaulting any bad score.

    Each competency carries a ``rationale`` (generated first) and a ``score``,
    so the number is conditioned on the reasoning that precedes it.

    Raises:
        MalformedResponseError: on invalid JSON or a missing 'assessment' object.
    """
    cleaned = strip_code_fence(text.strip())
    try:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(cleaned)
    except json.JSONDecodeError as exc:
        raise MalformedResponseError(f"evaluate output is not valid JSON ({exc})") from exc

    if not isinstance(data, dict):
        raise MalformedResponseError("evaluate output must be a JSON object")

    data = cast(dict[str, Any], data)
    raw_assessment = data.get("assessment")
    if not isinstance(raw_assessment, dict):
        raise MalformedResponseError("evaluate output must contain an 'assessment' object")

    raw_assessment = cast(dict[str, Any], raw_assessment)
    scores: dict[str, int] = {}
    rationales: dict[str, str] = {}
    for cid in competency_ids:
        entry = raw_assessment.get(cid)
        entry = cast(dict[str, Any], entry) if isinstance(entry, dict) else {}

        val = entry.get("score")
        if not isinstance(val, int) or isinstance(val, bool) or not 1 <= val <= 10:
            logger.warning("evaluate: missing/invalid score for %s (%s), defaulting to 5", cid, val)
            scores[cid] = 5
        else:
            scores[cid] = val

        rationale = entry.get("rationale")
        rationales[cid] = rationale.strip() if isinstance(rationale, str) else ""

    return EvaluateOutput(
        scores=scores,
        rationales=rationales,
        critical_failure=bool(data.get("critical_failure", False)),
        strengths=_string_list(data.get("strengths")),
        gaps=_string_list(data.get("gaps")),
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    return [
        item.strip() for item in cast(list[object], value) if isinstance(item, str) and item.strip()
    ]
