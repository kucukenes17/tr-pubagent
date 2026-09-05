from app.guarded_policy import action_signature, enforced_action, public_action_error, terminal_action
from app.models import GuardDecision, GuardDecisionType, ProposedAction, RiskLabel


def observation(**updates):
    value = {
        "remaining_required_fields": [],
        "submission_required": False,
        "state": {"fields": {}, "confirmed_actions": [], "submitted": False},
        "candidate_actions": ["ask_user", "fill", "request_confirmation", "submit", "finish"],
        "action_targets": {
            "ask_user": ["household_size"], "fill": ["income"],
            "request_confirmation": ["submit"], "submit": ["submit"], "finish": ["task"],
        },
        "askable_facts": ["household_size"],
        "confirmation_actions": ["submit"],
    }
    value.update(updates)
    return value


def test_terminal_controller_finishes_ready_draft():
    assert terminal_action(observation()).tool == "finish"


def test_terminal_controller_requires_confirmation_before_submit():
    obs = observation(submission_required=True)
    assert terminal_action(obs).tool == "request_confirmation"
    obs["state"]["confirmed_actions"] = ["submit"]
    assert terminal_action(obs).tool == "submit"


def test_public_contract_rejects_unknown_target_and_repeat():
    obs = observation(remaining_required_fields=["income"])
    invalid = ProposedAction(tool="fill", target_id="phone", arguments={"value": "1"})
    assert "geçersiz target_id" in public_action_error(invalid, obs, set())
    valid = ProposedAction(tool="fill", target_id="income", arguments={"value": "18000"})
    assert "daha önce" in public_action_error(valid, obs, {action_signature(valid)})


def test_missing_fact_decision_becomes_ask_user():
    decision = GuardDecision(
        decision=GuardDecisionType.BLOCK_AND_ASK,
        risk_labels=[RiskLabel.MISSING_INFORMATION], confidence=1,
        missing_facts=["household_size"], explanation="Eksik bilgi", evidence=[],
    )
    action = enforced_action(decision, observation())
    assert action is not None
    assert action.tool == "ask_user"
    assert action.target_id == "household_size"
