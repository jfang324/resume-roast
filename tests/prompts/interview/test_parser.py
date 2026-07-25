"""Tests for the interview's plan and verdict parsers."""

import json
from typing import Any

import pytest

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.prompts.interview.output.parser import parse_plan, parse_verdict


def _verdict(**overrides: Any) -> str:
    payload: dict[str, Any] = {
        "summary": "Solid across the board.",
        "strengths": ["Clear communication"],
        "growth_areas": ["Depth on trade-offs"],
        "verdict": "hire",
        "overall_rating": 7.5,
    }
    payload.update(overrides)

    return json.dumps(payload)


# -- plan --------------------------------------------------------------------


def test_parses_a_well_formed_plan() -> None:
    text = json.dumps({"questions": ["Q1", "Q2", "Q3", "Q4"]})

    assert parse_plan(text) == ["Q1", "Q2", "Q3", "Q4"]


def test_rejects_a_plan_below_the_minimum() -> None:
    with pytest.raises(MalformedResponseError, match="at least 4 questions"):
        parse_plan(json.dumps({"questions": ["Q1", "Q2", "Q3"]}))


def test_truncates_a_plan_past_the_maximum() -> None:
    text = json.dumps({"questions": [f"Q{i}" for i in range(1, 9)]})

    assert len(parse_plan(text)) == 6


# -- verdict -----------------------------------------------------------------


def test_parses_a_well_formed_verdict() -> None:
    parsed = parse_verdict(_verdict())

    assert parsed.verdict == "hire"
    assert parsed.overall_rating == 7.5


@pytest.mark.parametrize("rating", [0, 0.0, 10, 10.0, 5.5])
def test_accepts_every_rating_in_range(rating: float) -> None:
    """0 is inside the scale: the competency scores it summarizes start there."""
    assert parse_verdict(_verdict(overall_rating=rating)).overall_rating == float(rating)


@pytest.mark.parametrize("rating", [-0.1, 10.1, 11, "7", None, True, False])
def test_rejects_a_rating_outside_the_scale(rating: object) -> None:
    """Booleans are ints in Python, so True/False would otherwise land as 1.0/0.0."""
    with pytest.raises(MalformedResponseError, match="overall_rating"):
        parse_verdict(_verdict(overall_rating=rating))


def test_rejects_an_unknown_verdict_label() -> None:
    with pytest.raises(MalformedResponseError, match="verdict must be"):
        parse_verdict(_verdict(verdict="strong_hire"))
