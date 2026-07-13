"""Tests for the roast report parser."""

import json
from typing import Any

import pytest

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.evaluate.output.parser import RoastReportParser
from resume_roast.prompts.evaluate.output.schema import CATEGORY_NAMES

parser = RoastReportParser()


def _suggestion() -> dict[str, Any]:
    return {
        "recommendation": "Quantify your impact",
        "examples": [
            {"quote": "Used Python to analyze data", "rewrite": "Built a Python ETL pipeline"},
        ],
    }


def _category() -> dict[str, Any]:
    return {"score": 5, "findings": "needs work.", "suggestions": [_suggestion()]}


def _payload() -> dict[str, Any]:
    return {
        "overall": "A promising draft undermined by vague bullets.",
        "overall_score": 6,
        "categories": {name: _category() for name in CATEGORY_NAMES},
        "strengths": ["Concise single page"],
        "weaknesses": ["No metrics anywhere"],
    }


def _dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload)


def test_parses_a_valid_report() -> None:
    report = parser.parse(_dumps(_payload()))

    assert report.overall_score == 6
    assert tuple(report.categories) == CATEGORY_NAMES
    assert report.strengths == ("Concise single page",)
    assert report.weaknesses == ("No metrics anywhere",)
    skills = report.categories["Clarity"]
    assert skills.findings == "needs work."
    assert skills.suggestions[0].recommendation == "Quantify your impact"
    assert skills.suggestions[0].examples[0].rewrite == "Built a Python ETL pipeline"


def test_accepts_a_category_with_no_suggestions() -> None:
    payload = _payload()
    payload["categories"]["Polish"]["suggestions"] = []

    report = parser.parse(_dumps(payload))

    assert report.categories["Polish"].suggestions == ()


def test_accepts_an_additive_example_with_an_empty_quote() -> None:
    payload = _payload()
    example = payload["categories"]["Polish"]["suggestions"][0]["examples"][0]
    example["quote"] = ""
    example["rewrite"] = "Add an Education section"

    report = parser.parse(_dumps(payload))

    parsed = report.categories["Polish"].suggestions[0].examples[0]
    assert parsed.quote == ""
    assert parsed.rewrite == "Add an Education section"


def test_treats_a_missing_quote_as_empty() -> None:
    payload = _payload()
    del payload["categories"]["Polish"]["suggestions"][0]["examples"][0]["quote"]

    report = parser.parse(_dumps(payload))

    assert report.categories["Polish"].suggestions[0].examples[0].quote == ""


def test_strips_a_surrounding_code_fence() -> None:
    fenced = f"```json\n{_dumps(_payload())}\n```"

    assert parser.parse(fenced).overall_score == 6


def test_rejects_non_json() -> None:
    with pytest.raises(MalformedResponseError, match="not valid JSON"):
        parser.parse("## Overall Assessment\nA markdown response.")


def test_rejects_a_non_object_root() -> None:
    with pytest.raises(MalformedResponseError, match="single JSON object"):
        parser.parse("[1, 2, 3]")


def test_rejects_a_missing_category() -> None:
    payload = _payload()
    del payload["categories"]["Content"]

    with pytest.raises(MalformedResponseError, match=r"categories\.Content"):
        parser.parse(_dumps(payload))


def test_rejects_an_out_of_range_score() -> None:
    payload = _payload()
    payload["categories"]["Clarity"]["score"] = 87

    with pytest.raises(MalformedResponseError, match=r"categories\.Clarity\.score is 87"):
        parser.parse(_dumps(payload))


@pytest.mark.parametrize("bad_score", [7.5, "7", None, True])
def test_rejects_non_integer_scores(bad_score: object) -> None:
    payload = _payload()
    payload["overall_score"] = bad_score

    with pytest.raises(MalformedResponseError, match="overall_score"):
        parser.parse(_dumps(payload))


def test_rejects_blank_findings() -> None:
    payload = _payload()
    payload["categories"]["Content"]["findings"] = "  "

    with pytest.raises(MalformedResponseError, match=r"categories\.Content\.findings"):
        parser.parse(_dumps(payload))


def test_rejects_a_suggestion_missing_its_recommendation() -> None:
    payload = _payload()
    del payload["categories"]["Clarity"]["suggestions"][0]["recommendation"]

    with pytest.raises(
        MalformedResponseError, match=r"categories\.Clarity\.suggestions\[0\]\.recommendation"
    ):
        parser.parse(_dumps(payload))


def test_accepts_a_suggestion_with_no_examples() -> None:
    payload = _payload()
    payload["categories"]["Clarity"]["suggestions"][0]["examples"] = []

    report = parser.parse(_dumps(payload))

    assert report.categories["Clarity"].suggestions[0].examples == ()


def test_treats_a_suggestion_missing_examples_as_none() -> None:
    payload = _payload()
    del payload["categories"]["Clarity"]["suggestions"][0]["examples"]

    report = parser.parse(_dumps(payload))

    assert report.categories["Clarity"].suggestions[0].examples == ()


def test_rejects_more_than_three_examples() -> None:
    payload = _payload()
    example = {"quote": "q", "rewrite": "r"}
    payload["categories"]["Clarity"]["suggestions"][0]["examples"] = [example] * 4

    with pytest.raises(MalformedResponseError, match=r"examples has 4 items; keep it to at most 3"):
        parser.parse(_dumps(payload))


def test_rejects_an_example_missing_its_rewrite() -> None:
    payload = _payload()
    del payload["categories"]["Clarity"]["suggestions"][0]["examples"][0]["rewrite"]

    with pytest.raises(
        MalformedResponseError,
        match=r"categories\.Clarity\.suggestions\[0\]\.examples\[0\]\.rewrite",
    ):
        parser.parse(_dumps(payload))


def test_rejects_suggestions_that_are_not_an_array() -> None:
    payload = _payload()
    payload["categories"]["Clarity"]["suggestions"] = "none"

    with pytest.raises(MalformedResponseError, match=r"categories\.Clarity\.suggestions must be"):
        parser.parse(_dumps(payload))


def test_rejects_empty_strengths() -> None:
    payload = _payload()
    payload["strengths"] = []

    with pytest.raises(MalformedResponseError, match="strengths must be a non-empty array"):
        parser.parse(_dumps(payload))


def test_rejects_a_non_string_weakness() -> None:
    payload = _payload()
    payload["weaknesses"] = ["No metrics", 7]

    with pytest.raises(MalformedResponseError, match=r"weaknesses\[1\]"):
        parser.parse(_dumps(payload))


def test_rejects_a_blank_overall() -> None:
    payload = _payload()
    payload["overall"] = ""

    with pytest.raises(MalformedResponseError, match="overall must be a non-empty string"):
        parser.parse(_dumps(payload))
