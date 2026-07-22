"""Tests for the interview evaluate tool's output parser."""

import json
from typing import Any

import pytest

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.interview.tools.evaluate.parser import parse_output

COMPETENCY_IDS = ["ownership", "technical_competence", "problem_solving", "collaboration"]


def _assessment() -> dict[str, Any]:
    return {cid: {"rationale": f"{cid} was solid", "score": 7} for cid in COMPETENCY_IDS}


def _payload() -> dict[str, Any]:
    return {
        "strengths": ["Concrete metrics"],
        "gaps": ["No mention of trade-offs"],
        "assessment": _assessment(),
        "critical_failure": False,
    }


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload)


def test_parses_nested_assessment_into_scores_and_rationales() -> None:
    output = parse_output(_dumps(_payload()), COMPETENCY_IDS)

    assert output.scores == dict.fromkeys(COMPETENCY_IDS, 7)
    assert output.rationales == {cid: f"{cid} was solid" for cid in COMPETENCY_IDS}
    assert output.strengths == ["Concrete metrics"]
    assert output.gaps == ["No mention of trade-offs"]
    assert output.critical_failure is False


def test_rejects_a_missing_assessment() -> None:
    payload = _payload()
    del payload["assessment"]

    with pytest.raises(MalformedResponseError, match="'assessment' object"):
        parse_output(_dumps(payload), COMPETENCY_IDS)


def test_rejects_non_json() -> None:
    with pytest.raises(MalformedResponseError, match="not valid JSON"):
        parse_output("Strengths: the answer was great.", COMPETENCY_IDS)


@pytest.mark.parametrize("bad_score", [0, 11, 7.5, "7", None, True])
def test_defaults_an_invalid_score_to_five(bad_score: object) -> None:
    payload = _payload()
    payload["assessment"]["ownership"]["score"] = bad_score

    output = parse_output(_dumps(payload), COMPETENCY_IDS)

    assert output.scores["ownership"] == 5
    # The rationale still survives even when its score is unusable.
    assert output.rationales["ownership"] == "ownership was solid"


def test_defaults_a_missing_competency_score_to_five() -> None:
    payload = _payload()
    del payload["assessment"]["collaboration"]

    output = parse_output(_dumps(payload), COMPETENCY_IDS)

    assert output.scores["collaboration"] == 5
    assert output.rationales["collaboration"] == ""


def test_treats_a_missing_rationale_as_empty() -> None:
    payload = _payload()
    del payload["assessment"]["problem_solving"]["rationale"]

    output = parse_output(_dumps(payload), COMPETENCY_IDS)

    assert output.rationales["problem_solving"] == ""
    assert output.scores["problem_solving"] == 7


def test_strips_a_surrounding_code_fence() -> None:
    fenced = f"```json\n{_dumps(_payload())}\n```"

    output = parse_output(fenced, COMPETENCY_IDS)

    assert output.scores["ownership"] == 7
