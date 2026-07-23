"""Unit tests for the interview call model."""

import json

import pytest

from resume_roast.integrations.errors import MalformedResponseError
from resume_roast.services.interview.tool_calls import (
    AskFollowupCall,
    ConcludeCall,
    EvaluateCall,
    ParseFailure,
    UnknownTool,
    VerifyCall,
    parse_tool_call,
    tool_call_from_dict,
)


class TestToolCallFromDict:
    def test_verify(self) -> None:
        call = tool_call_from_dict({"tool": "verify", "claims": ["c1", "c2"]})
        assert call == VerifyCall(claims=("c1", "c2"))

    def test_verify_no_claims(self) -> None:
        call = tool_call_from_dict({"tool": "verify"})
        assert call == VerifyCall()

    def test_verify_null_claims_is_a_parse_failure(self) -> None:
        call = tool_call_from_dict({"tool": "verify", "claims": None})
        assert isinstance(call, ParseFailure)

    def test_verify_string_claims_is_a_parse_failure(self) -> None:
        call = tool_call_from_dict({"tool": "verify", "claims": "one claim"})
        assert isinstance(call, ParseFailure)

    def test_verify_non_string_claim_item_is_a_parse_failure(self) -> None:
        call = tool_call_from_dict({"tool": "verify", "claims": ["ok", 5]})
        assert isinstance(call, ParseFailure)

    def test_carries_the_thought_alongside_the_call(self) -> None:
        call = tool_call_from_dict({"tool": "evaluate", "thought": "the cycle is complete"})
        assert call == EvaluateCall(thought="the cycle is complete")

    def test_blank_thought_normalizes_to_none(self) -> None:
        call = tool_call_from_dict({"tool": "evaluate", "thought": "  "})
        assert call == EvaluateCall(thought=None)

    def test_evaluate(self) -> None:
        call = tool_call_from_dict({"tool": "evaluate"})
        assert call == EvaluateCall()

    def test_ask_followup(self) -> None:
        call = tool_call_from_dict({"tool": "ask_followup", "question": "Tell me more?"})
        assert call == AskFollowupCall(question="Tell me more?")

    def test_ask_followup_no_question(self) -> None:
        call = tool_call_from_dict({"tool": "ask_followup"})
        assert call == AskFollowupCall()

    def test_ask_followup_non_string_question_is_a_parse_failure(self) -> None:
        call = tool_call_from_dict({"tool": "ask_followup", "question": {"text": "?"}})
        assert isinstance(call, ParseFailure)

    def test_conclude(self) -> None:
        call = tool_call_from_dict({"tool": "conclude"})
        assert call == ConcludeCall()

    def test_ask_is_not_loop_vocabulary(self) -> None:
        call = tool_call_from_dict({"tool": "ask"})
        assert call == UnknownTool(name="ask")

    def test_plan_is_not_loop_vocabulary(self) -> None:
        call = tool_call_from_dict({"tool": "plan", "questions": ["q1", "q2"]})
        assert call == UnknownTool(name="plan")

    def test_unknown_action_keeps_its_name_for_feedback(self) -> None:
        call = tool_call_from_dict({"tool": "dance"})
        assert call == UnknownTool(name="dance")

    def test_missing_action(self) -> None:
        call = tool_call_from_dict({"claims": ["c1"]})
        assert isinstance(call, ParseFailure)

    def test_empty_dict(self) -> None:
        call = tool_call_from_dict({})
        assert isinstance(call, ParseFailure)

    def test_int_action_value(self) -> None:
        call = tool_call_from_dict({"action": 42})
        assert isinstance(call, ParseFailure)


class TestParseToolCall:
    def test_plain_json(self) -> None:
        call = parse_tool_call(json.dumps({"tool": "evaluate"}))
        assert call == EvaluateCall()

    def test_triple_backtick_json(self) -> None:
        text = f"```json\n{json.dumps({'tool': 'verify', 'claims': ['c1']})}\n```"
        call = parse_tool_call(text)
        assert call == VerifyCall(claims=("c1",))

    def test_backtick_no_lang(self) -> None:
        text = f"```\n{json.dumps({'tool': 'conclude'})}\n```"
        call = parse_tool_call(text)
        assert call == ConcludeCall()

    def test_invalid_json(self) -> None:
        with pytest.raises(MalformedResponseError):
            parse_tool_call("not json at all")

    def test_not_a_dict(self) -> None:
        with pytest.raises(MalformedResponseError):
            parse_tool_call(json.dumps(["list", "of", "items"]))

    def test_empty_string(self) -> None:
        with pytest.raises(MalformedResponseError):
            parse_tool_call("")
