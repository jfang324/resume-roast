"""Unit tests for the interview action model."""

import json

import pytest

from resume_roast.cli.interview.actions import (
    AskAction,
    AskFollowupAction,
    ConcludeAction,
    EvaluateAction,
    FollowUpAction,
    ParseFailure,
    PlanAction,
    VerifyAction,
    action_from_dict,
    parse_llm_action,
)
from resume_roast.integrations.errors import MalformedResponseError


class TestActionFromDict:
    def test_verify(self) -> None:
        action = action_from_dict({"action": "verify", "claims": ["c1", "c2"]})
        assert action == VerifyAction(claims=("c1", "c2"))

    def test_verify_no_claims(self) -> None:
        action = action_from_dict({"action": "verify"})
        assert action == VerifyAction()

    def test_evaluate(self) -> None:
        action = action_from_dict({"action": "evaluate"})
        assert action == EvaluateAction()

    def test_follow_up(self) -> None:
        action = action_from_dict({"action": "follow_up"})
        assert action == FollowUpAction()

    def test_ask_followup(self) -> None:
        action = action_from_dict({"action": "ask_followup", "question": "Tell me more?"})
        assert action == AskFollowupAction(question="Tell me more?")

    def test_ask_followup_no_question(self) -> None:
        action = action_from_dict({"action": "ask_followup"})
        assert action == AskFollowupAction()

    def test_conclude(self) -> None:
        action = action_from_dict({"action": "conclude"})
        assert action == ConcludeAction()

    def test_ask(self) -> None:
        action = action_from_dict({"action": "ask"})
        assert action == AskAction()

    def test_plan(self) -> None:
        action = action_from_dict({"action": "plan", "questions": ["q1", "q2"]})
        assert action == PlanAction(questions=("q1", "q2"))

    def test_plan_no_questions(self) -> None:
        action = action_from_dict({"action": "plan"})
        assert action == PlanAction()

    def test_unknown_action(self) -> None:
        action = action_from_dict({"action": "dance"})
        assert isinstance(action, ParseFailure)

    def test_missing_action(self) -> None:
        action = action_from_dict({"claims": ["c1"]})
        assert isinstance(action, ParseFailure)

    def test_empty_dict(self) -> None:
        action = action_from_dict({})
        assert isinstance(action, ParseFailure)

    def test_int_action_value(self) -> None:
        action = action_from_dict({"action": 42})
        assert isinstance(action, ParseFailure)


class TestParseLlmAction:
    def test_plain_json(self) -> None:
        action = parse_llm_action(json.dumps({"action": "evaluate"}))
        assert action == EvaluateAction()

    def test_triple_backtick_json(self) -> None:
        text = f"```json\n{json.dumps({'action': 'verify', 'claims': ['c1']})}\n```"
        action = parse_llm_action(text)
        assert action == VerifyAction(claims=("c1",))

    def test_backtick_no_lang(self) -> None:
        text = f"```\n{json.dumps({'action': 'conclude'})}\n```"
        action = parse_llm_action(text)
        assert action == ConcludeAction()

    def test_invalid_json(self) -> None:
        with pytest.raises(MalformedResponseError):
            parse_llm_action("not json at all")

    def test_not_a_dict(self) -> None:
        with pytest.raises(MalformedResponseError):
            parse_llm_action(json.dumps(["list", "of", "items"]))

    def test_empty_string(self) -> None:
        with pytest.raises(MalformedResponseError):
            parse_llm_action("")
