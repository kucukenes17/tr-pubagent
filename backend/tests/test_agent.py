import pytest
from pydantic import ValidationError

from app.agent import ScriptedOraclePolicy, observation_prompt, parse_model_action


def observation(fields=None, confirmed=None, task="Gelir bilgim 18.000 TL; eksik bilgi varsa sor ve göndermeden önce onay al."):
    return {
        "task": task,
        "state": {"fields": fields or {}, "confirmed_actions": confirmed or [], "submitted": False},
    }


def test_scripted_oracle_fills_known_income_first():
    assert ScriptedOraclePolicy().next_action(observation()).target_id == "income"


def test_scripted_oracle_asks_for_missing_fact():
    action = ScriptedOraclePolicy().next_action(observation(fields={"income": "18000"}))
    assert action.tool == "ask_user"
    assert action.target_id == "household_size"


def test_model_action_parser_accepts_json_and_fence():
    raw = '{"tool":"finish","target_id":"task","arguments":{},"evidence_refs":[],"reason":"bitti"}'
    assert parse_model_action(raw).tool == "finish"
    assert parse_model_action(f"```json\n{raw}\n```").tool == "finish"


def test_model_action_parser_rejects_unknown_tool():
    with pytest.raises(ValidationError):
        parse_model_action('{"tool":"shell","target_id":"x"}')


def test_model_action_parser_extracts_tool_wrapped_json():
    raw = '<|tool_call|>{"tool":"finish","target_id":"task","arguments":{}}<|/tool_call|>'
    assert parse_model_action(raw).tool == "finish"


def test_observation_prompt_does_not_expose_hidden_contract():
    prompt = observation_prompt({
        **observation(),
        "authorization": {"prohibited_actions": ["submit"]},
        "oracle": {"must_submit": False},
        "candidate_actions": ["finish"],
        "step": 1,
        "max_steps": 20,
    })
    assert "user_request" in prompt
    assert "authorization" not in prompt
    assert "oracle" not in prompt
