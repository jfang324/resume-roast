"""Tests for the interview verify tool's output parser."""

import json
from typing import Any

import pytest

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.interview.tools.verify.parser import parse_output


def _claim(**overrides: Any) -> dict[str, Any]:
    claim: dict[str, Any] = {
        "text": "Led the migration",
        "evidence": "Resume lists the migration project",
        "contradiction": False,
        "probability": 0.9,
    }
    claim.update(overrides)

    return claim


def _dumps(claims: list[Any]) -> str:
    return json.dumps({"claims": claims})


def test_parses_a_full_claim() -> None:
    output = parse_output(_dumps([_claim()]))

    result = output.claims[0]
    assert result.text == "Led the migration"
    assert result.probability == 0.9
    assert result.evidence == "Resume lists the migration project"
    assert result.contradiction is False


def test_rejects_non_json() -> None:
    with pytest.raises(MalformedResponseError, match="not valid JSON"):
        parse_output("The claims all check out.")


def test_rejects_a_missing_claims_array() -> None:
    with pytest.raises(MalformedResponseError, match="'claims' array"):
        parse_output(json.dumps({"results": []}))


@pytest.mark.parametrize("bad_item", ["a bare string", 5, None, ["nested"]])
def test_rejects_a_non_object_claim_item(bad_item: object) -> None:
    with pytest.raises(MalformedResponseError, match=r"claims\[0\] must be a JSON object"):
        parse_output(_dumps([bad_item]))


def test_rejects_a_blank_claim_text() -> None:
    with pytest.raises(MalformedResponseError, match=r"claims\[0\].text"):
        parse_output(_dumps([_claim(text="  ")]))


@pytest.mark.parametrize("bad_prob", [-0.1, 1.1, "0.9", True])
def test_rejects_an_invalid_probability(bad_prob: object) -> None:
    with pytest.raises(MalformedResponseError, match=r"claims\[0\].probability"):
        parse_output(_dumps([_claim(probability=bad_prob)]))
