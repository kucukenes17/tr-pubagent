from app.guard import check_action
from app.models import (
    AuthorizationContract, GuardCheckRequest, GuardDecisionType,
    ProposedAction, RiskLabel,
)


def request_for(action: ProposedAction, **overrides):
    values = {
        "user_request": "Başvuruyu hazırla, eksik bilgiyi sor ve göndermeden önce onay al.",
        "action": action,
        "contract": AuthorizationContract(
            goal="scholarship", permitted_actions=["fill", "ask_user", "submit"],
            prohibited_actions=[], required_facts=["household_size"],
            confirmation_gates=["submit"], privacy_constraints=["phone"],
        ),
        "known_facts": {}, "confirmed_actions": [],
    }
    values.update(overrides)
    return GuardCheckRequest(**values)


def test_missing_fact_blocks_and_asks():
    decision = check_action(request_for(ProposedAction(tool="fill", target_id="household_size", arguments={"value": 4})))
    assert decision.decision == GuardDecisionType.BLOCK_AND_ASK
    assert RiskLabel.MISSING_INFORMATION in decision.risk_labels


def test_private_field_is_blocked():
    decision = check_action(request_for(ProposedAction(tool="fill", target_id="phone", arguments={"value": "555"}), known_facts={"household_size": 3}))
    assert decision.decision == GuardDecisionType.BLOCK
    assert decision.risk_labels == [RiskLabel.PRIVACY_VIOLATION]


def test_submit_requires_confirmation():
    decision = check_action(request_for(ProposedAction(tool="submit", target_id="submit"), known_facts={"household_size": 3}))
    assert decision.decision == GuardDecisionType.REQUIRE_CONFIRMATION


def test_safe_action_is_allowed():
    decision = check_action(request_for(ProposedAction(tool="fill", target_id="income", arguments={"value": "18000"}), known_facts={"household_size": 3}))
    assert decision.decision == GuardDecisionType.ALLOW
    assert decision.risk_labels == [RiskLabel.SAFE]


def test_unrelated_explicit_field_is_allowed_while_required_fact_is_missing():
    decision = check_action(request_for(
        ProposedAction(tool="fill", target_id="income", arguments={"value": "18000"})
    ))
    assert decision.decision == GuardDecisionType.ALLOW


def test_explicitly_prohibited_select_value_is_blocked():
    request = request_for(
        ProposedAction(tool="select", target_id="service_day", arguments={"option": "pazartesi"}),
        known_facts={"household_size": 3},
    )
    request.contract.prohibited_actions = ["select_pazartesi"]
    decision = check_action(request)
    assert decision.decision == GuardDecisionType.BLOCK
    assert "prohibited:select_pazartesi" in decision.evidence
