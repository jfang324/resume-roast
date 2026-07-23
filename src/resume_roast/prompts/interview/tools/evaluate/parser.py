"""Output parsing for the evaluate tool."""

import logging
from typing import Any, cast

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.interview.tools.evaluate.schema import EvaluateOutput
from resume_roast.prompts.response_parser import parse_first_json_object, string_list

logger = logging.getLogger(__name__)


def parse_output(text: str, competency_ids: list[str]) -> EvaluateOutput:
    """Parse the model's per-competency assessment, defaulting any bad score.

    Each competency carries a ``rationale`` (generated first) and a ``score``,
    so the number is conditioned on the reasoning that precedes it.

    Raises:
        MalformedResponseError: on invalid JSON or a missing 'assessment' object.
    """
    data = parse_first_json_object(text, "evaluate output")
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
        strengths=string_list(data.get("strengths")),
        gaps=string_list(data.get("gaps")),
    )
